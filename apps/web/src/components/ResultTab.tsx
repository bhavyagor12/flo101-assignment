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
import { Row } from "./Row";

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
      <div className="flex h-full items-center justify-center px-8 py-20 text-center">
        <p className="text-[12px] leading-relaxed text-[--color-fg-faint]">
          No evaluation yet. Submit an artifact in the editor to see scores,
          cited evidence, and the recommended next action here.
        </p>
      </div>
    );
  }

  const overall = evaluation.overall_score;
  const overall100 =
    overall === null || overall === undefined ? null : Math.round(overall * 20);
  const dimByID = new Map(spec.rubric.dimensions.map((d) => [d.id, d]));
  const headline = headlineFor(evaluation);
  const elapsed = elapsedSeconds(evaluation);

  return (
    <div className="animate-result-enter">
      <div className="border-b border-[--color-border]">
        <Row label="Target file" value={artifactFilename} />
        <Row label="Applied rubric" value={spec.goal_text} />
      </div>

      <section className="border-b border-[--color-border] px-5 py-5">
        <div className="flex items-baseline gap-3">
          <span className="text-[44px] font-semibold leading-none tracking-tight tabular-nums">
            {overall100 === null ? "—" : overall100}
          </span>
          <span className="text-[14px] text-[--color-fg-faint]">/ 100</span>
        </div>
        <div className="mt-3 flex flex-col leading-tight">
          <span
            className={`text-[11px] font-semibold uppercase tracking-wider ${headline.tone}`}
          >
            {headline.label}
          </span>
          {elapsed !== null && (
            <span className="mt-1 text-[11px] text-[--color-fg-dim]">
              Evaluation completed in {elapsed.toFixed(1)}s
            </span>
          )}
        </div>
        {evaluation.refused_reason && (
          <p className="mt-3 text-[12px] leading-relaxed text-[--color-fg-dim]">
            {evaluation.refused_reason}
          </p>
        )}
      </section>

      {evaluation.dimension_scores.length > 0 && (
        <CollapsibleSection title="Dimension Scores" flush>
          <ul className="divide-y divide-[--color-border]">
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
        <CollapsibleSection
          title="Gaps"
          flush
          meta={
            <span className="tabular-nums">{evaluation.gaps.length}</span>
          }
        >
          <ul>
            {evaluation.gaps.map((g, i) => (
              <GapRow key={i} gap={g} />
            ))}
          </ul>
        </CollapsibleSection>
      )}

      {evaluation.next_step && (
        <section className="border-b border-[--color-border] bg-[--color-surface]/40 px-5 py-5">
          <div className="text-[10px] font-medium uppercase tracking-wider text-[--color-fg-faint]">
            Recommended next action
          </div>
          <p className="mt-2.5 text-[14px] leading-snug text-[--color-fg]">
            {evaluation.next_step.title}.
          </p>
          <p className="mt-2 text-[12px] leading-relaxed text-[--color-fg-dim]">
            {evaluation.next_step.rationale}
          </p>
          <button
            type="button"
            onClick={onRefactor}
            className="mt-4 w-full rounded-md bg-[--color-primary] px-4 py-3 text-[12px] font-semibold text-white transition-colors hover:bg-[--color-primary-hover]"
          >
            Generate revision · {evaluation.next_step.estimated_minutes} min
          </button>
        </section>
      )}

      <CollapsibleSection
        title="Capability checks"
        defaultOpen={false}
        flush
        meta={<CapabilityCounts results={evaluation.capability_results} />}
      >
        {evaluation.capability_results.length === 0 ? (
          <Row label="—" value="No checks ran." />
        ) : (
          <ul>
            {evaluation.capability_results.map((r, i) => (
              <li
                key={i}
                className="flex items-center justify-between gap-3 border-b border-[--color-border] px-5 py-2.5 text-[12px] last:border-b-0"
              >
                <span className="font-mono text-[11px] text-[--color-fg-dim]">
                  {r.kind}
                </span>
                <span className="flex items-center gap-3">
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

      <CollapsibleSection title="Metadata" defaultOpen={false} flush>
        <Row label="Disposition" value={dispositionLabel(evaluation.safety_disposition)} />
        <Row label="Status" value={evaluation.status} />
        {evaluation.created_at && (
          <Row label="Submitted" value={formatTime(evaluation.created_at)} />
        )}
        {evaluation.completed_at && (
          <Row label="Completed" value={formatTime(evaluation.completed_at)} />
        )}
        {evaluation.trace_id && (
          <Row label="Trace ID">
            <span className="font-mono text-[11px] text-[--color-fg-dim]">
              {evaluation.trace_id}
            </span>
          </Row>
        )}
      </CollapsibleSection>
    </div>
  );
}

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
    <li>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="group flex w-full items-center gap-3 px-5 py-3.5 text-left transition-colors hover:bg-[--color-surface]/60"
      >
        <span
          aria-hidden
          className="h-8 w-1 flex-none rounded-sm"
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
        <div className="border-t border-[--color-border] bg-[--color-bg-deep] px-5 py-4">
          <div className="text-[10px] font-medium uppercase tracking-wider text-[--color-fg-faint]">
            Cited evidence · {dim?.title ?? score.dimension_id}
          </div>
          <p className="mt-2.5 text-[12px] leading-relaxed text-[--color-fg-dim]">
            {score.feedback}
          </p>
          {score.evidence.length > 0 && (
            <ul className="mt-3.5 space-y-3.5">
              {score.evidence.map((e, i) => (
                <EvidenceBlock
                  key={i}
                  evidence={e}
                  artifactContent={artifactContent}
                />
              ))}
            </ul>
          )}
          <div className="mt-3.5 flex items-center gap-4 text-[10px] text-[--color-fg-faint]">
            <span>confidence {(score.confidence * 100).toFixed(0)}%</span>
            {dim && <span>weight {(dim.weight * 100).toFixed(0)}%</span>}
            <span>raw {score.score}/5</span>
          </div>
        </div>
      )}
    </li>
  );
}

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
      <div className="mb-1.5 flex items-center gap-2 text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
        <SourceBadge source={evidence.source} />
        {evidence.location && (
          <span className="text-[--color-fg-dim] normal-case tracking-normal">
            {evidence.location}
          </span>
        )}
      </div>
      {excerpt ? (
        <pre className="overflow-x-auto rounded-md bg-black/40 py-2 font-mono text-[11px] leading-[1.55]">
          {excerpt.lines.map((line, i) => {
            const lineNo = excerpt.start + i;
            const violation = lineNo === lineNum;
            return (
              <div
                key={lineNo}
                className={
                  violation
                    ? "border-l-2 border-[--color-score-low] bg-[--color-violation-bg-strong] pl-3 pr-3 text-[--color-fg]"
                    : "border-l-2 border-transparent pl-3 pr-3 text-[--color-fg-dim]"
                }
              >
                <span className="mr-3 inline-block w-7 text-right tabular-nums text-[--color-fg-faint]">
                  {lineNo}
                </span>
                <span className="text-[--color-fg-faint]">|</span>{" "}
                <span>{line || " "}</span>
              </div>
            );
          })}
        </pre>
      ) : (
        <pre className="overflow-x-auto whitespace-pre-wrap rounded-md bg-black/40 px-3 py-2 font-mono text-[11px] leading-[1.55] text-[--color-fg-dim]">
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

function GapRow({ gap }: { gap: Gap }) {
  const stripeCss =
    gap.severity === "critical"
      ? "var(--color-score-low)"
      : gap.severity === "major"
        ? "var(--color-score-mid)"
        : "var(--color-fg-faint)";
  return (
    <li className="border-b border-[--color-border] px-5 py-3 last:border-b-0">
      <div className="flex items-baseline gap-3 text-[12px]">
        <span
          className="h-3 w-1 flex-none rounded-sm"
          style={{ backgroundColor: stripeCss }}
          aria-hidden
        />
        <span className="flex-1 text-[--color-fg-dim]">{gap.description}</span>
        <span className="font-mono text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
          {gap.severity}
        </span>
      </div>
    </li>
  );
}

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
    <span className="tabular-nums">{parts.join(" · ") || "—"}</span>
  );
}

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
    return { barCss: "var(--color-score-low)", numCss: "var(--color-score-low)" };
  }
  if (score >= 4) {
    return { barCss: "var(--color-score-good)", numCss: "var(--color-link)" };
  }
  return { barCss: "var(--color-score-mid)", numCss: "var(--color-link)" };
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
  return { start, lines: all.slice(start - 1, end) };
}
