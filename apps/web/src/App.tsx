import { useEffect, useRef, useState } from "react";

import type { ArtifactKind, ArtifactSubmission } from "@flo101/api-types";

import { ActivityRail } from "./components/ActivityRail";
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
  const [activeRail, setActiveRail] = useState<
    "artifact" | "library" | "settings"
  >("artifact");

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
        <ActivityRail active={activeRail} onSelect={setActiveRail} />

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
    <div className="flex flex-1 items-center justify-center px-8 py-16 text-center">
      <div className="max-w-sm">
        <p className="text-[14px] text-[--color-fg]">
          Pick a skill in the Config panel.
        </p>
        <p className="mt-2 text-[12px] text-[--color-fg-dim]">
          Or synthesize a new one from a goal. The artifact editor activates
          once a skill is selected.
        </p>
        <button
          type="button"
          onClick={onJumpToConfig}
          className="mt-5 rounded border border-[--color-border] px-3 py-1.5 text-[11px] text-[--color-fg-dim] hover:border-[--color-primary]/60 hover:text-[--color-fg]"
        >
          Open Config
        </button>
      </div>
    </div>
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
    <div className="flex-none border-t border-[--color-border] bg-[--color-bg-deep] px-4 py-2.5">
      <div className="flex items-center gap-3">
        <label className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
          kind
          <select
            value={kind}
            onChange={(e) => onKindChange(e.target.value as ArtifactKind)}
            disabled={!specSelected}
            className="rounded border border-[--color-border] bg-[--color-bg] px-2 py-1 text-[11px] tracking-normal text-[--color-fg] normal-case focus:border-[--color-primary]/60 focus:outline-none disabled:opacity-50"
          >
            {KINDS.map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
        </label>
        <span className="text-[11px] text-[--color-fg-dim]">
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
          className="ml-auto rounded bg-[--color-primary] px-4 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-white transition-colors hover:bg-[--color-primary-hover] disabled:opacity-40"
        >
          {busy ? "Critiquing" : "Submit for critique"}
        </button>
      </div>
      {error && (
        <div className="mt-2 rounded border border-[--color-score-low]/40 bg-[--color-score-low]/10 px-2 py-1.5 text-[11px] text-[--color-score-low]">
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
