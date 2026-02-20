import { useState } from "react";
import { useTraces } from "@/hooks/use-traces";
import { TraceFilters } from "@/features/traces/trace-filters";
import { TraceListTable } from "@/features/traces/trace-list-table";
import { TraceDetailView } from "@/features/traces/trace-detail-view";

export default function TracesPage() {
  const [sessionId, setSessionId] = useState("");
  const [eventType, setEventType] = useState("all");
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);

  const { data, isLoading } = useTraces(
    1,
    50,
    sessionId || undefined,
    eventType !== "all" ? eventType : undefined
  );

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-foreground">Traces</h2>
        <p className="text-sm text-muted-foreground">
          Inspect detailed operation traces for every RAG interaction.
        </p>
      </div>

      <TraceFilters
        sessionId={sessionId}
        eventType={eventType}
        onSessionIdChange={setSessionId}
        onEventTypeChange={setEventType}
        onClear={() => {
          setSessionId("");
          setEventType("all");
        }}
      />

      <TraceListTable
        traces={data?.traces ?? []}
        isLoading={isLoading}
        onSelectTrace={setSelectedTraceId}
        selectedTraceId={selectedTraceId}
      />

      {selectedTraceId && <TraceDetailView runId={selectedTraceId} />}
    </div>
  );
}
