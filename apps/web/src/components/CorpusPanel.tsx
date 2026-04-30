import { useState } from "react";

import { Panel } from "./Panel";
import { useSpec, useUploadCorpus } from "@/lib/hooks";

interface CorpusPanelProps {
  specId: string | null;
}

export function CorpusPanel({ specId }: CorpusPanelProps) {
  const spec = useSpec(specId);
  const upload = useUploadCorpus();
  const [files, setFiles] = useState<File[]>([]);

  return (
    <Panel
      step={2}
      title="Corpus (optional)"
      hint="Upload reference materials. Used by the Critic for grounded evidence."
      active={!!spec.data?.has_corpus}
    >
      {!specId && (
        <div className="text-xs text-[--color-fg-dim]">Pick a skill first.</div>
      )}

      {specId && (
        <div className="space-y-3">
          <input
            type="file"
            multiple
            accept=".txt,.md,.markdown,text/plain,text/markdown"
            onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
            className="w-full text-xs text-[--color-fg-dim] file:mr-2 file:rounded-md file:border file:border-[--color-border] file:bg-[--color-bg] file:px-2 file:py-1 file:text-xs file:text-[--color-fg]"
          />

          {files.length > 0 && (
            <ul className="space-y-1 text-xs text-[--color-fg-dim]">
              {files.map((f) => (
                <li key={f.name}>
                  · {f.name} <span className="opacity-60">({Math.ceil(f.size / 1024)} KB)</span>
                </li>
              ))}
            </ul>
          )}

          <button
            type="button"
            disabled={!files.length || upload.isPending}
            onClick={() => upload.mutate({ specId, files })}
            className="w-full rounded-md bg-[--color-accent]/15 border border-[--color-accent]/60 px-3 py-2 text-xs font-medium text-[--color-accent] disabled:opacity-50"
          >
            {upload.isPending ? "Embedding…" : "Upload & embed"}
          </button>

          {upload.isSuccess && (
            <div className="rounded-md border border-[--color-accent]/50 bg-[--color-accent]/5 px-3 py-2 text-xs text-[--color-accent]">
              {upload.data.chunks_added} chunks added · {upload.data.total_tokens} tokens · {upload.data.sources.length} source(s)
            </div>
          )}
          {upload.isError && (
            <div className="rounded-md border border-[--color-danger]/50 bg-[--color-danger]/10 px-3 py-2 text-xs text-[--color-danger]">
              {upload.error.message}
            </div>
          )}
          {spec.data?.has_corpus && !upload.isSuccess && (
            <div className="text-xs text-[--color-fg-dim]">
              This skill already has corpus material attached.
            </div>
          )}
        </div>
      )}
    </Panel>
  );
}
