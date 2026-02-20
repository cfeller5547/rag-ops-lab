import { Search, Bot, Wrench, CheckCircle, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatDuration, formatDateShort } from "@/lib/format";
import type { TraceEventResponse } from "@/types/api";

const eventConfig: Record<
  string,
  { icon: typeof Search; color: string; borderColor: string }
> = {
  retrieval: {
    icon: Search,
    color: "text-blue-400",
    borderColor: "border-l-blue-400",
  },
  model_call: {
    icon: Bot,
    color: "text-primary",
    borderColor: "border-l-primary",
  },
  tool_call: {
    icon: Wrench,
    color: "text-warning",
    borderColor: "border-l-warning",
  },
  validation: {
    icon: CheckCircle,
    color: "text-ok",
    borderColor: "border-l-ok",
  },
  error: {
    icon: AlertTriangle,
    color: "text-destructive",
    borderColor: "border-l-destructive",
  },
};

interface TraceEventCardProps {
  event: TraceEventResponse;
}

export function TraceEventCard({ event }: TraceEventCardProps) {
  const config = eventConfig[event.event_type] ?? eventConfig.error;
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "rounded-lg border border-border border-l-2 bg-card p-3",
        config.borderColor
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Icon className={cn("h-4 w-4 shrink-0", config.color)} />
          <div>
            <span className="text-xs font-medium text-foreground">
              {event.event_name}
            </span>
            <span className="ml-2 rounded bg-surface-2 px-1.5 py-0.5 text-[10px] text-muted-foreground">
              {event.event_type}
            </span>
          </div>
        </div>
        <span className="shrink-0 text-[10px] text-muted-foreground">
          {formatDateShort(event.timestamp)}
        </span>
      </div>

      <div className="mt-2 flex flex-wrap gap-3 text-[10px] text-muted-foreground">
        {event.duration_ms != null && (
          <span>Duration: {formatDuration(event.duration_ms)}</span>
        )}
        {event.tokens_in != null && <span>In: {event.tokens_in} tok</span>}
        {event.tokens_out != null && <span>Out: {event.tokens_out} tok</span>}
        {event.cost_usd != null && (
          <span>Cost: ${event.cost_usd.toFixed(4)}</span>
        )}
      </div>

      {event.event_type === "retrieval" && event.event_data && (
        <p className="mt-1 truncate text-[10px] text-muted-foreground">
          Query: {String(event.event_data.query ?? "")}
          {event.event_data.results_count != null &&
            ` (${String(event.event_data.results_count)} results)`}
        </p>
      )}

      {event.event_type === "model_call" && event.event_data?.model != null && (
        <p className="mt-1 text-[10px] text-muted-foreground">
          Model: {String(event.event_data.model)}
        </p>
      )}

      {event.error_message && (
        <p className="mt-1 text-[10px] text-destructive">
          {event.error_message}
        </p>
      )}
    </div>
  );
}
