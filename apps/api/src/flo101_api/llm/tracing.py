"""Tracer protocol with a LangSmith adapter and a NoOp.

LangSmith auto-traces `@traceable`-decorated functions when env vars are
set; `Tracer.span()` is for non-LLM custom spans (corpus retrieval,
sandbox runs). A Langfuse adapter would implement the same protocol.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import AbstractContextManager, contextmanager
from typing import Any, Protocol

from flo101_api.config import Settings
from flo101_api.observability import get_logger


class Tracer(Protocol):
    def span(self, name: str, **metadata: Any) -> AbstractContextManager[None]: ...


class NoOpTracer:
    @contextmanager
    def span(self, name: str, **metadata: Any) -> Generator[None]:
        _ = (name, metadata)
        yield


class LangSmithTracer:
    def __init__(self, project: str) -> None:
        self._project = project
        self._log = get_logger("flo101_api.llm.tracing")

    @contextmanager
    def span(self, name: str, **metadata: Any) -> Generator[None]:
        try:
            from langsmith.run_trees import RunTree
        except ImportError:
            self._log.warning("langsmith.tracing.import_failed", name=name)
            yield
            return

        run = RunTree(
            name=name,
            run_type="chain",
            project_name=self._project,
            inputs=dict(metadata),
        )
        try:
            run.post()
        except Exception as exc:
            # Tracing failures must not propagate to business logic.
            self._log.warning("langsmith.span.post_failed", name=name, error=str(exc))
            yield
            return

        try:
            yield
        except Exception as exc:
            try:
                run.end(error=str(exc))
                run.patch()
            except Exception:
                pass
            raise
        else:
            try:
                run.end(outputs={"ok": True})
                run.patch()
            except Exception as exc:
                self._log.warning("langsmith.span.patch_failed", name=name, error=str(exc))


def configure_langsmith(settings: Settings) -> None:
    """Push LangSmith env vars into the process. Call once at startup."""
    if settings.langsmith_tracing and settings.langsmith_api_key:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
        os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
    else:
        os.environ.setdefault("LANGSMITH_TRACING", "false")
