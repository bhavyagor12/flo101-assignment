"""Critic calibration eval.

For each seeded spec, submit a `weak` exemplar and a `great` exemplar; the
weak score must be lower than the great score. This is the smoke test that
the rubric + critic actually discriminate quality.

Skipped without LLM keys.
"""

from __future__ import annotations

import pytest

from flo101_api.critic.run import run_critic
from flo101_api.db.specs import get_spec
from flo101_api.domain.artifact import ArtifactSubmission

from .conftest import needs_embed, needs_llm


WEAK_PRD = "we should build a feature for users."
GREAT_PRD = (
    "Problem: small-team admins lose 3+ hours/week reconciling permission drift "
    "across SSO + native roles.\n\n"
    "User: org admin at a 50-200 person company using Okta + our app's native roles.\n\n"
    "Success metrics: north star = weekly drift incidents; guardrails = admin "
    "satisfaction (NPS+25), no regression in invitation TTI; counter = false "
    "positives < 5%.\n\n"
    "Scope: read-only drift detection for v1. Out of scope: auto-remediation.\n\n"
    "Risks: false positives erode trust; mitigations: confidence threshold, "
    "admin override, weekly digest before alerting.\n"
)


@needs_llm
async def test_system_design_calibration_discriminates_quality() -> None:
    spec = get_spec("seed-system-design-001")
    assert spec is not None

    weak_eval = await run_critic(
        spec_id=spec.id,
        submission=ArtifactSubmission(kind=spec.artifact_kind, content=WEAK_PRD, filename=None, metadata={}),
    )
    great_eval = await run_critic(
        spec_id=spec.id,
        submission=ArtifactSubmission(kind=spec.artifact_kind, content=GREAT_PRD, filename=None, metadata={}),
    )

    # The "weak" PRD-shaped artifact won't even be a system design — it should
    # score lower than a coherent one. We don't require a specific overall_score
    # because expert-review-required dispositions withhold it; we compare the
    # *mean of dimension scores* instead.
    weak_mean = _mean_score(weak_eval.dimension_scores)
    great_mean = _mean_score(great_eval.dimension_scores)
    assert weak_mean < great_mean, (
        f"calibration broken: weak={weak_mean:.2f} >= great={great_mean:.2f}"
    )


@needs_llm
@needs_embed
async def test_soap_high_stakes_yields_review_disposition() -> None:
    """High-stakes specs (medical) must NOT auto-publish a numeric score."""
    spec = get_spec("seed-soap-note-001")
    assert spec is not None
    weak = await run_critic(
        spec_id=spec.id,
        submission=ArtifactSubmission(
            kind=spec.artifact_kind,
            content="patient has chest pain. give aspirin.",
            filename=None,
            metadata={},
        ),
    )
    assert weak.safety_disposition.value in {
        "expert_review_required",
        "human_review_suggested",
    }


def _mean_score(dims: list) -> float:  # type: ignore[type-arg]
    if not dims:
        return 0.0
    return sum(d.score for d in dims) / len(dims)


@pytest.mark.parametrize("_x", [0])
def test_calibration_fixtures_present(_x: int) -> None:
    """Sanity: the strings exist (so an offline run still validates this file)."""
    assert WEAK_PRD
    assert GREAT_PRD
