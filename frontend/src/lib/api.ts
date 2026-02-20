import { API_BASE } from "./constants";
import type {
  ChatRequest,
  ChatResponse,
  DocumentListResponse,
  DocumentResponse,
  EvalDatasetInfo,
  EvalRunDetailResponse,
  EvalRunListResponse,
  EvalRunRequest,
  EvalRunResponse,
  HealthResponse,
  TraceDetailResponse,
  TraceEventResponse,
  TraceListResponse,
} from "@/types/api";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

// Documents API
export const documents = {
  list: (page = 1, pageSize = 100) =>
    apiFetch<DocumentListResponse>(
      `/api/documents?page=${page}&page_size=${pageSize}`
    ),

  upload: async (file: File): Promise<DocumentResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`${API_BASE}/api/documents`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Upload failed: ${response.status}`);
    }
    return response.json();
  },

  get: (id: number) => apiFetch<DocumentResponse>(`/api/documents/${id}`),

  delete: async (id: number): Promise<void> => {
    const response = await fetch(`${API_BASE}/api/documents/${id}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Delete failed: ${response.status}`);
    }
  },

  reprocess: (id: number) =>
    apiFetch<DocumentResponse>(`/api/documents/${id}/reprocess`, {
      method: "POST",
    }),
};

// Chat API
export const chat = {
  send: (request: ChatRequest) =>
    apiFetch<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify(request),
    }),

  stream: (request: ChatRequest, signal?: AbortSignal) =>
    fetch(`${API_BASE}/api/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal,
    }),

  history: (sessionId: string, limit = 50) =>
    apiFetch<{ session_id: string; messages: ChatResponse["message"][] }>(
      `/api/chat/history/${sessionId}?limit=${limit}`
    ),
};

// Evaluations API
export const evals = {
  list: (page = 1, pageSize = 50) =>
    apiFetch<EvalRunListResponse>(
      `/api/evals?page=${page}&page_size=${pageSize}`
    ),

  datasets: () => apiFetch<EvalDatasetInfo[]>("/api/evals/datasets"),

  create: (request: EvalRunRequest) =>
    apiFetch<EvalRunResponse>("/api/evals", {
      method: "POST",
      body: JSON.stringify(request),
    }),

  get: (evalId: string) =>
    apiFetch<EvalRunDetailResponse>(`/api/evals/${evalId}`),

  delete: async (evalId: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/api/evals/${evalId}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Delete failed: ${response.status}`);
    }
  },

  cancel: (evalId: string) =>
    apiFetch<EvalRunResponse>(`/api/evals/${evalId}/cancel`, {
      method: "POST",
    }),
};

// Traces API
export const traces = {
  list: (
    page = 1,
    pageSize = 50,
    sessionId?: string,
    eventType?: string
  ) => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (sessionId) params.set("session_id", sessionId);
    if (eventType && eventType !== "all")
      params.set("event_type", eventType);
    return apiFetch<TraceListResponse>(`/api/traces?${params}`);
  },

  get: (runId: string) =>
    apiFetch<TraceDetailResponse>(`/api/traces/${runId}`),

  events: (runId: string, eventType?: string) => {
    const params = eventType
      ? `?event_type=${eventType}`
      : "";
    return apiFetch<TraceEventResponse[]>(
      `/api/traces/${runId}/events${params}`
    );
  },

  delete: async (runId: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/api/traces/${runId}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `Delete failed: ${response.status}`);
    }
  },
};

// Health API
export const health = {
  check: () => apiFetch<HealthResponse>("/health"),
};
