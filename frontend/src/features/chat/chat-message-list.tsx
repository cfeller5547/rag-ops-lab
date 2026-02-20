import { useEffect, useRef } from "react";
import type { ChatMessage as ChatMessageType } from "@/types/api";
import { ChatMessage } from "./chat-message";
import { EmptyState } from "@/components/shared/empty-state";
import { MessageSquare } from "lucide-react";

interface ChatMessageListProps {
  messages: ChatMessageType[];
  isStreaming: boolean;
}

export function ChatMessageList({
  messages,
  isStreaming,
}: ChatMessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <EmptyState
          icon={MessageSquare}
          title="Start a conversation"
          description="Ask questions about your uploaded documents. Responses include citations to source material."
        />
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto">
      {messages.map((msg, i) => (
        <ChatMessage
          key={i}
          message={msg}
          isStreaming={
            isStreaming && i === messages.length - 1 && msg.role === "assistant"
          }
        />
      ))}
    </div>
  );
}
