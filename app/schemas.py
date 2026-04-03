"""
SiteScout (灵嗅) – Pydantic Schemas
All request/response shapes live here; keep the rest of the app import-safe.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


# ── Request ───────────────────────────────────────────────────────────────────


class SearchRequest(BaseModel):
    """Payload sent to POST /search."""

    query: str = Field(..., min_length=1, max_length=512, description="The search query.")
    domains: List[str] = Field(
        ...,
        min_length=1,
        description="List of domains to target (e.g. ['reddit.com', 'github.com']).",
    )
    raw_n: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of raw results to fetch per domain.",
    )

    @field_validator("domains")
    @classmethod
    def strip_domains(cls, v: List[str]) -> List[str]:
        cleaned = [d.strip().lower().removeprefix("http://").removeprefix("https://").rstrip("/") for d in v]
        return [d for d in cleaned if d]


# ── Per-result ────────────────────────────────────────────────────────────────


class SearchResult(BaseModel):
    """A single search result entry returned by the provider."""

    title: str
    url: str
    snippet: str
    site: Optional[str] = None
    published_date: Optional[str] = None


# ── Per-domain bucket ─────────────────────────────────────────────────────────


class DomainResults(BaseModel):
    """All results scraped for a single domain."""

    domain: str
    results: List[SearchResult] = Field(default_factory=list)
    total: int = 0
    error: Optional[str] = None


# ── Top-level response ────────────────────────────────────────────────────────



class SearchResponse(BaseModel):
    """Full response returned by POST /search."""

    query: str
    provider: str
    domains_queried: List[str]
    results_per_domain: List[DomainResults]
    grand_total: int = 0


# ── LLM Refiner schemas ────────────────────────────────────────────────────────────────


class ResourceStatus(str):
    """Freeform status tag returned by the LLM."""


class RefinedResource(BaseModel):
    """A single resource entry extracted by the LLM."""

    resource_name: str = Field(..., description="Name or title of the resource.")
    source: str = Field(..., description="Domain / site the resource was found on.")
    direct_link: Optional[str] = Field(None, description="Direct download or access URL.")
    password: Optional[str] = Field(None, description="Access password if present, else null.")
    status: str = Field(
        ...,
        description=(
            "Verification status: '✅ Verified', '⚠️ Unverified', '❌ Dead link', "
            "or '🔒 Paywalled'."
        ),
    )


class RefineRequest(BaseModel):
    """Payload for POST /refine – search + LLM extraction in one shot."""

    query: str = Field(..., min_length=1, max_length=512)
    domains: List[str] = Field(..., min_length=1)
    raw_n: int = Field(default=10, ge=1, le=50, description="Results fetched per domain.")
    llm_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Top-K results (across all domains) passed to the LLM for refinement.",
    )
    model_choice: str = Field(
        default="deepseek-chat",
        description="LLM model to use: 'deepseek-chat' | 'gpt-4o' | 'gpt-4o-mini'.",
    )

    @field_validator("domains")
    @classmethod
    def strip_domains(cls, v: List[str]) -> List[str]:
        cleaned = [
            d.strip().lower().removeprefix("http://").removeprefix("https://").rstrip("/")
            for d in v
        ]
        return [d for d in cleaned if d]


class RefineResponse(BaseModel):
    """Full response from POST /refine."""

    query: str
    model_used: str
    llm_k: int
    refined: List[RefinedResource]
    raw_search: SearchResponse  # the full upstream search result is also returned
