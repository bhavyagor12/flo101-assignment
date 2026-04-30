"""Disposition decider — runs after rubric critique."""

from __future__ import annotations

SAFETY_DISPOSITION_SYSTEM_V1 = """You decide what posture the system takes on a completed evaluation.

Given:
  - The SkillSpec's stakes_class: low | medium | high
  - The dimension scores, gaps, and overall_score from the rubric critic
  - Whether programmatic checks passed/failed
  - Whether corpus-grounded evidence was used

Output one of:
  - self_evaluated: ship the score as-is.
    Use when: stakes_class=low AND no critical gaps AND no contradicting
    programmatic failures.
  - human_review_suggested: ship the score but surface a soft warning.
    Use when: stakes_class=medium, OR any major gap, OR overall_score
    confidence is mixed across dimensions.
  - expert_review_required: DO NOT publish a numeric score. Produce
    structured feedback for an expert reviewer. Use when: stakes_class=
    high, OR a critical gap, OR the artifact is in a regulated domain
    (medical, legal, safety-critical).
  - refused: artifact is fundamentally unevaluable (empty, off-topic,
    contradicts spec's artifact_kind). Use sparingly.

Return JSON {disposition: <one of above>, rationale: str}. The rationale
is shown to the learner alongside the disposition — keep it short and
specific. For expert_review_required, the rationale must explain WHY a
human is needed for this domain, not just "high stakes"."""


def render_safety_disposition_user(
    *,
    stakes_class: str,
    overall_score: float | None,
    dimension_summary: str,
    gap_summary: str,
    programmatic_summary: str,
) -> str:
    overall = "n/a" if overall_score is None else f"{overall_score:.2f}"
    return (
        f"STAKES CLASS: {stakes_class}\n"
        f"OVERALL SCORE: {overall}\n\n"
        f"DIMENSION SCORES:\n{dimension_summary}\n\n"
        f"GAPS:\n{gap_summary}\n\n"
        f"PROGRAMMATIC CHECKS:\n{programmatic_summary}\n\n"
        "Decide disposition."
    )
