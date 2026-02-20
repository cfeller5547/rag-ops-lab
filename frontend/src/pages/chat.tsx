import { useChat } from "@/hooks/use-chat";
import { ChatMessageList } from "@/features/chat/chat-message-list";
import { ChatInput } from "@/features/chat/chat-input";
import { CitationPanel } from "@/features/chat/citation-panel";

export default function ChatPage() {
  const {
    messages,
    citations,
    sessionId,
    isStreaming,
    error,
    sendMessage,
    stopStreaming,
    clearChat,
  } = useChat();

  return (
    <div className="mx-auto flex h-[calc(100vh-6rem)] max-w-6xl gap-4">
      {/* Main chat area */}
      <div className="flex flex-1 flex-col rounded-xl border border-border bg-card">
        <ChatMessageList messages={messages} isStreaming={isStreaming} />
        {error && (
          <div className="mx-4 mb-2 rounded-lg bg-destructive/10 px-3 py-2 text-xs text-destructive">
            {error}
          </div>
        )}
        <ChatInput
          onSend={sendMessage}
          onStop={stopStreaming}
          onClear={clearChat}
          isStreaming={isStreaming}
          sessionId={sessionId}
        />
      </div>

      {/* Citation sidebar */}
      <div className="hidden w-72 shrink-0 overflow-y-auto rounded-xl border border-border bg-card lg:block">
        <CitationPanel citations={citations} />
      </div>
    </div>
  );
}
