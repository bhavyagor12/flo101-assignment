"""Pydantic response shapes for the Critic's LLM calls."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from flo101_api.domain._base import DomainModel
from flo101_api.domain.enums import SafetyDisposition
from flo101_api.domain.evaluation import DimensionScore, Gap, NextStep


class SafetyVerdict(DomainModel):
    allow: bool
    reason: str = Field(min_length=1)


class CritiqueResult(DomainModel):
    dimension_scores: list[DimensionScore] = Field(min_length=1)
    gaps: list[Gap] = Field(default_factory=list)
    next_step: NextStep | None = None
    overall_score: Annotated[float | None, Field(ge=0.0, le=5.0)] = None


class DispositionResult(DomainModel):
    disposition: SafetyDisposition
    rationale: str = Field(min_length=1)
