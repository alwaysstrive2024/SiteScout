"""
SiteScout (灵嗅) – LLM Refiner
Takes the top-K search results, cleans noise, builds a structured prompt,
and calls DeepSeek or OpenAI to extract actionable resource intelligence.

Supported models
────────────────
  deepseek-chat  →  DeepSeek API (OpenAI-compatible, base_url swap)
  gpt-4o         →  OpenAI
  gpt-4o-mini    →  OpenAI (faster / cheaper)
"""

from __future__ import annotations

import json
import logging
import re
from typing import List

from openai import AsyncOpenAI

from app.schemas import DomainResults, RefinedResource, SearchResponse

logger = logging.getLogger(__name__)

# ── Provider configs ──────────────────────────────────────────────────────────

_OPENAI_BASE   = "https://api.openai.com/v1"
_DEEPSEEK_BASE = "https://api.deepseek.com"

_MODEL_PROVIDER: dict[str, str] = {
    "deepseek-chat": "deepseek",
    "gpt-4o":        "openai",
    "gpt-4o-mini":   "openai",
}

# ── Text cleaning ─────────────────────────────────────────────────────────────

_HTML_TAG_RE    = re.compile(r"<[^>]+>")
_WHITESPACE_RE  = re.compile(r"\s+")
_JUNK_PHRASES   = re.compile(
    r"(join .{0,30} for (link|download)|reply to see|查看回复|加群领取|关注获取)",
    flags=re.IGNORECASE,
)


def _clean_text(raw: str) -> str:
    """Strip HTML tags, collapse whitespace, and drop known junk phrases."""
    text = _HTML_TAG_RE.sub(" ", raw)
    text = _JUNK_PHRASES.sub("[REDACTED_BAIT]", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


# ── Prompt builder ────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are SiteScout Refiner, a precision information-extraction agent.
You will receive a list of numbered search results (title + url + snippet).
Your task is to extract structured resource intelligence from them.

Return ONLY a valid JSON array. Each element must follow this exact schema:
{
  "resource_name": "<concise name of the resource>",
  "source":        "<domain the resource is from>",
  "direct_link":   "<direct URL if found, else null>",
  "password":      "<access password if mentioned, else null>",
  "status":        "<one of: ✅ Verified | ⚠️ Unverified | ❌ Dead link | 🔒 Paywalled>"
}

Rules:
- Output ONLY the JSON array, no markdown fences, no explanations.
- If several results describe the same resource, merge them into one entry.
- Ignore results that are clearly ads, bait ("reply to see"), or off-topic.
- Prefer direct links over landing pages when both are present.
- If you cannot determine a field, use null (not the string "null").
"""


def _build_user_message(query: str, candidates: list[dict]) -> str:
    lines = [f"Search query: {query!r}\n", "Results:"]
    for i, c in enumerate(candidates, 1):
        lines.append(
            f"\n[{i}] Title: {c['title']}\n"
            f"    URL:   {c['url']}\n"
            f"    Text:  {c['snippet']}"
        )
    return "\n".join(lines)


# ── Top-K selector ────────────────────────────────────────────────────────────

def _top_k_results(search: SearchResponse, k: int) -> list[dict]:
    """
    Flatten all domain results, deduplicate by URL, and return the top-K
    after cleaning each snippet.  Results from domains with errors are skipped.
    """
    seen_urls: set[str] = set()
    candidates: list[dict] = []

    for dr in search.results_per_domain:
        if dr.error:
            continue
        for r in dr.results:
            if r.url in seen_urls:
                continue
            seen_urls.add(r.url)
            candidates.append(
                {
                    "title":   _clean_text(r.title),
                    "url":     r.url,
                    "snippet": _clean_text(r.snippet),
                    "domain":  dr.domain,
                }
            )
            if len(candidates) >= k:
                break
        if len(candidates) >= k:
            break

    return candidates[:k]


# ── Refiner class ─────────────────────────────────────────────────────────────


class Refiner:
    """
    Orchestrates LLM-based extraction from a SearchResponse.

    Usage
    -----
        refiner = Refiner(model_choice="deepseek-chat", deepseek_key="sk-...")
        refined  = await refiner.refine(search_response, query="...", llm_k=5)
    """

    def __init__(
        self,
        model_choice: str,
        deepseek_key: str = "",
        openai_key: str   = "",
    ) -> None:
        provider = _MODEL_PROVIDER.get(model_choice)
        if provider is None:
            raise ValueError(
                f"Unsupported model: {model_choice!r}. "
                f"Choose from: {list(_MODEL_PROVIDER)}"
            )

        self.model = model_choice

        if provider == "deepseek":
            if not deepseek_key:
                raise ValueError("Refiner: DEEPSEEK_API_KEY is not set.")
            self._client = AsyncOpenAI(
                api_key=deepseek_key,
                base_url=_DEEPSEEK_BASE,
            )
        else:
            if not openai_key:
                raise ValueError("Refiner: OPENAI_API_KEY is not set.")
            self._client = AsyncOpenAI(
                api_key=openai_key,
                base_url=_OPENAI_BASE,
            )

    async def refine(
        self,
        search: SearchResponse,
        query: str,
        llm_k: int,
    ) -> List[RefinedResource]:
        """
        Select the top-K results, call the LLM, and parse the JSON response
        into a list of validated RefinedResource objects.
        """
        candidates = _top_k_results(search, llm_k)
        if not candidates:
            logger.warning("Refiner: no viable candidates after filtering – returning empty list.")
            return []

        user_msg = _build_user_message(query, candidates)

        logger.info(
            "Refiner calling model=%s with k=%d candidates", self.model, len(candidates)
        )

        completion = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.1,   # low temperature → deterministic structured output
            max_tokens=2048,
            response_format={"type": "json_object"} if "gpt" in self.model else None,
        )

        raw_output = completion.choices[0].message.content or ""
        logger.debug("Refiner raw LLM output: %s", raw_output[:500])

        return self._parse_response(raw_output)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _parse_response(self, raw: str) -> List[RefinedResource]:
        """
        Robustly parse LLM output that should be a JSON array.
        Handles cases where the model wraps the array in an object key
        or adds markdown fences.
        """
        # Strip markdown fences if present
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error("Refiner: JSON parse failed – %s\nRaw: %s", exc, raw[:300])
            return []

        # Unwrap {"results": [...]} or {"resources": [...]} style
        if isinstance(parsed, dict):
            for val in parsed.values():
                if isinstance(val, list):
                    parsed = val
                    break
            else:
                logger.warning("Refiner: LLM returned a dict with no list value.")
                return []

        if not isinstance(parsed, list):
            logger.warning("Refiner: expected a JSON array, got %s.", type(parsed).__name__)
            return []

        resources: List[RefinedResource] = []
        for item in parsed:
            try:
                resources.append(RefinedResource(**item))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Refiner: skipping malformed entry %s – %s", item, exc)

        return resources
