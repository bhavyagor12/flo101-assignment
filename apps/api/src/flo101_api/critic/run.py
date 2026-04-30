"""Public entry point for running an evaluation through the Critic graph."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from flo101_api.config import get_settings
from flo101_api.critic.graph import get_critic_graph
from flo101_api.critic.state import CriticState
from flo101_api.db.artifacts import insert_artifact
from flo101_api.db.evaluations import insert_evaluation
from flo101_api.domain.artifact import Artifact, ArtifactSubmission
from flo101_api.domain.enums import EvaluationStatus, SafetyDisposition
from flo101_api.domain.evaluation import Evaluation
from flo101_api.observability import get_logger

_log = get_logger("flo101_api.critic.run")


async def run_critic(
    *,
    spec_id: str,
    submission: ArtifactSubmission,
) -> Evaluation:
    """Run the Critic graph for an artifact submission against a spec.

    Wraps the graph in a wall-clock timeout (configurable via
    `EVALUATION_WALLCLOCK_SECONDS`). On timeout, persists a structured
    FAILED Evaluation rather than hanging the request.
    """
    settings = get_settings()
    artifact = Artifact(
        id=str(uuid4()),
        spec_id=spec_id,
        kind=submission.kind,
        content=submission.content,
        filename=submission.filename,
        metadata=submission.metadata,
        submitted_at=datetime.now(UTC),
    )
    initial: CriticState = {
        "spec_id": spec_id,
        "artifact": artifact,
    }
    _log.info(
        "critic.run.start",
        spec_id=spec_id,
        artifact_id=artifact.id,
        wallclock_s=settings.evaluation_wallclock_seconds,
    )
    graph = get_critic_graph()
    try:
        async with asyncio.timeout(settings.evaluation_wallclock_seconds):
            final_state = await graph.ainvoke(initial)
    except TimeoutError:
        _log.warning(
            "critic.run.timeout",
            spec_id=spec_id,
            artifact_id=artifact.id,
            seconds=settings.evaluation_wallclock_seconds,
        )
        return _build_timeout_evaluation(
            spec_id=spec_id,
            artifact=artifact,
            seconds=settings.evaluation_wallclock_seconds,
        )

    evaluation = final_state.get("evaluation")
    if evaluation is None:
        raise RuntimeError("critic graph completed without producing an Evaluation")
    return evaluation


def _build_timeout_evaluation(
    *, spec_id: str, artifact: Artifact, seconds: int
) -> Evaluation:
    """Persist a structured FAILED Evaluation when the wall-clock fires.

    Status=FAILED communicates that the system couldn't complete; safety
    disposition=REFUSED conveys "no posture; please retry or shorten."
    """
    insert_artifact(artifact)
    now = datetime.now(UTC)
    evaluation = Evaluation(
        id=str(uuid4()),
        spec_id=spec_id,
        artifact_id=artifact.id,
        status=EvaluationStatus.FAILED,
        safety_disposition=SafetyDisposition.REFUSED,
        overall_score=None,
        dimension_scores=[],
        gaps=[],
        next_step=None,
        refused_reason=(
            f"evaluation exceeded the wall-clock budget of {seconds}s. "
            "Try a shorter artifact or retry shortly."
        ),
        capability_results=[],
        trace_id=None,
        created_at=now,
        completed_at=now,
    )
    insert_evaluation(evaluation)
    return evaluation
