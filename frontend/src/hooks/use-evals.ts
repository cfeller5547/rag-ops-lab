import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { evals } from "@/lib/api";
import type { EvalRunRequest } from "@/types/api";

export function useEvalRuns(page = 1, pageSize = 50) {
  return useQuery({
    queryKey: ["eval-runs", page, pageSize],
    queryFn: () => evals.list(page, pageSize),
  });
}

export function useEvalDatasets() {
  return useQuery({
    queryKey: ["eval-datasets"],
    queryFn: () => evals.datasets(),
  });
}

export function useEvalDetail(evalId: string | null) {
  return useQuery({
    queryKey: ["eval-detail", evalId],
    queryFn: () => evals.get(evalId!),
    enabled: !!evalId,
  });
}

export function useCreateEvalRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: EvalRunRequest) => evals.create(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["eval-runs"] });
    },
  });
}

export function useDeleteEvalRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (evalId: string) => evals.delete(evalId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["eval-runs"] });
      queryClient.invalidateQueries({ queryKey: ["eval-detail"] });
    },
  });
}

export function useCancelEvalRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (evalId: string) => evals.cancel(evalId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["eval-runs"] });
    },
  });
}
