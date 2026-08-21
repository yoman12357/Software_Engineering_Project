"use client";

import { useState, useRef, useEffect, FormEvent } from "react";
import { cn } from "../../lib/utils";
import { ArrowUp, Paperclip, X } from "lucide-react";

interface ComposerProps {
  disabled?: boolean;
  onSend: (content: string) => void | Promise<void>;
  placeholder?: string;
  value?: string;
  onValueChange?: (value: string) => void;
  attachments?: File[];
  onFilesSelected?: (files: File[]) => void | Promise<void>;
  onRemoveAttachment?: (index: number) => void;
}

export function Composer({
  disabled = false,
  onSend,
  placeholder = "Message CyberSRS...",
  value: controlledValue,
  onValueChange,
  attachments = [],
  onFilesSelected,
  onRemoveAttachment,
}: ComposerProps) {
  const [internalValue, setInternalValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isComposing, setIsComposing] = useState(false);
  const value = controlledValue ?? internalValue;
  const setValue = onValueChange ?? setInternalValue;

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const newHeight = Math.min(textareaRef.current.scrollHeight, 200);
      textareaRef.current.style.height = `${newHeight}px`;
    }
  }, [value]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    setValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    await onSend(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey && !isComposing) {
      e.preventDefault();
      const trimmed = value.trim();
      if (trimmed && !disabled) {
        setValue("");
        if (textareaRef.current) textareaRef.current.style.height = "auto";
        onSend(trimmed);
      }
    }
  };

  return (
    <div className="w-full max-w-[768px] mx-auto px-4 pb-4">
      <form
        onSubmit={handleSubmit}
        className="relative"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          if (!disabled && event.dataTransfer.files.length) {
            void onFilesSelected?.(Array.from(event.dataTransfer.files));
          }
        }}
      >
        {attachments.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-2" aria-label="Pending attachments">
            {attachments.map((file, index) => (
              <span key={`${file.name}-${file.size}-${index}`} className="flex max-w-full items-center gap-2 rounded-lg border border-[#424242] bg-[#2f2f2f] px-3 py-2 text-xs text-white">
                <Paperclip className="h-3.5 w-3.5 shrink-0" />
                <span className="max-w-48 truncate">{file.name}</span>
                <button type="button" aria-label={`Remove ${file.name}`} onClick={() => onRemoveAttachment?.(index)} className="text-[#b4b4b4] hover:text-white">
                  <X className="h-3.5 w-3.5" />
                </button>
              </span>
            ))}
          </div>
        )}
        <div
          className={cn(
            "flex items-end rounded-2xl border transition-all duration-200",
            "bg-[#2f2f2f] border-[#424242]",
            "focus-within:border-[#676767]",
            disabled && "opacity-50 pointer-events-none"
          )}
        >
          {onFilesSelected && (
            <>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.md,.markdown,.txt,.csv"
                className="hidden"
                onChange={(event) => {
                  const files = Array.from(event.target.files ?? []);
                  if (files.length) void onFilesSelected(files);
                  event.target.value = "";
                }}
              />
              <button
                type="button"
                disabled={disabled}
                onClick={() => fileInputRef.current?.click()}
                aria-label="Attach project documents"
                title="Attach PDF, Markdown, text, or CSV"
                className="m-2 mr-0 rounded-full p-1.5 text-[#b4b4b4] hover:bg-[#424242] hover:text-white"
              >
                <Paperclip className="h-4 w-4" />
              </button>
            </>
          )}
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onCompositionStart={() => setIsComposing(true)}
            onCompositionEnd={() => setIsComposing(false)}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            aria-label="Message input"
            className={cn(
              "flex-1 bg-transparent text-[15px] text-white placeholder:text-[#8e8e8e]",
              "px-4 py-3 resize-none focus:outline-none",
              "min-h-[44px] max-h-[200px]"
            )}
          />
          <button
            type="submit"
            disabled={disabled || !value.trim()}
            aria-label="Send message"
            className={cn(
              "flex-shrink-0 m-2 p-1.5 rounded-full transition-colors",
              value.trim()
                ? "bg-white text-black hover:bg-gray-200"
                : "bg-[#616161] text-[#b4b4b4] cursor-not-allowed"
            )}
          >
            <ArrowUp className="h-4 w-4" />
          </button>
        </div>
      </form>
      <p className="text-center text-xs text-[#8e8e8e] mt-2">
        CyberSRS can make mistakes. Consider verifying important information.
      </p>
    </div>
  );
}

export default Composer;
