import { useDeleteTrace } from "@/hooks/use-traces";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import { EmptyState } from "@/components/shared/empty-state";
import { formatDuration, formatCost, formatDateShort, shortId } from "@/lib/format";
import { Activity, Trash2, CheckCircle, XCircle } from "lucide-react";
import { toast } from "sonner";
import type { TraceSummary } from "@/types/api";

interface TraceListTableProps {
  traces: TraceSummary[];
  isLoading: boolean;
  onSelectTrace: (runId: string) => void;
  selectedTraceId: string | null;
}

export function TraceListTable({
  traces,
  isLoading,
  onSelectTrace,
  selectedTraceId,
}: TraceListTableProps) {
  const deleteTrace = useDeleteTrace();
  const { confirm, dialogProps } = useConfirmDialog();

  const handleDelete = async (runId: string) => {
    const confirmed = await confirm({
      title: "Delete Trace",
      description: `Delete trace ${shortId(runId)}? This cannot be undone.`,
      confirmLabel: "Delete",
    });
    if (confirmed) {
      deleteTrace.mutate(runId, {
        onSuccess: () => toast.success("Trace deleted"),
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

  if (traces.length === 0) {
    return (
      <EmptyState
        icon={Activity}
        title="No traces yet"
        description="Send a chat message to generate traces."
      />
    );
  }

  return (
    <>
      <div className="overflow-hidden rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-surface-2">
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Run ID</th>
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Session</th>
              <th className="px-4 py-2.5 text-right text-xs font-medium text-muted-foreground">Events</th>
              <th className="px-4 py-2.5 text-right text-xs font-medium text-muted-foreground">Duration</th>
              <th className="px-4 py-2.5 text-right text-xs font-medium text-muted-foreground">Tokens</th>
              <th className="px-4 py-2.5 text-right text-xs font-medium text-muted-foreground">Cost</th>
              <th className="px-4 py-2.5 text-center text-xs font-medium text-muted-foreground">Status</th>
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Time</th>
              <th className="w-10 px-4 py-2.5" />
            </tr>
          </thead>
          <tbody>
            {traces.map((trace) => (
              <tr
                key={trace.run_id}
                onClick={() => onSelectTrace(trace.run_id)}
                className={`cursor-pointer border-b border-border transition-colors ${
                  selectedTraceId === trace.run_id ? "bg-primary/5" : "hover:bg-card/80"
                }`}
              >
                <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground">
                  {shortId(trace.run_id)}
                </td>
                <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground">
                  {trace.session_id ? shortId(trace.session_id) : "N/A"}
                </td>
                <td className="px-4 py-2.5 text-right text-muted-foreground">
                  {trace.event_count}
                </td>
                <td className="px-4 py-2.5 text-right text-muted-foreground">
                  {formatDuration(trace.total_duration_ms)}
                </td>
                <td className="px-4 py-2.5 text-right text-muted-foreground">
                  {trace.total_tokens}
                </td>
                <td className="px-4 py-2.5 text-right text-muted-foreground">
                  {formatCost(trace.total_cost_usd)}
                </td>
                <td className="px-4 py-2.5 text-center">
                  {trace.status === "success" ? (
                    <CheckCircle className="mx-auto h-4 w-4 text-ok" />
                  ) : (
                    <XCircle className="mx-auto h-4 w-4 text-destructive" />
                  )}
                </td>
                <td className="px-4 py-2.5 text-muted-foreground">
                  {trace.last_event_at ? formatDateShort(trace.last_event_at) : "-"}
                </td>
                <td className="px-4 py-2.5">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(trace.run_id);
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
