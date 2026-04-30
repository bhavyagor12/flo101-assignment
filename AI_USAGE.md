# AI Usage Disclosure

This implementation was built end-to-end with **Claude Opus 4.7** (Claude
Code CLI). The model produced most of the source; I (Bhavya) drove the
architecture and reviewed every commit.

The honest version of this is a list of redirects — places where the
model produced something plausible and I rejected it for something
better. Those are the actual decisions of the build. In rough order:

1. **Track scope.** The brief invites picking one of three tracks. The
   model defaulted to "smallest useful Track C, narrow domain demo" —
   anchored on PRD-writing only. I pushed back: the system needs to
   handle engineer / student / doctor / designer artifacts, and the demo
   needs to prove that across more than one persona. PRD-only would
   have read as scope-cutting.

2. **No config-pack architecture.** The model proposed
   `domain_packs/<name>.yaml` as the way to add new skills. I rejected
   it. YAML-per-domain is the *passive content* model flo101 explicitly
   says it isn't — it bottlenecks on author hours and can't handle the
   long tail. The model then produced the synthesizer-driven SkillSpec
   design, which is the actual differentiator.

3. **Vite, not Next.js.** The model scaffolded Next.js 15 first. Once
   it was clear the FastAPI backend owned all logic, I redirected:
   Next.js's strengths (RSC, server actions) are unused; pay setup +
   bundle cost for nothing. Switched mid-build to Vite + React 19 +
   TanStack Query against a typed API client.

4. **No time budgeting.** The model kept producing per-task hour
   estimates. I told it to stop and just ship — estimates are noise in
   an iterative session.

5. **Tooling expectations.** `make setup`, Turborepo + pnpm workspaces,
   Docker compose with healthchecks, end-to-end type safety (Pydantic
   → OpenAPI → openapi-typescript → TanStack Query hooks), strict
   pyright + strict TS. Specified up front; non-negotiable.

6. **First-pass code review (9 issues found).** After v1 was passing I
   read it and flagged:
   - `next_step` was optional on completed evaluations; users would
     see a score with no action.
   - Corpus uploaded to a spec synthesized without it never actually
     surfaced in evaluation, because the capability wasn't wired
     retroactively.
   - The chat-retry block was catching retryable errors *before*
     tenacity could retry them, defeating the retry policy.
   - `CapabilityResult.success: bool` conflated "passed", "failed",
     and "skipped" — an unsupported lint check looked like a successful
     one.
   - Lint and sandbox tests asserted "either it ran successfully or
     not", which always passes. Made them assert specific behaviour
     (F401 for lint, exact stdout for sandbox).
   - No fake-LLM test layer, so graph paths weren't tested at all.
   - Frontend `setTimeout` hack to sync state in render. Replaced with
     a `useEffect` keyed on spec id.
   - `citation_resolve` capability advertised but never implemented.
     Removed it from the enum.
   - No request-level timeout. A slow LLM call could hang for minutes.
     Added `asyncio.timeout` that produces a structured FAILED
     evaluation.

7. **Doc + comment review.** First-draft docs and many source
   docstrings read AI-generated — phrases like "load-bearing,"
   "single boundary," "first-class," "kernel," "production would…"
   appeared throughout. I made the model:
   - cut comments narrating obvious code, keep only ones explaining
     non-obvious constraints / safety / tradeoffs;
   - replace AI-tells with normal language;
   - add concrete evidence — sample SkillSpec JSON, sample Evaluation
     JSON, a real demo curl, refusal and timeout response shapes;
   - rewrite the calibration eval fixtures from "WEAK_PRD / GREAT_PRD"
     placeholders into realistic URL-shortener system designs;
   - demote unimplemented capabilities from the main narrative;
   - rewrite this file (AI_USAGE.md) to list specific redirects
     rather than "model authored most code."

8. **`.gitignore` audit.** Asked the model to widen the ignore set
   beyond the first-pass list — `.eslintcache`, vite `*.timestamp-*`,
   `*.local`, sqlite WAL/SHM files, `.swc/`, coverage outputs. Verified
   `git status --ignored` showed only caches/venv/data getting ignored
   and no source files surface as untracked unintentionally.

## What the model did well unaided

- Type-gen pipeline (Pydantic → app.openapi() → openapi-typescript)
  scaffolded first try and didn't drift.
- Typed exception hierarchy with `to_model()` for serialization — a
  clean separation between raised exceptions and wire-format error
  objects, which I hadn't asked for explicitly.
- LangGraph wiring (TypedDict state with `NotRequired` fields,
  monkeypatch-friendly imports for the FakeGateway) — got it right
  on the first pyright pass.

## What the model did poorly without correction

- Initial scope was PRD-only.
- Initial extensibility was config files.
- Initial frontend was Next.js where Vite was correct.
- Initial docs were dense with AI-prose tells.
- Initial tests asserted "things ran" rather than "things produced
  the right answer."
- Stub capabilities (`citation_resolve`) were left advertised in the
  main narrative as if implemented.

## Tools

Claude Opus 4.7 (1M-context) via Claude Code · pnpm 10 · uv 0.11 ·
Turbo 2 · Vite 6 · Docker 28 · LangGraph (latest) · LangSmith ·
openai SDK · sqlite-vec · Anthropic prompt caching via OpenRouter.

## What I did not do

- Run a real evaluation against live models. The calibration tests are
  written to be runnable with keys; I shipped the architecture, not
  the spend.
- Deploy this. `make setup` brings everything up locally.
- Build the Curator or Composer agents. Both are out of scope for
  Track C.
