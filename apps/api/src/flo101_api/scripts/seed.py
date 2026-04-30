"""Seeded SkillSpecs — hand-authored so `make demo-seed` doesn't call an LLM
and the UI starts from a known state. Synthesizer-generated specs come from
the UI for fresh goals.

  1. system_design  — engineering, mixed, no corpus
  2. soap_note      — medical, text, corpus, high stakes
  3. python_review  — code, lint + sandbox
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

from flo101_api.corpus.ingest import IngestDocument
from flo101_api.db.specs import get_spec, insert_spec
from flo101_api.domain.enums import ArtifactKind, CapabilityKind, StakesClass
from flo101_api.domain.rubric import Rubric, RubricAnchor, RubricDimension
from flo101_api.domain.spec import CapabilityWiring, SkillSpec


_SOAP_CORPUS = """\
SOAP Note Documentation Standards (excerpt)

Subjective: capture the patient's chief complaint, history of present illness
(OPQRST), pertinent positives and negatives, and relevant past medical /
surgical / family / social history. Quote patient verbatim where useful.

Objective: vitals, focused exam findings ordered by system, and imaging or
lab results. Distinguish observed from reported. Use objective measurements
(BP, HR, RR, SpO2, temp).

Assessment: a prioritized differential diagnosis with brief reasoning per
item. Identify the most likely cause AND any can't-miss diagnoses, even when
unlikely. Stratify risk where applicable (e.g., HEART score for chest pain).

Plan: per-problem plan covering diagnostics, therapeutics, disposition, and
follow-up. Include patient education and shared decision-making notes.

Common pitfalls:
- Listing a single diagnosis as the assessment without considering can't-miss
  causes (e.g., missing aortic dissection in chest pain).
- Failing to document risk stratification.
- Subjective and Objective sections containing assessment-level reasoning.
- Plan that doesn't address each problem listed in the Assessment.
"""


def _now() -> datetime:
    return datetime.now(UTC)


def _build_system_design_spec() -> SkillSpec:
    return SkillSpec(
        id="seed-system-design-001",
        goal_text="Design a system at 100M-MAU scale, with capacity, sharding, caching, and failure modes.",
        audience_hint="mid-level engineer prepping for senior interviews",
        artifact_kind=ArtifactKind.MIXED,
        stakes_class=StakesClass.LOW,
        rubric=Rubric(
            dimensions=[
                RubricDimension(
                    id="problem_framing",
                    title="Problem framing & requirements",
                    weight=0.20,
                    anchors=[
                        RubricAnchor(score=1, description="No requirements identified; jumps to solution."),
                        RubricAnchor(score=2, description="Names obvious functional requirements; no NFRs."),
                        RubricAnchor(score=3, description="Captures functional + scale numbers; misses tradeoff context."),
                        RubricAnchor(score=4, description="Solid functional + non-functional with explicit numbers."),
                        RubricAnchor(score=5, description="Concise, complete; explicit out-of-scope decisions."),
                    ],
                ),
                RubricDimension(
                    id="capacity_estimation",
                    title="Capacity estimation",
                    weight=0.15,
                    anchors=[
                        RubricAnchor(score=1, description="No numbers."),
                        RubricAnchor(score=2, description="Vague 'high traffic' claims, no QPS / storage."),
                        RubricAnchor(score=3, description="Reasonable QPS / storage estimates with weak math."),
                        RubricAnchor(score=4, description="Defended estimates with assumptions stated."),
                        RubricAnchor(score=5, description="Estimates connect to design choices (sharding, caching, etc.)."),
                    ],
                ),
                RubricDimension(
                    id="data_model",
                    title="Data model & storage choice",
                    weight=0.20,
                    anchors=[
                        RubricAnchor(score=1, description="No schema."),
                        RubricAnchor(score=2, description="Schema present; storage choice undefended."),
                        RubricAnchor(score=3, description="Storage choice reasoned; access patterns implicit."),
                        RubricAnchor(score=4, description="Schema + storage tied to access patterns + scale."),
                        RubricAnchor(score=5, description="Multi-store reasoning; explicit consistency tradeoffs."),
                    ],
                ),
                RubricDimension(
                    id="scale_strategies",
                    title="Sharding, caching, replication",
                    weight=0.20,
                    anchors=[
                        RubricAnchor(score=1, description="None addressed."),
                        RubricAnchor(score=2, description="One mentioned; no rationale."),
                        RubricAnchor(score=3, description="At least two mechanisms; mostly correct rationale."),
                        RubricAnchor(score=4, description="Three mechanisms wired into the design."),
                        RubricAnchor(score=5, description="Quantified hit rates / shard counts / failover semantics."),
                    ],
                ),
                RubricDimension(
                    id="failure_modes",
                    title="Failure modes & operational concerns",
                    weight=0.15,
                    anchors=[
                        RubricAnchor(score=1, description="No failure analysis."),
                        RubricAnchor(score=2, description="Mentions one failure case; no mitigation."),
                        RubricAnchor(score=3, description="Multiple failure modes; partial mitigation."),
                        RubricAnchor(score=4, description="Systematic failure-mode analysis with mitigations."),
                        RubricAnchor(score=5, description="Includes monitoring, alerts, and runbook implications."),
                    ],
                ),
                RubricDimension(
                    id="tradeoff_communication",
                    title="Tradeoff articulation",
                    weight=0.10,
                    anchors=[
                        RubricAnchor(score=1, description="No tradeoffs named."),
                        RubricAnchor(score=2, description="Tradeoffs hinted but not weighed."),
                        RubricAnchor(score=3, description="Major tradeoffs named; chooses with rationale."),
                        RubricAnchor(score=4, description="Multiple tradeoffs; clear decision criteria."),
                        RubricAnchor(score=5, description="Decisions revisitable, criteria explicit."),
                    ],
                ),
            ]
        ),
        capabilities=[
            CapabilityWiring(kind=CapabilityKind.LLM_RUBRIC),
            CapabilityWiring(kind=CapabilityKind.STRUCTURAL_CHECK, config={"required_sections": ["requirements", "data model", "failure"]}),
        ],
        challenge_templates=[
            "Design a URL shortener serving 1B reads/day with sub-50ms p99.",
            "Design a feature flag service used by 50 internal services.",
            "Critique the attached design and propose two specific improvements.",
        ],
        pathway_archetypes=[
            "read_and_annotate",
            "reproduce_from_spec",
            "modify_with_constraint",
            "design_from_scratch",
            "self_critique",
        ],
        exemplar_prompts={
            "great": "Produce a senior-level system design for a URL shortener at 1B reads/day with explicit capacity, sharding, caching hit rate, and failure modes.",
            "medium": "Produce a competent system design for a URL shortener that mentions sharding and caching but doesn't quantify capacity.",
            "weak": "Produce a beginner system design for a URL shortener with no scale numbers and only a single happy-path data model.",
        },
        meta_critique_score=0.92,
        has_corpus=False,
        version=1,
        authored_by="seed",
        created_at=_now(),
        updated_at=_now(),
    )


def _build_soap_spec() -> SkillSpec:
    return SkillSpec(
        id="seed-soap-note-001",
        goal_text="Write a SOAP note for an adult patient presenting with chest pain.",
        audience_hint="medical resident",
        artifact_kind=ArtifactKind.TEXT,
        stakes_class=StakesClass.HIGH,
        rubric=Rubric(
            dimensions=[
                RubricDimension(
                    id="subjective_completeness",
                    title="Subjective completeness (HPI / OPQRST)",
                    weight=0.20,
                    anchors=[
                        RubricAnchor(score=1, description="Missing core HPI elements; no OPQRST structure."),
                        RubricAnchor(score=2, description="Partial HPI; pertinent negatives absent."),
                        RubricAnchor(score=3, description="HPI covered; PMHx/SHx thin."),
                        RubricAnchor(score=4, description="Complete HPI with pertinent positives + negatives + relevant history."),
                        RubricAnchor(score=5, description="Complete + patient-quoted detail clarifying ambiguity."),
                    ],
                ),
                RubricDimension(
                    id="objective_rigor",
                    title="Objective documentation rigor",
                    weight=0.20,
                    anchors=[
                        RubricAnchor(score=1, description="Vitals or focused exam absent."),
                        RubricAnchor(score=2, description="Vitals only; no focused exam."),
                        RubricAnchor(score=3, description="Vitals + general exam; targeted exam thin."),
                        RubricAnchor(score=4, description="Focused exam aligned to chief complaint; results documented."),
                        RubricAnchor(score=5, description="All above + clear separation of observed vs. reported."),
                    ],
                ),
                RubricDimension(
                    id="differential_breadth",
                    title="Differential diagnosis breadth incl. can't-miss",
                    weight=0.25,
                    anchors=[
                        RubricAnchor(score=1, description="Single diagnosis; no differential."),
                        RubricAnchor(score=2, description="Two-three options; no can't-miss."),
                        RubricAnchor(score=3, description="Differential present; one can't-miss listed."),
                        RubricAnchor(score=4, description="Prioritized differential incl. ACS, dissection, PE, pneumothorax."),
                        RubricAnchor(score=5, description="Differential with reasoning per item, including risk stratification."),
                    ],
                ),
                RubricDimension(
                    id="risk_stratification",
                    title="Risk stratification",
                    weight=0.15,
                    anchors=[
                        RubricAnchor(score=1, description="None."),
                        RubricAnchor(score=2, description="Implicit risk ordering only."),
                        RubricAnchor(score=3, description="One scoring tool referenced (HEART, Wells, etc.)."),
                        RubricAnchor(score=4, description="Score applied with components."),
                        RubricAnchor(score=5, description="Score + disposition implication called out."),
                    ],
                ),
                RubricDimension(
                    id="plan_completeness",
                    title="Plan completeness (per-problem)",
                    weight=0.15,
                    anchors=[
                        RubricAnchor(score=1, description="No plan."),
                        RubricAnchor(score=2, description="Plan addresses one issue only."),
                        RubricAnchor(score=3, description="Plan covers diagnostics + treatment; disposition unclear."),
                        RubricAnchor(score=4, description="Per-problem plan with disposition + follow-up."),
                        RubricAnchor(score=5, description="Plus shared decision-making and patient education noted."),
                    ],
                ),
                RubricDimension(
                    id="documentation_quality",
                    title="Documentation quality (clarity, structure)",
                    weight=0.05,
                    anchors=[
                        RubricAnchor(score=1, description="Disorganized; sections conflated."),
                        RubricAnchor(score=2, description="Some structure; assessment leaks into S/O."),
                        RubricAnchor(score=3, description="Clear sections; minor leaks."),
                        RubricAnchor(score=4, description="Clean SOAP structure."),
                        RubricAnchor(score=5, description="Clean structure + concise, scannable."),
                    ],
                ),
            ]
        ),
        capabilities=[
            CapabilityWiring(kind=CapabilityKind.LLM_RUBRIC),
            CapabilityWiring(kind=CapabilityKind.CORPUS_GROUNDED_EVIDENCE, config={"k": 5}),
            CapabilityWiring(
                kind=CapabilityKind.STRUCTURAL_CHECK,
                config={"required_sections": ["subjective", "objective", "assessment", "plan"]},
            ),
        ],
        challenge_templates=[
            "Write a SOAP note for a 58yo male with new substernal chest pressure.",
            "Critique the attached SOAP note and identify missing differentials.",
        ],
        pathway_archetypes=["read_and_annotate", "reproduce_from_spec", "modify_with_constraint", "self_critique"],
        exemplar_prompts={
            "great": "Compose an attending-quality SOAP note covering all OPQRST, prioritized differential including can't-miss, applied HEART score, and per-problem plan.",
            "medium": "Compose a competent resident-level SOAP note that misses one can't-miss diagnosis and lacks risk stratification.",
            "weak": "Compose a junior SOAP note that only addresses ACS without ddx, misses risk stratification, and has a single-line plan.",
        },
        meta_critique_score=0.95,
        has_corpus=True,
        version=1,
        authored_by="seed",
        created_at=_now(),
        updated_at=_now(),
    )


def _build_python_review_spec() -> SkillSpec:
    return SkillSpec(
        id="seed-python-review-001",
        goal_text="Write idempotent worker code for a job queue (Python).",
        audience_hint="mid-level Python engineer",
        artifact_kind=ArtifactKind.CODE,
        stakes_class=StakesClass.LOW,
        rubric=Rubric(
            dimensions=[
                RubricDimension(
                    id="correctness",
                    title="Correctness on inputs",
                    weight=0.30,
                    anchors=[
                        RubricAnchor(score=1, description="Doesn't run; obvious bugs."),
                        RubricAnchor(score=2, description="Runs but happy-path-only; edges break."),
                        RubricAnchor(score=3, description="Works on common inputs; edge cases unclear."),
                        RubricAnchor(score=4, description="Correct including reasonable edges."),
                        RubricAnchor(score=5, description="Correct + edges visibly handled with comments / tests."),
                    ],
                ),
                RubricDimension(
                    id="idempotency",
                    title="Idempotency under retries",
                    weight=0.25,
                    anchors=[
                        RubricAnchor(score=1, description="No idempotency consideration."),
                        RubricAnchor(score=2, description="Hopes for idempotency without enforcing it."),
                        RubricAnchor(score=3, description="Idempotency key used but partial."),
                        RubricAnchor(score=4, description="Idempotency enforced via key + persisted dedupe."),
                        RubricAnchor(score=5, description="Plus explicit semantics for partial-success retries."),
                    ],
                ),
                RubricDimension(
                    id="failure_handling",
                    title="Failure handling & observability",
                    weight=0.20,
                    anchors=[
                        RubricAnchor(score=1, description="Bare except / no logging."),
                        RubricAnchor(score=2, description="Generic exception handling; print only."),
                        RubricAnchor(score=3, description="Targeted exceptions; some structured logging."),
                        RubricAnchor(score=4, description="Specific exceptions, structured logs, retry policy."),
                        RubricAnchor(score=5, description="All above + DLQ / poison-message strategy."),
                    ],
                ),
                RubricDimension(
                    id="testability",
                    title="Testability",
                    weight=0.15,
                    anchors=[
                        RubricAnchor(score=1, description="Not unit-testable; tight coupling."),
                        RubricAnchor(score=2, description="Hard to test; state hidden."),
                        RubricAnchor(score=3, description="Testable with effort; some seams."),
                        RubricAnchor(score=4, description="Pure functions where possible; interfaces injectable."),
                        RubricAnchor(score=5, description="Plus example tests included."),
                    ],
                ),
                RubricDimension(
                    id="readability",
                    title="Readability & idiomatic Python",
                    weight=0.10,
                    anchors=[
                        RubricAnchor(score=1, description="Unreadable / non-idiomatic."),
                        RubricAnchor(score=2, description="Names unclear; long functions."),
                        RubricAnchor(score=3, description="Acceptable; minor smells."),
                        RubricAnchor(score=4, description="Clean; idiomatic; type-hinted."),
                        RubricAnchor(score=5, description="Excellent — would merge as-is."),
                    ],
                ),
            ]
        ),
        capabilities=[
            CapabilityWiring(kind=CapabilityKind.LLM_RUBRIC),
            CapabilityWiring(kind=CapabilityKind.CODE_LINT, config={"language": "python"}),
            CapabilityWiring(kind=CapabilityKind.CODE_SANDBOX_EXECUTE, config={"language": "python", "timeout_seconds": 5}),
        ],
        challenge_templates=[
            "Implement a `process_message(payload, idempotency_key) -> Result` worker.",
            "Refactor an attached non-idempotent worker to be idempotent under retries.",
        ],
        pathway_archetypes=[
            "reproduce_from_spec",
            "modify_with_constraint",
            "design_from_scratch",
            "self_critique",
        ],
        exemplar_prompts={
            "great": "Produce a Python worker that is correct, idempotent via persisted key, with structured logging, retry policy, DLQ, and 3 unit tests.",
            "medium": "Produce a Python worker that handles happy path and one failure mode with logging but no DLQ, partial idempotency.",
            "weak": "Produce a Python worker that just calls the handler with a bare except clause, no idempotency or logging.",
        },
        meta_critique_score=0.90,
        has_corpus=False,
        version=1,
        authored_by="seed",
        created_at=_now(),
        updated_at=_now(),
    )


def main() -> int:
    seeds = [_build_system_design_spec(), _build_soap_spec(), _build_python_review_spec()]
    inserted = 0
    skipped = 0
    for spec in seeds:
        if get_spec(spec.id) is not None:
            print(f"· {spec.id} already seeded, skipping")
            skipped += 1
            continue
        insert_spec(spec)
        print(f"✓ inserted {spec.id} — {spec.goal_text[:60]}…")
        inserted += 1

    # Corpus seeding for SOAP requires OPENAI_API_KEY (embedding call).
    # Skipped silently otherwise so `make demo-seed` works keyless.
    import os

    if os.environ.get("OPENAI_API_KEY") and inserted:
        try:
            import asyncio

            from flo101_api.corpus.ingest import ingest_documents

            async def _seed_corpus() -> None:
                soap_spec = _build_soap_spec()
                if get_spec(soap_spec.id) is not None:
                    res = await ingest_documents(
                        spec_id=soap_spec.id,
                        documents=[
                            IngestDocument(
                                source="soap_note_standards.md",
                                content=_SOAP_CORPUS,
                                metadata={"seed": "true"},
                            )
                        ],
                    )
                    print(f"✓ seeded corpus: {res.chunks_added} chunks for SOAP spec")

            asyncio.run(_seed_corpus())
        except Exception as exc:  # pragma: no cover
            print(f"⚠ corpus seed skipped: {exc}")

    print(f"\nseed: {inserted} inserted, {skipped} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
