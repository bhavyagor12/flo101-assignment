"""SkillSpec: the structured description of *what* good looks like for a skill.

Synthesized from a natural-language goal (and optional reference corpus), then cached.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import Field

from flo101_api.domain._base import DomainModel
from flo101_api.domain.enums import ArtifactKind, CapabilityKind, StakesClass
from flo101_api.domain.rubric import Rubric


class CapabilityWiring(DomainModel):
    """Which capabilities the Critic should run for this skill, and with what config."""

    kind: CapabilityKind
    config: dict[str, Any] = Field(default_factory=dict)


class SkillSpec(DomainModel):
    """Generated, versioned, persistable description of a skill."""

    id: str = Field(description="UUID v4 as string")
    goal_text: str = Field(min_length=4)
    audience_hint: str | None = Field(
        default=None, description="e.g. 'junior PM', 'medical resident', 'mid-level engineer'"
    )
    artifact_kind: ArtifactKind
    stakes_class: StakesClass
    rubric: Rubric
    capabilities: list[CapabilityWiring] = Field(min_length=1)
    challenge_templates: list[str] = Field(
        default_factory=list,
        description="Natural-language templates the Curator instantiates",
    )
    pathway_archetypes: list[str] = Field(
        default_factory=list,
        description="Step shapes the Composer composes (e.g. 'reproduce_from_spec')",
    )
    exemplar_prompts: dict[str, str] = Field(
        default_factory=dict,
        description="Keys: 'great' | 'medium' | 'weak' — prompts that elicit each",
    )
    meta_critique_score: Annotated[
        float,
        Field(ge=0.0, le=1.0, description="Synthesizer's self-grade on this spec"),
    ]
    has_corpus: bool = False
    version: int = Field(default=1, ge=1)
    authored_by: str | None = None
    created_at: datetime
    updated_at: datetime


class SynthesizeRequest(DomainModel):
    """Input to the Synthesizer. Corpus is uploaded separately after creation."""

    goal_text: str = Field(min_length=4, max_length=2000)
    audience_hint: str | None = Field(default=None, max_length=400)
    output_goal: str | None = Field(
        default=None,
        max_length=400,
        description="Optional: the concrete deliverable the learner aims to produce",
    )
    time_budget_minutes: int | None = Field(default=None, gt=0, le=10_000)
