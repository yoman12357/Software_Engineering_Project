"use client";

import { cn } from "../../lib/utils";
import { FileText, ExternalLink } from "lucide-react";
import { Badge } from "../../components/ui/Badge";
import { Tooltip } from "../../components/ui/Tooltip";
import type { SourceReference } from "../../api/types";

interface SourceChipsProps {
  sources: SourceReference[];
  maxVisible?: number;
  onClick?: (source: SourceReference) => void;
  compact?: boolean;
}

export function SourceChips({ sources, maxVisible = 3, onClick, compact = false }: SourceChipsProps) {
  if (!sources.length) return null;

  const visibleSources = sources.slice(0, maxVisible);
  const remainingCount = sources.length - maxVisible;

  return (
    <div className={cn("flex flex-wrap gap-1.5", compact && "items-center")}>
      {visibleSources.map((source) => (
        <Tooltip key={source.source_id} content={source.document_title}>
          <Badge
            variant="outline"
            className={cn("gap-1 cursor-pointer hover:bg-primary/5 transition-colors", compact && "text-xs")}
            onClick={() => onClick?.(source)}
          >
            <FileText className="h-3 w-3" />
            <span className={cn("font-mono", compact && "text-xs")}>{source.source_id}</span>
            {source.section_heading && !compact && (
              <span className="text-xs text-muted-foreground">{source.section_heading}</span>
            )}
            {source.relevance_score && !compact && (
              <span className="text-xs text-muted-foreground">({(source.relevance_score * 100).toFixed(0)}%)</span>
            )}
          </Badge>
        </Tooltip>
      ))}
      {remainingCount > 0 && (
        <Badge variant="outline" className="gap-1 text-muted-foreground">
          <ExternalLink className="h-3 w-3" />
          +{remainingCount} more
        </Badge>
      )}
    </div>
  );
}

export default SourceChips;