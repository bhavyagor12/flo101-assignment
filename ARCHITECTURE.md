# Architecture

## What this is

A Critic agent that takes a learner's artifact and a SkillSpec and produces
a rubric-grounded evaluation: per-dimension scores with cited evidence, a
gap list, and exactly one next-best step. The SkillSpec itself is generated
on-demand from a natural-language goal (Opus + a self-critique pass), then
cached, so adding a domain doesn't mean writing config.

## A real SkillSpec

The synthesizer for `"learn to write a SOAP note for chest pain"` produces
this shape (truncated):

```json
{
  "id": "01HZX0M3QC...",
  "goal_text": "learn to write a SOAP note for chest pain",
  "audience_hint": "medical resident",
  "artifact_kind": "text",
  "stakes_class": "high",
  "rubric": {
    "dimensions": [
      {
        "id": "differential_breadth",
        "title": "Differential breadth incl. can't-miss",
        "weight": 0.25,
        "anchors": [
          {"score": 1, "description": "Single diagnosis; no differential."},
          {"score": 3, "description": "Differential present; one can't-miss listed."},
          {"score": 5, "description": "Prioritized differential w/ reasoning per item, risk stratified."}
        ]
      }
    ]
  },
  "capabilities": [
    {"kind": "llm_rubric", "config": {}},
    {"kind": "structural_check", "config": {"required_sections": ["subjective","objective","assessment","plan"]}},
    {"kind": "corpus_grounded_evidence", "config": {"k": 6}}
  ],
  "challenge_templates": ["..."],
  "exemplar_prompts": {"great": "...", "medium": "...", "weak": "..."},
  "meta_critique_score": 0.91
}
```

Two things matter here. First, every rubric dimension has anchored
descriptions per score level — that's what stops the LLM critic from
drifting. Second, `capabilities` is wired by the synthesizer based on
`artifact_kind` and `stakes_class`. A code skill gets `code_lint` and
`code_sandbox_execute` instead. No code branches on domain.

## Critic graph

```
              ┌────────────────┐
              │  safety_input  │  Haiku — refuse pre-graph
              └───┬────────┬───┘
        refused  │        │ allowed
                 ▼        ▼
                       ┌────────────┐
                       │ load_spec  │  SQLite read
                       └─────┬──────┘
                             ▼
                  ┌──────────────────────┐
                  │ capability_runner    │  asyncio.gather of
                  │   structural / lint  │  whatever's wired
                  │   sandbox / sql /    │
                  │   corpus_rag         │
                  └─────────┬────────────┘
                            ▼
                  ┌──────────────────────┐
                  │ rubric_critique      │  Sonnet — anchored
                  │ (rubric + evidence)  │  scoring + evidence
                  └─────────┬────────────┘
                            ▼
                  ┌──────────────────────┐
                  │ safety_disposition   │  Haiku — low/med/high routing,
                  │                      │  withholds score on expert review
                  └─────────┬────────────┘
                            ▼
                       ┌────────────┐
                       │  assemble  │  fallback next_step if LLM omits;
                       │            │  persist Evaluation
                       └─────┬──────┘
                             ▼ END
```

## Capability table (currently implemented)

| capability                 | runs when                                          | output                                |
|----------------------------|----------------------------------------------------|---------------------------------------|
| `llm_rubric`               | always (handled in `rubric_critique` node)         | per-dim scores + evidence             |
| `structural_check`         | always when wired                                  | section coverage, char/word counts    |
| `corpus_grounded_evidence` | `spec.has_corpus`                                  | top-k chunks → evidence with citation |
| `code_lint`                | `artifact.kind ∈ {code, mixed}` and ruff on PATH   | violations (e.g., F401)               |
| `code_sandbox_execute`     | `artifact.kind ∈ {code, mixed}`                    | stdout/stderr, exit code, ms          |
| `sql_parse`                | `artifact.kind == sql`                             | parse error or success                |
| `sql_execute`              | `artifact.kind == sql` + config has `fixture_sql`  | row count + columns                   |

A capability either passes, fails, or is skipped. `skipped` is suppressed
from the rubric prompt so it doesn't read as a passed signal.

## Stack and routing

| layer                  | choice                              | why                                                                     |
|------------------------|-------------------------------------|-------------------------------------------------------------------------|
| LLM transport          | OpenRouter                          | one client, model routing in config                                     |
| Synthesizer + critique | Anthropic Opus 4.7                  | runs once per spec; a bad rubric ruins everything downstream            |
| Rubric critique        | Anthropic Sonnet 4.6                | the workhorse; balanced cost vs. anchored-scoring depth                 |
| Safety gates           | Anthropic Haiku 4.5                 | trivial classification, called twice per evaluation                      |
| Embeddings             | OpenRouter `openai/text-embedding-3-small` | one key, one transport; trade a small per-token premium for simpler ops |
| Tracing                | LangSmith via `@traceable`          | one env var; `Tracer` protocol covers non-LLM spans                     |
| Storage                | SQLite + sqlite-vec                 | one file, vector search inline; switch to Postgres+pgvector at scale    |

## Robustness — six failure modes handled

1. **Malformed LLM JSON.** Pydantic validates structured output; on failure
   the gateway re-prompts with the previous (invalid) text and a repair
   instruction up to 2 times. After exhaustion → typed
   `ValidationFailedException` → 502.
2. **Adversarial input.** `safety_input` Haiku call before any heavy work
   short-circuits the graph straight to `assemble` with `status=refused`.
3. **High-stakes domain.** `safety_disposition` for `expert_review_required`
   withholds `overall_score` and surfaces a structured packet for an
   attending/senior reviewer instead of a numeric grade.
4. **Untrusted code execution.** `subprocess.run(..., preexec_fn=)` with
   `RLIMIT_AS` (memory) and `RLIMIT_CPU` (cpu seconds), wall-clock
   timeout, env scrubbed, `python -I` to suppress site-packages
   discovery from the user's directory.
5. **Network errors / 429.** Retryable openai/openrouter exceptions
   propagate through tenacity (3 attempts, exponential backoff). Wrapping
   to `UpstreamException` happens only after exhaustion or for
   non-retryable APIError.
6. **Wall-clock runaway.** `asyncio.timeout(EVALUATION_WALLCLOCK_SECONDS)`
   wraps `graph.ainvoke`; on overrun, persists a `status=failed`
   evaluation with a clear `refused_reason` instead of hanging the request.

## Cost / quality / latency tradeoff

Model routing is the single biggest tradeoff. Opus once per spec
(synthesize + self-critique, ~6k tokens out, ~$0.30) covers a
multi-month skill; Sonnet runs per evaluation (~3k in, ~1k out, ~$0.02
with prompt caching); Haiku runs twice per evaluation (~$0.001 total).
One Opus call worth of spend buys ~15 evaluations after the cache warms.

If the rubric were a hand-authored YAML you'd save the Opus call but
lose the long tail. The synthesizer is the difference between "add a
domain" being a config commit and being a code change.

## Out of scope for this build

- **Curator** — challenge generation per pathway step.
- **Composer** — multi-step pathway planning with re-plan loop.
- **Spec evolution** — versioned specs are wired, but feedback-driven
  rubric updates aren't.
- **VM-isolated sandbox** — currently process-isolated (rlimits +
  scrubbed env). E2B / Modal / firecracker is the upgrade path.
- **Postgres + pgvector** — the SqliteStore protocol can be reimplemented
  against pg without changing call sites; not done because SQLite is
  enough for one node.
