const MENU_ITEMS = ["File", "Edit", "Artifact", "Rubric", "View", "Window", "Help"];

export function MenuBar() {
  return (
    <header className="flex h-9 flex-none items-center border-b border-[--color-border] bg-[--color-bg-deep] px-4">
      <span className="mr-6 text-[11px] font-bold tracking-widest text-[--color-fg]">
        FLO101
      </span>
      <nav className="flex items-center gap-1 text-[11px] text-[--color-fg-dim]">
        {MENU_ITEMS.map((label) => (
          <button
            key={label}
            type="button"
            className="rounded px-2.5 py-1 hover:bg-[--color-surface-2] hover:text-[--color-fg]"
          >
            {label}
          </button>
        ))}
      </nav>
    </header>
  );
}
