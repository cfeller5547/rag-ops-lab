import { useState } from "react";
import { NewEvalForm } from "@/features/evals/new-eval-form";
import { EvalRunsTable } from "@/features/evals/eval-runs-table";
import { EvalDetailPanel } from "@/features/evals/eval-detail-panel";

export default function EvaluationsPage() {
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-foreground">Evaluations</h2>
        <p className="text-sm text-muted-foreground">
          Run and monitor RAG pipeline evaluation suites.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        <div className="lg:col-span-1">
          <NewEvalForm />
        </div>
        <div className="space-y-4 lg:col-span-3">
          <EvalRunsTable
            onSelectRun={setSelectedRunId}
            selectedRunId={selectedRunId}
          />
          {selectedRunId && <EvalDetailPanel evalId={selectedRunId} />}
        </div>
      </div>
    </div>
  );
}
