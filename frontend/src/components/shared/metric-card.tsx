import { cn } from "@/lib/utils";

interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  className?: string;
  accentColor?: "primary" | "ok" | "warning" | "destructive" | "muted";
}

const accentColors = {
  primary: "text-primary",
  ok: "text-ok",
  warning: "text-warning",
  destructive: "text-destructive",
  muted: "text-muted-foreground",
};

export function MetricCard({
  label,
  value,
  subValue,
  className,
  accentColor = "primary",
}: MetricCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-card p-4",
        className
      )}
    >
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className={cn("mt-1 text-2xl font-bold", accentColors[accentColor])}>
        {value}
      </p>
      {subValue && (
        <p className="mt-0.5 text-xs text-muted-foreground">{subValue}</p>
      )}
    </div>
  );
}
