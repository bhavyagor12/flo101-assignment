# flo101 — Critic Agent

Evaluates a learner's artifact (text, code, SQL, design doc, SOAP note,
…) against a generated rubric, with cited evidence, named gaps, and one
next-best step. Bring your own knowledge corpus when the domain calls
for grounded evaluation.

This repo is **Track C** of the flo101 Applied AI Engineer assessment.

## Quick start

Requires Docker + Make. Copy `.env.example` to `.env` and fill the
`OPENROUTER_API_KEY` (handles both chat and embeddings), then:

```bash
make setup            # install deps, build images, boot, seed 3 demo specs
```

- API:  <http://localhost:8000/docs>
- Web:  <http://localhost:3000>

The seeded specs (`system_design`, `soap_note`, `python_review`) make
the UI usable immediately. Synthesizing a brand-new skill from a goal
takes ~3–6 seconds.

## Sample evaluation

`POST /spec/seed-system-design-001/evaluate` with a thin URL-shortener
design returns (truncated):

```json
{
  "status": "completed",
  "overall_score": 1.65,
  "dimension_scores": [
    {"dimension_id": "capacity_estimation", "score": 1, "feedback": "Zero numbers..."}
  ],
  "next_step": {
    "title": "Add a 100-word capacity-estimation section",
    "rationale": "capacity_estimation scored lowest at 1/5...",
    "estimated_minutes": 15
  }
}
```

See `EVAL.md` for the full transcript including refusal and timeout
shapes.

## Commands

```bash
make dev          # hot-reload api + web
make eval         # pytest harness (offline + LLM-gated)
make type-check   # pyright (api) + tsc (web, types)
make type-gen     # Pydantic → OpenAPI → TypeScript
make demo-seed    # re-seed the 3 demo specs
make logs         # tail container logs
make nuke         # stop + remove containers AND volumes (destructive)
```

## Stack

Turborepo + pnpm · Python 3.13 + FastAPI + Pydantic v2 + LangGraph ·
OpenRouter (Opus / Sonnet / Haiku for chat + embeddings) · SQLite +
sqlite-vec · Vite + React 19 + Tailwind v4 + TanStack Query · LangSmith
via `@traceable` · Docker compose v2.

## Docs in this repo

- `ARCHITECTURE.md` — system shape, capability table, robustness
- `PRODUCT.md` — north-star metric and why it's that one
- `EVAL.md` — sample transcripts, test taxonomy, known limits
- `AI_USAGE.md` — what the model authored, what I redirected
- `DEPLOY_AWS.md` — single-instance EC2 deployment
