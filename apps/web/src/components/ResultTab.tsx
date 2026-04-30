import { useState } from "react";

import type {
  CapabilityResult,
  DimensionScore,
  Evaluation,
  EvidenceItem,
  Gap,
  RubricDimension,
  SafetyDisposition,
  SkillSpec,
} from "@flo101/api-types";

import { CollapsibleSection } from "./CollapsibleSection";

interface ResultTabProps {
  evaluation: Evaluation | null;
  spec: SkillSpec | null;
  artifactContent: string;
  artifactFilename: string;
  onRefactor?: () => void;
}

export function ResultTab({
  evaluation,
  spec,
  artifactContent,
  artifactFilename,
  onRefactor,
}: ResultTabProps) {
  if (!evaluation || !spec) {
    return (
      <div className="flex h-full items-center justify-center px-8 py-16 text-center">
        <p className="text-[12px] text-[--color-fg-faint]">
          No evaluation yet. Submit an artifact in the editor to see scores,
          cited evidence, and the recommended next action here.
        </p>
      </div>
    );
  }

  const overall = evaluation.overall_score;
  // The reference shows /100. Our scores are 1-5; multiplying by 20 maps cleanly.
  const overall100 =
    overall === null || overall === undefined ? null : Math.round(overall * 20);
  const dimByID = new Map(spec.rubric.dimensions.map((d) => [d.id, d]));
  const headline = headlineFor(evaluation);
  const elapsed = elapsedSeconds(evaluation);

  return (
    <div className="animate-result-enter text-[12px]">
      <header className="border-b border-[--color-border]">
        <Field label="Target File" value={artifactFilename} mono />
        <Field
          label="Applied Rubric"
          value={spec.goal_text}
        />
      </header>

      <section className="border-b border-[--color-border] px-4 py-4">
        <div className="flex items-baseline gap-3">
          <span className="text-[44px] font-semibold leading-none tracking-tight tabular-nums">
            {overall100 === null ? "—" : overall100}
          </span>
          <span className="text-[14px] text-[--color-fg-faint]">/ 100</span>
          <div className="ml-3 flex flex-col leading-tight">
            <span
              className={`text-[11px] font-semibold uppercase tracking-wider ${headline.tone}`}
            >
              {headline.label}
            </span>
            {elapsed !== null && (
              <span className="mt-0.5 text-[11px] text-[--color-fg-dim]">
                Evaluation completed in {elapsed.toFixed(1)}s
              </span>
            )}
          </div>
        </div>
        {evaluation.refused_reason && (
          <p className="mt-3 text-[11px] leading-relaxed text-[--color-fg-dim]">
            {evaluation.refused_reason}
          </p>
        )}
      </section>

      {evaluation.dimension_scores.length > 0 && (
        <CollapsibleSection title="Dimension Scores">
          <ul className="-mx-2 divide-y divide-[--color-border]">
            {evaluation.dimension_scores.map((d) => (
              <DimensionRow
                key={d.dimension_id}
                score={d}
                dim={dimByID.get(d.dimension_id)}
                artifactContent={artifactContent}
              />
            ))}
          </ul>
        </CollapsibleSection>
      )}

      {evaluation.gaps.length > 0 && (
        <CollapsibleSection title={`Gaps · ${evaluation.gaps.length}`}>
          <ul className="space-y-2">
            {evaluation.gaps.map((g, i) => (
              <GapRow key={i} gap={g} />
            ))}
          </ul>
        </CollapsibleSection>
      )}

      {evaluation.next_step && (
        <section className="border-b border-[--color-border] px-4 py-4">
          <div className="text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
            Recommended Next Action
          </div>
          <p className="mt-2 text-[13px] leading-relaxed text-[--color-fg]">
            {evaluation.next_step.title}.
          </p>
          <p className="mt-1.5 text-[11px] leading-relaxed text-[--color-fg-dim]">
            {evaluation.next_step.rationale}
          </p>
          <button
            type="button"
            onClick={onRefactor}
            className="mt-3 w-full rounded bg-[--color-primary] px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-white transition-colors hover:bg-[--color-primary-hover]"
          >
            Generate revision · {evaluation.next_step.estimated_minutes} min
          </button>
        </section>
      )}

      <CollapsibleSection
        title="Capability Checks"
        defaultOpen={false}
        meta={<CapabilityCounts results={evaluation.capability_results} />}
      >
        {evaluation.capability_results.length === 0 ? (
          <p className="text-[11px] text-[--color-fg-faint]">No checks ran.</p>
        ) : (
          <ul className="space-y-1">
            {evaluation.capability_results.map((r, i) => (
              <li
                key={i}
                className="flex items-center justify-between gap-3 text-[11px]"
              >
                <span className="font-mono text-[--color-fg-dim]">{r.kind}</span>
                <span className="flex items-center gap-2">
                  <CapabilityStatusBadge status={r.status} />
                  <span className="tabular-nums text-[10px] text-[--color-fg-faint]">
                    {r.duration_ms}ms
                  </span>
                </span>
              </li>
            ))}
          </ul>
        )}
      </CollapsibleSection>

      <CollapsibleSection title="Metadata" defaultOpen={false}>
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-[11px]">
          <dt className="text-[--color-fg-faint]">Disposition</dt>
          <dd className="text-[--color-fg-dim]">
            {dispositionLabel(evaluation.safety_disposition)}
          </dd>
          <dt className="text-[--color-fg-faint]">Status</dt>
          <dd className="text-[--color-fg-dim]">{evaluation.status}</dd>
          {evaluation.created_at && (
            <>
              <dt className="text-[--color-fg-faint]">Submitted</dt>
              <dd className="text-[--color-fg-dim]">
                {formatTime(evaluation.created_at)}
              </dd>
            </>
          )}
          {evaluation.completed_at && (
            <>
              <dt className="text-[--color-fg-faint]">Completed</dt>
              <dd className="text-[--color-fg-dim]">
                {formatTime(evaluation.completed_at)}
              </dd>
            </>
          )}
          {evaluation.trace_id && (
            <>
              <dt className="text-[--color-fg-faint]">Trace</dt>
              <dd className="font-mono text-[10px] text-[--color-fg-dim]">
                {evaluation.trace_id.slice(0, 12)}…
              </dd>
            </>
          )}
        </dl>
      </CollapsibleSection>
    </div>
  );
}

// ─── Dimension row with cited-evidence expansion ─────────────────────────────

function DimensionRow({
  score,
  dim,
  artifactContent,
}: {
  score: DimensionScore;
  dim?: RubricDimension;
  artifactContent: string;
}) {
  const [open, setOpen] = useState(false);
  const pct = score.score * 20;
  const tone = scoreTone(score.score);

  return (
    <li className="px-2">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="group flex w-full items-center gap-2 py-2.5 text-left transition-colors hover:bg-[--color-surface]/40"
      >
        <span
          aria-hidden
          className="h-7 w-1 flex-none rounded-sm"
          style={{ backgroundColor: tone.barCss }}
        />
        <ExpandChevron open={open} />
        <span className="flex-1 truncate text-[13px] text-[--color-fg]">
          {dim?.title ?? score.dimension_id}
        </span>
        <span
          className="font-mono text-[12px] tabular-nums"
          style={{ color: tone.numCss }}
        >
          {pct}%
        </span>
      </button>
      {open && (
        <div className="-mx-2 border-t border-[--color-border] bg-[--color-bg-deep]/50 px-4 py-3">
          <div className="text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
            Cited Evidence: {dim?.title ?? score.dimension_id}
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-[--color-fg-dim]">
            {score.feedback}
          </p>
          {score.evidence.length > 0 && (
            <ul className="mt-3 space-y-3">
              {score.evidence.map((e, i) => (
                <EvidenceBlock
                  key={i}
                  evidence={e}
                  artifactContent={artifactContent}
                />
              ))}
            </ul>
          )}
          <div className="mt-3 flex items-center gap-3 text-[10px] text-[--color-fg-faint]">
            <span>confidence {(score.confidence * 100).toFixed(0)}%</span>
            {dim && <span>weight {(dim.weight * 100).toFixed(0)}%</span>}
            <span>raw {score.score}/5</span>
          </div>
        </div>
      )}
    </li>
  );
}

// ─── Cited evidence block (code excerpt with violation highlight) ────────────

function EvidenceBlock({
  evidence,
  artifactContent,
}: {
  evidence: EvidenceItem;
  artifactContent: string;
}) {
  const lineNum = parseLineNumber(evidence.location);
  const excerpt =
    lineNum && evidence.source === "artifact"
      ? buildExcerpt(artifactContent, lineNum, 1)
      : null;

  return (
    <li>
      <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
        <SourceBadge source={evidence.source} />
        {evidence.location && (
          <span className="text-[--color-fg-dim]">{evidence.location}</span>
        )}
      </div>
      {excerpt ? (
        <pre className="mt-1.5 overflow-x-auto rounded bg-[--color-bg-deep] py-2 font-mono text-[11px] leading-[1.55] text-[--color-fg]">
          {excerpt.lines.map((line, i) => {
            const lineNo = excerpt.start + i;
            const violation = lineNo === lineNum;
            return (
              <div
                key={lineNo}
                className={
                  violation
                    ? "border-l-2 border-[--color-score-low] bg-[--color-violation-bg-strong] pl-3 pr-3"
                    : "border-l-2 border-transparent pl-3 pr-3 text-[--color-fg-dim]"
                }
              >
                <span className="mr-3 inline-block w-6 text-right text-[--color-fg-faint] tabular-nums">
                  {lineNo}
                </span>
                <span className="text-[--color-fg-dim]">|</span>{" "}
                <span className={violation ? "text-[--color-fg]" : ""}>
                  {line || " "}
                </span>
              </div>
            );
          })}
        </pre>
      ) : (
        <pre className="mt-1.5 overflow-x-auto rounded bg-[--color-bg-deep] px-3 py-2 font-mono text-[11px] leading-[1.55] text-[--color-fg-dim] whitespace-pre-wrap">
          {evidence.content}
        </pre>
      )}
    </li>
  );
}

function SourceBadge({ source }: { source: string }) {
  const colorClass =
    source === "corpus"
      ? "text-[--color-primary]"
      : source === "programmatic"
        ? "text-[--color-score-mid]"
        : source === "llm_rubric"
          ? "text-[--color-fg-dim]"
          : "text-[--color-score-low]";
  return <span className={colorClass}>{source}</span>;
}

// ─── Gap row ────────────────────────────────────────────────────────────────

function GapRow({ gap }: { gap: Gap }) {
  const stripeCss =
    gap.severity === "critical"
      ? "var(--color-score-low)"
      : gap.severity === "major"
        ? "var(--color-score-mid)"
        : "var(--color-fg-faint)";
  return (
    <li
      className="border-l-2 pl-3 text-[12px]"
      style={{ borderColor: stripeCss }}
    >
      <div className="text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
        {gap.severity}
      </div>
      <div className="text-[--color-fg-dim]">{gap.description}</div>
    </li>
  );
}

// ─── Capability status pieces ───────────────────────────────────────────────

function CapabilityStatusBadge({ status }: { status: string }) {
  const cls =
    status === "passed"
      ? "text-[--color-score-good]"
      : status === "failed"
        ? "text-[--color-score-low]"
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
  const parts: string[] = [];
  if (counts.passed) parts.push(`${counts.passed} ok`);
  if (counts.failed) parts.push(`${counts.failed} fail`);
  if (counts.skipped) parts.push(`${counts.skipped} skipped`);
  return (
    <span className="text-[10px] tabular-nums">{parts.join(" · ") || "—"}</span>
  );
}

// ─── Header field ──────────────────────────────────────────────────────────

function Field({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="border-b border-[--color-border] px-4 py-2.5 last:border-b-0">
      <div className="text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
        {label}
      </div>
      <div
        className={`mt-0.5 text-[12px] text-[--color-fg] ${
          mono ? "font-mono" : ""
        }`}
      >
        {value}
      </div>
    </div>
  );
}

// ─── helpers ────────────────────────────────────────────────────────────────

function ExpandChevron({ open }: { open: boolean }) {
  return (
    <svg
      width="9"
      height="9"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`flex-none text-[--color-fg-faint] transition-transform duration-150 ${
        open ? "rotate-90" : ""
      }`}
      aria-hidden
    >
      <path d="m9 6 6 6-6 6" />
    </svg>
  );
}

function scoreTone(score: number): { barCss: string; numCss: string } {
  if (score <= 2) {
    return {
      barCss: "var(--color-score-low)",
      numCss: "var(--color-score-low)",
    };
  }
  if (score >= 4) {
    return {
      barCss: "var(--color-score-good)",
      numCss: "var(--color-link)",
    };
  }
  return {
    barCss: "var(--color-score-mid)",
    numCss: "var(--color-link)",
  };
}

function headlineFor(ev: Evaluation): { label: string; tone: string } {
  if (ev.status === "refused") {
    return { label: "Refused", tone: "text-[--color-score-low]" };
  }
  if (ev.status === "failed") {
    return { label: "Evaluation failed", tone: "text-[--color-score-low]" };
  }
  if (ev.gaps.some((g) => g.severity === "critical")) {
    return { label: "Critical gaps found", tone: "text-[--color-score-low]" };
  }
  if (ev.gaps.some((g) => g.severity === "major")) {
    return { label: "Major gaps found", tone: "text-[--color-score-mid]" };
  }
  if (ev.gaps.length > 0) {
    return { label: "Minor gaps found", tone: "text-[--color-fg-dim]" };
  }
  return { label: "No gaps", tone: "text-[--color-score-good]" };
}

function elapsedSeconds(ev: Evaluation): number | null {
  if (!ev.created_at || !ev.completed_at) return null;
  const t1 = Date.parse(ev.created_at);
  const t2 = Date.parse(ev.completed_at);
  if (Number.isNaN(t1) || Number.isNaN(t2)) return null;
  return Math.max(0, (t2 - t1) / 1000);
}

function dispositionLabel(d: SafetyDisposition): string {
  switch (d) {
    case "self_evaluated":
      return "self-evaluated";
    case "human_review_suggested":
      return "human review suggested";
    case "expert_review_required":
      return "expert review required";
    case "refused":
      return "refused";
  }
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString();
  } catch {
    return iso;
  }
}

function parseLineNumber(location: string | null | undefined): number | null {
  if (!location) return null;
  const m = location.match(/(?:line\s*|#\s*|:)\s*(\d+)/i);
  if (m && m[1]) {
    const n = Number.parseInt(m[1], 10);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function buildExcerpt(
  content: string,
  lineNum: number,
  context: number,
): { start: number; lines: string[] } | null {
  const all = content.split("\n");
  if (lineNum < 1 || lineNum > all.length) return null;
  const start = Math.max(1, lineNum - context);
  const end = Math.min(all.length, lineNum + context);
  return {
    start,
    lines: all.slice(start - 1, end),
  };
}
