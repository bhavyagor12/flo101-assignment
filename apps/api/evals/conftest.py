"""Eval-harness fixtures.

Tests fall into two buckets:
  - **offline**: deterministic, no API keys needed (chunking, DB round-trips,
    programmatic capabilities). Always run.
  - **online**: LLM-using (synthesizer, critic, safety). Skipped when
    OPENROUTER_API_KEY is unset, so the harness is safe to run on every
    commit but only does the cheap layer in CI without secrets.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from flo101_api.config import get_settings


def _has_chat_key() -> bool:
    return bool(os.environ.get("OPENROUTER_API_KEY"))


def _has_embed_key() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


needs_llm = pytest.mark.skipif(
    not _has_chat_key(),
    reason="OPENROUTER_API_KEY unset — skipping online eval",
)

needs_embed = pytest.mark.skipif(
    not _has_embed_key(),
    reason="OPENAI_API_KEY unset — skipping embedding-dependent eval",
)


@pytest.fixture(scope="session", autouse=True)
def _isolated_sqlite() -> None:  # pyright: ignore[reportUnusedFunction]
    """Each eval session uses a fresh tmp SQLite file; never touches /data."""
    if "SQLITE_PATH" not in os.environ:
        tmp = Path(tempfile.mkdtemp(prefix="flo101-eval-")) / "evals.sqlite"
        os.environ["SQLITE_PATH"] = str(tmp)
    # Force settings cache reload.
    get_settings.cache_clear()


@pytest.fixture(scope="session", autouse=True)
def _seed_specs(_isolated_sqlite: None) -> None:  # pyright: ignore[reportUnusedFunction]
    """Insert the three demo specs so calibration tests have rubrics to evaluate."""
    from flo101_api.scripts.seed import main as seed_main

    seed_main()
