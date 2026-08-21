"use client";

import { useRef, useEffect } from "react";
import { UserMessage } from "./UserMessage";
import { AssistantMessage } from "./AssistantMessage";
import type { ChatMessage } from "../../api/types";
import { SkeletonLoader } from "../../components/ui/Skeleton";

interface ChatThreadProps {
  messages: ChatMessage[];
  isLoading?: boolean;
  onSubmitClarifications?: (answers: Array<{ question_id: string; answer_text: string; skipped: boolean }>) => void | Promise<void>;
  onOpenSRS?: () => void;
  onRegenerateMessage?: (messageId: string) => void;
  onEditMessage?: (messageId: string) => void;
  onDeleteMessage?: (messageId: string) => void;
}

export function ChatThread({ messages, isLoading, onSubmitClarifications, onOpenSRS, onRegenerateMessage, onEditMessage, onDeleteMessage }: ChatThreadProps) {
  const endRef = useRef<HTMLDivElement>(null);
  const visibleMessages = messages.filter((message, index) => {
    const previous = messages[index - 1];
    return !(
      message.type === "error" &&
      previous?.type === "error" &&
      previous.content === message.content
    );
  });

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) return null;

  return (
    <div className="h-full min-h-0 flex-1 overflow-y-auto overscroll-contain">
      <div className="max-w-[768px] mx-auto py-6 px-4">
        <div className="space-y-6">
          {visibleMessages.map((message) => (
            <div key={message.id} className="group">
              {message.role === "user" ? (
                <UserMessage
                  content={message.content}
                  onEdit={onEditMessage ? () => onEditMessage(message.id) : undefined}
                  onDelete={onDeleteMessage ? () => onDeleteMessage(message.id) : undefined}
                />
              ) : (
                <AssistantMessage
                  content={message.content}
                  type={message.type}
                  metadata={message.metadata as Record<string, unknown> | undefined}
                  timestamp={message.timestamp}
                  onSubmitClarifications={onSubmitClarifications}
                  onOpenSRS={onOpenSRS}
                  onRegenerate={onRegenerateMessage ? () => onRegenerateMessage(message.id) : undefined}
                  onEdit={onEditMessage ? () => onEditMessage(message.id) : undefined}
                  onDelete={onDeleteMessage ? () => onDeleteMessage(message.id) : undefined}
                  messageId={message.id}
                />
              )}
            </div>
          ))}
        </div>
        {isLoading && <SkeletonLoader count={2} />}
        <div ref={endRef} />
      </div>
    </div>
  );
}

export default ChatThread;
