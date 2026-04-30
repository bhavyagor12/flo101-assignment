import { useState } from "react";

import type { SkillSpec, SynthesizeRequest } from "@flo101/api-types";

import { CollapsibleSection } from "./CollapsibleSection";
import {
  useCreateSpec,
  useSpec,
  useSpecs,
  useUploadCorpus,
} from "@/lib/hooks";

interface ConfigTabProps {
  selectedSpecId: string | null;
  onSelectSpec: (id: string) => void;
}

export function ConfigTab({ selectedSpecId, onSelectSpec }: ConfigTabProps) {
  const specs = useSpecs();
  const spec = useSpec(selectedSpecId);
  const create = useCreateSpec({ onSuccess: (s) => onSelectSpec(s.id) });
  const upload = useUploadCorpus();
  const [showSynth, setShowSynth] = useState(false);
  const [files, setFiles] = useState<File[]>([]);

  const list = specs.data ?? [];

  return (
    <div className="text-[12px]">
      <CollapsibleSection
        title="Skill Configuration"
        meta={
          <span className="text-[10px] text-[--color-fg-faint] tabular-nums">
            {list.length} {list.length === 1 ? "skill" : "skills"}
          </span>
        }
      >
        <div className="space-y-3">
          <Field label="Skill">
            <div className="flex items-center gap-2">
              <select
                value={selectedSpecId ?? ""}
                onChange={(e) => onSelectSpec(e.target.value)}
                className="flex-1 rounded border border-[--color-border] bg-[--color-bg] px-2 py-1.5 text-[12px] text-[--color-fg] focus:border-[--color-primary]/60 focus:outline-none"
              >
                <option value="" disabled>
                  {list.length === 0 ? "No skills yet" : "Select a skill…"}
                </option>
                {list.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.goal_text.length > 60
                      ? s.goal_text.slice(0, 57) + "…"
                      : s.goal_text}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => setShowSynth((v) => !v)}
                className="rounded border border-[--color-border] px-2 py-1.5 text-[11px] text-[--color-fg-dim] hover:border-[--color-primary]/60 hover:text-[--color-fg]"
              >
                {showSynth ? "Cancel" : "+ New"}
              </button>
            </div>
          </Field>

          {showSynth && (
            <SynthForm
              disabled={create.isPending}
              onSubmit={(payload) => {
                create.mutate(payload);
                setShowSynth(false);
              }}
            />
          )}
          {create.isPending && (
            <div className="text-[11px] text-[--color-fg-dim]">
              Synthesizing skill profile, ~5 seconds.
            </div>
          )}
          {create.isError && (
            <div className="rounded border border-[--color-score-low]/40 bg-[--color-score-low]/10 px-2 py-1.5 text-[11px] text-[--color-score-low]">
              {create.error.message}
            </div>
          )}

          {spec.data && (
            <>
              <Field label="Audience">
                <div className="text-[12px] text-[--color-fg-dim]">
                  {spec.data.audience_hint || "any"}
                </div>
              </Field>
              <Field label="Artifact kind">
                <div className="text-[12px] text-[--color-fg-dim]">
                  {spec.data.artifact_kind}
                </div>
              </Field>
              <Field label="Stakes">
                <span
                  className={`inline-block rounded px-1.5 py-0.5 text-[11px] ${
                    spec.data.stakes_class === "high"
                      ? "bg-[--color-score-low]/15 text-[--color-score-low]"
                      : spec.data.stakes_class === "medium"
                        ? "bg-[--color-score-mid]/15 text-[--color-score-mid]"
                        : "bg-[--color-surface-2] text-[--color-fg-dim]"
                  }`}
                >
                  {spec.data.stakes_class}
                </span>
              </Field>
              <Field
                label={`Rubric · ${spec.data.rubric.dimensions.length} dimensions`}
              >
                <ul className="space-y-1 text-[11px] text-[--color-fg-dim]">
                  {spec.data.rubric.dimensions.map((d) => (
                    <li
                      key={d.id}
                      className="flex items-baseline justify-between gap-3"
                    >
                      <span className="truncate text-[--color-fg]">
                        {d.title}
                      </span>
                      <span className="tabular-nums text-[--color-fg-faint]">
                        {(d.weight * 100).toFixed(0)}%
                      </span>
                    </li>
                  ))}
                </ul>
              </Field>
            </>
          )}
        </div>
      </CollapsibleSection>

      {selectedSpecId && spec.data && (
        <CollapsibleSection
          title="Reference material"
          defaultOpen={!spec.data.has_corpus}
          meta={
            spec.data.has_corpus ? (
              <span className="text-[10px] text-[--color-score-good]">attached</span>
            ) : (
              <span className="text-[10px] text-[--color-fg-faint]">none</span>
            )
          }
        >
          <p className="mb-3 text-[11px] leading-relaxed text-[--color-fg-dim]">
            Plain-text or markdown. Embedded once on upload, retrieved per
            evaluation, cited verbatim in evidence.
          </p>
          <input
            type="file"
            multiple
            accept=".txt,.md,.markdown,text/plain,text/markdown"
            onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
            className="block w-full text-[11px] text-[--color-fg-dim] file:mr-3 file:rounded file:border file:border-[--color-border] file:bg-[--color-surface-2] file:px-2.5 file:py-1 file:text-[11px] file:text-[--color-fg] hover:file:border-[--color-primary]/50"
          />
          {files.length > 0 && (
            <ul className="mt-2 space-y-0.5 text-[11px] text-[--color-fg-dim]">
              {files.map((f) => (
                <li key={f.name} className="flex justify-between gap-2">
                  <span className="truncate">{f.name}</span>
                  <span className="tabular-nums text-[--color-fg-faint]">
                    {Math.ceil(f.size / 1024)} KB
                  </span>
                </li>
              ))}
            </ul>
          )}
          {files.length > 0 && (
            <button
              type="button"
              disabled={!files.length || upload.isPending}
              onClick={() =>
                upload.mutate({ specId: selectedSpecId, files })
              }
              className="mt-2 rounded border border-[--color-primary]/60 bg-[--color-primary-soft] px-3 py-1.5 text-[11px] font-medium text-[--color-primary] hover:bg-[--color-primary]/25 disabled:opacity-40"
            >
              {upload.isPending ? "Embedding…" : "Upload and embed"}
            </button>
          )}
          {upload.isSuccess && (
            <p className="mt-2 text-[11px] text-[--color-score-good]">
              {upload.data.chunks_added} chunks added,{" "}
              {upload.data.total_tokens.toLocaleString()} tokens.
            </p>
          )}
          {upload.isError && (
            <div className="mt-2 rounded border border-[--color-score-low]/40 bg-[--color-score-low]/10 px-2 py-1.5 text-[11px] text-[--color-score-low]">
              {upload.error.message}
            </div>
          )}
        </CollapsibleSection>
      )}
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="mb-1 text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
        {label}
      </div>
      {children}
    </div>
  );
}

function SynthForm({
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
      className="space-y-2 rounded border border-[--color-border] bg-[--color-surface] p-3"
    >
      <FormField
        label="Goal"
        value={goal}
        onChange={setGoal}
        placeholder="learn to write a SOAP note for chest pain"
        required
      />
      <FormField
        label="Audience (optional)"
        value={audience}
        onChange={setAudience}
        placeholder="medical resident, junior PM, mid-eng"
      />
      <FormField
        label="Output goal (optional)"
        value={outputGoal}
        onChange={setOutputGoal}
        placeholder="a 1-page memo, a passing query"
      />
      <button
        type="submit"
        disabled={disabled || !goal.trim()}
        className="w-full rounded border border-[--color-primary]/60 bg-[--color-primary-soft] px-3 py-1.5 text-[11px] font-medium text-[--color-primary] hover:bg-[--color-primary]/25 disabled:opacity-40"
      >
        Synthesize
      </button>
    </form>
  );
}

function FormField({
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
      <span className="block text-[10px] uppercase tracking-wider text-[--color-fg-faint]">
        {label}
      </span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        className="mt-1 w-full rounded border border-[--color-border] bg-[--color-bg] px-2 py-1.5 text-[11px] text-[--color-fg] placeholder:text-[--color-fg-faint] focus:border-[--color-primary]/60 focus:outline-none"
      />
    </label>
  );
}
