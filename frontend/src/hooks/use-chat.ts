import { useState, useCallback, useRef } from "react";
import { chat } from "@/lib/api";
import type { ChatMessage, Citation, StreamChunk } from "@/types/api";

interface ChatState {
  messages: ChatMessage[];
  citations: Citation[];
  sessionId: string | null;
  isStreaming: boolean;
  error: string | null;
}

export function useChat() {
  const [state, setState] = useState<ChatState>({
    messages: [],
    citations: [],
    sessionId: null,
    isStreaming: false,
    error: null,
  });
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || state.isStreaming) return;

      const userMessage: ChatMessage = {
        role: "user",
        content: text,
        citations: null,
        is_refusal: false,
        refusal_reason: null,
      };

      setState((s) => ({
        ...s,
        messages: [...s.messages, userMessage],
        citations: [],
        isStreaming: true,
        error: null,
      }));

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: "",
        citations: null,
        is_refusal: false,
        refusal_reason: null,
      };

      setState((s) => ({
        ...s,
        messages: [...s.messages, assistantMessage],
      }));

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const response = await chat.stream(
          {
            message: text,
            session_id: state.sessionId,
            include_sources: true,
            max_sources: 5,
          },
          controller.signal
        );

        if (!response.ok) {
          const err = await response
            .json()
            .catch(() => ({ detail: "Stream request failed" }));
          throw new Error(err.detail || `Error: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let buffer = "";
        const collectedCitations: Citation[] = [];

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue;

            try {
              const chunk: StreamChunk = JSON.parse(jsonStr);

              if (chunk.type === "content" && chunk.content) {
                setState((s) => {
                  const msgs = [...s.messages];
                  const last = msgs[msgs.length - 1];
                  if (last?.role === "assistant") {
                    msgs[msgs.length - 1] = {
                      ...last,
                      content: last.content + chunk.content,
                    };
                  }
                  return { ...s, messages: msgs };
                });
              } else if (chunk.type === "citation" && chunk.citation) {
                collectedCitations.push(chunk.citation);
                setState((s) => ({
                  ...s,
                  citations: [...collectedCitations],
                }));
              } else if (chunk.type === "done") {
                setState((s) => {
                  const msgs = [...s.messages];
                  const last = msgs[msgs.length - 1];
                  if (last?.role === "assistant") {
                    msgs[msgs.length - 1] = {
                      ...last,
                      citations: collectedCitations.length
                        ? collectedCitations
                        : null,
                    };
                  }
                  return {
                    ...s,
                    messages: msgs,
                    sessionId: chunk.session_id || s.sessionId,
                    isStreaming: false,
                  };
                });
              } else if (chunk.type === "error") {
                setState((s) => ({
                  ...s,
                  error: chunk.error || "Unknown error",
                  isStreaming: false,
                }));
              }
            } catch {
              // Skip malformed JSON lines
            }
          }
        }

        // If stream ends without a "done" chunk
        setState((s) => ({ ...s, isStreaming: false }));
      } catch (err) {
        if ((err as Error).name === "AbortError") {
          setState((s) => ({ ...s, isStreaming: false }));
        } else {
          setState((s) => ({
            ...s,
            error: (err as Error).message,
            isStreaming: false,
          }));
        }
      } finally {
        abortRef.current = null;
      }
    },
    [state.sessionId, state.isStreaming]
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const clearChat = useCallback(() => {
    abortRef.current?.abort();
    setState({
      messages: [],
      citations: [],
      sessionId: null,
      isStreaming: false,
      error: null,
    });
  }, []);

  return {
    messages: state.messages,
    citations: state.citations,
    sessionId: state.sessionId,
    isStreaming: state.isStreaming,
    error: state.error,
    sendMessage,
    stopStreaming,
    clearChat,
  };
}
