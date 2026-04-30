import type { Rubric, SkillSpec } from "@flo101/api-types";

import { Accordion } from "./Accordion";

interface SkillSummaryProps {
  spec: SkillSpec;
}

export function SkillSummary({ spec }: SkillSummaryProps) {
  return (
    <section className="rounded-xl border border-[--color-border] bg-[--color-surface]">
      <header className="flex items-start justify-between gap-4 px-4 py-3">
        <div className="min-w-0">
          <h2 className="truncate text-sm font-medium text-[--color-fg]">
            {spec.goal_text}
          </h2>
          <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[10px] text-[--color-fg-faint]">
            <Pill label={spec.artifact_kind} />
            <Pill label={`${spec.stakes_class} stakes`} />
            {spec.audience_hint && <Pill label={spec.audience_hint} />}
            {spec.has_corpus && (
              <Pill label="corpus" tone="accent" />
            )}
            <span className="ml-auto tabular-nums text-[--color-fg-faint]">
              meta {spec.meta_critique_score.toFixed(2)}
            </span>
          </div>
        </div>
      </header>
      <div className="border-t border-[--color-border] px-4">
        <Accordion
          resetKey={spec.id}
          title={
            <span className="text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
              Rubric
            </span>
          }
          meta={
            <span className="tabular-nums">
              {spec.rubric.dimensions.length} dimensions
            </span>
          }
        >
          <RubricList rubric={spec.rubric} />
        </Accordion>
      </div>
    </section>
  );
}

function RubricList({ rubric }: { rubric: Rubric }) {
  return (
    <ul className="space-y-2">
      {rubric.dimensions.map((d) => (
        <li
          key={d.id}
          className="flex items-baseline justify-between gap-3 text-xs"
        >
          <span className="min-w-0 flex-1">
            <span className="text-[--color-fg]">{d.title}</span>
            <span className="ml-2 font-mono text-[10px] text-[--color-fg-faint]">
              {d.id}
            </span>
          </span>
          <span className="tabular-nums text-[--color-fg-dim]">
            weight {d.weight.toFixed(2)}
          </span>
        </li>
      ))}
    </ul>
  );
}

function Pill({
  label,
  tone = "default",
}: {
  label: string;
  tone?: "default" | "accent";
}) {
  const cls =
    tone === "accent"
      ? "border-[--color-accent]/30 text-[--color-accent]"
      : "border-[--color-border] text-[--color-fg-dim]";
  return (
    <span
      className={`inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] tracking-wide ${cls}`}
    >
      {label}
    </span>
  );
}
