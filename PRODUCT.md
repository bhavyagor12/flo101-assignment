# Product Note

## Why this matters

flo101's stated thesis is "guided execution, feedback, dynamic learning
flows, and **verifiable proof-of-work** rather than passive content
consumption."

The Critic is the closest expression of that thesis. Content gets you to
"I read it." The artifact and the evaluation get you to "I can do it."
Without rigorous, evidence-cited evaluation of the artifact, the loop
never closes — which is exactly what passive content does.

Picking Track C is a bet on this. Curator (challenge generation) and
Composer (pathway planning) both produce artifacts the Critic evaluates;
getting the Critic right first means the other two are incremental.

## Who it's for

The same architecture serves:

| user           | skill                                  | upload                       |
|----------------|----------------------------------------|------------------------------|
| Engineer       | "design URL shortener at scale"        | a markdown design doc        |
| Junior PM      | "write a 1-page PRD"                   | a markdown brief             |
| Med resident   | "SOAP note for chest pain"             | the note + a guideline PDF   |
| Data analyst   | "SQL for cohort retention"             | a `.sql` file + sample DB    |
| Mid-engineer   | "idempotent worker code"               | a `.py` file + tests         |

Every row goes through the same pipeline. Domain-specific behaviour comes
from the synthesized SkillSpec (rubric language, capability wiring,
stakes class) and any uploaded corpus — not from per-domain code.

## North-star metric

**Median dimension-score lift between consecutive submissions of the same
artifact by the same learner.**

Plain version: when a learner reads the critique, addresses the gap
named in `next_step`, and resubmits, do their dimension scores actually
go up — or are we producing feedback that doesn't compound?

This is the metric most aligned with flo101's thesis. DAU and
time-on-page test whether people show up. Score lift on resubmit tests
whether they get better.

The data is in the table: `evaluations(spec_id, artifact_id,
dimension_scores_json, created_at)`. Computing the metric is
`MAX(score) - MIN(score) GROUP BY (learner_id, spec_id, dimension_id)`
across consecutive evaluations.

## Supporting metrics

- **Critic calibration drift.** Standard deviation of `overall_score`
  on golden artifacts across runs. >0.4 means scores aren't stable;
  >0.7 means the rubric is broken. Tracked weekly.
- **Refusal rate.** How often `safety_input` refuses. Sudden spikes
  indicate prompt-injection probes or a regression in the safety prompt.
- **Expert-review queue length.** High-stakes specs route to a queue;
  length is a leading indicator of expert capacity needed.
- **Cold-start time.** Time from `POST /spec` to first
  `POST /spec/{id}/evaluate` returning. Targets: p50 < 10s, p95 < 25s
  (synthesis is the long pole).

## Why "BYO knowledge" is the right shape

There is no plausible product where flo101 owns enough trustworthy domain
knowledge to evaluate medical, legal, financial, or specialized
engineering work without a domain expert in the loop. The choice
"specialists upload the standards their organization already trusts" is
also the choice that produces evaluations specialists trust.

The bonus: the same upload mechanism lets a single team's engineering
manager upload "our PRD template" and get evaluations that match *their*
idea of good. The lever that makes medical safe makes engineering
culture-fit accurate.

## What ships next

1. **Curator** — concrete challenge per pathway step, grounded in the
   spec's corpus.
2. **Composer** — 3–5 step pathway, re-plans when Critic emits a
   skill_delta indicating the step is too easy or too hard.
3. **Spec evolution loop** — when a learner disputes a score and
   provides reviewer feedback, an evolution record is added; the next
   synthesis weighs it.
4. **Expert review tooling** — a dedicated queue for
   `expert_review_required` evaluations with structured fields for the
   reviewer.
5. **Multi-modal artifacts** — diagrams, screenshots, voice notes; same
   capability-routing pattern with new verifier types.
