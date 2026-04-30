import { useEffect, useRef, useState } from "react";

import type { ArtifactKind, ArtifactSubmission } from "@flo101/api-types";

import { Panel } from "./Panel";
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
  // Tracked via a ref so user-driven changes after the first sync are preserved
  // until the next spec selection.
  const syncedSpecRef = useRef<string | null>(null);
  useEffect(() => {
    if (!spec.data) return;
    if (syncedSpecRef.current === spec.data.id) return;
    syncedSpecRef.current = spec.data.id;
    if (KINDS.includes(spec.data.artifact_kind)) {
      setKind(spec.data.artifact_kind);
    }
  }, [spec.data]);

  return (
    <Panel
      step={3}
      title="Evaluate"
      hint="Paste your work. Get rubric-grounded feedback with evidence and one next-best step."
      active={!!evaluate.data}
    >
      {!specId && (
        <div className="text-xs text-[--color-fg-dim]">Pick a skill first.</div>
      )}

      {specId && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <select
              value={kind}
              onChange={(e) => setKind(e.target.value as ArtifactKind)}
              className="rounded-md border border-[--color-border] bg-[--color-bg] px-2 py-1.5 text-xs"
            >
              {KINDS.map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
            <div className="text-right text-[10px] text-[--color-fg-dim] self-center">
              {content.length.toLocaleString()} chars
            </div>
          </div>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder={"Paste your artifact (PRD, code, SQL query, design doc, SOAP note…)"}
            className="h-44 w-full rounded-md border border-[--color-border] bg-[--color-bg] px-2 py-1.5 font-mono text-xs leading-relaxed focus:border-[--color-accent]/60 focus:outline-none"
          />
          <button
            type="button"
            disabled={!content.trim() || evaluate.isPending}
            onClick={() => {
              const submission: ArtifactSubmission = {
                kind,
                content: content,
                filename: null,
                metadata: {},
              };
              evaluate.mutate({ specId, submission });
            }}
            className="w-full rounded-md bg-[--color-accent]/15 border border-[--color-accent]/60 px-3 py-2 text-xs font-medium text-[--color-accent] disabled:opacity-50"
          >
            {evaluate.isPending ? "Critiquing…" : "Submit for critique"}
          </button>

          {evaluate.isError && (
            <div className="rounded-md border border-[--color-danger]/50 bg-[--color-danger]/10 px-3 py-2 text-xs text-[--color-danger]">
              {evaluate.error.message}
            </div>
          )}

          {evaluate.data && spec.data && (
            <EvaluationResult evaluation={evaluate.data} spec={spec.data} />
          )}
        </div>
      )}
    </Panel>
  );
}
