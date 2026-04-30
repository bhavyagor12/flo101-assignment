import { type ReactNode } from "react";

interface PanelProps {
  title: string;
  hint?: string;
  step?: number;
  active?: boolean;
  /** "rail" = bordered surface (use in sidebar). "step" = borderless flow item. */
  variant?: "rail" | "step";
  children: ReactNode;
}

export function Panel({
  title,
  hint,
  step,
  active,
  variant = "rail",
  children,
}: PanelProps) {
  if (variant === "step") {
    return (
      <section className="relative pl-9">
        <StepDot index={step} active={active} />
        <header className="mb-2">
          <h2 className="text-base font-medium tracking-tight text-[--color-fg]">
            {title}
          </h2>
          {hint && (
            <p className="mt-0.5 text-xs leading-relaxed text-[--color-fg-dim]">
              {hint}
            </p>
          )}
        </header>
        <div>{children}</div>
      </section>
    );
  }

  return (
    <section
      className={`rounded-xl border bg-[--color-surface] p-5 transition-colors duration-200 ${
        active
          ? "border-[--color-accent]/50"
          : "border-[--color-border]"
      }`}
    >
      <header className="mb-4">
        <h2 className="text-sm font-semibold tracking-tight">{title}</h2>
        {hint && (
          <p className="mt-1 text-xs leading-relaxed text-[--color-fg-dim]">
            {hint}
          </p>
        )}
      </header>
      <div>{children}</div>
    </section>
  );
}

function StepDot({ index, active }: { index?: number; active?: boolean }) {
  if (index === undefined) return null;
  return (
    <span
      aria-hidden
      className={`absolute left-0 top-0 inline-flex h-6 w-6 items-center justify-center rounded-full border text-[10px] font-medium tabular-nums ${
        active
          ? "border-[--color-accent]/70 bg-[--color-accent-soft] text-[--color-accent]"
          : "border-[--color-border] bg-[--color-surface] text-[--color-fg-dim]"
      }`}
    >
      {index}
    </span>
  );
}
