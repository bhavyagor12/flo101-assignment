"""Artifact persistence."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from flo101_api.db.store import SqliteStore, get_store
from flo101_api.domain.artifact import Artifact
from flo101_api.domain.enums import ArtifactKind


def insert_artifact(artifact: Artifact, *, store: SqliteStore | None = None) -> None:
    s = store or get_store()
    with s.transaction() as cur:
        cur.execute(
            """
            INSERT INTO artifacts (
                id, spec_id, kind, content, filename, metadata_json, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact.id,
                artifact.spec_id,
                artifact.kind.value,
                artifact.content,
                artifact.filename,
                json.dumps(artifact.metadata),
                artifact.submitted_at.isoformat(),
            ),
        )


def get_artifact(
    artifact_id: str, *, store: SqliteStore | None = None
) -> Artifact | None:
    s = store or get_store()
    with s.cursor() as cur:
        row = cur.execute(
            "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
        ).fetchone()
    return _row_to_artifact(row) if row else None


def _row_to_artifact(row: sqlite3.Row) -> Artifact:
    return Artifact(
        id=str(row["id"]),
        spec_id=str(row["spec_id"]),
        kind=ArtifactKind(row["kind"]),
        content=str(row["content"]),
        filename=row["filename"],
        metadata=json.loads(row["metadata_json"]),
        submitted_at=datetime.fromisoformat(row["submitted_at"]),
    )
