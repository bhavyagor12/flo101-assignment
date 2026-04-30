"""Synthesizer-internal types. LLM emits a Draft; the agent fills system fields."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from flo101_api.domain._base import DomainModel
from flo101_api.domain.enums import ArtifactKind, StakesClass
from flo101_api.domain.rubric import Rubric
from flo101_api.domain.spec import CapabilityWiring


class SkillSpecDraft(DomainModel):
    # The synthesizer LLM produces this. id / timestamps / has_corpus etc.
    # are filled by `synthesize_skill_spec` after self-critique.
    goal_text: str = Field(min_length=4)
    audience_hint: str | None = None
    artifact_kind: ArtifactKind
    stakes_class: StakesClass
    rubric: Rubric
    capabilities: list[CapabilityWiring] = Field(min_length=1)
    challenge_templates: list[str] = Field(default_factory=list)
    pathway_archetypes: list[str] = Field(default_factory=list)
    exemplar_prompts: dict[str, str] = Field(default_factory=dict)
    meta_critique_score: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0


class SynthesisCritique(DomainModel):
    coherence: Annotated[float, Field(ge=0.0, le=1.0)]
    anchoring: Annotated[float, Field(ge=0.0, le=1.0)]
    actionability: Annotated[float, Field(ge=0.0, le=1.0)]
    calibration: Annotated[float, Field(ge=0.0, le=1.0)]
    meta_critique_score: Annotated[float, Field(ge=0.0, le=1.0)]
    accepted: bool
    feedback: str = Field(min_length=1)
