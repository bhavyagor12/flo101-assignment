import { useEffect, useRef, useState } from "react";

import type { ArtifactKind, ArtifactSubmission } from "@flo101/api-types";

import { ArtifactEditor } from "./components/ArtifactEditor";
import { ConfigTab } from "./components/ConfigTab";
import { MenuBar } from "./components/MenuBar";
import { ResultTab } from "./components/ResultTab";
import { RightPanel, type RightTab } from "./components/RightPanel";
import { StatusBar } from "./components/StatusBar";
import { useEvaluate, useHealth, useSpec } from "./lib/hooks";

const KINDS: ArtifactKind[] = [
  "text",
  "code",
  "sql",
  "diagram_markdown",
  "mixed",
];

export function App() {
  const [selectedSpecId, setSelectedSpecId] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [kind, setKind] = useState<ArtifactKind>("text");
  const [activeTab, setActiveTab] = useState<RightTab>("config");

  const health = useHealth();
  const spec = useSpec(selectedSpecId);
  const evaluate = useEvaluate({
    onSuccess: () => setActiveTab("result"),
  });

  // Sync `kind` to the spec's preferred artifact kind once per spec change.
  const syncedSpecRef = useRef<string | null>(null);
  useEffect(() => {
    if (!spec.data) return;
    if (syncedSpecRef.current === spec.data.id) return;
    syncedSpecRef.current = spec.data.id;
    if (KINDS.includes(spec.data.artifact_kind)) {
      setKind(spec.data.artifact_kind);
    }
  }, [spec.data]);

  const apiStatus =
    health.data?.status ?? (health.isLoading ? "starting" : "down");

  const filename = filenameFor(kind);
  const evaluation = evaluate.data ?? null;

  const handleSubmit = () => {
    if (!selectedSpecId || !content.trim() || evaluate.isPending) return;
    const submission: ArtifactSubmission = {
      kind,
      content,
      filename: null,
      metadata: {},
    };
    evaluate.mutate({ specId: selectedSpecId, submission });
  };

  return (
    <div className="flex h-screen min-h-screen flex-col overflow-hidden bg-[--color-bg] text-[--color-fg]">
      <MenuBar />
      <div className="flex min-h-0 flex-1">
        <main className="flex min-h-0 min-w-0 flex-1 flex-col">
          {!selectedSpecId ? (
            <EmptyEditor onJumpToConfig={() => setActiveTab("config")} />
          ) : (
            <ArtifactEditor
              value={content}
              onChange={setContent}
              filename={filename}
              kind={kind}
              busy={evaluate.isPending}
            />
          )}
          <SubmitBar
            specSelected={!!selectedSpecId}
            kind={kind}
            onKindChange={setKind}
            content={content}
            busy={evaluate.isPending}
            error={evaluate.error?.message}
            onSubmit={handleSubmit}
          />
        </main>

        <RightPanel
          activeTab={activeTab}
          onTabChange={setActiveTab}
          hasResult={!!evaluation}
          config={
            <ConfigTab
              selectedSpecId={selectedSpecId}
              onSelectSpec={setSelectedSpecId}
            />
          }
          result={
            <ResultTab
              evaluation={evaluation}
              spec={spec.data ?? null}
              artifactContent={content}
              artifactFilename={filename}
            />
          }
        />
      </div>
      <StatusBar
        apiStatus={apiStatus}
        chars={content.length}
        busy={evaluate.isPending}
      />
    </div>
  );
}

function EmptyEditor({ onJumpToConfig }: { onJumpToConfig: () => void }) {
  return (
    <div className="flex flex-1 items-center justify-center px-8 py-16">
      <div className="max-w-md text-center">
        <h2 className="text-[18px] font-medium tracking-tight text-[--color-fg]">
          Start by picking a skill
        </h2>
        <p className="mt-2 text-[13px] leading-relaxed text-[--color-fg-dim]">
          Choose one in the Config panel on the right, or synthesize a new
          skill from a learning goal. The artifact editor activates once
          a skill is selected.
        </p>
        <ol className="mx-auto mt-6 max-w-sm space-y-2.5 text-left text-[12px] leading-relaxed text-[--color-fg-dim]">
          <li className="flex gap-3">
            <Pill>1</Pill>
            <span>Select a skill, or synthesize a new one.</span>
          </li>
          <li className="flex gap-3">
            <Pill>2</Pill>
            <span>Optionally upload reference material.</span>
          </li>
          <li className="flex gap-3">
            <Pill>3</Pill>
            <span>Paste your work, then submit for critique.</span>
          </li>
        </ol>
        <button
          type="button"
          onClick={onJumpToConfig}
          className="mt-7 rounded-md bg-[--color-primary] px-5 py-2.5 text-[12px] font-semibold text-white transition-colors hover:bg-[--color-primary-hover]"
        >
          Open Config
        </button>
      </div>
    </div>
  );
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span
      aria-hidden
      className="flex h-5 w-5 flex-none items-center justify-center rounded-full bg-[--color-surface-2] text-[10px] font-semibold text-[--color-fg]"
    >
      {children}
    </span>
  );
}

function SubmitBar({
  specSelected,
  kind,
  onKindChange,
  content,
  busy,
  error,
  onSubmit,
}: {
  specSelected: boolean;
  kind: ArtifactKind;
  onKindChange: (k: ArtifactKind) => void;
  content: string;
  busy: boolean;
  error: string | undefined;
  onSubmit: () => void;
}) {
  const canSubmit = specSelected && !!content.trim() && !busy;
  return (
    <div className="flex-none border-t border-[--color-border] bg-[--color-bg-deep] px-4 py-3">
      <div className="flex items-center gap-3">
        <label className="flex items-center gap-2 text-[10px] font-medium uppercase tracking-wider text-[--color-fg-faint]">
          kind
          <select
            value={kind}
            onChange={(e) => onKindChange(e.target.value as ArtifactKind)}
            disabled={!specSelected}
            className="rounded-md border border-[--color-border-strong] bg-[--color-surface-2] px-2.5 py-1.5 text-[12px] tracking-normal text-[--color-fg] normal-case focus:border-[--color-primary] focus:outline-none focus:ring-1 focus:ring-[--color-primary]/40 disabled:opacity-50"
          >
            {KINDS.map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
        </label>
        <span className="text-[12px] text-[--color-fg-dim]">
          {busy
            ? "Running safety check, capabilities, then rubric critique."
            : specSelected
              ? "Submit when ready. Typically 8 to 15 seconds."
              : "Select a skill to begin."}
        </span>
        <button
          type="button"
          disabled={!canSubmit}
          onClick={onSubmit}
          className="ml-auto rounded-md bg-[--color-primary] px-5 py-2 text-[12px] font-semibold text-white shadow-sm transition-colors hover:bg-[--color-primary-hover] disabled:cursor-not-allowed disabled:bg-[--color-surface-2] disabled:text-[--color-fg-faint] disabled:shadow-none"
        >
          {busy ? "Critiquing…" : "Submit for critique"}
        </button>
      </div>
      {error && (
        <div className="mt-2.5 rounded border border-[--color-score-low]/40 bg-[--color-score-low]/10 px-2.5 py-1.5 text-[11px] text-[--color-score-low]">
          {error}
        </div>
      )}
    </div>
  );
}

function filenameFor(kind: ArtifactKind): string {
  switch (kind) {
    case "code":
      return "artifact.py";
    case "sql":
      return "query.sql";
    case "diagram_markdown":
      return "diagram.md";
    case "mixed":
      return "design.md";
    case "text":
    default:
      return "artifact.md";
  }
}
