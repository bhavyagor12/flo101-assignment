"""LangGraph nodes. Each is async, returns a partial state dict to merge."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from flo101_api.config import get_settings
from flo101_api.critic.capabilities import run_enabled_capabilities
from flo101_api.critic.responses import (
    CritiqueResult,
    DispositionResult,
    SafetyVerdict,
)
from flo101_api.critic.state import CriticState
from flo101_api.db.artifacts import insert_artifact
from flo101_api.db.evaluations import insert_evaluation
from flo101_api.db.specs import get_spec
from flo101_api.domain.enums import (
    CapabilityStatus,
    EvaluationStatus,
    EvidenceSource,
    SafetyDisposition,
)
from flo101_api.domain.evaluation import (
    CapabilityResult,
    DimensionScore,
    Evaluation,
    EvidenceItem,
    Gap,
    NextStep,
)
from flo101_api.domain.errors import RefusedException
from flo101_api.domain.spec import SkillSpec
from flo101_api.llm import build_gateway
from flo101_api.llm.gateway import LLMRequestMetadata
from flo101_api.llm.prompts import (
    RUBRIC_CRITIQUE_SYSTEM_V1,
    SAFETY_DISPOSITION_SYSTEM_V1,
    SAFETY_INPUT_SYSTEM_V1,
    render_rubric_critique_user,
    render_safety_disposition_user,
    render_safety_input_user,
)
from flo101_api.observability import get_logger

_log = get_logger("flo101_api.critic.nodes")


# ─── 1. safety input ───────────────────────────────────────────────────────


async def safety_input_node(state: CriticState) -> dict[str, object]:
    artifact = state["artifact"]
    settings = get_settings()
    gateway = build_gateway()
    verdict = await gateway.structured(
        model=settings.model_safety_guard,
        system=SAFETY_INPUT_SYSTEM_V1,
        user=render_safety_input_user(kind="artifact", text=artifact.content),
        response_model=SafetyVerdict,
        metadata=LLMRequestMetadata(
            operation="safety_input",
            prompt_name="safety_input.system",
            prompt_version="v1",
            spec_id=state["spec_id"],
            artifact_id=artifact.id,
        ),
        temperature=0.0,
        cache_system=True,
    )
    _log.info(
        "critic.safety_input",
        spec_id=state["spec_id"],
        allow=verdict.allow,
        reason=verdict.reason,
    )
    return {
        "safety_input_allow": verdict.allow,
        "safety_input_reason": verdict.reason,
    }


# ─── 2. load spec ──────────────────────────────────────────────────────────


async def load_spec_node(state: CriticState) -> dict[str, object]:
    spec = get_spec(state["spec_id"])
    if spec is None:
        raise RefusedException(reason=f"unknown spec: {state['spec_id']}")
    return {"spec": spec}


# ─── 3. capability runner ──────────────────────────────────────────────────


async def capability_runner_node(state: CriticState) -> dict[str, object]:
    spec = _require_spec(state)
    artifact = state["artifact"]
    cap_results, evidence = await run_enabled_capabilities(spec=spec, artifact=artifact)
    _log.info(
        "critic.capabilities.done",
        spec_id=spec.id,
        passed=sum(1 for c in cap_results if c.status is CapabilityStatus.PASSED),
        failed=sum(1 for c in cap_results if c.status is CapabilityStatus.FAILED),
        skipped=sum(1 for c in cap_results if c.status is CapabilityStatus.SKIPPED),
        evidence_items=len(evidence),
    )
    return {
        "capability_results": cap_results,
        "extra_evidence": evidence,
    }


# ─── 4. rubric critique ────────────────────────────────────────────────────


async def rubric_critique_node(state: CriticState) -> dict[str, object]:
    spec = _require_spec(state)
    artifact = state["artifact"]
    cap_results: list[CapabilityResult] = state.get("capability_results", []) or []
    evidence: list[EvidenceItem] = state.get("extra_evidence", []) or []

    settings = get_settings()
    gateway = build_gateway()

    programmatic_block = _format_programmatic(cap_results)
    corpus_block = _format_corpus_evidence(evidence)

    user = render_rubric_critique_user(
        artifact_kind=artifact.kind.value,
        artifact_content=artifact.content[:60_000],
        rubric_json=spec.rubric.model_dump_json(indent=2),
        programmatic_results_block=programmatic_block,
        corpus_block=corpus_block,
    )

    result = await gateway.structured(
        model=settings.model_rubric_critique,
        system=RUBRIC_CRITIQUE_SYSTEM_V1,
        user=user,
        response_model=CritiqueResult,
        metadata=LLMRequestMetadata(
            operation="rubric_critique",
            prompt_name="rubric_critique.system",
            prompt_version="v1",
            spec_id=spec.id,
            artifact_id=artifact.id,
        ),
        temperature=0.0,
        cache_system=True,
        max_tokens=4096,
    )

    # Compute overall_score deterministically from weighted dimensions if the
    # model omitted it; trust the model's null when set explicitly.
    overall = result.overall_score
    if overall is None and result.dimension_scores:
        weight_by_id = {d.id: d.weight for d in spec.rubric.dimensions}
        weighted = 0.0
        total_w = 0.0
        for ds in result.dimension_scores:
            w = weight_by_id.get(ds.dimension_id, 0.0)
            weighted += ds.score * w
            total_w += w
        overall = weighted / total_w if total_w > 0 else None

    return {
        "dimension_scores": result.dimension_scores,
        "gaps": result.gaps,
        "next_step": result.next_step,
        "overall_score": overall,
    }


# ─── 5. safety disposition ─────────────────────────────────────────────────


async def safety_disposition_node(state: CriticState) -> dict[str, object]:
    spec = _require_spec(state)
    cap_results: list[CapabilityResult] = state.get("capability_results", []) or []
    dim_scores: list[DimensionScore] = state.get("dimension_scores", []) or []
    gaps: list[Gap] = state.get("gaps", []) or []
    overall = state.get("overall_score")

    settings = get_settings()
    gateway = build_gateway()

    user = render_safety_disposition_user(
        stakes_class=spec.stakes_class.value,
        overall_score=overall,
        dimension_summary=_format_dimensions(dim_scores),
        gap_summary=_format_gaps(gaps),
        programmatic_summary=_format_programmatic(cap_results),
    )
    result = await gateway.structured(
        model=settings.model_safety_guard,
        system=SAFETY_DISPOSITION_SYSTEM_V1,
        user=user,
        response_model=DispositionResult,
        metadata=LLMRequestMetadata(
            operation="safety_disposition",
            prompt_name="safety_disposition.system",
            prompt_version="v1",
            spec_id=spec.id,
            artifact_id=state["artifact"].id,
        ),
        temperature=0.0,
        cache_system=True,
    )
    _log.info(
        "critic.safety_disposition",
        spec_id=spec.id,
        disposition=result.disposition.value,
    )
    final_overall = overall
    if result.disposition is SafetyDisposition.EXPERT_REVIEW_REQUIRED:
        # Withhold numeric score for expert-review cases.
        final_overall = None
    return {
        "safety_disposition": result.disposition,
        "overall_score": final_overall,
        "refused_reason": result.rationale
        if result.disposition is SafetyDisposition.REFUSED
        else None,
    }


# ─── 6. assemble + persist ────────────────────────────────────────────────


async def assemble_node(state: CriticState) -> dict[str, object]:
    spec_id = state["spec_id"]
    artifact = state["artifact"]
    now = datetime.now(UTC)

    # Persist the artifact record. Idempotent-ish: insert may fail if rerun
    # with the same artifact id, which we deliberately don't catch.
    insert_artifact(artifact)

    if not state.get("safety_input_allow", True):
        evaluation = Evaluation(
            id=str(uuid4()),
            spec_id=spec_id,
            artifact_id=artifact.id,
            status=EvaluationStatus.REFUSED,
            safety_disposition=SafetyDisposition.REFUSED,
            overall_score=None,
            dimension_scores=[],
            gaps=[],
            next_step=None,
            refused_reason=state.get("safety_input_reason", "input refused"),
            capability_results=[],
            trace_id=state.get("trace_id"),
            created_at=now,
            completed_at=now,
        )
    else:
        disposition = state.get(
            "safety_disposition", SafetyDisposition.SELF_EVALUATED
        )
        dimension_scores = state.get("dimension_scores", []) or []
        gaps = state.get("gaps", []) or []
        next_step = state.get("next_step")
        # Track C depends on "what should I do next?" — guarantee one for
        # completed evaluations even if the LLM omits it.
        if (
            next_step is None
            and disposition is not SafetyDisposition.REFUSED
            and dimension_scores
        ):
            next_step = _fallback_next_step(
                dimension_scores=dimension_scores,
                spec=_require_spec(state),
            )
            _log.info(
                "critic.assemble.fallback_next_step",
                spec_id=spec_id,
                dimension_id=next_step.title,
            )
        evaluation = Evaluation(
            id=str(uuid4()),
            spec_id=spec_id,
            artifact_id=artifact.id,
            status=EvaluationStatus.COMPLETED,
            safety_disposition=disposition,
            overall_score=state.get("overall_score"),
            dimension_scores=dimension_scores,
            gaps=gaps,
            next_step=next_step,
            refused_reason=state.get("refused_reason"),
            capability_results=state.get("capability_results", []) or [],
            trace_id=state.get("trace_id"),
            created_at=now,
            completed_at=now,
        )

    insert_evaluation(evaluation)
    _log.info(
        "critic.assemble",
        evaluation_id=evaluation.id,
        spec_id=spec_id,
        artifact_id=artifact.id,
        status=evaluation.status.value,
        disposition=evaluation.safety_disposition.value,
        overall_score=evaluation.overall_score,
    )
    return {"evaluation": evaluation}


# ─── internal guards / formatting helpers ─────────────────────────────────


def _require_spec(state: CriticState) -> SkillSpec:
    spec = state.get("spec")
    if spec is None:
        raise RuntimeError("internal: load_spec_node must run before this node")
    return spec


def _fallback_next_step(
    *, dimension_scores: list[DimensionScore], spec: SkillSpec
) -> NextStep:
    # Deterministic fallback when the rubric LLM omits next_step. Picks
    # the lowest-scoring dimension; ties go to the higher-weighted one
    # so the suggested action targets the highest-leverage gap.
    weight_by_id = {d.id: d.weight for d in spec.rubric.dimensions}
    title_by_id = {d.id: d.title for d in spec.rubric.dimensions}
    lowest = min(
        dimension_scores,
        key=lambda d: (d.score, -weight_by_id.get(d.dimension_id, 0.0)),
    )
    title = title_by_id.get(lowest.dimension_id, lowest.dimension_id)
    rationale = (
        f"`{title}` scored lowest at {lowest.score}/5 "
        f"(confidence {lowest.confidence:.2f}). The fastest path to lift "
        f"the overall score is to address the rubric feedback for this "
        f"dimension directly: {lowest.feedback}"
    )
    return NextStep(
        title=f"Address {title}",
        rationale=rationale,
        estimated_minutes=20,
    )



def _format_programmatic(results: list[CapabilityResult]) -> str:
    # Skipped checks are dropped from the rubric prompt — showing them as
    # "skipped" was leaking through earlier as effectively a passed signal.
    visible = [r for r in results if r.status is not CapabilityStatus.SKIPPED]
    if not visible:
        return "(no programmatic checks ran)"
    lines: list[str] = []
    for r in visible:
        line = f"- {r.kind.value} [{r.status.value}]"
        if r.error:
            line += f" — {r.error}"
        if r.output:
            preview = json.dumps(r.output)[:300]
            line += f"\n  output: {preview}"
        lines.append(line)
    return "\n".join(lines)


def _format_corpus_evidence(evidence: list[EvidenceItem]) -> str | None:
    corpus_only = [e for e in evidence if e.source is EvidenceSource.CORPUS]
    if not corpus_only:
        return None
    lines = [
        f"[{i + 1}] {e.location or 'corpus'}\n{e.content[:1000]}"
        for i, e in enumerate(corpus_only)
    ]
    return "\n\n".join(lines)


def _format_dimensions(dim_scores: list[DimensionScore]) -> str:
    if not dim_scores:
        return "(none)"
    return "\n".join(
        f"- {d.dimension_id}: {d.score}/5 (conf {d.confidence:.2f})"
        for d in dim_scores
    )


def _format_gaps(gaps: list[Gap]) -> str:
    if not gaps:
        return "(none)"
    return "\n".join(f"- [{g.severity.value}] {g.description}" for g in gaps)
