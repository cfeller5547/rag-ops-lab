import { useState, useCallback } from "react";
import { Upload, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUploadDocument, useDocuments } from "@/hooks/use-documents";
import { toast } from "sonner";

export function UploadZone() {
  const [isDragOver, setIsDragOver] = useState(false);
  const upload = useUploadDocument();
  const { data: docData } = useDocuments();

  const handleFile = useCallback(
    (file: File) => {
      const allowed = [
        "application/pdf",
        "text/plain",
        "text/markdown",
      ];
      if (!allowed.includes(file.type) && !file.name.endsWith(".md")) {
        toast.error("Unsupported file type. Use PDF, TXT, or MD.");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        toast.error("File too large. Maximum size is 10MB.");
        return;
      }
      const existing = docData?.documents.find(
        (d) => d.original_filename === file.name
      );
      if (existing) {
        toast.warning(`"${file.name}" already exists in your corpus. Uploading a duplicate.`);
      }
      upload.mutate(file, {
        onSuccess: (doc) => {
          toast.success(`Uploaded "${doc.original_filename}" successfully`);
        },
        onError: (err) => {
          toast.error(`Upload failed: ${err.message}`);
        },
      });
    },
    [upload]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
      e.target.value = "";
    },
    [handleFile]
  );

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragOver(true);
      }}
      onDragLeave={() => setIsDragOver(false)}
      className={cn(
        "relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-colors",
        isDragOver
          ? "border-primary bg-primary/5"
          : "border-border hover:border-muted-foreground/30",
        upload.isPending && "pointer-events-none opacity-60"
      )}
    >
      {upload.isPending ? (
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      ) : (
        <Upload className="h-8 w-8 text-muted-foreground/50" />
      )}
      <p className="mt-3 text-sm font-medium text-foreground">
        {upload.isPending ? "Uploading..." : "Drop a file here"}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">
        PDF, TXT, or MD up to 10MB
      </p>
      <label className="mt-4 cursor-pointer rounded-lg bg-primary px-4 py-2 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90">
        Browse Files
        <input
          type="file"
          accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown"
          onChange={handleChange}
          className="hidden"
        />
      </label>
    </div>
  );
}
