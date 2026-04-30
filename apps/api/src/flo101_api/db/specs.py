"""SkillSpec persistence."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from flo101_api.db.store import SqliteStore, get_store
from flo101_api.domain.enums import ArtifactKind, CapabilityKind, StakesClass
from flo101_api.domain.rubric import Rubric
from flo101_api.domain.spec import CapabilityWiring, SkillSpec


def insert_spec(spec: SkillSpec, *, store: SqliteStore | None = None) -> None:
    s = store or get_store()
    with s.transaction() as cur:
        cur.execute(
            """
            INSERT INTO skill_specs (
                id, goal_text, audience_hint, artifact_kind, stakes_class,
                rubric_json, capabilities_json, challenge_templates_json,
                pathway_archetypes_json, exemplar_prompts_json,
                meta_critique_score, has_corpus, version, authored_by,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                spec.id,
                spec.goal_text,
                spec.audience_hint,
                spec.artifact_kind.value,
                spec.stakes_class.value,
                spec.rubric.model_dump_json(),
                json.dumps([c.model_dump() for c in spec.capabilities]),
                json.dumps(spec.challenge_templates),
                json.dumps(spec.pathway_archetypes),
                json.dumps(spec.exemplar_prompts),
                spec.meta_critique_score,
                int(spec.has_corpus),
                spec.version,
                spec.authored_by,
                spec.created_at.isoformat(),
                spec.updated_at.isoformat(),
            ),
        )


def get_spec(spec_id: str, *, store: SqliteStore | None = None) -> SkillSpec | None:
    s = store or get_store()
    with s.cursor() as cur:
        row = cur.execute(
            "SELECT * FROM skill_specs WHERE id = ?", (spec_id,)
        ).fetchone()
    return _row_to_spec(row) if row else None


def list_specs(*, limit: int = 100, store: SqliteStore | None = None) -> list[SkillSpec]:
    s = store or get_store()
    with s.cursor() as cur:
        rows = cur.execute(
            "SELECT * FROM skill_specs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row_to_spec(r) for r in rows]


def mark_has_corpus(spec_id: str, *, store: SqliteStore | None = None) -> None:
    # If the spec was synthesized before corpus upload it won't have the
    # CORPUS_GROUNDED_EVIDENCE capability wired — patch it in here so
    # evaluations actually consult the uploaded material.
    s = store or get_store()
    spec = get_spec(spec_id, store=s)
    if spec is None:
        return
    capabilities = list(spec.capabilities)
    has_cge = any(
        c.kind is CapabilityKind.CORPUS_GROUNDED_EVIDENCE for c in capabilities
    )
    if not has_cge:
        capabilities.append(
            CapabilityWiring(
                kind=CapabilityKind.CORPUS_GROUNDED_EVIDENCE,
                config={"k": 6},
            )
        )
    capabilities_json = json.dumps([c.model_dump() for c in capabilities])
    now = datetime.now(UTC).isoformat()
    with s.transaction() as cur:
        cur.execute(
            "UPDATE skill_specs SET has_corpus = 1, capabilities_json = ?, updated_at = ? WHERE id = ?",
            (capabilities_json, now, spec_id),
        )


def _row_to_spec(row: sqlite3.Row) -> SkillSpec:
    return SkillSpec(
        id=str(row["id"]),
        goal_text=str(row["goal_text"]),
        audience_hint=row["audience_hint"],
        artifact_kind=ArtifactKind(row["artifact_kind"]),
        stakes_class=StakesClass(row["stakes_class"]),
        rubric=Rubric.model_validate_json(row["rubric_json"]),
        capabilities=[
            CapabilityWiring.model_validate(c)
            for c in json.loads(row["capabilities_json"])
        ],
        challenge_templates=json.loads(row["challenge_templates_json"]),
        pathway_archetypes=json.loads(row["pathway_archetypes_json"]),
        exemplar_prompts=json.loads(row["exemplar_prompts_json"]),
        meta_critique_score=float(row["meta_critique_score"]),
        has_corpus=bool(row["has_corpus"]),
        version=int(row["version"]),
        authored_by=row["authored_by"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )
