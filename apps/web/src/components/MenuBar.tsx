export function MenuBar() {
  return (
    <header className="flex h-11 flex-none items-center border-b border-[--color-border] bg-[--color-bg-deep] px-5">
      <div className="flex items-baseline gap-2.5">
        <span className="text-[12px] font-bold tracking-widest text-[--color-fg]">
          FLO101
        </span>
        <span className="text-[11px] text-[--color-fg-faint]">
          Critic
        </span>
      </div>
    </header>
  );
}
