import { ModelConfig, RetrievalConfig } from "@/features/settings/model-config";
import { HealthCheck } from "@/features/settings/health-check";
import { SystemStats } from "@/features/settings/system-stats";

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-foreground">Settings</h2>
        <p className="text-sm text-muted-foreground">
          View system configuration, health status, and usage statistics.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <ModelConfig />
          <RetrievalConfig />
        </div>
        <div className="space-y-6">
          <HealthCheck />
          <SystemStats />
        </div>
      </div>
    </div>
  );
}
