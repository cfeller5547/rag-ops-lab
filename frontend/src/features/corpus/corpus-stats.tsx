import { useDocuments } from "@/hooks/use-documents";
import { MetricCard } from "@/components/shared/metric-card";
import { formatFileSize } from "@/lib/format";

export function CorpusStats() {
  const { data } = useDocuments();
  const docs = data?.documents ?? [];

  const totalDocs = docs.length;
  const completedDocs = docs.filter((d) => d.status === "completed").length;
  const failedDocs = docs.filter((d) => d.status === "failed").length;
  const totalChunks = docs.reduce((sum, d) => sum + d.chunk_count, 0);
  const totalSize = docs.reduce((sum, d) => sum + d.file_size, 0);

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <MetricCard
        label="Documents"
        value={totalDocs}
        subValue={`${completedDocs} indexed`}
      />
      <MetricCard
        label="Total Chunks"
        value={totalChunks}
        accentColor="ok"
      />
      <MetricCard
        label="Total Size"
        value={formatFileSize(totalSize)}
        accentColor="muted"
      />
      <MetricCard
        label="Failed"
        value={failedDocs}
        accentColor={failedDocs > 0 ? "destructive" : "muted"}
      />
    </div>
  );
}
