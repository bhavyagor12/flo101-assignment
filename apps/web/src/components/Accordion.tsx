import { useEffect, useRef, useState, type ReactNode } from "react";

interface AccordionProps {
  title: ReactNode;
  /** Right-side content displayed in the header bar. */
  meta?: ReactNode;
  defaultOpen?: boolean;
  /** When this changes, the accordion re-evaluates `defaultOpen` for new values. */
  resetKey?: string | number;
  children: ReactNode;
}

export function Accordion({
  title,
  meta,
  defaultOpen = false,
  resetKey,
  children,
}: AccordionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const lastResetRef = useRef(resetKey);

  useEffect(() => {
    if (lastResetRef.current !== resetKey) {
      lastResetRef.current = resetKey;
      setOpen(defaultOpen);
    }
  }, [resetKey, defaultOpen]);

  return (
    <div className="border-t border-[--color-border] first:border-t-0">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="group flex w-full items-center justify-between gap-3 px-1 py-3 text-left text-xs transition-colors hover:bg-[--color-surface-2]/40"
        aria-expanded={open}
      >
        <span className="flex items-center gap-2">
          <span
            aria-hidden
            className={`inline-block text-[--color-fg-faint] transition-transform duration-150 ${
              open ? "rotate-90" : ""
            }`}
          >
            ›
          </span>
          <span className="text-[--color-fg]">{title}</span>
        </span>
        {meta && (
          <span className="text-[10px] text-[--color-fg-faint]">{meta}</span>
        )}
      </button>
      {open && <div className="px-1 pb-4">{children}</div>}
    </div>
  );
}
