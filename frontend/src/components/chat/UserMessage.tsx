"use client";

import { cn } from "../../lib/utils";

interface UserMessageProps {
  content: string;
  timestamp: Date;
}

export function UserMessage({ content, timestamp }: UserMessageProps) {
  return (
    <div className={cn("flex justify-end animate-in slide-in-right")}>
      <div className="max-w-[80%] lg:max-w-[70%]">
        <div className="bg-primary text-primary-foreground rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
        </div>
        <div className="flex justify-end mt-1">
          <time className="text-xs text-muted-foreground">
            {new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </time>
        </div>
      </div>
    </div>
  );
}

export default UserMessage;