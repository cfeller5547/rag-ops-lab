import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { AppShell } from "@/components/layout/app-shell";
import ChatPage from "@/pages/chat";
import CorpusPage from "@/pages/corpus";
import EvaluationsPage from "@/pages/evaluations";
import TracesPage from "@/pages/traces";
import SettingsPage from "@/pages/settings";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10_000,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<ChatPage />} />
            <Route path="/corpus" element={<CorpusPage />} />
            <Route path="/evaluations" element={<EvaluationsPage />} />
            <Route path="/evals" element={<Navigate to="/evaluations" replace />} />
            <Route path="/traces" element={<TracesPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: "#0F0F10",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            color: "#EAEAEA",
          },
        }}
      />
    </QueryClientProvider>
  );
}

export default App;
