"""Capability implementations.

Each capability returns (CapabilityResult, list[EvidenceItem]); the
capability_runner node calls them concurrently with asyncio.gather.
The sandbox is subprocess-based with rlimits — adequate for a process-
isolated build; an actual VM/microVM (E2B, firecracker) is the proper
sandbox for hostile code.
"""

from __future__ import annotations

import asyncio
import re
import resource
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from flo101_api.config import get_settings
from flo101_api.corpus.retrieve import retrieve_relevant
from flo101_api.domain.artifact import Artifact
from flo101_api.domain.enums import (
    ArtifactKind,
    CapabilityKind,
    CapabilityStatus,
    EvidenceSource,
)
from flo101_api.domain.evaluation import CapabilityResult, EvidenceItem
from flo101_api.domain.spec import SkillSpec
from flo101_api.observability import get_logger

_log = get_logger("flo101_api.critic.capabilities")


async def run_enabled_capabilities(
    *, spec: SkillSpec, artifact: Artifact
) -> tuple[list[CapabilityResult], list[EvidenceItem]]:
    tasks = [
        _dispatch(cap.kind, cap.config, spec=spec, artifact=artifact)
        for cap in spec.capabilities
    ]
    outcomes: list[tuple[CapabilityResult, list[EvidenceItem]]] = []
    if tasks:
        # return_exceptions=True so one failed capability doesn't sink the rest.
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for cap, res in zip(spec.capabilities, results, strict=True):
            if isinstance(res, BaseException):
                _log.warning(
                    "capability.error", kind=cap.kind.value, error=str(res)
                )
                outcomes.append(
                    (
                        CapabilityResult(
                            kind=cap.kind,
                            status=CapabilityStatus.FAILED,
                            error=str(res),
                            duration_ms=0,
                        ),
                        [],
                    )
                )
            else:
                outcomes.append(res)

    cap_results = [c for c, _ in outcomes]
    evidence = [e for _, evs in outcomes for e in evs]
    return cap_results, evidence


async def _dispatch(
    kind: CapabilityKind,
    config: dict[str, Any],
    *,
    spec: SkillSpec,
    artifact: Artifact,
) -> tuple[CapabilityResult, list[EvidenceItem]]:
    if kind is CapabilityKind.STRUCTURAL_CHECK:
        return await asyncio.to_thread(_structural_check, artifact, config)
    if kind is CapabilityKind.CODE_LINT:
        return await asyncio.to_thread(_code_lint, artifact, config)
    if kind is CapabilityKind.CODE_SANDBOX_EXECUTE:
        return await asyncio.to_thread(_code_sandbox, artifact, config)
    if kind is CapabilityKind.SQL_PARSE:
        return await asyncio.to_thread(_sql_parse, artifact, config)
    if kind is CapabilityKind.SQL_EXECUTE:
        return await asyncio.to_thread(_sql_execute, artifact, config)
    if kind is CapabilityKind.CORPUS_GROUNDED_EVIDENCE:
        return await _corpus_rag(spec=spec, artifact=artifact, config=config)
    if kind is CapabilityKind.LLM_RUBRIC:
        # The rubric LLM call lives in rubric_critique_node, not here.
        return _skipped(kind, "deferred to rubric_critique node")
    return (
        CapabilityResult(
            kind=kind,
            status=CapabilityStatus.FAILED,
            error=f"unknown capability kind: {kind}",
            duration_ms=0,
        ),
        [],
    )


# ─── structural ────────────────────────────────────────────────────────────


def _structural_check(
    artifact: Artifact, config: dict[str, Any]
) -> tuple[CapabilityResult, list[EvidenceItem]]:
    # Cheap, deterministic shape check. Looks at section presence and basic
    # markdown structure — used as evidence the critic can cite.
    t0 = time.perf_counter()
    text = artifact.content
    findings: dict[str, Any] = {
        "char_count": len(text),
        "line_count": text.count("\n") + 1,
        "word_count": len(text.split()),
        "has_headers": bool(re.search(r"^#{1,6}\s", text, re.MULTILINE)),
        "has_code_block": "```" in text,
        "has_list": bool(re.search(r"^\s*[-*]\s", text, re.MULTILINE)),
    }
    required_sections = config.get("required_sections", [])
    missing: list[str] = []
    for section in required_sections:
        if section.lower() not in text.lower():
            missing.append(section)
    findings["missing_required_sections"] = missing
    status = CapabilityStatus.PASSED if not missing else CapabilityStatus.FAILED
    return (
        CapabilityResult(
            kind=CapabilityKind.STRUCTURAL_CHECK,
            status=status,
            output=findings,
            duration_ms=int((time.perf_counter() - t0) * 1000),
            error=None if not missing else f"missing sections: {missing}",
        ),
        [],
    )


# ─── code lint ────────────────────────────────────────────────────────────


def _code_lint(
    artifact: Artifact, config: dict[str, Any]
) -> tuple[CapabilityResult, list[EvidenceItem]]:
    t0 = time.perf_counter()
    if artifact.kind not in {ArtifactKind.CODE, ArtifactKind.MIXED}:
        return _skipped(CapabilityKind.CODE_LINT, "artifact is not code")
    language: str = config.get("language", "python")
    if language != "python":
        return _skipped(
            CapabilityKind.CODE_LINT, f"only python lint supported (got {language})"
        )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(artifact.content)
        tmp = Path(f.name)
    try:
        try:
            proc = subprocess.run(
                ["ruff", "check", "--output-format=concise", str(tmp)],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except FileNotFoundError:
            return _skipped(CapabilityKind.CODE_LINT, "ruff not available on PATH")
        violations = [
            line.strip() for line in proc.stdout.splitlines() if line.strip()
        ]
        clean = proc.returncode == 0
        status = CapabilityStatus.PASSED if clean else CapabilityStatus.FAILED
        return (
            CapabilityResult(
                kind=CapabilityKind.CODE_LINT,
                status=status,
                output={"violations": violations, "exit_code": proc.returncode},
                duration_ms=int((time.perf_counter() - t0) * 1000),
                error=None if clean else f"{len(violations)} lint issue(s)",
            ),
            [
                EvidenceItem(
                    source=EvidenceSource.PROGRAMMATIC,
                    content=f"ruff: {len(violations)} violation(s)\n"
                    + "\n".join(violations[:8]),
                    location="lint",
                    confidence=1.0,
                )
            ]
            if violations
            else [],
        )
    finally:
        tmp.unlink(missing_ok=True)


# ─── code sandbox ──────────────────────────────────────────────────────────


def _code_sandbox(
    artifact: Artifact, config: dict[str, Any]
) -> tuple[CapabilityResult, list[EvidenceItem]]:
    t0 = time.perf_counter()
    if artifact.kind not in {ArtifactKind.CODE, ArtifactKind.MIXED}:
        return _skipped(CapabilityKind.CODE_SANDBOX_EXECUTE, "artifact is not code")
    language: str = config.get("language", "python")
    if language != "python":
        return _skipped(
            CapabilityKind.CODE_SANDBOX_EXECUTE,
            f"only python sandbox supported (got {language})",
        )
    settings = get_settings()
    timeout = config.get("timeout_seconds", settings.sandbox_timeout_seconds)
    mem_mb = config.get("memory_mb", settings.sandbox_memory_mb)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(artifact.content)
        tmp = Path(f.name)
    try:
        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(tmp)],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
                preexec_fn=_apply_rlimits(mem_mb=mem_mb, cpu_seconds=timeout),
            )
        except OSError as exc:
            return _skipped(
                CapabilityKind.CODE_SANDBOX_EXECUTE,
                f"sandbox unavailable on this platform: {exc}",
            )
        ok = proc.returncode == 0
        status = CapabilityStatus.PASSED if ok else CapabilityStatus.FAILED
        evidence: list[EvidenceItem] = []
        snippet = (proc.stdout + ("\n" + proc.stderr if proc.stderr else ""))[:1500]
        if snippet.strip():
            evidence.append(
                EvidenceItem(
                    source=EvidenceSource.PROGRAMMATIC,
                    content=snippet,
                    location="sandbox",
                    confidence=1.0,
                )
            )
        return (
            CapabilityResult(
                kind=CapabilityKind.CODE_SANDBOX_EXECUTE,
                status=status,
                output={
                    "exit_code": proc.returncode,
                    "stdout_snippet": proc.stdout[:1000],
                    "stderr_snippet": proc.stderr[:1000],
                },
                duration_ms=int((time.perf_counter() - t0) * 1000),
                error=None if ok else f"exit {proc.returncode}",
            ),
            evidence,
        )
    except subprocess.TimeoutExpired:
        return (
            CapabilityResult(
                kind=CapabilityKind.CODE_SANDBOX_EXECUTE,
                status=CapabilityStatus.FAILED,
                output={"timed_out": True},
                duration_ms=int((time.perf_counter() - t0) * 1000),
                error=f"sandbox timeout after {timeout}s",
            ),
            [],
        )
    finally:
        tmp.unlink(missing_ok=True)


def _apply_rlimits(*, mem_mb: int, cpu_seconds: int):
    # preexec_fn for subprocess.run: caps RLIMIT_AS and RLIMIT_CPU on the child.
    # macOS RLIMIT_AS support is partial; the setrlimit calls are guarded.
    def _setup() -> None:
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
        except (ValueError, OSError):
            pass
        try:
            mem_bytes = mem_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        except (ValueError, OSError):
            pass

    return _setup


# ─── sql ───────────────────────────────────────────────────────────────────


def _sql_parse(
    artifact: Artifact, config: dict[str, Any]
) -> tuple[CapabilityResult, list[EvidenceItem]]:
    _ = config
    t0 = time.perf_counter()
    if artifact.kind != ArtifactKind.SQL:
        return _skipped(CapabilityKind.SQL_PARSE, "artifact is not sql")
    try:
        # `EXPLAIN <q>` validates the parse without execution. SQLite-flavored —
        # not a substitute for the target dialect's parser.
        conn = sqlite3.connect(":memory:")
        try:
            conn.execute(f"EXPLAIN {artifact.content}")
            ok = True
            err: str | None = None
        finally:
            conn.close()
    except sqlite3.Error as exc:
        ok = False
        err = str(exc)
    status = CapabilityStatus.PASSED if ok else CapabilityStatus.FAILED
    return (
        CapabilityResult(
            kind=CapabilityKind.SQL_PARSE,
            status=status,
            output={"parsed": ok},
            duration_ms=int((time.perf_counter() - t0) * 1000),
            error=err,
        ),
        [
            EvidenceItem(
                source=EvidenceSource.PROGRAMMATIC,
                content=f"sql parse error: {err}",
                location="sql_parse",
                confidence=1.0,
            )
        ]
        if not ok and err
        else [],
    )


def _sql_execute(
    artifact: Artifact, config: dict[str, Any]
) -> tuple[CapabilityResult, list[EvidenceItem]]:
    # Runs the query against an in-memory SQLite seeded with `fixture_sql`
    # from capability config. No fixture → SKIPPED.
    t0 = time.perf_counter()
    if artifact.kind != ArtifactKind.SQL:
        return _skipped(CapabilityKind.SQL_EXECUTE, "artifact is not sql")
    fixture_sql: str = config.get("fixture_sql", "")
    if not fixture_sql:
        return _skipped(CapabilityKind.SQL_EXECUTE, "no fixture_sql provided")
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(fixture_sql)
        cur = conn.execute(artifact.content)
        rows = cur.fetchmany(20)
        cols = [d[0] for d in cur.description] if cur.description else []
        return (
            CapabilityResult(
                kind=CapabilityKind.SQL_EXECUTE,
                status=CapabilityStatus.PASSED,
                output={"row_count": len(rows), "columns": cols},
                duration_ms=int((time.perf_counter() - t0) * 1000),
            ),
            [
                EvidenceItem(
                    source=EvidenceSource.PROGRAMMATIC,
                    content=f"query returned {len(rows)} row(s); columns={cols}",
                    location="sql_execute",
                    confidence=1.0,
                )
            ],
        )
    except sqlite3.Error as exc:
        return (
            CapabilityResult(
                kind=CapabilityKind.SQL_EXECUTE,
                status=CapabilityStatus.FAILED,
                output={},
                duration_ms=int((time.perf_counter() - t0) * 1000),
                error=str(exc),
            ),
            [
                EvidenceItem(
                    source=EvidenceSource.PROGRAMMATIC,
                    content=f"sql execute error: {exc}",
                    location="sql_execute",
                    confidence=1.0,
                )
            ],
        )
    finally:
        conn.close()


# ─── corpus rag ────────────────────────────────────────────────────────────


async def _corpus_rag(
    *, spec: SkillSpec, artifact: Artifact, config: dict[str, Any]
) -> tuple[CapabilityResult, list[EvidenceItem]]:
    t0 = time.perf_counter()
    if not spec.has_corpus:
        return _skipped(
            CapabilityKind.CORPUS_GROUNDED_EVIDENCE, "spec has no corpus"
        )
    k = int(config.get("k", 6))
    # Use the head of the artifact as the retrieval query so we surface
    # corpus content semantically near what the learner is actually saying.
    query = artifact.content[:2000]
    hits = await retrieve_relevant(spec_id=spec.id, query=query, k=k)
    evidence = [
        EvidenceItem(
            source=EvidenceSource.CORPUS,
            content=h.chunk.content[:1500],
            location=f"{h.chunk.source}#chunk{h.chunk.chunk_index}",
            confidence=max(0.0, min(1.0, 1.0 - h.distance)),
        )
        for h in hits
    ]
    return (
        CapabilityResult(
            kind=CapabilityKind.CORPUS_GROUNDED_EVIDENCE,
            status=CapabilityStatus.PASSED,
            output={"hits": len(hits)},
            duration_ms=int((time.perf_counter() - t0) * 1000),
        ),
        evidence,
    )


# ─── helpers ───────────────────────────────────────────────────────────────


def _skipped(
    kind: CapabilityKind, reason: str
) -> tuple[CapabilityResult, list[EvidenceItem]]:
    return (
        CapabilityResult(
            kind=kind,
            status=CapabilityStatus.SKIPPED,
            output={"reason": reason},
            duration_ms=0,
        ),
        [],
    )
