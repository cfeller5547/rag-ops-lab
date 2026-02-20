import { FileText, BookOpen } from "lucide-react";
import type { Citation } from "@/types/api";
import { truncate, formatScore } from "@/lib/format";

interface CitationPanelProps {
  citations: Citation[];
}

export function CitationPanel({ citations }: CitationPanelProps) {
  if (citations.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center px-4 py-12 text-center">
        <BookOpen className="h-8 w-8 text-muted-foreground/30" />
        <p className="mt-2 text-xs text-muted-foreground">
          Send a message to see sources
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3 p-4">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        Sources
      </h3>
      {citations.map((citation, i) => (
        <div
          key={`${citation.chunk_id}-${i}`}
          className="rounded-lg border border-border bg-surface-2 p-3"
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2">
              <FileText className="h-3.5 w-3.5 shrink-0 text-primary" />
              <span className="text-xs font-medium text-foreground">
                {citation.document_name}
              </span>
            </div>
            <span className="shrink-0 rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">
              {formatScore(citation.relevance_score)}
            </span>
          </div>
          {citation.page_number && (
            <p className="mt-1 text-[10px] text-muted-foreground">
              Page {citation.page_number}
            </p>
          )}
          <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
            {truncate(citation.content, 200)}
          </p>
        </div>
      ))}
    </div>
  );
}
