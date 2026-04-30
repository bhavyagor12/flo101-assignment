"""Evaluation persistence."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from flo101_api.db.store import SqliteStore, get_store
from flo101_api.domain.enums import EvaluationStatus, SafetyDisposition
from flo101_api.domain.evaluation import (
    CapabilityResult,
    DimensionScore,
    Evaluation,
    Gap,
    NextStep,
)


def insert_evaluation(
    evaluation: Evaluation, *, store: SqliteStore | None = None
) -> None:
    s = store or get_store()
    with s.transaction() as cur:
        cur.execute(
            """
            INSERT INTO evaluations (
                id, spec_id, artifact_id, status, safety_disposition,
                overall_score, dimension_scores_json, gaps_json,
                next_step_json, refused_reason, capability_results_json,
                trace_id, created_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evaluation.id,
                evaluation.spec_id,
                evaluation.artifact_id,
                evaluation.status.value,
                evaluation.safety_disposition.value,
                evaluation.overall_score,
                json.dumps([d.model_dump() for d in evaluation.dimension_scores]),
                json.dumps([g.model_dump() for g in evaluation.gaps]),
                evaluation.next_step.model_dump_json() if evaluation.next_step else None,
                evaluation.refused_reason,
                json.dumps([c.model_dump() for c in evaluation.capability_results]),
                evaluation.trace_id,
                evaluation.created_at.isoformat(),
                evaluation.completed_at.isoformat() if evaluation.completed_at else None,
            ),
        )


def get_evaluation(
    evaluation_id: str, *, store: SqliteStore | None = None
) -> Evaluation | None:
    s = store or get_store()
    with s.cursor() as cur:
        row = cur.execute(
            "SELECT * FROM evaluations WHERE id = ?", (evaluation_id,)
        ).fetchone()
    return _row_to_evaluation(row) if row else None


def list_evaluations(
    *, limit: int = 50, store: SqliteStore | None = None
) -> list[Evaluation]:
    s = store or get_store()
    with s.cursor() as cur:
        rows = cur.execute(
            "SELECT * FROM evaluations ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row_to_evaluation(r) for r in rows]


def _row_to_evaluation(row: sqlite3.Row) -> Evaluation:
    next_step_json = row["next_step_json"]
    return Evaluation(
        id=str(row["id"]),
        spec_id=str(row["spec_id"]),
        artifact_id=str(row["artifact_id"]),
        status=EvaluationStatus(row["status"]),
        safety_disposition=SafetyDisposition(row["safety_disposition"]),
        overall_score=row["overall_score"],
        dimension_scores=[
            DimensionScore.model_validate(d)
            for d in json.loads(row["dimension_scores_json"])
        ],
        gaps=[Gap.model_validate(g) for g in json.loads(row["gaps_json"])],
        next_step=NextStep.model_validate_json(next_step_json) if next_step_json else None,
        refused_reason=row["refused_reason"],
        capability_results=[
            CapabilityResult.model_validate(c)
            for c in json.loads(row["capability_results_json"])
        ],
        trace_id=row["trace_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
        completed_at=datetime.fromisoformat(row["completed_at"])
        if row["completed_at"]
        else None,
    )
