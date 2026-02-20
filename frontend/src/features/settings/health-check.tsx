import { useHealth } from "@/hooks/use-health";
import { CheckCircle, XCircle, RefreshCw } from "lucide-react";

export function HealthCheck() {
  const { data, isLoading, refetch } = useHealth();

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">System Health</h3>
        <button
          onClick={() => refetch()}
          disabled={isLoading}
          className="rounded p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {data ? (
        <div className="mt-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">API Server</span>
            <div className="flex items-center gap-1">
              {data.status === "healthy" ? (
                <CheckCircle className="h-3.5 w-3.5 text-ok" />
              ) : (
                <XCircle className="h-3.5 w-3.5 text-destructive" />
              )}
              <span className="text-xs text-foreground">{data.status}</span>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Database</span>
            <span className="text-xs text-foreground">{data.database}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Version</span>
            <span className="text-xs text-foreground">{data.version}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Reranking</span>
            <span className="text-xs text-foreground">
              {data.reranking_enabled ? "Enabled" : "Disabled"}
            </span>
          </div>
        </div>
      ) : (
        <div className="mt-3 space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-4 animate-pulse rounded bg-surface-2" />
          ))}
        </div>
      )}
    </div>
  );
}
