"""
SiteScout (灵嗅) – FastAPI Application Factory
"""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routes import router

# ── Logging setup ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── App factory ───────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    app = FastAPI(
        title="SiteScout 灵嗅",
        description=(
            "Precision multi-site search engine. "
            "Fan-out parallel `site:` queries across a custom domain pool "
            "and return structured results ready for LLM refinement."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],   # tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request timing middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        logger.info(
            "%s %s → %d  (%.0f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    # ── Global error handler ──────────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Check server logs."},
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(router)

    return app


app = create_app()
