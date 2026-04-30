"""SQLite store with sqlite-vec loaded. WAL mode, RLock-serialized writes.

Repository functions are sync; FastAPI calls them directly inside async
routes. Switch to `asyncio.to_thread` if write contention becomes a
problem (single-writer SQLite tops out around a few hundred writes/sec).
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Any

import sqlite_vec

from flo101_api.config import get_settings
from flo101_api.observability import get_logger


_MIGRATIONS: tuple[str, ...] = (
    # 0001 — initial schema
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY
    );

    CREATE TABLE IF NOT EXISTS skill_specs (
        id TEXT PRIMARY KEY,
        goal_text TEXT NOT NULL,
        audience_hint TEXT,
        artifact_kind TEXT NOT NULL,
        stakes_class TEXT NOT NULL,
        rubric_json TEXT NOT NULL,
        capabilities_json TEXT NOT NULL,
        challenge_templates_json TEXT NOT NULL,
        pathway_archetypes_json TEXT NOT NULL,
        exemplar_prompts_json TEXT NOT NULL,
        meta_critique_score REAL NOT NULL,
        has_corpus INTEGER NOT NULL DEFAULT 0,
        version INTEGER NOT NULL DEFAULT 1,
        authored_by TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS corpus_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        public_id TEXT NOT NULL UNIQUE,
        spec_id TEXT NOT NULL REFERENCES skill_specs(id) ON DELETE CASCADE,
        source TEXT NOT NULL,
        content TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        token_count INTEGER NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS ix_corpus_chunks_spec ON corpus_chunks(spec_id);

    CREATE TABLE IF NOT EXISTS artifacts (
        id TEXT PRIMARY KEY,
        spec_id TEXT NOT NULL REFERENCES skill_specs(id) ON DELETE CASCADE,
        kind TEXT NOT NULL,
        content TEXT NOT NULL,
        filename TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        submitted_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS ix_artifacts_spec ON artifacts(spec_id);

    CREATE TABLE IF NOT EXISTS evaluations (
        id TEXT PRIMARY KEY,
        spec_id TEXT NOT NULL REFERENCES skill_specs(id) ON DELETE CASCADE,
        artifact_id TEXT NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
        status TEXT NOT NULL,
        safety_disposition TEXT NOT NULL,
        overall_score REAL,
        dimension_scores_json TEXT NOT NULL,
        gaps_json TEXT NOT NULL,
        next_step_json TEXT,
        refused_reason TEXT,
        capability_results_json TEXT NOT NULL,
        trace_id TEXT,
        created_at TEXT NOT NULL,
        completed_at TEXT
    );

    CREATE INDEX IF NOT EXISTS ix_evaluations_spec ON evaluations(spec_id);
    CREATE INDEX IF NOT EXISTS ix_evaluations_artifact ON evaluations(artifact_id);

    CREATE VIRTUAL TABLE IF NOT EXISTS corpus_chunks_vec USING vec0(
        embedding float[1536]
    );
    """,
)


class SqliteStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._log = get_logger("flo101_api.db.store")
        self._lock = threading.RLock()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(path),
            check_same_thread=False,
            isolation_level=None,  # autocommit; we manage tx via BEGIN/COMMIT
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._load_vec_extension()
        self._migrate()
        self._log.info("db.ready", path=str(path))

    def _load_vec_extension(self) -> None:
        self._conn.enable_load_extension(True)
        try:
            sqlite_vec.load(self._conn)  # type: ignore[no-untyped-call]
        finally:
            self._conn.enable_load_extension(False)

    def _migrate(self) -> None:
        with self._lock:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)"
            )
            current = self._conn.execute(
                "SELECT MAX(version) FROM schema_version"
            ).fetchone()
            current_version = current[0] if current and current[0] is not None else 0
            for i, sql in enumerate(_MIGRATIONS, start=1):
                if i <= current_version:
                    continue
                self._conn.executescript(sql)
                self._conn.execute(
                    "INSERT INTO schema_version (version) VALUES (?)", (i,)
                )
                self._log.info("db.migrated", version=i)

    @contextmanager
    def cursor(self) -> Iterator[sqlite3.Cursor]:
        with self._lock:
            cur = self._conn.cursor()
            try:
                yield cur
            finally:
                cur.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Cursor]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("BEGIN")
            try:
                yield cur
            except Exception:
                cur.execute("ROLLBACK")
                raise
            else:
                cur.execute("COMMIT")
            finally:
                cur.close()

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.execute(sql, params)

    def close(self) -> None:
        with self._lock:
            self._conn.close()


@lru_cache(maxsize=1)
def get_store() -> SqliteStore:
    return SqliteStore(get_settings().sqlite_path)
