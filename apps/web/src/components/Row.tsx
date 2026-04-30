import { type ReactNode } from "react";

interface RowProps {
  label: string;
  /** Quick path: render a string or simple node as the value with default styling. */
  value?: ReactNode;
  /** Right-aligned helper inline with the label. */
  meta?: ReactNode;
  /** Custom value content. Takes precedence over `value`. */
  children?: ReactNode;
  /** Drop the bottom border for the last row in a stack. */
  noDivider?: boolean;
}

export function Row({ label, value, meta, children, noDivider }: RowProps) {
  return (
    <div
      className={`px-5 py-3 ${
        noDivider ? "" : "border-b border-[var(--color-border)]/60 last:border-b-0"
      }`}
    >
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-[10px] font-medium uppercase tracking-wider text-[var(--color-fg-faint)]">
          {label}
        </span>
        {meta && <span className="text-[10px] text-[var(--color-fg-faint)]">{meta}</span>}
      </div>
      <div className="mt-1.5">
        {children !== undefined ? (
          children
        ) : (
          <span className="text-[13px] text-[var(--color-fg)]">{value ?? "—"}</span>
        )}
      </div>
    </div>
  );
}
