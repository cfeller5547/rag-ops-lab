import { Search, X } from "lucide-react";

interface TraceFiltersProps {
  sessionId: string;
  eventType: string;
  onSessionIdChange: (value: string) => void;
  onEventTypeChange: (value: string) => void;
  onClear: () => void;
}

const eventTypes = [
  { value: "all", label: "All Events" },
  { value: "retrieval", label: "Retrieval" },
  { value: "model_call", label: "Model Call" },
  { value: "tool_call", label: "Tool Call" },
  { value: "validation", label: "Validation" },
  { value: "error", label: "Error" },
];

export function TraceFilters({
  sessionId,
  eventType,
  onSessionIdChange,
  onEventTypeChange,
  onClear,
}: TraceFiltersProps) {
  return (
    <div className="flex items-center gap-3">
      <div className="relative flex-1 max-w-xs">
        <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
        <input
          value={sessionId}
          onChange={(e) => onSessionIdChange(e.target.value)}
          placeholder="Filter by session ID..."
          className="w-full rounded-lg border border-border bg-background py-2 pl-9 pr-3 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        />
      </div>
      <select
        value={eventType}
        onChange={(e) => onEventTypeChange(e.target.value)}
        className="rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
      >
        {eventTypes.map((et) => (
          <option key={et.value} value={et.value}>
            {et.label}
          </option>
        ))}
      </select>
      {(sessionId || eventType !== "all") && (
        <button
          onClick={onClear}
          className="flex items-center gap-1 rounded-lg border border-border px-3 py-2 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        >
          <X className="h-3 w-3" />
          Clear
        </button>
      )}
    </div>
  );
}
