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
      title="Skills"
      hint="Pick an existing skill, or synthesize a new one from a goal."
      active={!!selectedSpecId}
    >
      <div className="space-y-4">
        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-[10px] font-medium uppercase tracking-wider text-[--color-fg-faint]">
              Available
            </span>
            <span className="text-[10px] text-[--color-fg-faint] tabular-nums">
              {specs.data?.length ?? 0}
            </span>
          </div>
          {specs.isLoading && (
            <SkeletonRow />
          )}
          {specs.data && specs.data.length === 0 && (
            <p className="text-xs text-[--color-fg-dim]">
              Nothing here yet. Synthesize a skill below to begin.
            </p>
          )}
          <ul className="space-y-1.5">
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

        <div className="space-y-2 border-t border-[--color-border] pt-4">
          <button
            type="button"
            onClick={() => setShowForm((v) => !v)}
            className="w-full rounded-md border border-dashed border-[--color-border] bg-transparent px-3 py-2 text-xs text-[--color-fg-dim] transition-colors hover:border-[--color-accent]/50 hover:text-[--color-fg]"
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
            <p className="text-xs text-[--color-fg-dim]">
              Preparing your skill profile, ~5 seconds.
            </p>
          )}
          {create.isError && <ErrorBanner message={create.error.message} />}
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
      className="space-y-2.5"
    >
      <Field
        label="Goal"
        value={goal}
        onChange={setGoal}
        placeholder="learn to write a SOAP note for chest pain"
        required
      />
      <Field
        label="Audience"
        optional
        value={audience}
        onChange={setAudience}
        placeholder="medical resident, junior PM, mid-eng"
      />
      <Field
        label="Output goal"
        optional
        value={outputGoal}
        onChange={setOutputGoal}
        placeholder="a 1-page memo, a passing query"
      />
      <button
        type="submit"
        disabled={disabled || !goal.trim()}
        className="w-full rounded-md border border-[--color-accent]/60 bg-[--color-accent-soft] px-3 py-2 text-xs font-medium text-[--color-accent] transition-colors hover:bg-[--color-accent]/20 disabled:opacity-40"
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
  optional,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  required?: boolean;
  optional?: boolean;
}) {
  return (
    <label className="block">
      <span className="block text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
        {label}
        {optional && (
          <span className="ml-1 normal-case tracking-normal opacity-70">
            (optional)
          </span>
        )}
      </span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        className="mt-1 w-full rounded-md border border-[--color-border] bg-[--color-bg] px-2.5 py-1.5 text-xs text-[--color-fg] placeholder:text-[--color-fg-faint] focus:border-[--color-accent]/60 focus:outline-none focus:ring-1 focus:ring-[--color-accent]/30"
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
        className={`group flex w-full items-start gap-2.5 rounded-md px-2 py-2 text-left text-xs transition-colors ${
          selected
            ? "bg-[--color-accent-soft] text-[--color-fg]"
            : "text-[--color-fg-dim] hover:bg-[--color-surface-2] hover:text-[--color-fg]"
        }`}
      >
        <span
          aria-hidden
          className={`mt-1 inline-block h-1.5 w-1.5 flex-none rounded-full ${
            selected
              ? "bg-[--color-accent]"
              : "bg-[--color-border-strong] group-hover:bg-[--color-fg-dim]"
          }`}
        />
        <span className="min-w-0 flex-1">
          <span className="line-clamp-2 block font-medium leading-snug">
            {spec.goal_text}
          </span>
          <span className="mt-1 flex items-center gap-1.5 text-[10px] text-[--color-fg-faint]">
            <span>{spec.artifact_kind}</span>
            <span aria-hidden>·</span>
            <span>{spec.stakes_class} stakes</span>
            {spec.has_corpus && (
              <>
                <span aria-hidden>·</span>
                <span className="text-[--color-accent]">corpus</span>
              </>
            )}
            <span className="ml-auto tabular-nums">
              {spec.meta_critique_score.toFixed(2)}
            </span>
          </span>
        </span>
      </button>
    </li>
  );
}

function SkeletonRow() {
  return (
    <div className="space-y-1.5">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="h-8 animate-pulse rounded-md bg-[--color-surface-2]"
          style={{ animationDelay: `${i * 80}ms` }}
        />
      ))}
    </div>
  );
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-[--color-danger]/50 bg-[--color-danger]/10 px-3 py-2 text-xs text-[--color-danger]">
      {message}
    </div>
  );
}
