import { User, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/types/api";

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
}

export function ChatMessage({ message, isStreaming }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex gap-3 px-4 py-3",
        isUser ? "bg-transparent" : "bg-card/50"
      )}
    >
      <div
        className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg",
          isUser ? "bg-secondary" : "bg-primary/10"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-muted-foreground" />
        ) : (
          <Bot className="h-4 w-4 text-primary" />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <p className="mb-1 text-xs font-medium text-muted-foreground">
          {isUser ? "You" : "Assistant"}
        </p>
        <div
          className={cn(
            "prose prose-sm prose-invert max-w-none text-sm leading-relaxed text-foreground",
            isStreaming && "streaming-cursor"
          )}
        >
          {message.content || (isStreaming ? "" : "...")}
          {message.is_refusal && (
            <span className="mt-2 block text-xs text-warning">
              {message.refusal_reason || "Insufficient evidence to answer."}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
