"""Evaluation: the Critic's output for a (spec, artifact) pair."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import Field

from flo101_api.domain._base import DomainModel
from flo101_api.domain.enums import (
    CapabilityKind,
    CapabilityStatus,
    EvaluationStatus,
    EvidenceSource,
    GapSeverity,
    SafetyDisposition,
)


class EvidenceItem(DomainModel):
    """A piece of evidence cited for a score, with provenance."""

    source: EvidenceSource
    content: str = Field(min_length=1, max_length=4_000)
    location: str | None = Field(
        default=None, description="line range / chunk id / file path"
    )
    confidence: Annotated[float, Field(ge=0.0, le=1.0)] = 1.0


class DimensionScore(DomainModel):
    """A score on one rubric dimension, with feedback and evidence."""

    dimension_id: str
    score: Annotated[int, Field(ge=1, le=5)]
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    feedback: str = Field(min_length=1)
    evidence: list[EvidenceItem]


class Gap(DomainModel):
    """Something the artifact is missing relative to the rubric."""

    description: str = Field(min_length=1)
    severity: GapSeverity


class NextStep(DomainModel):
    """The single highest-leverage next action for the learner."""

    title: str = Field(min_length=1, max_length=200)
    rationale: str = Field(min_length=1)
    estimated_minutes: int = Field(gt=0, le=600)


class CapabilityResult(DomainModel):
    """Outcome of running one capability node during evaluation."""

    kind: CapabilityKind
    status: CapabilityStatus
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    duration_ms: int = Field(ge=0)


class Evaluation(DomainModel):
    """Top-level Critic output. `overall_score` is None when disposition forbids scoring."""

    id: str
    spec_id: str
    artifact_id: str
    status: EvaluationStatus
    safety_disposition: SafetyDisposition
    overall_score: float | None = Field(default=None, ge=0.0, le=5.0)
    dimension_scores: list[DimensionScore]
    gaps: list[Gap]
    next_step: NextStep | None
    refused_reason: str | None = None
    capability_results: list[CapabilityResult]
    trace_id: str | None = Field(
        default=None, description="LangSmith trace id for the evaluation run"
    )
    created_at: datetime
    completed_at: datetime | None
