import { useEvalRuns, useDeleteEvalRun } from "@/hooks/use-evals";
import { StatusBadge } from "@/components/shared/status-badge";
import { EmptyState } from "@/components/shared/empty-state";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import { formatScore, formatDuration, shortId } from "@/lib/format";
import { FlaskConical, Trash2 } from "lucide-react";
import { toast } from "sonner";

interface EvalRunsTableProps {
  onSelectRun: (evalId: string) => void;
  selectedRunId: string | null;
}

export function EvalRunsTable({ onSelectRun, selectedRunId }: EvalRunsTableProps) {
  const { data, isLoading } = useEvalRuns();
  const deleteRun = useDeleteEvalRun();
  const { confirm, dialogProps } = useConfirmDialog();

  const runs = data?.eval_runs ?? [];

  const handleDelete = async (evalId: string, name: string) => {
    const confirmed = await confirm({
      title: "Delete Evaluation",
      description: `Delete evaluation "${name}"? This cannot be undone.`,
      confirmLabel: "Delete",
    });
    if (confirmed) {
      deleteRun.mutate(evalId, {
        onSuccess: () => toast.success(`Deleted "${name}"`),
        onError: (err) => toast.error(`Delete failed: ${err.message}`),
      });
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-12 animate-pulse rounded-lg bg-card" />
        ))}
      </div>
    );
  }

  if (runs.length === 0) {
    return (
      <EmptyState
        icon={FlaskConical}
        title="No evaluations yet"
        description="Create a new evaluation to test your RAG pipeline."
      />
    );
  }

  return (
    <>
      <div className="overflow-hidden rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-surface-2">
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">ID</th>
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Name</th>
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Dataset</th>
              <th className="px-4 py-2.5 text-right text-xs font-medium text-muted-foreground">Progress</th>
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Status</th>
              <th className="px-4 py-2.5 text-right text-xs font-medium text-muted-foreground">Grounded</th>
              <th className="px-4 py-2.5 text-right text-xs font-medium text-muted-foreground">Halluc.</th>
              <th className="px-4 py-2.5 text-right text-xs font-medium text-muted-foreground">P95</th>
              <th className="w-10 px-4 py-2.5" />
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr
                key={run.eval_id}
                onClick={() => onSelectRun(run.eval_id)}
                className={`cursor-pointer border-b border-border transition-colors ${
                  selectedRunId === run.eval_id ? "bg-primary/5" : "hover:bg-card/80"
                }`}
              >
                <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground">
                  {shortId(run.eval_id)}
                </td>
                <td className="px-4 py-2.5 font-medium text-foreground">{run.name}</td>
                <td className="px-4 py-2.5 text-muted-foreground">{run.dataset_name}</td>
                <td className="px-4 py-2.5 text-right text-muted-foreground">
                  {run.completed_cases}/{run.total_cases}
                </td>
                <td className="px-4 py-2.5">
                  <StatusBadge status={run.status} />
                </td>
                <td className="px-4 py-2.5 text-right text-muted-foreground">
                  {run.metrics ? formatScore(run.metrics.groundedness_score) : "-"}
                </td>
                <td className="px-4 py-2.5 text-right text-muted-foreground">
                  {run.metrics ? formatScore(run.metrics.hallucination_rate) : "-"}
                </td>
                <td className="px-4 py-2.5 text-right text-muted-foreground">
                  {run.metrics ? formatDuration(run.metrics.latency_p95_ms) : "-"}
                </td>
                <td className="px-4 py-2.5">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(run.eval_id, run.name);
                    }}
                    className="rounded p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-destructive"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ConfirmDialog {...dialogProps} />
    </>
  );
}
