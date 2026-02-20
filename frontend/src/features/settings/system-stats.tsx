import { useHealth } from "@/hooks/use-health";
import { useDocuments } from "@/hooks/use-documents";
import { useEvalRuns } from "@/hooks/use-evals";
import { useTraces } from "@/hooks/use-traces";
import { MetricCard } from "@/components/shared/metric-card";
import { formatFileSize } from "@/lib/format";

export function SystemStats() {
  const { data: healthData } = useHealth();
  const { data: docsData } = useDocuments();
  const { data: evalsData } = useEvalRuns();
  const { data: tracesData } = useTraces();

  const docs = docsData?.documents ?? [];
  const totalSize = docs.reduce((sum, d) => sum + d.file_size, 0);

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-foreground">
        System Statistics
      </h3>
      <div className="grid grid-cols-2 gap-3">
        <MetricCard
          label="Documents"
          value={healthData?.total_documents ?? docs.length}
        />
        <MetricCard
          label="Chunks"
          value={healthData?.total_chunks ?? 0}
          accentColor="ok"
        />
        <MetricCard
          label="Storage"
          value={formatFileSize(totalSize)}
          accentColor="muted"
        />
        <MetricCard
          label="Eval Runs"
          value={evalsData?.total ?? 0}
          accentColor="muted"
        />
        <MetricCard
          label="Traces"
          value={tracesData?.total ?? 0}
          accentColor="muted"
        />
      </div>
    </div>
  );
}
