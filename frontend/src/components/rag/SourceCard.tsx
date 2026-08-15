"use client";

import { cn } from "../../lib/utils";
import { FileText, Copy, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import type { SourceReference } from "../../api/types";

interface SourceCardProps {
  source: SourceReference;
  onClick?: (source: SourceReference) => void;
  expanded?: boolean;
  onExpand?: (sourceId: string) => void;
  showActions?: boolean;
}

export function SourceCard({ source, onClick, expanded = false, onExpand, showActions = true }: SourceCardProps) {
  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
  };

  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-card overflow-hidden transition-all",
        expanded && "border-primary/50 shadow-lg"
      )}
      onClick={() => onClick?.(source)}
    >
      {/* Header */}
      <div className="p-3 border-b border-border bg-muted/30">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="p-2 rounded-lg bg-primary/10 text-primary flex-shrink-0">
              <FileText className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <h4 className="font-medium truncate">{source.document_title}</h4>
              <p className="text-xs text-muted-foreground truncate font-mono">{source.source_id}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {source.relevance_score && (
              <Badge variant="outline" className="gap-1">
                <FileText className="h-3 w-3" />
                {(source.relevance_score * 100).toFixed(1)}%
              </Badge>
            )}
            {showActions && (
              <Button variant="ghost" size="icon" onClick={(e) => { e.stopPropagation(); onExpand?.(source.source_id); }} className="h-7 w-7">
                {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Section */}
      {source.section_heading && (
        <div className="px-3 py-2 border-b border-border bg-muted/20">
          <p className="text-xs text-muted-foreground">Section</p>
          <p className="font-medium truncate">{source.section_heading}</p>
        </div>
      )}

      {/* Excerpt */}
      <div className="p-3">
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Excerpt</p>
          {showActions && (
            <Button variant="ghost" size="icon" onClick={(e) => { e.stopPropagation(); handleCopy(source.excerpt || ""); }} className="h-7 w-7">
              <Copy className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
        <div className="p-3 rounded-lg bg-muted/30 border border-border font-mono text-sm whitespace-pre-wrap max-h-40 overflow-y-auto">
          {source.excerpt || "No excerpt available"}
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="px-3 pb-3 border-t border-border bg-muted/20 animate-in slide-down">
          <details>
            <summary className="cursor-pointer text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
              Technical Details
            </summary>
            <div className="grid gap-2 sm:grid-cols-2 text-xs">
              <div><span className="text-muted-foreground">Source ID:</span> <code className="ml-2 font-mono text-foreground">{source.source_id}</code></div>
              <div><span className="text-muted-foreground">Relevance:</span> <code className="ml-2 font-mono text-foreground">{(source.relevance_score * 100).toFixed(2)}%</code></div>
              {source.document_title && <div><span className="text-muted-foreground">Document:</span> <code className="ml-2 font-mono text-foreground">{source.document_title}</code></div>}
              {source.section_heading && <div><span className="text-muted-foreground">Section:</span> <code className="ml-2 font-mono text-foreground">{source.section_heading}</code></div>}
            </div>
          </details>
        </div>
      )}
    </div>
  );
}

export default SourceCard;
