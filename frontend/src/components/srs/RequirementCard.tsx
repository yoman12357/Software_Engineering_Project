"use client";

import { useState } from "react";
import { FileText, Shield, Database, Globe, Edit, ExternalLink, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Badge, PriorityBadge, ConfidenceBadge } from "../../components/ui/Badge";
import { Tooltip } from "../../components/ui/Tooltip";
import type { Requirement, SourceReference } from "../../api/types";

interface RequirementCardProps {
  requirement: Requirement;
  onEdit?: (requirement: Requirement) => void;
  onViewSources?: (sources: SourceReference[]) => void;
  onCopy?: (requirement: Requirement) => void;
  compact?: boolean;
  showSources?: boolean;
}

const categoryIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  functional: FileText,
  security: Shield,
  non_functional: FileText,
  data: Database,
  network: Globe,
};

export function RequirementCard({
  requirement,
  onEdit,
  onViewSources,
  compact = false,
  showSources = true,
}: RequirementCardProps) {
  const [expanded, setExpanded] = useState(!compact);
  const CategoryIcon = categoryIcons[requirement.category] || FileText;

  if (compact) {
    return (
      <div className="p-3 rounded-lg border border-border bg-card hover:border-primary/50 transition-colors">
        <div className="flex items-start gap-3">
          <div className="p-1.5 rounded-lg bg-primary/10 text-primary flex-shrink-0">
            <CategoryIcon className="h-4 w-4" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-sm text-muted-foreground">{requirement.id}</span>
              <PriorityBadge priority={requirement.priority as "must" | "should" | "could"} />
              <ConfidenceBadge confidence={requirement.confidence as "high" | "medium" | "low"} />
              {requirement.user_confirmed && (
                <Badge variant="success" size="sm">Confirmed</Badge>
              )}
            </div>
            <h4 className="font-medium truncate">{requirement.title}</h4>
            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{requirement.statement}</p>
          </div>
          <div className="flex items-center gap-1">
            {onEdit && (
              <Button variant="ghost" size="icon" onClick={() => onEdit?.(requirement)} className="h-7 w-7">
                <Edit className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <article className="rounded-xl border border-border bg-card overflow-hidden animate-in slide-up" data-requirement-id={requirement.id}>
      {/* Header */}
      <div className="flex items-start gap-3 p-4 border-b border-border bg-muted/30">
        <div className="p-2 rounded-lg bg-primary/10 text-primary flex-shrink-0">
          <CategoryIcon className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <span className="font-mono text-sm text-muted-foreground">{requirement.id}</span>
            <PriorityBadge priority={requirement.priority as "must" | "should" | "could"} />
            <ConfidenceBadge confidence={requirement.confidence as "high" | "medium" | "low"} />
            {requirement.user_confirmed && (
              <Badge variant="success" size="sm">Confirmed</Badge>
            )}
          </div>
          <h3 className="font-semibold text-lg">{requirement.title}</h3>
        </div>
        <div className="flex items-center gap-1">
          {showSources && requirement.source_references.length > 0 && (
            <Tooltip content={`${requirement.source_references.length} source(s)`}>
              <Button variant="ghost" size="icon" onClick={() => onViewSources?.(requirement.source_references)} className="h-7 w-7">
                <ExternalLink className="h-3.5 w-3.5" />
              </Button>
            </Tooltip>
          )}
          {onEdit && (
            <Button variant="ghost" size="icon" onClick={() => onEdit?.(requirement)} className="h-7 w-7">
              <Edit className="h-3.5 w-3.5" />
            </Button>
          )}
          <Button variant="ghost" size="icon" onClick={() => setExpanded(!expanded)} className="h-7 w-7">
            {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </Button>
        </div>
      </div>

      {/* Content */}
      {expanded && (
        <div className="p-4 space-y-4 animate-in fade-in">
          {/* Statement */}
          <div>
            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-2">Statement</h4>
            <p className="text-foreground whitespace-pre-wrap">{requirement.statement}</p>
          </div>

          {/* Rationale */}
          <div>
            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-2">Rationale</h4>
            <p className="text-muted-foreground">{requirement.rationale}</p>
          </div>

          {/* Acceptance Criteria */}
          <div>
            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-2">Acceptance Criteria</h4>
            <div className="bg-muted/50 rounded-lg p-3">
              <p className="text-foreground whitespace-pre-wrap">{requirement.acceptance_criteria}</p>
            </div>
          </div>

          {/* Dependencies */}
          {requirement.dependencies.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-2">Dependencies</h4>
              <div className="flex flex-wrap gap-2">
                {requirement.dependencies.map((dep) => (
                  <Badge variant="outline" key={dep} className="font-mono text-xs">{dep}</Badge>
                ))}
              </div>
            </div>
          )}

          {/* Sources */}
          {showSources && requirement.source_references.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-2">Sources</h4>
              <div className="flex flex-wrap gap-2">
                {requirement.source_references.map((source) => (
                  <Tooltip key={source.source_id} content={source.document_title}>
                    <Badge variant="outline" className="gap-1 cursor-help">
                      <FileText className="h-3 w-3" />
                      {source.source_id}
                      {source.section_heading && (
                        <span className="text-xs text-muted-foreground">{source.section_heading}</span>
                      )}
                    </Badge>
                  </Tooltip>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </article>
  );
}

export default RequirementCard;
