import { useState } from "react";

import { CorpusPanel } from "./components/CorpusPanel";
import { EvaluatePanel } from "./components/EvaluatePanel";
import { SpecPanel } from "./components/SpecPanel";
import { useHealth } from "./lib/hooks";

export function App() {
  const [selectedSpecId, setSelectedSpecId] = useState<string | null>(null);
  const health = useHealth();

  return (
    <main className="mx-auto max-w-6xl p-6">
      <header className="mb-6 flex items-center justify-between border-b border-[--color-border] pb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">flo101 — Critic Agent</h1>
          <p className="mt-1 text-xs text-[--color-fg-dim]">
            Proof-of-Work Evaluator · BYO knowledge · safety-aware · LangGraph + LangSmith
          </p>
        </div>
        <span
          className={`rounded-full border px-3 py-1 text-xs ${
            health.data?.status === "ok"
              ? "border-[--color-accent] text-[--color-accent]"
              : "border-[--color-warn] text-[--color-warn]"
          }`}
        >
          api: {health.data?.status ?? (health.isLoading ? "…" : "down")}
        </span>
      </header>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <SpecPanel
          selectedSpecId={selectedSpecId}
          onSelectSpec={setSelectedSpecId}
        />
        <CorpusPanel specId={selectedSpecId} />
        <EvaluatePanel specId={selectedSpecId} />
      </div>

      <footer className="mt-8 text-[10px] text-[--color-fg-dim]">
        flo101 · Track C · subject to safety_disposition routing for high-stakes domains.
      </footer>
    </main>
  );
}
