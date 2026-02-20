import { useState } from "react";
import { MoreHorizontal, RefreshCw, Trash2 } from "lucide-react";
import { useDocuments, useDeleteDocument, useReprocessDocument } from "@/hooks/use-documents";
import { StatusBadge } from "@/components/shared/status-badge";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import { EmptyState } from "@/components/shared/empty-state";
import { formatFileSize, formatDateShort } from "@/lib/format";
import { toast } from "sonner";
import { Database } from "lucide-react";

export function DocumentTable() {
  const { data, isLoading } = useDocuments();
  const deleteDoc = useDeleteDocument();
  const reprocessDoc = useReprocessDocument();
  const { confirm, dialogProps } = useConfirmDialog();
  const [actionMenuId, setActionMenuId] = useState<number | null>(null);

  const docs = data?.documents ?? [];

  const handleDelete = async (id: number, name: string) => {
    const confirmed = await confirm({
      title: "Delete Document",
      description: `Are you sure you want to delete "${name}"? This will also delete all associated chunks and embeddings.`,
      confirmLabel: "Delete",
    });
    if (confirmed) {
      deleteDoc.mutate(id, {
        onSuccess: () => toast.success(`Deleted "${name}"`),
        onError: (err) => toast.error(`Delete failed: ${err.message}`),
      });
    }
  };

  const handleReprocess = (id: number, name: string) => {
    reprocessDoc.mutate(id, {
      onSuccess: () => toast.success(`Reprocessing "${name}"`),
      onError: (err) => toast.error(`Reprocess failed: ${err.message}`),
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className="h-12 animate-pulse rounded-lg bg-card"
          />
        ))}
      </div>
    );
  }

  if (docs.length === 0) {
    return (
      <EmptyState
        icon={Database}
        title="No documents yet"
        description="Upload a document to get started with RAG-powered chat."
      />
    );
  }

  return (
    <>
      <div className="overflow-hidden rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-surface-2">
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">
                Name
              </th>
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">
                Type
              </th>
              <th className="px-4 py-2.5 text-right text-xs font-medium text-muted-foreground">
                Size
              </th>
              <th className="px-4 py-2.5 text-right text-xs font-medium text-muted-foreground">
                Chunks
              </th>
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">
                Status
              </th>
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">
                Created
              </th>
              <th className="w-10 px-4 py-2.5" />
            </tr>
          </thead>
          <tbody>
            {docs.map((doc) => (
              <tr
                key={doc.id}
                className="border-b border-border transition-colors hover:bg-card/80"
              >
                <td className="px-4 py-2.5 font-medium text-foreground">
                  {doc.original_filename}
                </td>
                <td className="px-4 py-2.5 text-muted-foreground">
                  {doc.content_type.split("/")[1]?.toUpperCase() ?? doc.content_type}
                </td>
                <td className="px-4 py-2.5 text-right text-muted-foreground">
                  {formatFileSize(doc.file_size)}
                </td>
                <td className="px-4 py-2.5 text-right text-muted-foreground">
                  {doc.chunk_count}
                </td>
                <td className="px-4 py-2.5">
                  <StatusBadge status={doc.status} />
                </td>
                <td className="px-4 py-2.5 text-muted-foreground">
                  {formatDateShort(doc.created_at)}
                </td>
                <td className="px-4 py-2.5">
                  <div className="relative">
                    <button
                      onClick={() =>
                        setActionMenuId(
                          actionMenuId === doc.id ? null : doc.id
                        )
                      }
                      className="rounded p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                    >
                      <MoreHorizontal className="h-4 w-4" />
                    </button>
                    {actionMenuId === doc.id && (
                      <div className="absolute right-0 top-8 z-10 w-40 rounded-lg border border-border bg-card py-1 shadow-lg">
                        <button
                          onClick={() => {
                            setActionMenuId(null);
                            handleReprocess(doc.id, doc.original_filename);
                          }}
                          className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-foreground hover:bg-accent"
                        >
                          <RefreshCw className="h-3.5 w-3.5" />
                          Reprocess
                        </button>
                        <button
                          onClick={() => {
                            setActionMenuId(null);
                            handleDelete(doc.id, doc.original_filename);
                          }}
                          className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-destructive hover:bg-accent"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ConfirmDialog {...dialogProps} />
    </>
  );
}
