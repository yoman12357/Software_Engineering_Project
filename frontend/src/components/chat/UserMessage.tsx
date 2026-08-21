"use client";

import { useState } from "react";
import { Copy, Check, User, Edit, Trash2 } from "lucide-react";

interface UserMessageProps {
  content: string;
  onEdit?: () => void;
  onDelete?: () => void;
}

export function UserMessage({ content, onEdit, onDelete }: UserMessageProps) {
  const [copied, setCopied] = useState(false);
  const [showActions, setShowActions] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex justify-end animate-in slide-in-right group" onMouseEnter={() => setShowActions(true)} onMouseLeave={() => setShowActions(false)}>
      <div className="max-w-[70%] flex items-start gap-3">
        <div className="flex flex-col items-end flex-1">
          <div className="bg-[#2f2f2f] text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm relative">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
            {showActions && (
              <div className="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={handleCopy}
                  className="p-1.5 rounded-md hover:bg-muted text-muted-foreground transition-colors"
                  title="Copy"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
                </button>
                {onEdit && (
                  <button
                    onClick={onEdit}
                    className="p-1.5 rounded-md hover:bg-muted text-muted-foreground transition-colors"
                    title="Edit"
                  >
                    <Edit className="h-3.5 w-3.5" />
                  </button>
                )}
                {onDelete && (
                  <button
                    onClick={onDelete}
                    className="p-1.5 rounded-md hover:bg-muted text-muted-foreground transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-[#5436da] flex items-center justify-center mt-0.5">
          <User className="h-4 w-4 text-white" />
        </div>
      </div>
    </div>
  );
}

export default UserMessage;
