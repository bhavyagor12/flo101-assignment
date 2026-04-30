"""Synthesizer coherence eval — exercises the full draft → self-critique loop.

Skipped when OPENROUTER_API_KEY is unset.
"""

from __future__ import annotations

import pytest

from flo101_api.domain.spec import SynthesizeRequest
from flo101_api.synthesizer import synthesize_skill_spec

from .conftest import needs_llm


@needs_llm
@pytest.mark.parametrize(
    "request_payload",
    [
        SynthesizeRequest(
            goal_text="learn to write a one-page product update for an exec audience",
            audience_hint="senior PM",
        ),
        SynthesizeRequest(
            goal_text="learn to write a SQL query that computes weekly active users",
            audience_hint="data analyst",
        ),
    ],
)
async def test_synthesizer_produces_valid_spec(request_payload: SynthesizeRequest) -> None:
    spec = await synthesize_skill_spec(request=request_payload)
    # Pydantic already validates structure; we add semantic checks here.
    weights = sum(d.weight for d in spec.rubric.dimensions)
    assert abs(weights - 1.0) < 1e-3, f"rubric weights = {weights:.4f}"
    assert 3 <= len(spec.rubric.dimensions) <= 6
    for dim in spec.rubric.dimensions:
        anchor_scores = sorted(a.score for a in dim.anchors)
        assert anchor_scores == [1, 2, 3, 4, 5]
    assert spec.meta_critique_score > 0.0
    assert any(c.kind.value == "llm_rubric" for c in spec.capabilities)
