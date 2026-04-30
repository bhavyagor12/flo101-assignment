"""Artifact: the learner's submission to be evaluated."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from flo101_api.domain._base import DomainModel
from flo101_api.domain.enums import ArtifactKind


class Artifact(DomainModel):
    """A submitted artifact (text, code, sql, etc.) tied to a SkillSpec."""

    id: str
    spec_id: str
    kind: ArtifactKind
    content: str = Field(min_length=1, max_length=200_000)
    filename: str | None = Field(default=None, max_length=255)
    metadata: dict[str, str] = Field(default_factory=dict)
    submitted_at: datetime


class ArtifactSubmission(DomainModel):
    """Inbound payload for evaluation — system fills id and timestamps."""

    kind: ArtifactKind
    content: str = Field(min_length=1, max_length=200_000)
    filename: str | None = Field(default=None, max_length=255)
    metadata: dict[str, str] = Field(default_factory=dict)
