import { Outlet } from "react-router-dom";
import { Sidebar } from "./sidebar";
import { ExternalLink } from "lucide-react";

export function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-12 items-center justify-between border-b border-border bg-card/50 px-6">
          <div />
          <div className="flex items-center gap-4">
            <a
              href="/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
            >
              API Docs
              <ExternalLink className="h-3 w-3" />
            </a>
            <a
              href="/health"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
            >
              Health
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
