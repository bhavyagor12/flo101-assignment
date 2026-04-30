"""LLM stack factories. Cached singletons; tests monkey-patch import sites."""

from __future__ import annotations

from functools import lru_cache

from flo101_api.config import get_settings
from flo101_api.llm.gateway import LLMGateway
from flo101_api.llm.openrouter_gateway import OpenRouterGateway
from flo101_api.llm.tracing import (
    LangSmithTracer,
    NoOpTracer,
    Tracer,
    configure_langsmith,
)


@lru_cache(maxsize=1)
def build_tracer() -> Tracer:
    s = get_settings()
    configure_langsmith(s)
    if s.langsmith_tracing and s.langsmith_api_key:
        return LangSmithTracer(project=s.langsmith_project)
    return NoOpTracer()


@lru_cache(maxsize=1)
def build_gateway() -> LLMGateway:
    s = get_settings()
    tracer = build_tracer()
    return OpenRouterGateway(s, tracer)
