import { useState } from "react";

import { Accordion } from "./Accordion";
import { useSpec, useUploadCorpus } from "@/lib/hooks";

interface CorpusPanelProps {
  specId: string | null;
}

export function CorpusPanel({ specId }: CorpusPanelProps) {
  const spec = useSpec(specId);
  const upload = useUploadCorpus();
  const [files, setFiles] = useState<File[]>([]);

  if (!specId || !spec.data) return null;

  const hasCorpus = !!spec.data.has_corpus;

  return (
    <section className="rounded-xl border border-[--color-border] bg-[--color-surface] px-4">
      <Accordion
        resetKey={specId}
        defaultOpen={!hasCorpus && !upload.isSuccess}
        title={
          <span>
            Reference material{" "}
            <span className="text-[--color-fg-faint]">(optional)</span>
          </span>
        }
        meta={
          hasCorpus ? (
            <span className="text-[--color-accent]">attached</span>
          ) : (
            <span>none</span>
          )
        }
      >
        <div className="space-y-3">
          <p className="text-[11px] leading-relaxed text-[--color-fg-dim]">
            Plain-text or markdown. Embedded once on upload, retrieved per
            evaluation, cited in evidence.
          </p>

          <input
            type="file"
            multiple
            accept=".txt,.md,.markdown,text/plain,text/markdown"
            onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
            className="block w-full text-xs text-[--color-fg-dim] file:mr-3 file:rounded-md file:border file:border-[--color-border] file:bg-[--color-surface-2] file:px-3 file:py-1.5 file:text-xs file:text-[--color-fg] hover:file:border-[--color-accent]/50"
          />

          {files.length > 0 && (
            <ul className="space-y-1 text-[11px] text-[--color-fg-dim]">
              {files.map((f) => (
                <li
                  key={f.name}
                  className="flex items-center justify-between gap-2"
                >
                  <span className="truncate">{f.name}</span>
                  <span className="tabular-nums text-[--color-fg-faint]">
                    {Math.ceil(f.size / 1024)} KB
                  </span>
                </li>
              ))}
            </ul>
          )}

          <div className="flex items-center gap-3">
            <button
              type="button"
              disabled={!files.length || upload.isPending}
              onClick={() => upload.mutate({ specId, files })}
              className="rounded-md border border-[--color-accent]/60 bg-[--color-accent-soft] px-3 py-1.5 text-xs font-medium text-[--color-accent] transition-colors hover:bg-[--color-accent]/20 disabled:opacity-40"
            >
              {upload.isPending ? "Embedding…" : "Upload and embed"}
            </button>
            {upload.isSuccess && (
              <span className="text-[11px] text-[--color-accent]">
                {upload.data.chunks_added} chunks added,{" "}
                {upload.data.total_tokens.toLocaleString()} tokens.
              </span>
            )}
          </div>

          {upload.isError && (
            <div className="rounded-md border border-[--color-danger]/50 bg-[--color-danger]/10 px-3 py-2 text-xs text-[--color-danger]">
              {upload.error.message}
            </div>
          )}
        </div>
      </Accordion>
    </section>
  );
}
