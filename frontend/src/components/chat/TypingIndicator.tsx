"use client";

import { cn } from "../../lib/utils";

interface TypingIndicatorProps {
  message?: string;
}

export function TypingIndicator({ message = "AI is thinking" }: TypingIndicatorProps) {
  return (
    <div className={cn("flex items-center gap-2 py-2", "animate-in fade-in")} role="status" aria-live="polite">
      <div className="flex gap-1">
        <span className="w-2 h-2 rounded-full bg-muted-foreground/50 animate-bounce" style={{ animationDelay: "0ms" }} />
        <span className="w-2 h-2 rounded-full bg-muted-foreground/50 animate-bounce" style={{ animationDelay: "150ms" }} />
        <span className="w-2 h-2 rounded-full bg-muted-foreground/50 animate-bounce" style={{ animationDelay: "300ms" }} />
      </div>
      <span className="text-sm text-muted-foreground">{message}</span>
    </div>
  );
}

export function TypingIndicatorDots({ className }: { className?: string }) {
  return (
    <div className={cn("flex gap-1", className)} role="status" aria-live="polite">
      <span className="w-2 h-2 rounded-full bg-muted-foreground/50 animate-bounce" style={{ animationDelay: "0ms" }} />
      <span className="w-2 h-2 rounded-full bg-muted-foreground/50 animate-bounce" style={{ animationDelay: "150ms" }} />
      <span className="w-2 h-2 rounded-full bg-muted-foreground/50 animate-bounce" style={{ animationDelay: "300ms" }} />
    </div>
  );
}

export default TypingIndicator;