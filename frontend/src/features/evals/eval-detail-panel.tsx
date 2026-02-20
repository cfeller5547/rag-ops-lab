import { useEvalDetail } from "@/hooks/use-evals";
import { EvalMetricsCards } from "./eval-metrics-cards";
import { StatusBadge } from "@/components/shared/status-badge";
import { formatDateShort, truncate, formatScore, formatDuration } from "@/lib/format";

interface EvalDetailPanelProps {
  evalId: string;
}

export function EvalDetailPanel({ evalId }: EvalDetailPanelProps) {
  const { data: detail, isLoading } = useEvalDetail(evalId);

  if (isLoading) {
    return (
      <div className="space-y-4 rounded-xl border border-border bg-card p-4">
        <div className="h-6 w-48 animate-pulse rounded bg-surface-2" />
        <div className="grid grid-cols-5 gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-xl bg-surface-2" />
          ))}
        </div>
      </div>
    );
  }

  if (!detail) return null;

  return (
    <div className="space-y-4 rounded-xl border border-border bg-card p-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-foreground">
            {detail.name}
          </h3>
          <p className="text-xs text-muted-foreground">
            {detail.dataset_name} &middot; {detail.completed_cases}/{detail.total_cases} cases
            {detail.completed_at && ` &middot; ${formatDateShort(detail.completed_at)}`}
          </p>
        </div>
        <StatusBadge status={detail.status} />
      </div>

      {detail.metrics && <EvalMetricsCards metrics={detail.metrics} />}

      {detail.results && detail.results.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Results ({detail.results.length} cases)
          </h4>
          <div className="overflow-hidden rounded-lg border border-border">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border bg-surface-2">
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">Case</th>
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">Question</th>
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">Status</th>
                  <th className="px-3 py-2 text-right font-medium text-muted-foreground">Grounded</th>
                  <th className="px-3 py-2 text-right font-medium text-muted-foreground">Latency</th>
                </tr>
              </thead>
              <tbody>
                {detail.results.map((r) => (
                  <tr key={r.case_id} className="border-b border-border">
                    <td className="px-3 py-2 font-mono text-muted-foreground">{r.case_id}</td>
                    <td className="max-w-xs px-3 py-2 text-foreground">
                      {truncate(r.question, 60)}
                    </td>
                    <td className="px-3 py-2">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="px-3 py-2 text-right text-muted-foreground">
                      {formatScore(r.groundedness_score)}
                    </td>
                    <td className="px-3 py-2 text-right text-muted-foreground">
                      {formatDuration(r.latency_ms)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
