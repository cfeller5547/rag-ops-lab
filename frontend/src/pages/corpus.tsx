import { UploadZone } from "@/features/corpus/upload-zone";
import { DocumentTable } from "@/features/corpus/document-table";
import { CorpusStats } from "@/features/corpus/corpus-stats";

export default function CorpusPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-foreground">
          Document Corpus
        </h2>
        <p className="text-sm text-muted-foreground">
          Upload and manage documents for RAG-powered retrieval.
        </p>
      </div>

      <CorpusStats />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <UploadZone />
        </div>
        <div className="lg:col-span-2">
          <DocumentTable />
        </div>
      </div>
    </div>
  );
}
