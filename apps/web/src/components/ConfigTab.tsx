import { useState } from "react";

import type { SynthesizeRequest } from "@flo101/api-types";

import { CollapsibleSection } from "./CollapsibleSection";
import { Row } from "./Row";
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
    <div>
      <CollapsibleSection
        title="Skill"
        flush
        meta={
          <span className="tabular-nums">
            {list.length} {list.length === 1 ? "skill" : "skills"}
          </span>
        }
      >
        <Row label="Active skill">
          <div className="flex items-stretch gap-2">
            <select
              value={selectedSpecId ?? ""}
              onChange={(e) => onSelectSpec(e.target.value)}
              className="min-w-0 flex-1 truncate rounded-md border border-[--color-border-strong] bg-[--color-surface-2] px-3 py-2 text-[13px] text-[--color-fg] focus:border-[--color-primary] focus:outline-none focus:ring-1 focus:ring-[--color-primary]/40"
            >
              <option value="" disabled>
                {list.length === 0 ? "No skills yet" : "Select a skill"}
              </option>
              {list.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.goal_text.length > 56
                    ? s.goal_text.slice(0, 53) + "…"
                    : s.goal_text}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => setShowSynth((v) => !v)}
              className="flex-none rounded-md border border-[--color-border-strong] bg-[--color-surface-2] px-3 py-2 text-[12px] font-medium text-[--color-fg] transition-colors hover:bg-[--color-surface-3]"
            >
              {showSynth ? "Cancel" : "+ New"}
            </button>
          </div>
          {showSynth && (
            <div className="mt-3">
              <SynthForm
                disabled={create.isPending}
                onSubmit={(payload) => {
                  create.mutate(payload);
                  setShowSynth(false);
                }}
              />
            </div>
          )}
          {create.isPending && (
            <p className="mt-3 flex items-center gap-2 text-[11px] text-[--color-fg-dim]">
              <Spinner />
              Synthesizing skill profile, ~5 seconds.
            </p>
          )}
          {create.isError && (
            <div className="mt-2 rounded border border-[--color-score-low]/40 bg-[--color-score-low]/10 px-2 py-1.5 text-[11px] text-[--color-score-low]">
              {create.error.message}
            </div>
          )}
        </Row>

        {spec.data && (
          <>
            <Row label="Audience" value={spec.data.audience_hint || "any"} />
            <Row label="Artifact kind">
              <span className="rounded border border-[--color-border-strong] bg-[--color-surface-2] px-2 py-0.5 font-mono text-[11px] text-[--color-fg]">
                {spec.data.artifact_kind}
              </span>
            </Row>
            <Row label="Stakes">
              <StakesBadge stakes={spec.data.stakes_class} />
            </Row>
            <Row
              label="Rubric"
              meta={
                <span className="tabular-nums">
                  {spec.data.rubric.dimensions.length} dimensions
                </span>
              }
            >
              <ul className="-mx-1 mt-1 space-y-2">
                {spec.data.rubric.dimensions.map((d) => (
                  <li
                    key={d.id}
                    className="flex items-center justify-between gap-3 px-1 text-[12px]"
                  >
                    <span className="min-w-0 flex-1 truncate text-[--color-fg]">
                      {d.title}
                    </span>
                    <span className="flex items-center gap-2 text-[--color-fg-dim]">
                      <span
                        className="h-1 w-14 overflow-hidden rounded-full bg-[--color-surface-3]"
                        aria-hidden
                      >
                        <span
                          className="block h-full rounded-full bg-[--color-primary]"
                          style={{ width: `${d.weight * 100}%` }}
                        />
                      </span>
                      <span className="w-9 text-right tabular-nums">
                        {(d.weight * 100).toFixed(0)}%
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            </Row>
          </>
        )}
      </CollapsibleSection>

      {selectedSpecId && spec.data && (
        <CollapsibleSection
          title="Reference material"
          flush
          defaultOpen={!spec.data.has_corpus}
          meta={
            spec.data.has_corpus ? (
              <span className="text-[--color-score-good]">attached</span>
            ) : (
              <span>none</span>
            )
          }
        >
          <Row label="What this is for">
            <p className="text-[12px] leading-relaxed text-[--color-fg-dim]">
              Plain-text or markdown files. Embedded once on upload, retrieved
              per evaluation, cited verbatim in evidence.
            </p>
          </Row>
          <Row label="Files">
            <input
              type="file"
              multiple
              accept=".txt,.md,.markdown,text/plain,text/markdown"
              onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
              className="block w-full text-[11px] text-[--color-fg-dim] file:mr-3 file:rounded file:border file:border-[--color-border-strong] file:bg-[--color-surface-2] file:px-3 file:py-1.5 file:text-[12px] file:font-medium file:text-[--color-fg] hover:file:bg-[--color-surface-3]"
            />
            {files.length > 0 && (
              <ul className="mt-2.5 space-y-1 text-[11px] text-[--color-fg-dim]">
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
                className="mt-3 rounded-md bg-[--color-primary] px-4 py-2 text-[12px] font-semibold text-white transition-colors hover:bg-[--color-primary-hover] disabled:opacity-50"
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
          </Row>
        </CollapsibleSection>
      )}
    </div>
  );
}

function StakesBadge({ stakes }: { stakes: string }) {
  const cls =
    stakes === "high"
      ? "bg-[--color-score-low]/20 text-[--color-score-low] border-[--color-score-low]/40"
      : stakes === "medium"
        ? "bg-[--color-score-mid]/20 text-[--color-score-mid] border-[--color-score-mid]/40"
        : "bg-[--color-surface-2] text-[--color-fg-dim] border-[--color-border-strong]";
  return (
    <span
      className={`inline-flex items-center rounded border px-2 py-0.5 text-[11px] font-medium tracking-wide ${cls}`}
    >
      {stakes}
    </span>
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
      className="space-y-3 rounded-md border border-[--color-border-strong] bg-[--color-surface] p-3.5"
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
        className="w-full rounded-md bg-[--color-primary] px-3 py-2 text-[12px] font-semibold text-white transition-colors hover:bg-[--color-primary-hover] disabled:opacity-40"
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
      <span className="block text-[10px] font-medium uppercase tracking-wider text-[--color-fg-faint]">
        {label}
      </span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        className="mt-1.5 w-full rounded-md border border-[--color-border-strong] bg-[--color-bg] px-2.5 py-1.5 text-[12px] text-[--color-fg] placeholder:text-[--color-fg-faint] focus:border-[--color-primary] focus:outline-none focus:ring-1 focus:ring-[--color-primary]/40"
      />
    </label>
  );
}

function Spinner() {
  return (
    <span
      aria-hidden
      className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-[--color-fg-faint] border-t-[--color-primary]"
    />
  );
}
