"""Test-suite fixtures.

- Isolated SQLite path per session (no touching /data).
- Seeded specs available to every test.
- `fake_gateway` fixture monkey-patches every `build_gateway` import site so
  agents pick up the stub without thread-the-needle parameter passing.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Iterator

import pytest

from flo101_api.config import get_settings
from tests.fake_gateway import FakeGateway

_GATEWAY_IMPORT_SITES = (
    "flo101_api.critic.nodes",
    "flo101_api.synthesizer.agent",
    "flo101_api.corpus.ingest",
    "flo101_api.corpus.retrieve",
)


@pytest.fixture(scope="session", autouse=True)
def _isolated_sqlite() -> None:  # pyright: ignore[reportUnusedFunction]
    if "SQLITE_PATH" not in os.environ:
        tmp = Path(tempfile.mkdtemp(prefix="flo101-tests-")) / "tests.sqlite"
        os.environ["SQLITE_PATH"] = str(tmp)
    # Make the LLM keys present so config loads cleanly; the FakeGateway
    # is what actually services calls during tests.
    os.environ.setdefault("OPENROUTER_API_KEY", "test-fake")
    os.environ.setdefault("OPENAI_API_KEY", "test-fake")
    get_settings.cache_clear()


@pytest.fixture(scope="session", autouse=True)
def _seed(_isolated_sqlite: None) -> None:  # pyright: ignore[reportUnusedFunction]
    from flo101_api.scripts.seed import main as seed_main

    seed_main()


@pytest.fixture
def fake_gateway(monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeGateway]:
    """Provides a FakeGateway and patches every import site to use it."""
    fake = FakeGateway()
    for site in _GATEWAY_IMPORT_SITES:
        monkeypatch.setattr(f"{site}.build_gateway", lambda fake=fake: fake)
    yield fake
