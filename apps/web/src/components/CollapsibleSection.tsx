import { useState, type ReactNode } from "react";

interface CollapsibleSectionProps {
  title: string;
  defaultOpen?: boolean;
  meta?: ReactNode;
  /** Drop the inner padding so children can handle their own rhythm. */
  flush?: boolean;
  children: ReactNode;
}

export function CollapsibleSection({
  title,
  defaultOpen = true,
  meta,
  flush = false,
  children,
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="border-b border-[var(--color-border)] last:border-b-0">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-3 px-5 py-3 text-[11px] font-medium uppercase tracking-wider text-[var(--color-fg-dim)] transition-colors hover:text-[var(--color-fg)]"
      >
        <span className="flex items-center gap-2.5">
          <Chevron open={open} />
          {title}
        </span>
        {meta && (
          <span className="font-normal normal-case tracking-normal text-[10px] text-[var(--color-fg-faint)]">
            {meta}
          </span>
        )}
      </button>
      {open && <div className={flush ? "" : "px-5 pb-4"}>{children}</div>}
    </section>
  );
}

function Chevron({ open }: { open: boolean }) {
  return (
    <svg
      width="10"
      height="10"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`flex-none transition-transform duration-150 ${
        open ? "" : "-rotate-90"
      }`}
      aria-hidden
    >
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}
