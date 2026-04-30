export function MenuBar() {
  return (
    <header className="flex h-11 flex-none items-center border-b border-[var(--color-border)] bg-[var(--color-bg-deep)] px-5">
      <div className="flex items-baseline gap-2.5">
        <span className="text-[12px] font-bold tracking-widest text-[var(--color-fg)]">
          FLO101
        </span>
        <span className="text-[11px] text-[var(--color-fg-faint)]">
          Critic
        </span>
      </div>
    </header>
  );
}
