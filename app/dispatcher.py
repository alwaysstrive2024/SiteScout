"""
SiteScout (灵嗅) – Search Dispatcher
Fans-out parallel `site:<domain> <query>` searches using asyncio.gather,
collects results per domain, and assembles the final SearchResponse.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List

import httpx

from app.adapters import BaseSearchAdapter
from app.schemas import DomainResults, SearchResponse, SearchResult

logger = logging.getLogger(__name__)


async def _search_single_domain(
    client: httpx.AsyncClient,
    adapter: BaseSearchAdapter,
    query: str,
    domain: str,
    n: int,
) -> DomainResults:
    """
    Run a single `site:<domain> <query>` search and return a DomainResults bucket.
    Any error is captured into DomainResults.error rather than propagated, so one
    failing domain doesn't take down the whole fanout.
    """
    site_query = f"site:{domain} {query}"
    logger.info("[%s] Searching domain=%r  query=%r", adapter.name, domain, site_query)

    try:
        results: List[SearchResult] = await adapter.search(client, site_query, n)
        return DomainResults(
            domain=domain,
            results=results[:n],
            total=len(results[:n]),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[%s] Failed domain=%r: %s", adapter.name, domain, exc)
        return DomainResults(
            domain=domain,
            results=[],
            total=0,
            error=str(exc),
        )


async def dispatch(
    adapter: BaseSearchAdapter,
    query: str,
    domains: List[str],
    raw_n: int,
) -> SearchResponse:
    """
    Fan-out parallel searches across all domains.
    Returns a fully-assembled SearchResponse.
    """
    async with httpx.AsyncClient() as client:
        tasks = [
            _search_single_domain(client, adapter, query, domain, raw_n)
            for domain in domains
        ]
        domain_results: List[DomainResults] = await asyncio.gather(*tasks)

    grand_total = sum(dr.total for dr in domain_results)

    return SearchResponse(
        query=query,
        provider=adapter.name,
        domains_queried=domains,
        results_per_domain=domain_results,
        grand_total=grand_total,
    )
