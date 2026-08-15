"use client";

import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { X, FileText, ChevronLeft, ChevronRight, Copy, ChevronDown } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { ScrollArea } from "../../components/ui/ScrollArea";
import type { SourceReference } from "../../api/types";

interface SourceDrawerProps {
  open: boolean;
  onClose: () => void;
  sources: SourceReference[];
  selectedIndex?: number;
  onSelectIndex?: (index: number) => void;
  title?: string;
}

export function SourceDrawer({ open, onClose, sources, selectedIndex = 0, onSelectIndex, title = "Source Details" }: SourceDrawerProps) {
  const [currentIndex, setCurrentIndex] = useState(selectedIndex);

  useEffect(() => {
    setCurrentIndex(selectedIndex);
  }, [selectedIndex]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!open) return;
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowLeft" && currentIndex > 0) {
        setCurrentIndex(currentIndex - 1);
        onSelectIndex?.(currentIndex - 1);
      }
      if (e.key === "ArrowRight" && currentIndex < sources.length - 1) {
        setCurrentIndex(currentIndex + 1);
        onSelectIndex?.(currentIndex + 1);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, currentIndex, sources.length, onClose, onSelectIndex]);

  if (!open || sources.length === 0) return null;

  const source = sources[currentIndex];

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text);
  };

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="source-drawer-title">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in" aria-hidden="true" onClick={onClose} />
      <div className="relative z-50 w-full max-w-3xl max-h-[85vh] bg-card rounded-xl border border-border shadow-elevated animate-in slide-in-right overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 id="source-drawer-title" className="text-lg font-semibold">{title}</h2>
          <div className="flex items-center gap-2">
            {sources.length > 1 && (
              <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-muted">
                <Button variant="ghost" size="icon" onClick={() => { const next = currentIndex > 0 ? currentIndex - 1 : sources.length - 1; setCurrentIndex(next); onSelectIndex?.(next); }} disabled={sources.length <= 1} className="h-7 w-7">
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm font-mono text-muted-foreground">{currentIndex + 1} / {sources.length}</span>
                <Button variant="ghost" size="icon" onClick={() => { const next = currentIndex < sources.length - 1 ? currentIndex + 1 : 0; setCurrentIndex(next); onSelectIndex?.(next); }} disabled={sources.length <= 1} className="h-7 w-7">
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
            <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full p-4 space-y-6">
            {/* Source Metadata */}
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                <div className="p-2 rounded-lg bg-primary/10 text-primary">
                  <FileText className="h-5 w-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold truncate">{source.document_title}</h3>
                  <p className="text-sm text-muted-foreground truncate font-mono">{source.source_id}</p>
                </div>
                <Badge variant="outline" className="gap-1">
                  <FileText className="h-3 w-3" />
                  Relevance: {(source.relevance_score * 100).toFixed(1)}%
                </Badge>
              </div>

              {source.section_heading && (
                <div className="p-3 rounded-lg bg-muted/30 border border-border">
                  <p className="text-xs text-muted-foreground">Section</p>
                  <p className="font-medium">{source.section_heading}</p>
                </div>
              )}
            </div>

            {/* Source Content */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium">Excerpt</h3>
                <Button variant="ghost" size="sm" onClick={() => copyToClipboard(source.excerpt || "")}>
                  <Copy className="h-4 w-4 mr-1" />
                  Copy
                </Button>
              </div>
              <div className="p-4 rounded-lg bg-muted/30 border border-border font-mono text-sm whitespace-pre-wrap max-h-[50vh] overflow-y-auto">
                {source.excerpt || "No excerpt available"}
              </div>
            </div>

            {/* Technical Details */}
            <details className="border-t border-border pt-4">
              <summary className="cursor-pointer font-medium flex items-center gap-2 text-muted-foreground hover:text-foreground">
                <ChevronDown className="h-4 w-4" />
                Technical Details
              </summary>
              <div className="mt-4 space-y-3 text-sm">
                <div className="grid gap-2 sm:grid-cols-2">
                  <div><span className="text-muted-foreground">Source ID:</span> <code className="ml-2 font-mono text-foreground">{source.source_id}</code></div>
                  <div><span className="text-muted-foreground">Relevance Score:</span> <code className="ml-2 font-mono text-foreground">{(source.relevance_score * 100).toFixed(2)}%</code></div>
                  {source.document_title && (
                    <div><span className="text-muted-foreground">Document:</span> <code className="ml-2 font-mono text-foreground">{source.document_title}</code></div>
                  )}
                  {source.section_heading && (
                    <div><span className="text-muted-foreground">Section:</span> <code className="ml-2 font-mono text-foreground">{source.section_heading}</code></div>
                  )}
                </div>
              </div>
            </details>
          </ScrollArea>
        </div>
      </div>
    </div>,
    document.body
  );
}

export default SourceDrawer;
