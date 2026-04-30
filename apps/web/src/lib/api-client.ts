/**
 * Typed client over the FastAPI backend.
 *
 * In dev: requests go through Vite's `/api` proxy → api container.
 * In prod: requests go through nginx's `/api` location → api service.
 */

import type {
  ArtifactSubmission,
  CorpusUploadResult,
  Evaluation,
  SkillSpec,
  SynthesizeRequest,
} from "@flo101/api-types";

const API_BASE =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "/api";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {};
  if (!(init.body instanceof FormData) && init.body !== undefined) {
    headers["content-type"] = "application/json";
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { ...headers, ...(init.headers as Record<string, string> ?? {}) },
  });
  const text = await res.text();
  const body: unknown = text ? safeParseJson(text) : null;
  if (!res.ok) {
    throw new ApiError(res.status, `${res.status} ${res.statusText}`, body);
  }
  return body as T;
}

function safeParseJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export const api = {
  healthz: () => request<{ status: string; version: string }>("/healthz"),

  listSpecs: () => request<SkillSpec[]>("/spec"),
  getSpec: (id: string) => request<SkillSpec>(`/spec/${encodeURIComponent(id)}`),
  createSpec: (payload: SynthesizeRequest) =>
    request<SkillSpec>("/spec", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  uploadCorpus: (specId: string, files: File[]) => {
    const fd = new FormData();
    for (const f of files) fd.append("files", f);
    return request<CorpusUploadResult>(
      `/spec/${encodeURIComponent(specId)}/corpus`,
      { method: "POST", body: fd },
    );
  },
  getCorpusSummary: (specId: string) =>
    request<{ summary: string | null }>(
      `/spec/${encodeURIComponent(specId)}/corpus/summary`,
    ),

  evaluate: (specId: string, submission: ArtifactSubmission) =>
    request<Evaluation>(
      `/spec/${encodeURIComponent(specId)}/evaluate`,
      { method: "POST", body: JSON.stringify(submission) },
    ),
  getEvaluation: (id: string) =>
    request<Evaluation>(`/evaluation/${encodeURIComponent(id)}`),
  listEvaluations: () => request<Evaluation[]>("/evaluation"),
};
