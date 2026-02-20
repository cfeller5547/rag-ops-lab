import { useTraceDetail } from "@/hooks/use-traces";
import { TraceEventCard } from "./trace-event-card";
import { MetricCard } from "@/components/shared/metric-card";
import { formatDuration, formatCost } from "@/lib/format";

interface TraceDetailViewProps {
  runId: string;
}

export function TraceDetailView({ runId }: TraceDetailViewProps) {
  const { data: detail, isLoading } = useTraceDetail(runId);

  if (isLoading) {
    return (
      <div className="space-y-3 rounded-xl border border-border bg-card p-4">
        <div className="h-6 w-48 animate-pulse rounded bg-surface-2" />
        <div className="grid grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-xl bg-surface-2" />
          ))}
        </div>
      </div>
    );
  }

  if (!detail) return null;

  const { summary, events } = detail;

  return (
    <div className="space-y-4 rounded-xl border border-border bg-card p-4">
      <h3 className="text-sm font-semibold text-foreground">Trace Timeline</h3>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <MetricCard
          label="Events"
          value={summary.total_events}
          accentColor="primary"
        />
        <MetricCard
          label="Duration"
          value={formatDuration(summary.total_duration_ms)}
          accentColor="ok"
        />
        <MetricCard
          label="Tokens"
          value={summary.total_tokens}
          accentColor="muted"
        />
        <MetricCard
          label="Cost"
          value={formatCost(summary.total_cost_usd)}
          accentColor="muted"
        />
        <MetricCard
          label="Errors"
          value={summary.has_errors ? "Yes" : "None"}
          accentColor={summary.has_errors ? "destructive" : "ok"}
        />
      </div>

      <div className="space-y-2">
        {events.map((event) => (
          <TraceEventCard key={event.id} event={event} />
        ))}
      </div>
    </div>
  );
}
