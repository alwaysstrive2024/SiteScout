"""
SiteScout (灵嗅) – API Routes
All HTTP endpoints are registered here and then mounted in main.py.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.adapters import BaseSearchAdapter, build_adapter
from app.config import Settings, get_settings
from app.dispatcher import dispatch
from app.refiner import Refiner
from app.schemas import RefineRequest, RefineResponse, SearchRequest, SearchResponse

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Dependency: shared adapter instance ──────────────────────────────────────


def get_adapter(settings: Settings = Depends(get_settings)) -> BaseSearchAdapter:
    """
    FastAPI dependency that constructs (and caches per-request) the search adapter.
    The adapter is cheap to construct because it only stores the API key.
    """
    try:
        return build_adapter(
            provider=settings.search_provider,
            bocha_key=settings.bocha_api_key,
            tavily_key=settings.tavily_api_key,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Multi-site parallel search",
    description=(
        "Run a `site:<domain>` search for each provided domain in parallel. "
        "Returns raw results grouped by domain. "
        "`raw_n` controls how many results to fetch per domain (1–50)."
    ),
    tags=["Search"],
)
async def search(
    body: SearchRequest,
    adapter: BaseSearchAdapter = Depends(get_adapter),
) -> SearchResponse:
    logger.info(
        "POST /search query=%r domains=%s raw_n=%d provider=%s",
        body.query,
        body.domains,
        body.raw_n,
        adapter.name,
    )

    result = await dispatch(
        adapter=adapter,
        query=body.query,
        domains=body.domains,
        raw_n=body.raw_n,
    )

    return result


@router.get(
    "/health",
    summary="Health check",
    tags=["Ops"],
)
async def health(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "status": "ok",
        "provider": settings.search_provider,
        "supported_models": list(settings.supported_models),
    }


# ── /refine ────────────────────────────────────────────────────────────────────────


def get_refiner(body: RefineRequest, settings: Settings = Depends(get_settings)) -> Refiner:
    """
    Dependency: validates model_choice and builds a Refiner instance.
    Raised 400 if the requested model is not in the supported list.
    Raised 503 if the required API key is missing.
    """
    if body.model_choice not in settings.supported_models:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported model: {body.model_choice!r}. "
                f"Choose from: {list(settings.supported_models)}"
            ),
        )
    try:
        return Refiner(
            model_choice=body.model_choice,
            deepseek_key=settings.deepseek_api_key,
            openai_key=settings.openai_api_key,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.post(
    "/refine",
    response_model=RefineResponse,
    summary="Search + LLM Refinement (full pipeline)",
    description=(
        "Runs multi-site parallel search then passes the top `llm_k` results "
        "to an LLM (`model_choice`) for structured resource extraction. "
        "Returns both the AI-refined list and the raw search results."
    ),
    tags=["Refine"],
)
async def refine(
    body: RefineRequest,
    adapter: BaseSearchAdapter = Depends(get_adapter),
    refiner: Refiner = Depends(get_refiner),
) -> RefineResponse:
    logger.info(
        "POST /refine query=%r domains=%s raw_n=%d llm_k=%d model=%s",
        body.query,
        body.domains,
        body.raw_n,
        body.llm_k,
        body.model_choice,
    )

    # Step 1 – parallel site: search
    search_result = await dispatch(
        adapter=adapter,
        query=body.query,
        domains=body.domains,
        raw_n=body.raw_n,
    )

    # Step 2 – LLM extraction over top-K results
    refined = await refiner.refine(
        search=search_result,
        query=body.query,
        llm_k=body.llm_k,
    )

    return RefineResponse(
        query=body.query,
        model_used=body.model_choice,
        llm_k=body.llm_k,
        refined=refined,
        raw_search=search_result,
    )
