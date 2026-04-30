import { useMemo, useRef } from "react";

interface ArtifactEditorProps {
  value: string;
  onChange: (value: string) => void;
  filename?: string;
  kind?: string;
  /** Lines to highlight (1-indexed). Used when result evidence cites lines. */
  highlightedLines?: ReadonlySet<number>;
  busy?: boolean;
}

export function ArtifactEditor({
  value,
  onChange,
  filename = "untitled",
  kind,
  highlightedLines,
  busy,
}: ArtifactEditorProps) {
  const lines = useMemo(() => value.split("\n"), [value]);
  const lineCount = lines.length;
  const gutterRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-[var(--color-bg)]">
      <header className="flex h-9 flex-none items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-bg-deep)] px-4 text-[10px] uppercase tracking-wider text-[var(--color-fg-faint)]">
        <div className="flex items-center gap-3">
          <span>Artifact</span>
          <span className="text-[var(--color-border-strong)]">/</span>
          <span className="text-[var(--color-fg-dim)]">{filename}</span>
          {kind && (
            <span className="rounded border border-[var(--color-border)] px-1.5 py-0.5 text-[9px] tracking-wide normal-case text-[var(--color-fg-dim)]">
              {kind}
            </span>
          )}
        </div>
        <span className="tabular-nums">
          {lineCount} {lineCount === 1 ? "line" : "lines"} · {value.length.toLocaleString()} chars
        </span>
      </header>

      <div className="relative flex flex-1 overflow-hidden">
        {/* Line number gutter */}
        <div
          ref={gutterRef}
          className="no-scrollbar flex-none overflow-y-scroll bg-[var(--color-bg-deep)] py-3 text-right font-mono text-[12px] leading-[1.55] text-[var(--color-fg-faint)] select-none"
          style={{ width: "3.5rem" }}
        >
          <div className="px-3">
            {lines.map((_, i) => {
              const lineNum = i + 1;
              const flagged = highlightedLines?.has(lineNum) ?? false;
              return (
                <div
                  key={i}
                  className={
                    flagged
                      ? "text-[var(--color-score-low)]"
                      : ""
                  }
                >
                  {lineNum}
                </div>
              );
            })}
          </div>
        </div>

        {/* Text area */}
        <div className="relative flex-1 overflow-hidden">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            spellCheck={false}
            placeholder="// Paste your artifact here. PRD, code, SQL, design doc, SOAP note."
            disabled={busy}
            onScroll={(e) => {
              if (gutterRef.current) {
                gutterRef.current.scrollTop = e.currentTarget.scrollTop;
              }
            }}
            className="block h-full w-full resize-none border-0 bg-transparent px-4 py-3 font-mono text-[12px] leading-[1.55] text-[var(--color-fg)] placeholder:text-[var(--color-fg-faint)] focus:outline-none disabled:opacity-60"
          />
        </div>
      </div>
    </div>
  );
}
