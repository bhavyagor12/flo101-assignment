"""Liveness + service identity."""

from __future__ import annotations

from fastapi import APIRouter

from flo101_api import __version__

router = APIRouter(tags=["meta"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@router.get("/")
def root() -> dict[str, str]:
    return {"service": "flo101-critic", "version": __version__, "docs": "/docs"}
