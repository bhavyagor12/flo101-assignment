"""Application configuration. Single source of truth for env-driven settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings, loaded from env at startup."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── LLM access ──────────────────────────────────────────
    # Single key: chat and embeddings both go through OpenRouter.
    # Defaults to "" so the service can boot without it; the LLM gateway
    # raises a typed error when actually called with no key.
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # ─── Model routing ───────────────────────────────────────
    model_synthesizer: str = "anthropic/claude-opus-4-7"
    model_rubric_critique: str = "anthropic/claude-sonnet-4-6"
    model_safety_guard: str = "anthropic/claude-haiku-4-5"
    model_capability_router: str = "anthropic/claude-haiku-4-5"
    embedding_model: str = "openai/text-embedding-3-small"

    # ─── Observability ───────────────────────────────────────
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "flo101-critic"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    # ─── App config ──────────────────────────────────────────
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    sqlite_path: Path = Path("/data/flo101.sqlite")
    corpus_dir: Path = Path("/corpora")
    sandbox_timeout_seconds: int = 5
    sandbox_memory_mb: int = 256
    # Wall-clock budget for the entire critic graph run. After this elapses,
    # the API returns a structured FAILED Evaluation rather than hanging.
    evaluation_wallclock_seconds: int = 90

    # ─── HTTP ────────────────────────────────────────────────
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor. Reads env exactly once per process."""
    return Settings()  # type: ignore[call-arg]
