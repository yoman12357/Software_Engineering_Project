"use client";

import { cn } from "../../lib/utils";
import { FileText, Shield, Download, Edit, ExternalLink, ChevronDown, Info, CheckCircle } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuLabel } from "../../components/ui/DropdownMenu";
import type { SRSSchema } from "../../api/types";

interface SRSHeaderProps {
  srs: SRSSchema;
  versionId: string;
  onEdit?: () => void;
  onExport?: (format: "pdf" | "json" | "markdown") => void;
  onViewFull?: () => void;
}

export function SRSHeader({ srs, onEdit, onExport, onViewFull }: SRSHeaderProps) {
  const stats = [
    { label: "Functional", count: srs.functional_requirements?.length || 0, color: "text-primary" },
    { label: "Security", count: srs.security_requirements?.length || 0, color: "text-foreground" },
    { label: "Non-Functional", count: srs.non_functional_requirements?.length || 0, color: "text-muted-foreground" },
    { label: "Data", count: srs.data_requirements?.length || 0, color: "text-primary" },
    { label: "Network", count: srs.network_requirements?.length || 0, color: "text-foreground" },
    { label: "Threats", count: srs.threats?.length || 0, color: "text-muted-foreground" },
  ];

  return (
    <div className="space-y-4">
      {/* Title and metadata */}
      <div className="flex items-start justify-between gap-4 p-4 rounded-xl bg-card border border-border">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-primary/10 text-primary">
            <FileText className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">{srs.metadata.project_name}</h1>
            <p className="text-sm text-muted-foreground">
              Version {srs.metadata.version} • {new Date(srs.metadata.generated_at).toLocaleString()}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger className="h-8 border border-border bg-transparent px-3 text-sm hover:bg-muted">
              <Download className="h-4 w-4 mr-2" />
              Export
              <ChevronDown className="h-4 w-4 ml-1" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Export SRS</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => onExport?.("pdf")} disabled>
                <FileText className="h-4 w-4 mr-2" />
                PDF <span className="ml-auto text-xs text-muted-foreground">Coming soon</span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onExport?.("json")}>
                <FileText className="h-4 w-4 mr-2" />
                JSON
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onExport?.("markdown")}>
                <FileText className="h-4 w-4 mr-2" />
                Markdown
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {onEdit && (
            <Button variant="ghost" size="sm" onClick={onEdit}>
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </Button>
          )}

          {onViewFull && (
            <Button variant="ghost" size="sm" onClick={onViewFull}>
              <ExternalLink className="h-4 w-4 mr-2" />
              View Full
            </Button>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {stats.map((stat) => (
          <div key={stat.label} className="p-3 rounded-lg bg-card border border-border text-center">
            <div className={cn("text-2xl font-bold", stat.color)}>{stat.count}</div>
            <div className="text-xs text-muted-foreground mt-0.5">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Metadata badges */}
      <div className="flex flex-wrap items-center gap-2 p-3 rounded-lg bg-muted/50">
        <Badge variant="outline" className="gap-1">
          <Info className="h-3 w-3" />
          Model: {srs.metadata.model_name}
        </Badge>
        <Badge variant="outline" className="gap-1">
          <Shield className="h-3 w-3" />
          RAG: {srs.generation_metadata?.rag_enabled ? "Enabled" : "Disabled"}
        </Badge>
        {srs.generation_metadata?.rag_enabled && (
          <Badge variant="outline" className="gap-1">
            <FileText className="h-3 w-3" />
            {srs.generation_metadata.retrieved_chunks} chunks
          </Badge>
        )}
        <Badge variant="outline" className="gap-1">
          <Shield className="h-3 w-3" />
          Gen: {Math.round((srs.generation_metadata?.generation_time_ms || 0) / 1000)}s
        </Badge>
        {srs.validation_report && (
          <Badge variant={srs.validation_report.overall_score >= 80 ? "success" : srs.validation_report.overall_score >= 60 ? "warning" : "destructive"} className="gap-1">
            <CheckCircle className="h-3 w-3" />
            Quality: {srs.validation_report.overall_score}%
          </Badge>
        )}
      </div>
    </div>
  );
}

export default SRSHeader;
