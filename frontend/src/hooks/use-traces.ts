import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { traces } from "@/lib/api";

export function useTraces(
  page = 1,
  pageSize = 50,
  sessionId?: string,
  eventType?: string
) {
  return useQuery({
    queryKey: ["traces", page, pageSize, sessionId, eventType],
    queryFn: () => traces.list(page, pageSize, sessionId, eventType),
  });
}

export function useTraceDetail(runId: string | null) {
  return useQuery({
    queryKey: ["trace-detail", runId],
    queryFn: () => traces.get(runId!),
    enabled: !!runId,
  });
}

export function useDeleteTrace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (runId: string) => traces.delete(runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["traces"] });
      queryClient.invalidateQueries({ queryKey: ["trace-detail"] });
    },
  });
}
