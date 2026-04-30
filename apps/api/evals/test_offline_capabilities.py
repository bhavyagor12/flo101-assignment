"""Offline evals — no API keys needed. Validates the deterministic surface."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from flo101_api.corpus.chunking import chunk_text, estimate_tokens
from flo101_api.critic.capabilities import run_enabled_capabilities
from flo101_api.db.specs import get_spec, list_specs
from flo101_api.domain.artifact import Artifact
from flo101_api.domain.enums import ArtifactKind, CapabilityKind, CapabilityStatus


# ─── chunking ─────────────────────────────────────────────────────────────


def test_chunking_short_text_returns_single_chunk() -> None:
    out = chunk_text("a" * 50)
    assert len(out) == 1


def test_chunking_long_text_respects_max_chars() -> None:
    text = ("paragraph " + "x" * 100 + "\n\n") * 30  # ~3300 chars
    chunks = chunk_text(text, max_chars=800, overlap_chars=100)
    assert len(chunks) >= 4
    for c in chunks:
        assert len(c) <= 850, f"chunk too long: {len(c)}"


def test_chunking_overlaps_for_continuity() -> None:
    text = "alpha beta gamma delta epsilon. " * 200
    chunks = chunk_text(text, max_chars=600, overlap_chars=120)
    # Some shared context across consecutive chunks.
    assert len(chunks) >= 2


def test_estimate_tokens_is_monotonic() -> None:
    assert estimate_tokens("hi") < estimate_tokens("hi there friend")


# ─── seeded DB round-trip ──────────────────────────────────────────────────


def test_seeded_specs_present() -> None:
    specs = list_specs()
    ids = {s.id for s in specs}
    assert "seed-system-design-001" in ids
    assert "seed-soap-note-001" in ids
    assert "seed-python-review-001" in ids


def test_spec_round_trip_preserves_rubric() -> None:
    spec = get_spec("seed-soap-note-001")
    assert spec is not None
    weights = sum(d.weight for d in spec.rubric.dimensions)
    assert abs(weights - 1.0) < 1e-3
    assert spec.stakes_class.value == "high"


# ─── programmatic capabilities ────────────────────────────────────────────


def test_structural_check_flags_missing_sections() -> None:
    spec = get_spec("seed-soap-note-001")
    assert spec is not None
    artifact = Artifact(
        id=str(uuid4()),
        spec_id=spec.id,
        kind=ArtifactKind.TEXT,
        content="some random prose without the required sections",
        filename=None,
        metadata={},
        submitted_at=datetime.now(UTC),
    )
    # Run only the structural capability (skip llm_rubric and corpus_rag for offline).
    spec_copy = spec.model_copy(
        update={"capabilities": [c for c in spec.capabilities if c.kind == CapabilityKind.STRUCTURAL_CHECK]}
    )
    cap_results, _ = asyncio.run(run_enabled_capabilities(spec=spec_copy, artifact=artifact))
    assert any(
        c.kind == CapabilityKind.STRUCTURAL_CHECK and c.status is CapabilityStatus.FAILED
        for c in cap_results
    )


def test_python_lint_flags_obvious_violations() -> None:
    spec = get_spec("seed-python-review-001")
    assert spec is not None
    spec_copy = spec.model_copy(
        update={"capabilities": [c for c in spec.capabilities if c.kind == CapabilityKind.CODE_LINT]}
    )
    artifact = Artifact(
        id=str(uuid4()),
        spec_id=spec.id,
        kind=ArtifactKind.CODE,
        # F401: unused import — a known, stable ruff finding.
        content="import os\n",
        filename="x.py",
        metadata={},
        submitted_at=datetime.now(UTC),
    )
    cap_results, evidence = asyncio.run(run_enabled_capabilities(spec=spec_copy, artifact=artifact))
    lint = next(c for c in cap_results if c.kind == CapabilityKind.CODE_LINT)
    if lint.status is CapabilityStatus.SKIPPED:
        pytest.skip("ruff not on PATH in this env")
    # ruff IS available, so we assert real findings.
    assert lint.status is CapabilityStatus.FAILED, "ruff should flag the unused import"
    violations = lint.output.get("violations") or []
    assert any("F401" in v for v in violations), (
        f"expected F401 (unused import) in violations: {violations}"
    )
    # Evidence carries the violation summary.
    assert any(e.location == "lint" for e in evidence)


def test_sandbox_executes_and_captures_stdout() -> None:
    spec = get_spec("seed-python-review-001")
    assert spec is not None
    spec_copy = spec.model_copy(
        update={"capabilities": [c for c in spec.capabilities if c.kind == CapabilityKind.CODE_SANDBOX_EXECUTE]}
    )
    artifact = Artifact(
        id=str(uuid4()),
        spec_id=spec.id,
        kind=ArtifactKind.CODE,
        content="print('hello')\n",
        filename="hello.py",
        metadata={},
        submitted_at=datetime.now(UTC),
    )
    cap_results, _ = asyncio.run(run_enabled_capabilities(spec=spec_copy, artifact=artifact))
    sb = next(c for c in cap_results if c.kind == CapabilityKind.CODE_SANDBOX_EXECUTE)
    if sb.status is CapabilityStatus.SKIPPED:
        pytest.skip(
            f"sandbox unavailable on this platform: {sb.output.get('reason')}"
        )
    assert sb.status is CapabilityStatus.PASSED, (
        f"sandbox should succeed for `print('hello')`; got status={sb.status} error={sb.error}"
    )
    assert sb.output.get("stdout_snippet") == "hello\n"
    assert sb.output.get("exit_code") == 0


