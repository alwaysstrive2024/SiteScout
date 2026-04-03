"""
SiteScout (灵嗅) – Configuration & Environment Loader
Reads settings from a .env file (or real environment variables).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # ── Search providers ──────────────────────────────────────────────────────
    bocha_api_key: str = ""
    tavily_api_key: str = ""
    search_provider: str = "bocha"  # "bocha" | "tavily"

    # ── LLM ───────────────────────────────────────────────────────────────────
    deepseek_api_key: str = ""
    openai_api_key: str = ""

    # Canonical choices exposed to the /refine endpoint
    supported_models: tuple[str, ...] = ("deepseek-chat", "gpt-4o", "gpt-4o-mini")

    # ── Server ────────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton – import and call this everywhere you need config."""
    return Settings()
