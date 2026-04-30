import { type ReactNode } from "react";

interface PanelProps {
  title: string;
  hint?: string;
  step?: number;
  active?: boolean;
  children: ReactNode;
}

export function Panel({ title, hint, step, active, children }: PanelProps) {
  return (
    <section
      className={`rounded-lg border bg-[--color-surface] p-5 transition ${
        active ? "border-[--color-accent]/60" : "border-[--color-border]"
      }`}
    >
      <header className="mb-3 flex items-baseline justify-between">
        <h2 className="text-sm font-semibold tracking-tight">
          {step !== undefined && (
            <span className="mr-2 text-[--color-fg-dim]">{step}.</span>
          )}
          {title}
        </h2>
      </header>
      {hint && (
        <p className="mb-3 text-xs text-[--color-fg-dim]">{hint}</p>
      )}
      <div>{children}</div>
    </section>
  );
}
