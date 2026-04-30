import type {
  Evaluation,
  SafetyDisposition,
  SkillSpec,
} from "@flo101/api-types";

interface EvaluationResultProps {
  evaluation: Evaluation;
  spec: SkillSpec;
}

const dispositionMessage: Record<SafetyDisposition, { label: string; tone: "ok" | "warn" | "danger" }> = {
  self_evaluated: { label: "Self-evaluated", tone: "ok" },
  human_review_suggested: { label: "Human review suggested", tone: "warn" },
  expert_review_required: { label: "Expert review required — score withheld", tone: "danger" },
  refused: { label: "Refused", tone: "danger" },
};

export function EvaluationResult({ evaluation, spec }: EvaluationResultProps) {
  const disp = dispositionMessage[evaluation.safety_disposition];
  const dimByID = new Map(spec.rubric.dimensions.map((d) => [d.id, d]));

  return (
    <div className="mt-2 space-y-3 rounded-lg border border-[--color-border] bg-[--color-bg] p-3">
      {/* Disposition banner */}
      <div
        className={`rounded-md border px-3 py-2 text-xs ${toneClass(disp.tone)}`}
      >
        <span className="font-medium">{disp.label}</span>
        {evaluation.refused_reason && (
          <span className="ml-2 opacity-80">— {evaluation.refused_reason}</span>
        )}
      </div>

      {/* Overall + counts */}
      <div className="flex items-center gap-4 text-xs">
        <span className="text-[--color-fg-dim]">Overall:</span>
        <span className="text-base font-semibold">
          {evaluation.overall_score !== null && evaluation.overall_score !== undefined
            ? evaluation.overall_score.toFixed(2)
            : "—"}
        </span>
        <span className="text-[--color-fg-dim]">/ 5</span>
        <span className="ml-auto text-[--color-fg-dim]">
          {evaluation.dimension_scores.length} dims · {evaluation.gaps.length} gaps · {evaluation.capability_results.length} checks
        </span>
      </div>

      {/* Dimension scores */}
      {evaluation.dimension_scores.length > 0 && (
        <div className="space-y-1.5">
          {evaluation.dimension_scores.map((d) => {
            const dim = dimByID.get(d.dimension_id);
            return (
              <div
                key={d.dimension_id}
                className="rounded-md border border-[--color-border] px-2 py-1.5 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">
                    {dim?.title ?? d.dimension_id}
                  </span>
                  <span className="font-mono">
                    {d.score}/5{" "}
                    <span className="text-[--color-fg-dim]">
                      (conf {d.confidence.toFixed(2)})
                    </span>
                  </span>
                </div>
                <p className="mt-1 text-[--color-fg-dim]">{d.feedback}</p>
                {d.evidence.length > 0 && (
                  <details className="mt-1 text-[10px]">
                    <summary className="cursor-pointer text-[--color-fg-dim]">
                      {d.evidence.length} evidence item(s)
                    </summary>
                    <ul className="mt-1 space-y-1">
                      {d.evidence.map((e, i) => (
                        <li
                          key={i}
                          className="border-l-2 border-[--color-border] pl-2 text-[--color-fg-dim]"
                        >
                          <span className="text-[--color-accent]">[{e.source}]</span>{" "}
                          {e.location && <span className="opacity-60">{e.location}: </span>}
                          {e.content.slice(0, 280)}
                          {e.content.length > 280 && "…"}
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Gaps */}
      {evaluation.gaps.length > 0 && (
        <div>
          <div className="text-[10px] uppercase tracking-wide text-[--color-fg-dim]">Gaps</div>
          <ul className="mt-1 space-y-1 text-xs">
            {evaluation.gaps.map((g, i) => (
              <li key={i} className="flex items-start gap-2">
                <span
                  className={`rounded px-1.5 text-[10px] ${severityClass(g.severity)}`}
                >
                  {g.severity}
                </span>
                <span>{g.description}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Next step */}
      {evaluation.next_step && (
        <div className="rounded-md border border-[--color-accent]/40 bg-[--color-accent]/5 px-3 py-2 text-xs">
          <div className="text-[10px] uppercase tracking-wide text-[--color-accent]">
            Next best step · ~{evaluation.next_step.estimated_minutes} min
          </div>
          <div className="mt-1 font-medium">{evaluation.next_step.title}</div>
          <p className="mt-1 text-[--color-fg-dim]">{evaluation.next_step.rationale}</p>
        </div>
      )}
    </div>
  );
}

function toneClass(tone: "ok" | "warn" | "danger"): string {
  if (tone === "ok") return "border-[--color-accent]/40 bg-[--color-accent]/5 text-[--color-accent]";
  if (tone === "warn") return "border-[--color-warn]/50 bg-[--color-warn]/10 text-[--color-warn]";
  return "border-[--color-danger]/50 bg-[--color-danger]/10 text-[--color-danger]";
}

function severityClass(sev: string): string {
  if (sev === "critical") return "bg-[--color-danger]/20 text-[--color-danger]";
  if (sev === "major") return "bg-[--color-warn]/20 text-[--color-warn]";
  return "bg-[--color-fg-dim]/20 text-[--color-fg-dim]";
}
