"use client";

import { useRef, useEffect } from "react";
import { UserMessage } from "./UserMessage";
import { AssistantMessage } from "./AssistantMessage";
import { ScrollArea } from "../../components/ui/ScrollArea";

interface ChatThreadProps {
  messages: Array<{
    id: string;
    role: "user" | "assistant";
    content: string;
    type?: string;
    metadata?: Record<string, unknown>;
    timestamp: Date;
  }>;
  onSubmitClarifications?: (answers: Array<{ question_id: string; answer_text: string; skipped: boolean }>) => void | Promise<void>;
  onOpenSRS?: () => void;
}

export function ChatThread({ messages, onSubmitClarifications, onOpenSRS }: ChatThreadProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="text-center text-muted-foreground">
          <p className="text-lg font-medium">Start a conversation</p>
          <p className="text-sm mt-1">Describe your cybersecurity project to begin</p>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1 min-h-0 pr-2">
      <div className="flex flex-col gap-4 pb-4" role="log" aria-live="polite" aria-label="Conversation">
        {messages.map((message) =>
          message.role === "user" ? (
            <UserMessage key={message.id} content={message.content} timestamp={message.timestamp} />
          ) : (
            <AssistantMessage
              key={message.id}
              content={message.content}
              type={message.type}
              metadata={message.metadata}
              timestamp={message.timestamp}
              onSubmitClarifications={onSubmitClarifications}
              onOpenSRS={onOpenSRS}
            />
          )
        )}
        <div ref={endRef} />
      </div>
    </ScrollArea>
  );
}
