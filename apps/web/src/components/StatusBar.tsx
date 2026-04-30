interface StatusBarProps {
  apiStatus: string;
  chars: number;
  busy?: boolean;
}

export function StatusBar({ apiStatus, chars, busy }: StatusBarProps) {
  const apiOk = apiStatus === "ok";
  return (
    <footer className="flex h-6 flex-none items-center justify-between border-t border-[var(--color-border)] bg-[var(--color-bg-deep)] px-3 text-[10px] text-[var(--color-fg-faint)]">
      <div className="flex items-center gap-3">
        <span className="flex items-center gap-1.5">
          <span
            className={`inline-block h-1.5 w-1.5 rounded-full ${
              busy
                ? "bg-[var(--color-primary)] animate-pulse"
                : apiOk
                  ? "bg-[var(--color-score-good)]"
                  : "bg-[var(--color-score-low)]"
            }`}
          />
          <span className="text-[var(--color-fg-dim)]">
            {busy ? "Critiquing" : "Ready"}
          </span>
        </span>
        <span>api {apiStatus}</span>
      </div>
      <div className="flex items-center gap-3 tabular-nums">
        <span>UTF-8</span>
        <span>{chars.toLocaleString()} chars</span>
        <span>v0.1.0</span>
      </div>
    </footer>
  );
}
