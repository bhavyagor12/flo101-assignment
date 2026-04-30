import type {
  CapabilityResult,
  DimensionScore,
  Evaluation,
  RubricDimension,
  SafetyDisposition,
  SkillSpec,
} from "@flo101/api-types";

import { Accordion } from "./Accordion";

interface EvaluationResultProps {
  evaluation: Evaluation;
  spec: SkillSpec;
}

const dispositionMessage: Record<
  SafetyDisposition,
  { label: string; tone: "ok" | "warn" | "danger" }
> = {
  self_evaluated: { label: "Self-evaluated", tone: "ok" },
  human_review_suggested: { label: "Human review suggested", tone: "warn" },
  expert_review_required: {
    label: "Expert review required. Score withheld.",
    tone: "danger",
  },
  refused: { label: "Refused", tone: "danger" },
};

export function EvaluationResult({ evaluation, spec }: EvaluationResultProps) {
  const disp = dispositionMessage[evaluation.safety_disposition];
  const dimByID = new Map(spec.rubric.dimensions.map((d) => [d.id, d]));
  const overall = evaluation.overall_score;

  return (
    <article className="animate-result-enter rounded-xl border border-[--color-border] bg-[--color-surface]">
      <header className="flex items-start justify-between gap-4 border-b border-[--color-border] px-5 py-4">
        <div>
          <DispositionBadge tone={disp.tone} label={disp.label} />
          {evaluation.refused_reason && (
            <p className="mt-2 max-w-md text-[11px] leading-relaxed text-[--color-fg-dim]">
              {evaluation.refused_reason}
            </p>
          )}
        </div>
        <div className="flex flex-col items-end leading-none">
          <div className="flex items-baseline gap-1.5">
            <span className="text-3xl font-semibold tabular-nums tracking-tight">
              {overall === null || overall === undefined
                ? "n/a"
                : overall.toFixed(2)}
            </span>
            <span className="text-xs text-[--color-fg-faint]">/ 5</span>
          </div>
          <span className="mt-1 text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
            overall
          </span>
        </div>
      </header>

      {evaluation.dimension_scores.length > 0 && (
        <ul className="divide-y divide-[--color-border]">
          {evaluation.dimension_scores.map((d, i) => (
            <DimensionRow
              key={d.dimension_id}
              score={d}
              dim={dimByID.get(d.dimension_id)}
              orderIndex={i}
            />
          ))}
        </ul>
      )}

      {(evaluation.gaps.length > 0 || evaluation.next_step) && (
        <section className="border-t border-[--color-border] px-5 py-4">
          {evaluation.next_step && (
            <div className="rounded-md bg-[--color-accent-soft] p-4">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase tracking-wider text-[--color-accent]">
                  Next step
                </span>
                <span className="text-[10px] tabular-nums text-[--color-accent]/80">
                  ~{evaluation.next_step.estimated_minutes} min
                </span>
              </div>
              <h3 className="mt-1.5 text-sm font-medium text-[--color-fg]">
                {evaluation.next_step.title}
              </h3>
              <p className="mt-1.5 text-xs leading-relaxed text-[--color-fg-dim]">
                {evaluation.next_step.rationale}
              </p>
            </div>
          )}

          {evaluation.gaps.length > 0 && (
            <div className="mt-4">
              <div className="mb-2 text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
                Gaps · {evaluation.gaps.length}
              </div>
              <ul className="space-y-1.5 text-xs">
                {evaluation.gaps.map((g, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <SeverityChip severity={g.severity} />
                    <span className="text-[--color-fg-dim]">
                      {g.description}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {evaluation.capability_results.length > 0 && (
        <section className="border-t border-[--color-border] px-5">
          <Accordion
            title={
              <span className="text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
                Capability checks
              </span>
            }
            meta={<CapabilityCounts results={evaluation.capability_results} />}
          >
            <ul className="space-y-1.5 text-xs">
              {evaluation.capability_results.map((r, i) => (
                <li
                  key={i}
                  className="flex items-baseline justify-between gap-3"
                >
                  <span className="font-mono text-[11px] text-[--color-fg-dim]">
                    {r.kind}
                  </span>
                  <span className="flex items-center gap-2">
                    <CapabilityStatus status={r.status} />
                    <span className="tabular-nums text-[10px] text-[--color-fg-faint]">
                      {r.duration_ms}ms
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          </Accordion>
        </section>
      )}
    </article>
  );
}

function DimensionRow({
  score,
  dim,
  orderIndex,
}: {
  score: DimensionScore;
  dim?: RubricDimension;
  orderIndex: number;
}) {
  const scoreTone =
    score.score <= 2
      ? "text-[--color-warn]"
      : score.score >= 4
        ? "text-[--color-accent]"
        : "text-[--color-fg]";

  return (
    <li
      className="animate-row-stagger px-5 py-4"
      style={{ animationDelay: `${orderIndex * 35}ms` }}
    >
      <div className="flex items-baseline justify-between gap-4">
        <h3 className="text-[13px] font-medium text-[--color-fg]">
          {dim?.title ?? score.dimension_id}
        </h3>
        <ScoreMeter score={score.score} tone={scoreTone} />
      </div>
      <div className="mt-0.5 flex items-baseline gap-2 text-[10px] text-[--color-fg-faint]">
        <span className="tabular-nums">conf {score.confidence.toFixed(2)}</span>
        {dim && (
          <span className="tabular-nums">weight {dim.weight.toFixed(2)}</span>
        )}
      </div>
      <p className="mt-2 text-xs leading-relaxed text-[--color-fg-dim]">
        {score.feedback}
      </p>
      {score.evidence.length > 0 && (
        <details className="group mt-2">
          <summary className="cursor-pointer list-none text-[10px] uppercase tracking-wider text-[--color-fg-faint] transition-colors hover:text-[--color-fg-dim] [&::-webkit-details-marker]:hidden">
            <span className="inline-block transition-transform duration-150 group-open:rotate-90">
              ›
            </span>{" "}
            {score.evidence.length} evidence item
            {score.evidence.length === 1 ? "" : "s"}
          </summary>
          <ul className="mt-2 space-y-1.5 text-[11px]">
            {score.evidence.map((e, ei) => (
              <li key={ei} className="text-[--color-fg-dim]">
                <span className="mr-1.5 font-mono text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
                  {e.source}
                </span>
                {e.location && (
                  <span className="mr-1.5 text-[--color-fg-faint]">
                    {e.location}
                  </span>
                )}
                <span>
                  {e.content.slice(0, 280)}
                  {e.content.length > 280 ? "…" : ""}
                </span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </li>
  );
}

function ScoreMeter({ score, tone }: { score: number; tone: string }) {
  return (
    <span className="flex items-center gap-2">
      <span
        aria-hidden
        className="flex items-center gap-0.5"
        title={`${score}/5`}
      >
        {[1, 2, 3, 4, 5].map((n) => (
          <span
            key={n}
            className={`h-1 w-3 rounded-full ${
              n <= score
                ? score <= 2
                  ? "bg-[--color-warn]"
                  : score >= 4
                    ? "bg-[--color-accent]"
                    : "bg-[--color-fg]"
                : "bg-[--color-border]"
            }`}
          />
        ))}
      </span>
      <span className={`font-mono text-xs tabular-nums ${tone}`}>{score}</span>
      <span className="text-xs text-[--color-fg-faint]">/5</span>
    </span>
  );
}

function DispositionBadge({
  tone,
  label,
}: {
  tone: "ok" | "warn" | "danger";
  label: string;
}) {
  const cls =
    tone === "ok"
      ? "border-[--color-accent]/50 text-[--color-accent]"
      : tone === "warn"
        ? "border-[--color-warn]/50 text-[--color-warn]"
        : "border-[--color-danger]/50 text-[--color-danger]";
  const dotCls =
    tone === "ok"
      ? "bg-[--color-accent]"
      : tone === "warn"
        ? "bg-[--color-warn]"
        : "bg-[--color-danger]";
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-[11px] ${cls}`}
    >
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${dotCls}`} />
      {label}
    </span>
  );
}

function SeverityChip({ severity }: { severity: string }) {
  const cls =
    severity === "critical"
      ? "border-[--color-danger]/40 text-[--color-danger]"
      : severity === "major"
        ? "border-[--color-warn]/40 text-[--color-warn]"
        : "border-[--color-border] text-[--color-fg-faint]";
  return (
    <span
      className={`flex-none rounded border px-1.5 py-0.5 text-[9px] uppercase tracking-wider ${cls}`}
    >
      {severity}
    </span>
  );
}

function CapabilityStatus({ status }: { status: string }) {
  const cls =
    status === "passed"
      ? "text-[--color-accent]"
      : status === "failed"
        ? "text-[--color-danger]"
        : "text-[--color-fg-faint]";
  return (
    <span className={`text-[10px] uppercase tracking-wider ${cls}`}>
      {status}
    </span>
  );
}

function CapabilityCounts({ results }: { results: CapabilityResult[] }) {
  const counts = results.reduce<Record<string, number>>((acc, r) => {
    acc[r.status] = (acc[r.status] ?? 0) + 1;
    return acc;
  }, {});
  return (
    <span className="flex items-center gap-2 text-[10px] tabular-nums">
      {counts.passed && (
        <span className="text-[--color-accent]">{counts.passed} ok</span>
      )}
      {counts.failed && (
        <span className="text-[--color-danger]">
          {counts.failed} fail
        </span>
      )}
      {counts.skipped && (
        <span className="text-[--color-fg-faint]">
          {counts.skipped} skipped
        </span>
      )}
    </span>
  );
}
