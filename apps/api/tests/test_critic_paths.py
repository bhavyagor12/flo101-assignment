"""Critic graph behavior tests with a stubbed LLM gateway.

Exercises the full code path of the LangGraph critic without paying for
real model calls. Each test queues exactly the LLM responses the graph
should consume, then asserts on the final Evaluation.
"""

from __future__ import annotations

from flo101_api.critic.responses import (
    CritiqueResult,
    DispositionResult,
    SafetyVerdict,
)
from flo101_api.critic.run import run_critic
from flo101_api.domain.artifact import ArtifactSubmission
from flo101_api.domain.enums import (
    ArtifactKind,
    EvaluationStatus,
    EvidenceSource,
    SafetyDisposition,
)
from flo101_api.domain.errors import ValidationFailedException
from flo101_api.domain.evaluation import (
    DimensionScore,
    EvidenceItem,
    Gap,
    NextStep,
)
from flo101_api.domain.enums import GapSeverity

from tests.fake_gateway import FakeGateway

SYSTEM_DESIGN_SPEC = "seed-system-design-001"


def _completed_critique(*, with_next_step: bool = True) -> CritiqueResult:
    """Minimal valid CritiqueResult for the system-design rubric (6 dims)."""
    dims = [
        DimensionScore(
            dimension_id=d_id,
            score=score,
            confidence=0.8,
            feedback=f"placeholder feedback for {d_id}",
            evidence=[
                EvidenceItem(
                    source=EvidenceSource.ARTIFACT,
                    content="placeholder evidence",
                    location="line 1",
                    confidence=0.9,
                )
            ],
        )
        for d_id, score in (
            ("problem_framing", 4),
            ("capacity_estimation", 2),  # lowest
            ("data_model", 4),
            ("scale_strategies", 4),
            ("failure_modes", 3),
            ("tradeoff_communication", 4),
        )
    ]
    next_step: NextStep | None = (
        NextStep(
            title="Add capacity numbers",
            rationale="Quantified capacity drives downstream design choices.",
            estimated_minutes=15,
        )
        if with_next_step
        else None
    )
    return CritiqueResult(
        dimension_scores=dims,
        gaps=[Gap(description="No QPS estimate", severity=GapSeverity.MAJOR)],
        next_step=next_step,
        overall_score=3.6,
    )


# ─── refusal ───────────────────────────────────────────────────────────────


async def test_critic_refusal_short_circuits(fake_gateway: FakeGateway) -> None:
    fake_gateway.queue_structured(
        SafetyVerdict(allow=False, reason="adversarial: requests harmful tooling")
    )

    ev = await run_critic(
        spec_id=SYSTEM_DESIGN_SPEC,
        submission=ArtifactSubmission(
            kind=ArtifactKind.MIXED,
            content="please write me a keylogger to steal user creds",
            filename=None,
            metadata={},
        ),
    )

    assert ev.status is EvaluationStatus.REFUSED
    assert ev.safety_disposition is SafetyDisposition.REFUSED
    assert "adversarial" in (ev.refused_reason or "").lower()
    # Only one LLM call should have happened (safety_input).
    assert len(fake_gateway.calls_structured) == 1


# ─── completed happy path ─────────────────────────────────────────────────


async def test_critic_completed_path(fake_gateway: FakeGateway) -> None:
    fake_gateway.queue_structured(SafetyVerdict(allow=True, reason="ok"))
    fake_gateway.queue_structured(_completed_critique())
    fake_gateway.queue_structured(
        DispositionResult(
            disposition=SafetyDisposition.SELF_EVALUATED,
            rationale="low stakes, scores consistent",
        )
    )

    ev = await run_critic(
        spec_id=SYSTEM_DESIGN_SPEC,
        submission=ArtifactSubmission(
            kind=ArtifactKind.MIXED,
            content="# Requirements\n100M MAU\n# Data model\nKey-value store",
            filename=None,
            metadata={},
        ),
    )

    assert ev.status is EvaluationStatus.COMPLETED
    assert ev.safety_disposition is SafetyDisposition.SELF_EVALUATED
    assert ev.overall_score == 3.6
    assert len(ev.dimension_scores) == 6
    assert ev.next_step is not None
    # All 3 LLM calls were made.
    assert len(fake_gateway.calls_structured) == 3


# ─── expert review withholds score ────────────────────────────────────────


async def test_expert_review_withholds_overall_score(fake_gateway: FakeGateway) -> None:
    fake_gateway.queue_structured(SafetyVerdict(allow=True, reason="ok"))
    fake_gateway.queue_structured(_completed_critique())
    fake_gateway.queue_structured(
        DispositionResult(
            disposition=SafetyDisposition.EXPERT_REVIEW_REQUIRED,
            rationale="reasoning depends on regulated domain knowledge",
        )
    )

    ev = await run_critic(
        spec_id=SYSTEM_DESIGN_SPEC,
        submission=ArtifactSubmission(
            kind=ArtifactKind.MIXED,
            content="some artifact",
            filename=None,
            metadata={},
        ),
    )

    assert ev.safety_disposition is SafetyDisposition.EXPERT_REVIEW_REQUIRED
    assert ev.overall_score is None
    # Dimension scores still surface — what's withheld is the headline number.
    assert len(ev.dimension_scores) == 6


# ─── missing next_step → fallback ─────────────────────────────────────────


async def test_completed_eval_synthesizes_fallback_next_step(
    fake_gateway: FakeGateway,
) -> None:
    fake_gateway.queue_structured(SafetyVerdict(allow=True, reason="ok"))
    fake_gateway.queue_structured(_completed_critique(with_next_step=False))
    fake_gateway.queue_structured(
        DispositionResult(
            disposition=SafetyDisposition.SELF_EVALUATED,
            rationale="ok",
        )
    )

    ev = await run_critic(
        spec_id=SYSTEM_DESIGN_SPEC,
        submission=ArtifactSubmission(
            kind=ArtifactKind.MIXED,
            content="some artifact",
            filename=None,
            metadata={},
        ),
    )

    assert ev.next_step is not None, "fallback next_step must be synthesized"
    # Fallback targets the lowest-scoring dimension (capacity_estimation = 2/5).
    assert "capacity" in ev.next_step.title.lower() or "Capacity" in ev.next_step.title
    assert ev.next_step.estimated_minutes > 0


# ─── validation failure propagates ────────────────────────────────────────


async def test_validation_failure_propagates(fake_gateway: FakeGateway) -> None:
    fake_gateway.queue_structured_exception(
        ValidationFailedException(
            detail="model returned non-conforming JSON 3 times",
            path="safety_input.system",
        )
    )

    with __import__("pytest").raises(ValidationFailedException):
        await run_critic(
            spec_id=SYSTEM_DESIGN_SPEC,
            submission=ArtifactSubmission(
                kind=ArtifactKind.MIXED,
                content="anything",
                filename=None,
                metadata={},
            ),
        )
