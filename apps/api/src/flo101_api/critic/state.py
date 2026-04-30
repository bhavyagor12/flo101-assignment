"""LangGraph state. Inputs are required at invocation; node outputs are NotRequired."""

from __future__ import annotations

from typing import NotRequired, TypedDict

from flo101_api.db.corpus import ChunkHit
from flo101_api.domain.artifact import Artifact
from flo101_api.domain.enums import SafetyDisposition
from flo101_api.domain.evaluation import (
    CapabilityResult,
    DimensionScore,
    Evaluation,
    EvidenceItem,
    Gap,
    NextStep,
)
from flo101_api.domain.spec import SkillSpec


class CriticState(TypedDict):
    # Required at graph invocation
    spec_id: str
    artifact: Artifact

    # Loaded by nodes
    spec: NotRequired[SkillSpec]
    safety_input_allow: NotRequired[bool]
    safety_input_reason: NotRequired[str]
    capability_results: NotRequired[list[CapabilityResult]]
    extra_evidence: NotRequired[list[EvidenceItem]]
    corpus_hits: NotRequired[list[ChunkHit]]

    # Critique outputs
    dimension_scores: NotRequired[list[DimensionScore]]
    gaps: NotRequired[list[Gap]]
    next_step: NotRequired[NextStep | None]
    overall_score: NotRequired[float | None]
    safety_disposition: NotRequired[SafetyDisposition]
    refused_reason: NotRequired[str | None]

    # Tracing
    trace_id: NotRequired[str | None]

    # Final
    evaluation: NotRequired[Evaluation]
