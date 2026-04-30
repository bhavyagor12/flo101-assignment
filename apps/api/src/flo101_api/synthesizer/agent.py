"""Synthesizer: draft → self-critique. Retries once with feedback on rejection."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from flo101_api.config import Settings, get_settings
from flo101_api.domain.spec import SkillSpec, SynthesizeRequest
from flo101_api.llm import LLMGateway, LLMRequestMetadata, build_gateway
from flo101_api.llm.prompts import (
    SYNTHESIZER_SELF_CRITIQUE_SYSTEM_V1,
    SYNTHESIZER_SYSTEM_V1,
    render_synthesizer_self_critique_user,
    render_synthesizer_user,
)
from flo101_api.observability import get_logger
from flo101_api.synthesizer.models import SkillSpecDraft, SynthesisCritique


async def synthesize_skill_spec(
    *,
    request: SynthesizeRequest,
    has_corpus: bool = False,
    corpus_summary: str | None = None,
    authored_by: str | None = None,
    gateway: LLMGateway | None = None,
    settings: Settings | None = None,
) -> SkillSpec:
    # Always returns a SkillSpec. If the second attempt is also rejected,
    # the spec lands with the lower critique score so downstream safety
    # logic can react instead of receiving a hidden failure.
    settings = settings or get_settings()
    gateway = gateway or build_gateway()
    log = get_logger("flo101_api.synthesizer.agent")

    spec_id = str(uuid4())
    base_metadata = LLMRequestMetadata(
        operation="synthesize",
        prompt_name="synthesizer.system",
        prompt_version="v1",
        spec_id=spec_id,
    )

    log.info("synthesizer.start", spec_id=spec_id, has_corpus=has_corpus)

    draft = await _draft(
        request=request,
        corpus_summary=corpus_summary,
        gateway=gateway,
        model=settings.model_synthesizer,
        metadata=base_metadata,
    )
    critique = await _critique(
        draft=draft,
        gateway=gateway,
        model=settings.model_synthesizer,
        spec_id=spec_id,
    )
    log.info(
        "synthesizer.first_pass",
        spec_id=spec_id,
        meta_critique_score=critique.meta_critique_score,
        accepted=critique.accepted,
    )

    if not critique.accepted:
        log.info("synthesizer.retry", spec_id=spec_id, feedback=critique.feedback)
        draft = await _draft(
            request=request,
            corpus_summary=corpus_summary,
            gateway=gateway,
            model=settings.model_synthesizer,
            metadata=base_metadata.model_copy(
                update={"prompt_version": "v1+retry"}
            ),
            previous_critique=critique.feedback,
        )
        critique = await _critique(
            draft=draft,
            gateway=gateway,
            model=settings.model_synthesizer,
            spec_id=spec_id,
        )
        log.info(
            "synthesizer.second_pass",
            spec_id=spec_id,
            meta_critique_score=critique.meta_critique_score,
            accepted=critique.accepted,
        )
        if not critique.accepted:
            log.warning("synthesizer.unaccepted_after_retry", spec_id=spec_id)

    return _draft_to_spec(
        draft=draft,
        critique=critique,
        spec_id=spec_id,
        has_corpus=has_corpus,
        authored_by=authored_by,
    )


async def _draft(
    *,
    request: SynthesizeRequest,
    corpus_summary: str | None,
    gateway: LLMGateway,
    model: str,
    metadata: LLMRequestMetadata,
    previous_critique: str | None = None,
) -> SkillSpecDraft:
    user = render_synthesizer_user(
        goal_text=request.goal_text,
        audience_hint=request.audience_hint,
        output_goal=request.output_goal,
        time_budget_minutes=request.time_budget_minutes,
        corpus_summary=corpus_summary,
    )
    if previous_critique:
        user = (
            f"{user}\n\nA previous attempt was rejected. Reviewer feedback:\n"
            f"{previous_critique}\n\nAddress the feedback in your revised SkillSpec."
        )
    return await gateway.structured(
        model=model,
        system=SYNTHESIZER_SYSTEM_V1,
        user=user,
        response_model=SkillSpecDraft,
        metadata=metadata,
        temperature=0.0,
        cache_system=True,
    )


async def _critique(
    *,
    draft: SkillSpecDraft,
    gateway: LLMGateway,
    model: str,
    spec_id: str,
) -> SynthesisCritique:
    return await gateway.structured(
        model=model,
        system=SYNTHESIZER_SELF_CRITIQUE_SYSTEM_V1,
        user=render_synthesizer_self_critique_user(
            spec_json=draft.model_dump_json(indent=2)
        ),
        response_model=SynthesisCritique,
        metadata=LLMRequestMetadata(
            operation="synthesize.self_critique",
            prompt_name="synthesizer.self_critique.system",
            prompt_version="v1",
            spec_id=spec_id,
        ),
        temperature=0.0,
        cache_system=True,
    )


def _draft_to_spec(
    *,
    draft: SkillSpecDraft,
    critique: SynthesisCritique,
    spec_id: str,
    has_corpus: bool,
    authored_by: str | None,
) -> SkillSpec:
    now = datetime.now(UTC)
    # The independent critique is the more honest estimator; if it's lower
    # than the draft's self-report, trust it.
    score = min(draft.meta_critique_score, critique.meta_critique_score)
    return SkillSpec(
        id=spec_id,
        goal_text=draft.goal_text,
        audience_hint=draft.audience_hint,
        artifact_kind=draft.artifact_kind,
        stakes_class=draft.stakes_class,
        rubric=draft.rubric,
        capabilities=draft.capabilities,
        challenge_templates=draft.challenge_templates,
        pathway_archetypes=draft.pathway_archetypes,
        exemplar_prompts=draft.exemplar_prompts,
        meta_critique_score=score,
        has_corpus=has_corpus,
        version=1,
        authored_by=authored_by,
        created_at=now,
        updated_at=now,
    )
