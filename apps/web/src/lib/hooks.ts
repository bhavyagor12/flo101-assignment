/**
 * TanStack Query hooks. One per backend endpoint, typed end-to-end via
 * `@flo101/api-types`.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationOptions,
} from "@tanstack/react-query";

import type {
  ArtifactSubmission,
  CorpusUploadResult,
  Evaluation,
  SkillSpec,
  SynthesizeRequest,
} from "@flo101/api-types";

import { api, type ApiError } from "./api-client";

export const queryKeys = {
  health: ["health"] as const,
  specs: ["specs"] as const,
  spec: (id: string) => ["specs", id] as const,
  corpusSummary: (id: string) => ["specs", id, "corpus", "summary"] as const,
  evaluations: ["evaluations"] as const,
  evaluation: (id: string) => ["evaluations", id] as const,
};

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => api.healthz(),
    refetchInterval: 10_000,
  });
}

export function useSpecs() {
  return useQuery({
    queryKey: queryKeys.specs,
    queryFn: () => api.listSpecs(),
  });
}

export function useSpec(id: string | null) {
  return useQuery({
    queryKey: id ? queryKeys.spec(id) : ["specs", "none"],
    queryFn: () => api.getSpec(id as string),
    enabled: !!id,
  });
}

export function useEvaluations() {
  return useQuery({
    queryKey: queryKeys.evaluations,
    queryFn: () => api.listEvaluations(),
  });
}

export function useCreateSpec(
  opts?: UseMutationOptions<SkillSpec, ApiError, SynthesizeRequest>,
) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: SynthesizeRequest) => api.createSpec(payload),
    onSuccess: (...args) => {
      const [spec] = args;
      // Push the new spec into the cached list directly. invalidateQueries
      // alone wasn't reliably triggering a refetch on this version of
      // TanStack Query when the previous list returned [].
      qc.setQueryData<SkillSpec[]>(queryKeys.specs, (old = []) => {
        if (old.some((s) => s.id === spec.id)) return old;
        return [spec, ...old];
      });
      qc.setQueryData(queryKeys.spec(spec.id), spec);
      qc.invalidateQueries({ queryKey: queryKeys.specs });
      opts?.onSuccess?.(...args);
    },
    ...opts,
  });
}

export function useUploadCorpus(
  opts?: UseMutationOptions<
    CorpusUploadResult,
    ApiError,
    { specId: string; files: File[] }
  >,
) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ specId, files }: { specId: string; files: File[] }) =>
      api.uploadCorpus(specId, files),
    onSuccess: (...args) => {
      const [, vars] = args;
      qc.invalidateQueries({ queryKey: queryKeys.spec(vars.specId) });
      qc.invalidateQueries({ queryKey: queryKeys.corpusSummary(vars.specId) });
      opts?.onSuccess?.(...args);
    },
    ...opts,
  });
}

export function useEvaluate(
  opts?: UseMutationOptions<
    Evaluation,
    ApiError,
    { specId: string; submission: ArtifactSubmission }
  >,
) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ specId, submission }) => api.evaluate(specId, submission),
    onSuccess: (...args) => {
      const [ev] = args;
      qc.invalidateQueries({ queryKey: queryKeys.evaluations });
      qc.setQueryData(queryKeys.evaluation(ev.id), ev);
      opts?.onSuccess?.(...args);
    },
    ...opts,
  });
}
