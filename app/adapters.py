"""
SiteScout (灵嗅) – Search Provider Adapters
Each adapter implements the same async interface so the dispatcher is provider-agnostic.

Interface contract
──────────────────
async def search(client: httpx.AsyncClient, query: str, n: int) -> list[SearchResult]

New providers: subclass BaseAdapter and register in PROVIDER_MAP.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List

import httpx

from app.schemas import SearchResult

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Base
# ─────────────────────────────────────────────────────────────────────────────


class BaseSearchAdapter(ABC):
    """Abstract base – all providers must implement `search`."""

    name: str = "base"

    @abstractmethod
    async def search(
        self,
        client: httpx.AsyncClient,
        query: str,
        n: int,
    ) -> List[SearchResult]:
        """Execute a single search and return a list of results."""
        ...


# ─────────────────────────────────────────────────────────────────────────────
# Bocha AI
# ─────────────────────────────────────────────────────────────────────────────


class BochaAdapter(BaseSearchAdapter):
    """
    Bocha AI Web-Search adapter.
    Docs: https://open.bochaai.com/
    Endpoint: POST https://api.bochaai.com/v1/web-search
    """

    name = "bocha"
    _BASE_URL = "https://api.bochaai.com/v1/web-search"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("BochaAdapter: BOCHA_API_KEY is not set.")
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def search(
        self,
        client: httpx.AsyncClient,
        query: str,
        n: int,
    ) -> List[SearchResult]:
        payload = {
            "query": query,
            "count": min(n, 50),   # Bocha cap
            "freshness": "noLimit",
            "summary": False,      # raw results only; LLM refine happens later
        }

        try:
            response = await client.post(
                self._BASE_URL,
                json=payload,
                headers=self._headers,
                timeout=20.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("Bocha HTTP error %s for query=%r: %s", exc.response.status_code, query, exc)
            raise
        except httpx.RequestError as exc:
            logger.error("Bocha network error for query=%r: %s", query, exc)
            raise

        data = response.json()
        raw_results: list[dict] = (
            data.get("data", {}).get("webPages", {}).get("value", [])
        )

        return [
            SearchResult(
                title=r.get("name", ""),
                url=r.get("url", ""),
                snippet=r.get("snippet", ""),
                site=r.get("siteName", ""),
                published_date=r.get("dateLastCrawled"),
            )
            for r in raw_results
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Tavily
# ─────────────────────────────────────────────────────────────────────────────


class TavilyAdapter(BaseSearchAdapter):
    """
    Tavily Search adapter.
    Docs: https://docs.tavily.com/
    Endpoint: POST https://api.tavily.com/search
    """

    name = "tavily"
    _BASE_URL = "https://api.tavily.com/search"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("TavilyAdapter: TAVILY_API_KEY is not set.")
        self._api_key = api_key

    async def search(
        self,
        client: httpx.AsyncClient,
        query: str,
        n: int,
    ) -> List[SearchResult]:
        payload = {
            "api_key": self._api_key,
            "query": query,
            "max_results": min(n, 20),  # Tavily cap per request
            "search_depth": "basic",
            "include_answer": False,
            "include_raw_content": False,
        }

        try:
            response = await client.post(
                self._BASE_URL,
                json=payload,
                timeout=20.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("Tavily HTTP error %s for query=%r: %s", exc.response.status_code, query, exc)
            raise
        except httpx.RequestError as exc:
            logger.error("Tavily network error for query=%r: %s", query, exc)
            raise

        data = response.json()
        raw_results: list[dict] = data.get("results", [])

        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("content", ""),
                site=None,
                published_date=r.get("published_date"),
            )
            for r in raw_results
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────


def build_adapter(provider: str, bocha_key: str = "", tavily_key: str = "") -> BaseSearchAdapter:
    """Instantiate the correct adapter from the provider name."""
    match provider.lower():
        case "bocha":
            return BochaAdapter(api_key=bocha_key)
        case "tavily":
            return TavilyAdapter(api_key=tavily_key)
        case _:
            raise ValueError(f"Unknown search provider: {provider!r}. Choose 'bocha' or 'tavily'.")
