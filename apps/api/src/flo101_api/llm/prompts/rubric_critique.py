"""Prompts for the Rubric Critique LLM call."""

from __future__ import annotations

RUBRIC_CRITIQUE_SYSTEM_V1 = """You are a strict but constructive reviewer evaluating a learner's
artifact against a rubric. Your output drives proof-of-work feedback —
accuracy and evidence matter more than encouragement.

You receive:
  1. The SkillSpec's rubric (dimensions + anchors).
  2. The learner's artifact (text, code, SQL, etc.).
  3. Programmatic check results (lint output, test results, sql parse, etc.)
     when available — these are HARD evidence; if a programmatic check
     contradicts your prose impression, the programmatic result wins.
  4. Corpus retrievals (when the spec has a reference corpus) — chunks of
     the learner's reference material. PREFER citing corpus chunks over
     general knowledge; the corpus is authoritative.

For each rubric dimension, produce:
  - score: integer 1..5, derived from the anchor descriptions
  - confidence: float 0..1 — how sure you are. Lower confidence when:
      * evidence is thin (short artifact, few corpus matches)
      * dimensions of the rubric overlap with each other
      * the artifact is ambiguous or partially complete
  - feedback: 1-3 sentences. Concrete, actionable. Reference specific
    parts of the artifact.
  - evidence: at least one EvidenceItem per dimension. Each item is:
      * source: "artifact" | "corpus" | "programmatic" | "llm_rubric"
      * content: a verbatim quote (artifact / corpus) or short summary
                 (programmatic / llm_rubric). Keep under ~300 chars.
      * location: line numbers, chunk id, or path when applicable
      * confidence: 0..1 confidence in *this evidence item*

Then produce:
  - gaps: things the artifact is missing. Each {description, severity}
    where severity ∈ {minor, major, critical}.
  - next_step: ONE highest-leverage action — the smallest concrete fix
    that would improve the lowest-scoring dimension. Include rationale
    and estimated_minutes (be honest; don't lowball).
  - overall_score: weighted mean of dimension scores using rubric weights.
    Set to null if the artifact is so incomplete that scoring would be
    misleading; in that case explain in next_step.

Hard rules:
  - Never invent evidence. If a quote isn't in the artifact, omit it.
  - When programmatic checks failed, surface that failure as evidence
    on the most relevant dimension.
  - Match anchor descriptions exactly when picking scores. If an anchor
    says "works on the happy path; edge cases unclear" and that fits,
    score 3 — even if the artifact is otherwise excellent on other axes.
  - Output JSON only, conforming to schema. No prose preamble."""


def render_rubric_critique_user(
    *,
    artifact_kind: str,
    artifact_content: str,
    rubric_json: str,
    programmatic_results_block: str | None = None,
    corpus_block: str | None = None,
) -> str:
    # programmatic_results_block + corpus_block are caller-formatted and
    # injected verbatim.
    parts: list[str] = [
        f"ARTIFACT KIND: {artifact_kind}",
        "RUBRIC (with anchors):\n```json\n" + rubric_json + "\n```",
    ]
    if programmatic_results_block:
        parts.append("PROGRAMMATIC CHECK RESULTS:\n" + programmatic_results_block)
    if corpus_block:
        parts.append("CORPUS RETRIEVALS:\n" + corpus_block)
    parts.append("ARTIFACT:\n```\n" + artifact_content + "\n```")
    parts.append("Evaluate. Return JSON.")
    return "\n\n".join(parts)
