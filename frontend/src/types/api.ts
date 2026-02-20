export interface Citation {
  document_id: number;
  document_name: string;
  chunk_id: number;
  chunk_index: number;
  content: string;
  page_number: number | null;
  relevance_score: number;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  citations: Citation[] | null;
  is_refusal: boolean;
  refusal_reason: string | null;
  timestamp?: string | null;
}

export interface ChatRequest {
  message: string;
  session_id?: string | null;
  include_sources?: boolean;
  max_sources?: number;
}

export interface ChatResponse {
  run_id: string;
  session_id: string;
  message: ChatMessage;
  latency_ms: number;
  tokens_used: number | null;
}

export interface StreamChunk {
  type: "content" | "citation" | "done" | "error";
  content?: string | null;
  citation?: Citation | null;
  error?: string | null;
  run_id?: string | null;
  session_id?: string | null;
}

export interface DocumentResponse {
  id: number;
  filename: string;
  original_filename: string;
  content_type: string;
  file_size: number;
  status: string;
  error_message: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: DocumentResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface DocumentChunkResponse {
  id: number;
  chunk_index: number;
  content: string;
  start_char: number;
  end_char: number;
  page_number: number | null;
}

export interface DocumentDetailResponse extends DocumentResponse {
  has_raw_text: boolean;
  has_file_bytes: boolean;
  chunks: DocumentChunkResponse[];
}

export interface EvalMetrics {
  groundedness_score: number;
  hallucination_rate: number;
  schema_compliance: number;
  tool_correctness: number;
  latency_p95_ms: number;
}

export interface EvalRunResponse {
  eval_id: string;
  name: string;
  description: string | null;
  dataset_name: string;
  total_cases: number;
  completed_cases: number;
  status: string;
  error_message: string | null;
  metrics: EvalMetrics | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface EvalResultResponse {
  case_id: string;
  question: string;
  expected_answer: string | null;
  actual_answer: string | null;
  citations: Record<string, unknown>[] | null;
  groundedness_score: number | null;
  hallucination_detected: boolean | null;
  schema_compliant: boolean | null;
  tool_calls_correct: boolean | null;
  latency_ms: number | null;
  status: string;
  error_message: string | null;
}

export interface EvalRunDetailResponse extends EvalRunResponse {
  results: EvalResultResponse[];
}

export interface EvalRunListResponse {
  eval_runs: EvalRunResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface EvalDatasetInfo {
  name: string;
  filename: string;
  description: string;
  case_count: number;
}

export interface EvalRunRequest {
  name: string;
  description?: string;
  dataset_name: string;
}

export interface TraceSummary {
  run_id: string;
  session_id: string | null;
  event_count: number;
  total_duration_ms: number;
  total_tokens: number;
  total_cost_usd: number;
  status: string;
  first_event_at: string | null;
  last_event_at: string | null;
}

export interface TraceListResponse {
  traces: TraceSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface TraceEventResponse {
  id: number;
  trace_id: string;
  run_id: string;
  session_id: string;
  event_type:
    | "retrieval"
    | "tool_call"
    | "model_call"
    | "validation"
    | "error";
  event_name: string;
  event_data: Record<string, unknown>;
  duration_ms: number | null;
  tokens_in: number | null;
  tokens_out: number | null;
  cost_usd: number | null;
  status: string;
  error_message: string | null;
  timestamp: string;
}

export interface TraceDetailResponse {
  run_id: string;
  session_id: string;
  events: TraceEventResponse[];
  summary: {
    total_events: number;
    total_duration_ms: number;
    total_tokens: number;
    total_cost_usd: number;
    event_type_counts: Record<string, number>;
    has_errors: boolean;
  };
}

export interface HealthResponse {
  status: string;
  version: string;
  database: string;
  total_documents: number;
  total_chunks: number;
  reranking_enabled: boolean;
}
