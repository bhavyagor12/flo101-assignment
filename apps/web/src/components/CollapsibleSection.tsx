import { useState, type ReactNode } from "react";

interface CollapsibleSectionProps {
  title: string;
  defaultOpen?: boolean;
  meta?: ReactNode;
  children: ReactNode;
}

export function CollapsibleSection({
  title,
  defaultOpen = true,
  meta,
  children,
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="border-b border-[--color-border] last:border-b-0">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-3 px-4 py-2.5 text-[10px] uppercase tracking-wider text-[--color-fg-faint] transition-colors hover:bg-[--color-surface] hover:text-[--color-fg-dim]"
      >
        <span className="flex items-center gap-2">
          <Chevron open={open} />
          {title}
        </span>
        {meta && <span className="normal-case tracking-normal">{meta}</span>}
      </button>
      {open && <div className="px-4 pb-4">{children}</div>}
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
      className={`transition-transform duration-150 ${open ? "" : "-rotate-90"}`}
      aria-hidden
    >
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}
