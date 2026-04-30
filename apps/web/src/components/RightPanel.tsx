import { type ReactNode } from "react";

export type RightTab = "config" | "result";

interface RightPanelProps {
  activeTab: RightTab;
  onTabChange: (tab: RightTab) => void;
  hasResult: boolean;
  config: ReactNode;
  result: ReactNode;
}

export function RightPanel({
  activeTab,
  onTabChange,
  hasResult,
  config,
  result,
}: RightPanelProps) {
  return (
    <aside className="flex w-[460px] flex-none flex-col border-l border-[var(--color-border)] bg-[var(--color-bg-deep)]">
      <div role="tablist" className="flex flex-none border-b border-[var(--color-border)]">
        <Tab
          id="config"
          label="Config"
          active={activeTab === "config"}
          onClick={() => onTabChange("config")}
        />
        <Tab
          id="result"
          label="Result"
          active={activeTab === "result"}
          onClick={() => onTabChange("result")}
          dot={hasResult}
          disabled={!hasResult}
        />
        <div className="flex-1 border-b border-[var(--color-border)]" />
      </div>
      <div className="flex-1 overflow-y-auto">
        {activeTab === "config" ? config : result}
      </div>
    </aside>
  );
}

function Tab({
  id,
  label,
  active,
  onClick,
  dot,
  disabled,
}: {
  id: string;
  label: string;
  active: boolean;
  onClick: () => void;
  dot?: boolean;
  disabled?: boolean;
}) {
  return (
    <button
      role="tab"
      type="button"
      aria-selected={active}
      aria-controls={`panel-${id}`}
      onClick={onClick}
      disabled={disabled}
      className={`relative flex items-center gap-2 px-5 py-2.5 text-[11px] uppercase tracking-wider transition-colors ${
        active
          ? "text-[var(--color-fg)]"
          : disabled
            ? "text-[var(--color-fg-faint)]/60"
            : "text-[var(--color-fg-dim)] hover:text-[var(--color-fg)]"
      } disabled:cursor-not-allowed`}
    >
      {label}
      {dot && (
        <span
          aria-hidden
          className="inline-block h-1.5 w-1.5 rounded-full bg-[var(--color-primary)]"
        />
      )}
      {active && (
        <span
          aria-hidden
          className="absolute inset-x-3 -top-px h-0.5 rounded-b bg-[var(--color-primary)]"
        />
      )}
    </button>
  );
}
