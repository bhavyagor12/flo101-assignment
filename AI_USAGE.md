# AI Usage Disclosure

I used AI heavily while building this submission. The model generated a
large share of the implementation, tests, and first-draft docs. I directed
the architecture, reviewed the code, rejected weak designs, and made the
final product and scope decisions.

## Where AI Helped

- Scaffolding the FastAPI, LangGraph, React, Docker, and typed API layers.
- Drafting prompts, Pydantic models, tests, and documentation.
- Iterating on UI polish and deployment scripts.
- Generating first-pass eval fixtures and sample artifacts.

## Human Decisions And Corrections

- Chose Track C and kept scope on the Critic Agent rather than building all
  three tracks.
- Rejected a narrow PRD-only version; the final system evaluates design docs,
  code, SQL, SOAP notes, and mixed artifacts through synthesized SkillSpecs.
- Rejected domain YAML packs; domain behavior comes from generated SkillSpecs,
  wired capabilities, and optional uploaded corpora.
- Switched from an unnecessary Next.js scaffold to Vite + React because the
  backend owns all application logic.
- Added stricter tests after early versions only checked that code "ran":
  lint now asserts a concrete `F401`, sandbox asserts exact stdout, and graph
  tests use a fake gateway to cover refusal, completion, fallback next steps,
  expert review, and validation failure.
- Fixed issues found in review: skipped capabilities are explicit, corpus
  upload retrofits the spec capability, OpenRouter retry handling actually
  retries, completed evaluations always produce a next step, and graph runs
  have a wall-clock timeout.
- Removed or rewrote AI-sounding docs and comments so the final docs focus on
  concrete system behavior, eval outputs, failure modes, and tradeoffs.

## What Was Verified

- Real evaluations were run through the app.
- Offline and fake-gateway eval tests pass.
- The web build and Docker AWS compose build pass.
- The EC2 deployment path is documented in `DEPLOY_AWS.md`.

Curator and Composer were not built; they are intentionally out of scope for
Track C.
