"use client";

import { cn } from "../../lib/utils";
import { FileText, ExternalLink } from "lucide-react";
import { Badge } from "../../components/ui/Badge";
import { Tooltip } from "../../components/ui/Tooltip";
import type { SourceReference } from "../../api/types";

interface SourceChipProps {
  source: SourceReference;
  onClick?: (source: SourceReference) => void;
  showScore?: boolean;
  compact?: boolean;
}

export function SourceChip({ source, onClick, showScore = true, compact = false }: SourceChipProps) {
  return (
    <Tooltip content={source.document_title}>
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
        {showScore && source.relevance_score && !compact && (
          <span className="text-xs text-muted-foreground">({(source.relevance_score * 100).toFixed(0)}%)</span>
        )}
      </Badge>
    </Tooltip>
  );
}

export function SourceChipGroup({ sources, maxVisible = 5, onClick, compact = false }: { sources: SourceReference[]; maxVisible?: number; onClick?: (source: SourceReference) => void; compact?: boolean }) {
  if (!sources.length) return null;

  const visibleSources = sources.slice(0, maxVisible);
  const remainingCount = sources.length - maxVisible;

  return (
    <div className="flex flex-wrap gap-1.5">
      {visibleSources.map((source) => (
        <SourceChip key={source.source_id} source={source} onClick={onClick} compact={compact} />
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

export default SourceChip;
