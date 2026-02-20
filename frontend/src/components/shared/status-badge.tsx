import { cn } from "@/lib/utils";

const statusConfig: Record<string, { className: string; label?: string }> = {
  completed: { className: "bg-ok/10 text-ok" },
  success: { className: "bg-ok/10 text-ok" },
  passed: { className: "bg-ok/10 text-ok" },
  healthy: { className: "bg-ok/10 text-ok" },
  failed: { className: "bg-destructive/10 text-destructive" },
  error: { className: "bg-destructive/10 text-destructive" },
  pending: { className: "bg-warning/10 text-warning" },
  running: { className: "bg-warning/10 text-warning" },
  processing: { className: "bg-warning/10 text-warning" },
  cancelled: { className: "bg-muted text-muted-foreground" },
};

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status.toLowerCase()] ?? {
    className: "bg-muted text-muted-foreground",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium capitalize",
        config.className,
        className
      )}
    >
      {config.label ?? status}
    </span>
  );
}
