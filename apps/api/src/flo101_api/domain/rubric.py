"""Rubric primitives: anchored, validated, machine-evaluable."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, field_validator

from flo101_api.domain._base import DomainModel


class RubricAnchor(DomainModel):
    """A single score level on a dimension, with a concrete description."""

    score: Annotated[int, Field(ge=1, le=5, description="Score level, 1-5")]
    description: str = Field(min_length=1, description="What artifacts at this score look like")


class RubricDimension(DomainModel):
    """One axis of evaluation. Carries weight + anchors that pin scoring behavior."""

    id: str = Field(min_length=1, description="Stable snake_case identifier")
    title: str = Field(min_length=1, description="Human-readable dimension name")
    weight: Annotated[float, Field(gt=0.0, le=1.0)]
    anchors: list[RubricAnchor]

    @field_validator("anchors")
    @classmethod
    def _anchors_must_cover_1_to_5(cls, v: list[RubricAnchor]) -> list[RubricAnchor]:
        scores = sorted(a.score for a in v)
        if scores != [1, 2, 3, 4, 5]:
            raise ValueError("anchors must cover scores 1..5 exactly (one per level)")
        return v


class Rubric(DomainModel):
    """Collection of dimensions whose weights sum to 1.0."""

    dimensions: list[RubricDimension] = Field(min_length=2)

    @field_validator("dimensions")
    @classmethod
    def _dimensions_invariants(cls, v: list[RubricDimension]) -> list[RubricDimension]:
        ids = [d.id for d in v]
        if len(set(ids)) != len(ids):
            raise ValueError("dimension ids must be unique within a rubric")
        total = sum(d.weight for d in v)
        if abs(total - 1.0) > 1e-3:
            raise ValueError(f"dimension weights must sum to 1.0 (got {total:.4f})")
        return v
