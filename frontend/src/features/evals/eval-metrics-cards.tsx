import type { EvalMetrics } from "@/types/api";
import { MetricCard } from "@/components/shared/metric-card";
import { formatScore, formatDuration } from "@/lib/format";

interface EvalMetricsCardsProps {
  metrics: EvalMetrics;
}

export function EvalMetricsCards({ metrics }: EvalMetricsCardsProps) {
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
      <MetricCard
        label="Groundedness"
        value={formatScore(metrics.groundedness_score)}
        accentColor={metrics.groundedness_score >= 0.7 ? "ok" : "warning"}
      />
      <MetricCard
        label="Hallucination"
        value={formatScore(metrics.hallucination_rate)}
        accentColor={metrics.hallucination_rate <= 0.1 ? "ok" : "destructive"}
      />
      <MetricCard
        label="Schema Compliance"
        value={formatScore(metrics.schema_compliance)}
        accentColor={metrics.schema_compliance >= 0.9 ? "ok" : "warning"}
      />
      <MetricCard
        label="Tool Correctness"
        value={formatScore(metrics.tool_correctness)}
        accentColor={metrics.tool_correctness >= 0.9 ? "ok" : "warning"}
      />
      <MetricCard
        label="Latency P95"
        value={formatDuration(metrics.latency_p95_ms)}
        accentColor={metrics.latency_p95_ms <= 3000 ? "ok" : "warning"}
      />
    </div>
  );
}
