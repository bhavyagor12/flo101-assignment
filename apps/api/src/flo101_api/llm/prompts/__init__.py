"""Prompt constants + render functions.

Conventions: uppercase `_V<n>`-suffixed constants for system prompts;
`render_<name>_user(...)` for user-prompt templates. Bumping a prompt
means adding `_V2`, not mutating `_V1`. The registry at the bottom is
metadata only — used in logs/traces, not at runtime.
"""

from __future__ import annotations

from flo101_api.llm.prompts.rubric_critique import (
    RUBRIC_CRITIQUE_SYSTEM_V1,
    render_rubric_critique_user,
)
from flo101_api.llm.prompts.safety_disposition import (
    SAFETY_DISPOSITION_SYSTEM_V1,
    render_safety_disposition_user,
)
from flo101_api.llm.prompts.safety_input import (
    SAFETY_INPUT_SYSTEM_V1,
    render_safety_input_user,
)
from flo101_api.llm.prompts.synthesizer import (
    SYNTHESIZER_SELF_CRITIQUE_SYSTEM_V1,
    SYNTHESIZER_SYSTEM_V1,
    render_synthesizer_self_critique_user,
    render_synthesizer_user,
)


class PromptInfo:
    __slots__ = ("name", "version", "model_hint", "purpose")

    def __init__(self, *, name: str, version: str, model_hint: str, purpose: str) -> None:
        self.name = name
        self.version = version
        self.model_hint = model_hint
        self.purpose = purpose


PROMPT_REGISTRY: dict[str, PromptInfo] = {
    "synthesizer.system": PromptInfo(
        name="synthesizer.system",
        version="v1",
        model_hint="opus",
        purpose="Generate a SkillSpec from a natural-language goal (+ optional corpus).",
    ),
    "synthesizer.self_critique.system": PromptInfo(
        name="synthesizer.self_critique.system",
        version="v1",
        model_hint="opus",
        purpose="Score a freshly-generated SkillSpec for coherence, anchoring, actionability.",
    ),
    "rubric_critique.system": PromptInfo(
        name="rubric_critique.system",
        version="v1",
        model_hint="sonnet",
        purpose="Score an artifact against a rubric, citing evidence + identifying gaps.",
    ),
    "safety_input.system": PromptInfo(
        name="safety_input.system",
        version="v1",
        model_hint="haiku",
        purpose="Classify whether to refuse or proceed on a goal/artifact.",
    ),
    "safety_disposition.system": PromptInfo(
        name="safety_disposition.system",
        version="v1",
        model_hint="haiku",
        purpose="Decide self-evaluated / human-review / expert-required for an evaluation.",
    ),
}


__all__ = [
    "PROMPT_REGISTRY",
    "PromptInfo",
    "RUBRIC_CRITIQUE_SYSTEM_V1",
    "SAFETY_DISPOSITION_SYSTEM_V1",
    "SAFETY_INPUT_SYSTEM_V1",
    "SYNTHESIZER_SELF_CRITIQUE_SYSTEM_V1",
    "SYNTHESIZER_SYSTEM_V1",
    "render_rubric_critique_user",
    "render_safety_disposition_user",
    "render_safety_input_user",
    "render_synthesizer_self_critique_user",
    "render_synthesizer_user",
]
