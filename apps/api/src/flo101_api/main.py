"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from flo101_api import __version__
from flo101_api.api.meta import router as meta_router
from flo101_api.api.routes import router as api_router
from flo101_api.config import get_settings
from flo101_api.llm import build_tracer
from flo101_api.observability import configure_logging, get_logger


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    configure_logging(level=settings.log_level)
    # Warm the tracer so LangSmith env is exported before any @traceable runs.
    _ = settings
    build_tracer()
    log = get_logger("flo101_api.main")
    log.info(
        "service.starting",
        version=__version__,
        langsmith_tracing=settings.langsmith_tracing,
    )
    yield
    log.info("service.stopping")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="flo101 Critic Agent",
        version=__version__,
        description="Proof-of-Work Evaluator — Track C",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(meta_router)
    app.include_router(api_router)
    return app


app = create_app()
