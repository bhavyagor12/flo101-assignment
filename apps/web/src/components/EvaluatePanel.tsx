import { useEffect, useRef, useState } from "react";

import type { ArtifactKind, ArtifactSubmission } from "@flo101/api-types";

import { useEvaluate, useSpec } from "@/lib/hooks";
import { EvaluationResult } from "./EvaluationResult";

interface EvaluatePanelProps {
  specId: string | null;
}

const KINDS: ArtifactKind[] = ["text", "code", "sql", "diagram_markdown", "mixed"];

export function EvaluatePanel({ specId }: EvaluatePanelProps) {
  const spec = useSpec(specId);
  const evaluate = useEvaluate();
  const [content, setContent] = useState("");
  const [kind, setKind] = useState<ArtifactKind>("text");

  // Sync `kind` to the spec's preferred artifact kind once per spec change.
  // User-driven changes after that are preserved until the next selection.
  const syncedSpecRef = useRef<string | null>(null);
  useEffect(() => {
    if (!spec.data) return;
    if (syncedSpecRef.current === spec.data.id) return;
    syncedSpecRef.current = spec.data.id;
    if (KINDS.includes(spec.data.artifact_kind)) {
      setKind(spec.data.artifact_kind);
    }
  }, [spec.data]);

  if (!specId) {
    return (
      <section className="rounded-xl border border-dashed border-[--color-border] px-6 py-12 text-center">
        <p className="text-sm text-[--color-fg-dim]">
          Pick a skill in the sidebar.
        </p>
        <p className="mt-1 text-xs text-[--color-fg-faint]">
          Or synthesize a new one from a goal.
        </p>
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <div className="rounded-xl border border-[--color-border] bg-[--color-surface] p-5">
        <header className="mb-3 flex items-center justify-between gap-3">
          <h2 className="text-sm font-medium tracking-tight">
            Submit an artifact
          </h2>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
              kind
              <select
                value={kind}
                onChange={(e) => setKind(e.target.value as ArtifactKind)}
                className="rounded-md border border-[--color-border] bg-[--color-bg] px-2 py-1 text-[11px] tracking-normal text-[--color-fg] normal-case focus:border-[--color-accent]/60 focus:outline-none"
              >
                {KINDS.map((k) => (
                  <option key={k} value={k}>
                    {k}
                  </option>
                ))}
              </select>
            </label>
            <span className="text-[10px] tabular-nums text-[--color-fg-faint]">
              {content.length.toLocaleString()} chars
            </span>
          </div>
        </header>

        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Paste your work. PRD, code, SQL query, design doc, SOAP note."
          className="block h-56 w-full rounded-md border border-[--color-border] bg-[--color-bg] px-3 py-2.5 font-mono text-xs leading-relaxed text-[--color-fg] placeholder:text-[--color-fg-faint] focus:border-[--color-accent]/60 focus:outline-none focus:ring-1 focus:ring-[--color-accent]/30"
        />

        <div className="mt-3 flex items-center justify-between gap-3">
          <span className="text-[11px] text-[--color-fg-faint]">
            {evaluate.isPending
              ? "Running safety check, capabilities, then rubric critique."
              : "Typically 8 to 15 seconds."}
          </span>
          <button
            type="button"
            disabled={!content.trim() || evaluate.isPending}
            onClick={() => {
              const submission: ArtifactSubmission = {
                kind,
                content,
                filename: null,
                metadata: {},
              };
              evaluate.mutate({ specId, submission });
            }}
            className="rounded-md border border-[--color-accent]/60 bg-[--color-accent-soft] px-4 py-2 text-xs font-medium text-[--color-accent] transition-colors hover:bg-[--color-accent]/20 disabled:opacity-40"
          >
            {evaluate.isPending ? "Critiquing…" : "Submit for critique"}
          </button>
        </div>
      </div>

      {evaluate.isError && (
        <div className="rounded-md border border-[--color-danger]/50 bg-[--color-danger]/10 px-3 py-2 text-xs text-[--color-danger]">
          {evaluate.error.message}
        </div>
      )}

      {evaluate.data && spec.data && (
        <EvaluationResult evaluation={evaluate.data} spec={spec.data} />
      )}
    </section>
  );
}
