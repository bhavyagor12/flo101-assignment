"""Corpus chunk persistence + vec search."""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from datetime import datetime

from flo101_api.db.store import SqliteStore, get_store
from flo101_api.domain.corpus import CorpusChunk


@dataclass(frozen=True, slots=True)
class ChunkInsert:
    public_id: str
    spec_id: str
    source: str
    content: str
    chunk_index: int
    token_count: int
    embedding: list[float]
    metadata: dict[str, str]


@dataclass(frozen=True, slots=True)
class ChunkHit:
    chunk: CorpusChunk
    distance: float


def _serialize_embedding(values: list[float]) -> bytes:
    return struct.pack(f"{len(values)}f", *values)


def insert_chunks(rows: list[ChunkInsert], *, store: SqliteStore | None = None) -> int:
    if not rows:
        return 0
    s = store or get_store()
    now = datetime.utcnow().isoformat()
    with s.transaction() as cur:
        for row in rows:
            cur.execute(
                """
                INSERT INTO corpus_chunks (
                    public_id, spec_id, source, content, chunk_index,
                    token_count, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.public_id,
                    row.spec_id,
                    row.source,
                    row.content,
                    row.chunk_index,
                    row.token_count,
                    json.dumps(row.metadata),
                    now,
                ),
            )
            rowid = cur.lastrowid
            cur.execute(
                "INSERT INTO corpus_chunks_vec(rowid, embedding) VALUES (?, ?)",
                (rowid, _serialize_embedding(row.embedding)),
            )
    return len(rows)


def search_chunks(
    *,
    spec_id: str,
    query_embedding: list[float],
    k: int = 8,
    overfetch: int = 32,
    store: SqliteStore | None = None,
) -> list[ChunkHit]:
    # vec0 is global, so we over-fetch by `overfetch` and filter by spec_id
    # in the JOIN. Fast enough up to ~100k chunks per service.
    s = store or get_store()
    with s.cursor() as cur:
        rows = cur.execute(
            """
            SELECT cc.public_id, cc.spec_id, cc.source, cc.content,
                   cc.chunk_index, cc.token_count, cc.metadata_json,
                   cc.created_at, m.distance
            FROM corpus_chunks_vec m
            JOIN corpus_chunks cc ON cc.id = m.rowid
            WHERE m.embedding MATCH ? AND k = ?
              AND cc.spec_id = ?
            ORDER BY m.distance
            LIMIT ?
            """,
            (
                _serialize_embedding(query_embedding),
                overfetch,
                spec_id,
                k,
            ),
        ).fetchall()
    return [
        ChunkHit(
            chunk=CorpusChunk(
                id=r["public_id"],
                spec_id=r["spec_id"],
                source=r["source"],
                content=r["content"],
                chunk_index=r["chunk_index"],
                token_count=r["token_count"],
                metadata=json.loads(r["metadata_json"]),
                created_at=datetime.fromisoformat(r["created_at"]),
            ),
            distance=float(r["distance"]),
        )
        for r in rows
    ]


def list_chunks(
    *, spec_id: str, limit: int = 1000, store: SqliteStore | None = None
) -> list[CorpusChunk]:
    s = store or get_store()
    with s.cursor() as cur:
        rows = cur.execute(
            """
            SELECT public_id, spec_id, source, content, chunk_index,
                   token_count, metadata_json, created_at
            FROM corpus_chunks
            WHERE spec_id = ?
            ORDER BY chunk_index ASC
            LIMIT ?
            """,
            (spec_id, limit),
        ).fetchall()
    return [
        CorpusChunk(
            id=r["public_id"],
            spec_id=r["spec_id"],
            source=r["source"],
            content=r["content"],
            chunk_index=r["chunk_index"],
            token_count=r["token_count"],
            metadata=json.loads(r["metadata_json"]),
            created_at=datetime.fromisoformat(r["created_at"]),
        )
        for r in rows
    ]


def count_chunks(*, spec_id: str, store: SqliteStore | None = None) -> int:
    s = store or get_store()
    with s.cursor() as cur:
        row = cur.execute(
            "SELECT COUNT(*) FROM corpus_chunks WHERE spec_id = ?", (spec_id,)
        ).fetchone()
    return int(row[0]) if row else 0
