"use client";

import { useState, useRef, useEffect, FormEvent } from "react";
import { cn } from "../../lib/utils";
import { Send, X, Mic, Paperclip } from "lucide-react";

interface ComposerProps {
  disabled?: boolean;
  onSend: (content: string) => void | Promise<void>;
  placeholder?: string;
  value?: string;
  onValueChange?: (value: string) => void;
}

export function Composer({
  disabled = false,
  onSend,
  placeholder = "Describe your cybersecurity project...",
  value: controlledValue,
  onValueChange,
}: ComposerProps) {
  const [internalValue, setInternalValue] = useState("");
  const [height, setHeight] = useState(44);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isComposing, setIsComposing] = useState(false);
  const value = controlledValue ?? internalValue;
  const setValue = onValueChange ?? setInternalValue;

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const newHeight = Math.min(textareaRef.current.scrollHeight, 200);
      setHeight(newHeight);
    }
  }, [value]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    setValue("");
    setHeight(44);
    await onSend(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey && !isComposing) {
      e.preventDefault();
      const trimmed = value.trim();
      if (trimmed && !disabled) {
        setValue("");
        setHeight(44);
        onSend(trimmed);
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative">
        <div className="flex items-end gap-2 p-3 bg-card border border-border rounded-xl">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onCompositionStart={() => setIsComposing(true)}
            onCompositionEnd={() => setIsComposing(false)}
            placeholder={placeholder}
            disabled={disabled}
            className={cn(
              "w-full resize-none bg-transparent placeholder:text-muted-foreground",
              "text-sm leading-relaxed",
              "focus:outline-none",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "min-h-[44px] max-h-[200px]"
            )}
            style={{ height: height }}
            rows={1}
            aria-label="Message input"
          />
        </div>

        <div className="flex items-center justify-between px-3 pb-3">
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              disabled={disabled}
              aria-label="Attach file"
            >
              <Paperclip className="h-5 w-5" />
            </button>
            <button
              type="button"
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              disabled={disabled}
              aria-label="Voice input"
            >
              <Mic className="h-5 w-5" />
            </button>
          </div>

          <div className="flex items-center gap-2">
            {value.trim() && (
              <button
                type="button"
                onClick={() => setValue("")}
                className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                aria-label="Clear input"
              >
                <X className="h-5 w-5" />
              </button>
            )}
            <button
              type="submit"
              disabled={disabled || !value.trim()}
              className={cn(
                "p-2.5 rounded-lg transition-all duration-200",
                "bg-primary text-primary-foreground hover:bg-primary-hover",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                "focus-ring"
              )}
              aria-label="Send message"
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </form>
  );
}
