import { useState } from "react";

import { CorpusPanel } from "./components/CorpusPanel";
import { EvaluatePanel } from "./components/EvaluatePanel";
import { SkillSummary } from "./components/SkillSummary";
import { SpecPanel } from "./components/SpecPanel";
import { useHealth, useSpec } from "./lib/hooks";

export function App() {
  const [selectedSpecId, setSelectedSpecId] = useState<string | null>(null);
  const health = useHealth();
  const spec = useSpec(selectedSpecId);
  const status = health.data?.status ?? (health.isLoading ? "…" : "down");

  return (
    <main className="mx-auto max-w-6xl px-6 pt-8 pb-16">
      <header className="mb-10 flex items-end justify-between gap-6 border-b border-[--color-border] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">flo101</h1>
          <p className="mt-1 text-sm text-[--color-fg-dim]">
            Critic Agent. Bring your knowledge, submit your work, get
            evidence-cited feedback and one next step.
          </p>
        </div>
        <HealthBadge status={status} />
      </header>

      <div className="grid grid-cols-1 gap-x-10 gap-y-8 lg:grid-cols-12">
        <aside className="lg:col-span-4">
          <SpecPanel
            selectedSpecId={selectedSpecId}
            onSelectSpec={setSelectedSpecId}
          />
        </aside>

        <section className="space-y-5 lg:col-span-8">
          {spec.data && <SkillSummary spec={spec.data} />}
          <CorpusPanel specId={selectedSpecId} />
          <EvaluatePanel specId={selectedSpecId} />
        </section>
      </div>

      <footer className="mt-16 text-[10px] text-[--color-fg-faint]">
        Track C. High-stakes domains route through safety_disposition; numeric
        scores are withheld where expert review is required.
      </footer>
    </main>
  );
}

function HealthBadge({ status }: { status: string }) {
  const ok = status === "ok";
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs ${
        ok
          ? "border-[--color-accent]/40 text-[--color-accent]"
          : "border-[--color-warn]/50 text-[--color-warn]"
      }`}
    >
      <span
        className={`inline-block h-1.5 w-1.5 rounded-full ${
          ok ? "bg-[--color-accent]" : "bg-[--color-warn]"
        }`}
      />
      api {status}
    </span>
  );
}
