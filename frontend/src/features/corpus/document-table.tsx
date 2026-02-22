import { useState, useEffect, useRef, useCallback, useMemo } from "react";
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
  const [menuPos, setMenuPos] = useState<{ top: number; left: number } | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const buttonRefs = useRef<Record<number, HTMLButtonElement | null>>({});

  const closeMenu = useCallback(() => {
    setActionMenuId(null);
    setMenuPos(null);
  }, []);

  // Close menu on click outside or scroll
  useEffect(() => {
    if (actionMenuId === null) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(e.target as Node) &&
        !buttonRefs.current[actionMenuId]?.contains(e.target as Node)
      ) {
        closeMenu();
      }
    };
    const handleScroll = () => closeMenu();
    document.addEventListener("mousedown", handleClickOutside);
    window.addEventListener("scroll", handleScroll, true);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      window.removeEventListener("scroll", handleScroll, true);
    };
  }, [actionMenuId, closeMenu]);

  const toggleMenu = (docId: number) => {
    if (actionMenuId === docId) {
      closeMenu();
      return;
    }
    const btn = buttonRefs.current[docId];
    if (btn) {
      const rect = btn.getBoundingClientRect();
      setMenuPos({ top: rect.bottom + 4, left: rect.right - 160 });
    }
    setActionMenuId(docId);
  };

  const docs = data?.documents ?? [];

  const duplicateNames = useMemo(() => {
    const counts: Record<string, number> = {};
    docs.forEach((d) => {
      counts[d.original_filename] = (counts[d.original_filename] ?? 0) + 1;
    });
    return new Set(Object.keys(counts).filter((n) => counts[n] > 1));
  }, [docs]);

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
                  <div className="flex items-center gap-2">
                    {doc.original_filename}
                    {duplicateNames.has(doc.original_filename) && (
                      <span className="rounded border border-amber-500/20 bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium text-amber-500">
                        duplicate
                      </span>
                    )}
                  </div>
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
                  <button
                    ref={(el) => { buttonRefs.current[doc.id] = el; }}
                    onClick={() => toggleMenu(doc.id)}
                    className="rounded p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                  >
                    <MoreHorizontal className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {actionMenuId !== null && menuPos && (
        <div
          ref={menuRef}
          className="fixed z-50 w-40 rounded-lg border border-border bg-card py-1 shadow-lg"
          style={{ top: menuPos.top, left: menuPos.left }}
        >
          <button
            onClick={() => {
              const doc = docs.find((d) => d.id === actionMenuId);
              closeMenu();
              if (doc) handleReprocess(doc.id, doc.original_filename);
            }}
            className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-foreground hover:bg-accent"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Reprocess
          </button>
          <button
            onClick={() => {
              const doc = docs.find((d) => d.id === actionMenuId);
              closeMenu();
              if (doc) handleDelete(doc.id, doc.original_filename);
            }}
            className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-destructive hover:bg-accent"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Delete
          </button>
        </div>
      )}
      <ConfirmDialog {...dialogProps} />
    </>
  );
}
