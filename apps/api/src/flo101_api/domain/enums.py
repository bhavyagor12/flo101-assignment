"""StrEnum types used across the domain. Stable string values for JSON/SQL."""

from __future__ import annotations

from enum import StrEnum


class ArtifactKind(StrEnum):
    TEXT = "text"
    CODE = "code"
    SQL = "sql"
    DIAGRAM_MARKDOWN = "diagram_markdown"
    MIXED = "mixed"


class StakesClass(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SafetyDisposition(StrEnum):
    SELF_EVALUATED = "self_evaluated"
    HUMAN_REVIEW_SUGGESTED = "human_review_suggested"
    EXPERT_REVIEW_REQUIRED = "expert_review_required"
    REFUSED = "refused"


class CapabilityKind(StrEnum):
    LLM_RUBRIC = "llm_rubric"
    CORPUS_GROUNDED_EVIDENCE = "corpus_grounded_evidence"
    STRUCTURAL_CHECK = "structural_check"
    CODE_LINT = "code_lint"
    CODE_SANDBOX_EXECUTE = "code_sandbox_execute"
    SQL_PARSE = "sql_parse"
    SQL_EXECUTE = "sql_execute"


class EvaluationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    REFUSED = "refused"
    FAILED = "failed"


class GapSeverity(StrEnum):
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class EvidenceSource(StrEnum):
    ARTIFACT = "artifact"
    CORPUS = "corpus"
    PROGRAMMATIC = "programmatic"
    LLM_RUBRIC = "llm_rubric"


class CapabilityStatus(StrEnum):
    # `skipped` is distinct from `passed` so an unsupported lint or a missing
    # corpus doesn't masquerade as a successful check upstream.
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
