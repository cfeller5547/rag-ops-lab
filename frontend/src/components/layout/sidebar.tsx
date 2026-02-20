import { NavLink } from "react-router-dom";
import {
  MessageSquare,
  Database,
  FlaskConical,
  Activity,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/", icon: MessageSquare, label: "Chat" },
  { to: "/corpus", icon: Database, label: "Corpus" },
  { to: "/evaluations", icon: FlaskConical, label: "Evals" },
  { to: "/traces", icon: Activity, label: "Traces" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  return (
    <aside className="flex h-screen w-56 flex-col border-r border-border bg-card">
      <div className="flex items-center gap-2 px-4 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
          <span className="text-sm font-bold text-primary-foreground">R</span>
        </div>
        <div>
          <h1 className="text-sm font-semibold text-foreground">RAGOps Lab</h1>
          <p className="text-[10px] text-muted-foreground">
            Evaluation + Observability
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-2 py-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-primary" />
          <span className="text-xs text-muted-foreground">API Connected</span>
        </div>
      </div>
    </aside>
  );
}
