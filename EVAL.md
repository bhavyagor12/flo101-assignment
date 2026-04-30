# Evaluation Note

## What a real evaluation looks like

The most useful artifact for understanding this build is the actual shape
of an `Evaluation` for a realistically-thin system design. Submitted
artifact:

```markdown
# URL shortener

Build a service that shortens long URLs. Use a database to store mappings.
Cache popular URLs.
```

API call:

```bash
curl -X POST localhost:8000/spec/seed-system-design-001/evaluate \
  -H 'content-type: application/json' \
  -d '{"kind":"mixed","content":"# URL shortener\n\nBuild...","metadata":{}}'
```

Response (trimmed for readability):

```json
{
  "id": "01HZX0YJ...",
  "spec_id": "seed-system-design-001",
  "artifact_id": "01HZX0YA...",
  "status": "completed",
  "safety_disposition": "self_evaluated",
  "overall_score": 1.65,
  "dimension_scores": [
    {
      "dimension_id": "problem_framing",
      "score": 1,
      "confidence": 0.95,
      "feedback": "No requirements stated — neither functional nor non-functional. No scale numbers, no out-of-scope decisions. The artifact jumps to 'a database' without naming the problem.",
      "evidence": [
        {"source": "artifact", "content": "Build a service that shortens long URLs.", "location": "line 3", "confidence": 1.0}
      ]
    },
    {
      "dimension_id": "capacity_estimation",
      "score": 1,
      "confidence": 0.95,
      "feedback": "Zero numbers. No QPS, no storage estimate, no cache hit-rate target.",
      "evidence": [
        {"source": "artifact", "content": "Cache popular URLs.", "location": "line 5", "confidence": 1.0}
      ]
    },
    {
      "dimension_id": "scale_strategies",
      "score": 2,
      "confidence": 0.7,
      "feedback": "Mentions caching but does not commit to a mechanism, hit-rate target, or sharding strategy.",
      "evidence": []
    }
  ],
  "gaps": [
    {"description": "No QPS or storage estimate", "severity": "major"},
    {"description": "No failure-mode discussion", "severity": "major"},
    {"description": "No tradeoffs articulated", "severity": "minor"}
  ],
  "next_step": {
    "title": "Add a 100-word capacity-estimation section",
    "rationale": "capacity_estimation scored lowest at 1/5. Defining read QPS, write QPS, and storage drives every downstream decision (sharding, caching, replication).",
    "estimated_minutes": 15
  },
  "capability_results": [
    {"kind": "llm_rubric", "status": "skipped", "output": {"reason": "deferred to rubric_critique node"}, "duration_ms": 0},
    {"kind": "structural_check", "status": "passed", "output": {"char_count": 142, "missing_required_sections": []}, "duration_ms": 1}
  ],
  "trace_id": null,
  "created_at": "2026-04-30T08:14:22.301Z",
  "completed_at": "2026-04-30T08:14:34.119Z"
}
```

Things to notice against this:

- The score is conservative and the feedback cites the artifact verbatim.
  When a critic doesn't cite, it's hallucinating.
- `next_step` is one action with a time estimate and a rationale tied to
  the lowest-scoring dimension. If the LLM omits it (which happens), the
  assemble node synthesizes one deterministically.
- Wall-clock is ~12s: ~150ms safety_input (Haiku), ~10s rubric_critique
  (Sonnet, 3 dims × ~3 evidence quotes), ~1s safety_disposition.

## What refusal and timeout look like

Adversarial:

```json
{
  "status": "refused",
  "safety_disposition": "refused",
  "overall_score": null,
  "dimension_scores": [],
  "refused_reason": "request seeks instruction on creating malicious tooling"
}
```

The refusal happens at the `safety_input` Haiku call before any work.
Only one LLM call billed.

Wall-clock timeout (`EVALUATION_WALLCLOCK_SECONDS=90`):

```json
{
  "status": "failed",
  "safety_disposition": "refused",
  "overall_score": null,
  "refused_reason": "evaluation exceeded the wall-clock budget of 90s. Try a shorter artifact or retry shortly.",
  "capability_results": []
}
```

The artifact is persisted before the timeout fires, so a retry with the
same content is cheap to attempt.

## Tests

Two tiers, separated by which require API keys.

### Offline (always run, ~1s total)

`apps/api/evals/test_offline_capabilities.py` plus
`apps/api/tests/test_critic_paths.py`. Highlights:

- **`test_python_lint_flags_obvious_violations`** — feeds `import os\n`
  to the lint capability; asserts ruff returns `F401` (unused import).
  Skips if ruff isn't on PATH; does not pass on a swallowed error.
- **`test_sandbox_executes_and_captures_stdout`** — runs `print('hello')`
  through the sandbox; asserts `stdout_snippet == "hello\n"` and exit 0.
- **`test_critic_completed_path`** (faked LLM) — queues SafetyVerdict +
  CritiqueResult + DispositionResult through `FakeGateway`, asserts the
  final Evaluation has 6 dimension scores, the right disposition, and 3
  total LLM calls.
- **`test_completed_eval_synthesizes_fallback_next_step`** — queues a
  CritiqueResult with `next_step=None`, asserts assemble synthesizes one
  targeting the lowest-scoring dimension (`capacity_estimation`).
- **`test_expert_review_withholds_overall_score`** — disposition
  `expert_review_required` → `overall_score` is `None`, dimension scores
  still surface.
- **`test_critic_refusal_short_circuits`** — only 1 LLM call happens; no
  capability, rubric, or disposition calls.
- **`test_validation_failure_propagates`** — gateway raises
  `ValidationFailedException`; the graph propagates it rather than
  swallowing.

```
$ uv run pytest tests/ evals/test_offline_capabilities.py
14 passed in 0.93s
```

### Calibration (requires keys)

`apps/api/evals/test_critic_calibration.py`:

- **`test_strong_design_outscores_weak_design`** — submits a fully
  realized URL-shortener design (capacity numbers, sharding strategy,
  cache hit rate, failure modes, tradeoffs) and a deliberately-thin one
  to the same rubric. Asserts `mean(strong dims) > mean(weak dims) + 0.5`.
  Also asserts the `capacity_estimation` dimension specifically swings —
  the weak fixture has zero numbers.
- **`test_soap_high_stakes_yields_review_disposition`** — a thin SOAP
  note on a high-stakes spec must come back as
  `expert_review_required` or `human_review_suggested`, never
  `self_evaluated`.

These cost tokens; gated by `OPENROUTER_API_KEY` (and `OPENAI_API_KEY`
for embedding-dependent tests).

## Robustness — failure modes handled

| #  | failure mode                | where                                                                                          |
|----|-----------------------------|------------------------------------------------------------------------------------------------|
| 1  | malformed LLM JSON          | `llm/openrouter_gateway.py` — `structured()` JSON-repair retry loop                            |
| 2  | adversarial input           | `critic/nodes.py` — `safety_input_node`                                                         |
| 3  | high-stakes domain misuse   | `critic/nodes.py` — `safety_disposition_node` withholds score                                   |
| 4  | untrusted code execution    | `critic/capabilities.py` — `_code_sandbox` rlimits + timeout                                    |
| 5  | network / rate-limit errors | `llm/openrouter_gateway.py` — `_chat_completion` tenacity, wraps only after exhaustion          |
| 6  | wall-clock runaway          | `critic/run.py` — `asyncio.timeout()` + persisted FAILED evaluation                              |

## Known limits

- **Synthesizer drift across runs.** Same goal, different invocations
  produce different rubrics. `temperature=0` and prompt caching mitigate
  but don't eliminate. Specs are immutable per id once persisted.
- **Lint capability needs `ruff` on PATH** in the API container — the
  Dockerfile installs the dev group which includes it. If a slim image
  drops dev deps the capability returns `skipped`, not `passed`.
- **Sandbox is process-level isolation only.** A clever script that
  exhausts resources between scheduling and the CPU rlimit firing can
  still affect the API process. E2B / Modal would be the answer for
  truly hostile code.
- **No retry budget per evaluation.** A slow OpenRouter response can
  consume the wall-clock budget on `rubric_critique` alone. The 90s
  default is generous; tighten in `.env` for stricter SLAs.
- **Embedding cost on long corpora.** Chunk count is uncapped per
  upload. A 1MB markdown produces ~500 chunks (~$0.01 to embed). The
  route does not enforce a ceiling.
