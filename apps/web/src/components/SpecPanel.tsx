import { useState } from "react";

import type { SkillSpec, SynthesizeRequest } from "@flo101/api-types";

import { Panel } from "./Panel";
import { useCreateSpec, useSpecs } from "@/lib/hooks";

interface SpecPanelProps {
  selectedSpecId: string | null;
  onSelectSpec: (id: string) => void;
}

export function SpecPanel({ selectedSpecId, onSelectSpec }: SpecPanelProps) {
  const specs = useSpecs();
  const create = useCreateSpec({
    onSuccess: (spec) => onSelectSpec(spec.id),
  });
  const [showForm, setShowForm] = useState(false);

  return (
    <Panel
      step={1}
      title="Skill"
      hint="Synthesize a new skill or pick an existing one."
      active={!!selectedSpecId}
    >
      <div className="space-y-3">
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          className="w-full rounded-md border border-[--color-border] bg-[--color-bg] px-3 py-2 text-xs hover:border-[--color-accent]/60"
          disabled={create.isPending}
        >
          {showForm ? "Cancel" : "+ Synthesize new skill"}
        </button>

        {showForm && (
          <SpecForm
            disabled={create.isPending}
            onSubmit={(payload) => create.mutate(payload)}
          />
        )}

        {create.isPending && (
          <div className="rounded-md border border-[--color-border] bg-[--color-bg] px-3 py-2 text-xs text-[--color-fg-dim]">
            Preparing your skill profile…
          </div>
        )}
        {create.isError && (
          <ErrorBanner message={create.error.message} />
        )}

        <div className="space-y-1">
          <div className="text-xs uppercase tracking-wide text-[--color-fg-dim]">
            Available
          </div>
          {specs.isLoading && <div className="text-xs">Loading…</div>}
          {specs.data && specs.data.length === 0 && (
            <div className="text-xs text-[--color-fg-dim]">
              No skills yet — synthesize one.
            </div>
          )}
          <ul className="space-y-1">
            {specs.data?.map((s) => (
              <SpecRow
                key={s.id}
                spec={s}
                selected={s.id === selectedSpecId}
                onSelect={() => onSelectSpec(s.id)}
              />
            ))}
          </ul>
        </div>
      </div>
    </Panel>
  );
}

function SpecForm({
  disabled,
  onSubmit,
}: {
  disabled: boolean;
  onSubmit: (req: SynthesizeRequest) => void;
}) {
  const [goal, setGoal] = useState("");
  const [audience, setAudience] = useState("");
  const [outputGoal, setOutputGoal] = useState("");
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!goal.trim()) return;
        onSubmit({
          goal_text: goal.trim(),
          audience_hint: audience.trim() || null,
          output_goal: outputGoal.trim() || null,
          time_budget_minutes: null,
        });
      }}
      className="space-y-2"
    >
      <Field label="Goal" value={goal} onChange={setGoal} placeholder="e.g. learn to write a SOAP note for chest pain" required />
      <Field label="Audience (optional)" value={audience} onChange={setAudience} placeholder="medical resident, junior PM…" />
      <Field label="Output goal (optional)" value={outputGoal} onChange={setOutputGoal} placeholder="a 1-page memo, a passing query…" />
      <button
        type="submit"
        disabled={disabled || !goal.trim()}
        className="w-full rounded-md bg-[--color-accent]/15 border border-[--color-accent]/60 px-3 py-2 text-xs font-medium text-[--color-accent] hover:bg-[--color-accent]/20 disabled:opacity-50"
      >
        Synthesize
      </button>
    </form>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  required,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  required?: boolean;
}) {
  return (
    <label className="block">
      <span className="block text-xs text-[--color-fg-dim]">{label}</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        className="mt-1 w-full rounded-md border border-[--color-border] bg-[--color-bg] px-2 py-1.5 text-xs text-[--color-fg] placeholder:text-[--color-fg-dim]/60 focus:border-[--color-accent]/60 focus:outline-none"
      />
    </label>
  );
}

function SpecRow({
  spec,
  selected,
  onSelect,
}: {
  spec: SkillSpec;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <li>
      <button
        type="button"
        onClick={onSelect}
        className={`w-full rounded-md border px-2 py-2 text-left text-xs transition ${
          selected
            ? "border-[--color-accent]/60 bg-[--color-accent]/5"
            : "border-[--color-border] hover:border-[--color-fg-dim]"
        }`}
      >
        <div className="line-clamp-2 font-medium">{spec.goal_text}</div>
        <div className="mt-1 flex items-center gap-2 text-[10px] text-[--color-fg-dim]">
          <span>{spec.artifact_kind}</span>
          <span>·</span>
          <span>{spec.stakes_class} stakes</span>
          <span>·</span>
          <span>score {spec.meta_critique_score.toFixed(2)}</span>
          {spec.has_corpus && <span className="text-[--color-accent]">+corpus</span>}
        </div>
      </button>
    </li>
  );
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-[--color-danger]/50 bg-[--color-danger]/10 px-3 py-2 text-xs text-[--color-danger]">
      {message}
    </div>
  );
}
