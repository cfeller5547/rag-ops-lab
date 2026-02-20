import { useState, useMemo } from "react";
import { useTraces } from "@/hooks/use-traces";
import { TraceFilters } from "@/features/traces/trace-filters";
import { TraceListTable } from "@/features/traces/trace-list-table";
import { TraceDetailView } from "@/features/traces/trace-detail-view";

export default function TracesPage() {
  const [sessionFilter, setSessionFilter] = useState("");
  const [eventType, setEventType] = useState("all");
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);

  const { data, isLoading } = useTraces(
    1,
    50,
    undefined,
    eventType !== "all" ? eventType : undefined
  );

  // Client-side session filtering so truncated IDs (shown in table) work
  const filteredTraces = useMemo(() => {
    const traces = data?.traces ?? [];
    if (!sessionFilter) return traces;
    const filter = sessionFilter.toLowerCase();
    return traces.filter(
      (t) =>
        t.session_id?.toLowerCase().includes(filter) ||
        t.run_id.toLowerCase().includes(filter)
    );
  }, [data?.traces, sessionFilter]);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-foreground">Traces</h2>
        <p className="text-sm text-muted-foreground">
          Inspect detailed operation traces for every RAG interaction.
        </p>
      </div>

      <TraceFilters
        sessionId={sessionFilter}
        eventType={eventType}
        onSessionIdChange={(v) => {
          setSessionFilter(v);
          setSelectedTraceId(null);
        }}
        onEventTypeChange={(v) => {
          setEventType(v);
          setSelectedTraceId(null);
        }}
        onClear={() => {
          setSessionFilter("");
          setEventType("all");
          setSelectedTraceId(null);
        }}
      />

      <TraceListTable
        traces={filteredTraces}
        isLoading={isLoading}
        onSelectTrace={setSelectedTraceId}
        selectedTraceId={selectedTraceId}
      />

      {selectedTraceId && <TraceDetailView runId={selectedTraceId} />}
    </div>
  );
}
