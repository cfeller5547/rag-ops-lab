import { useState } from "react";
import { Play } from "lucide-react";
import { useEvalDatasets, useCreateEvalRun } from "@/hooks/use-evals";
import { toast } from "sonner";

export function NewEvalForm() {
  const [name, setName] = useState("");
  const [dataset, setDataset] = useState("");
  const { data: datasets } = useEvalDatasets();
  const createRun = useCreateEvalRun();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !dataset) return;

    createRun.mutate(
      { name: name.trim(), dataset_name: dataset },
      {
        onSuccess: (run) => {
          toast.success(`Started evaluation "${run.name}"`);
          setName("");
        },
        onError: (err) => {
          toast.error(`Failed to start: ${err.message}`);
        },
      }
    );
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-border bg-card p-4">
      <h3 className="text-sm font-semibold text-foreground">
        New Evaluation
      </h3>
      <div>
        <label className="mb-1 block text-xs font-medium text-muted-foreground">
          Name
        </label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., baseline_v1"
          className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        />
      </div>
      <div>
        <label className="mb-1 block text-xs font-medium text-muted-foreground">
          Dataset
        </label>
        <select
          value={dataset}
          onChange={(e) => setDataset(e.target.value)}
          className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">Select a dataset...</option>
          {datasets?.map((ds) => (
            <option key={ds.name} value={ds.name}>
              {ds.name} ({ds.case_count} cases)
            </option>
          ))}
        </select>
      </div>
      <button
        type="submit"
        disabled={!name.trim() || !dataset || createRun.isPending}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
      >
        <Play className="h-4 w-4" />
        {createRun.isPending ? "Starting..." : "Start Evaluation"}
      </button>
    </form>
  );
}
