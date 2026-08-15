"use client";

import { Shield, FileText, Clock, Database, Globe, AlertTriangle, CheckCircle, AlertCircle, Info } from "lucide-react";
import { Badge } from "../../components/ui/Badge";
import type { SRSSchema } from "../../api/types";

interface SRSMetadataPanelProps {
  srs: SRSSchema;
}

export function SRSMetadataPanel({ srs }: SRSMetadataPanelProps) {
  const validation = srs.validation_report;

  return (
    <div className="p-4 rounded-xl border border-border bg-card">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Info className="h-5 w-5 text-primary" />
        Generation Metadata
      </h3>

      <div className="space-y-4">
        {/* Model Info */}
        <div className="p-3 rounded-lg bg-muted/50">
          <h4 className="font-medium mb-2 flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Model
          </h4>
          <div className="grid gap-2 sm:grid-cols-2 text-sm">
            <div><span className="text-muted-foreground">Name:</span> <span className="ml-2 font-mono">{srs.metadata.model_name}</span></div>
            <div><span className="text-muted-foreground">Adapter:</span> <span className="ml-2 font-mono">{srs.metadata.adapter_name || "None"}</span></div>
            <div><span className="text-muted-foreground">Provider:</span> <span className="ml-2 font-mono">{srs.generation_metadata?.provider || "Unknown"}</span></div>
            <div><span className="text-muted-foreground">KB Version:</span> <span className="ml-2 font-mono">{srs.generation_metadata?.kb_version || "Unknown"}</span></div>
          </div>
        </div>

        {/* RAG Info */}
        {srs.generation_metadata?.rag_enabled && (
          <div className="p-3 rounded-lg bg-muted/50">
            <h4 className="font-medium mb-2 flex items-center gap-2">
              <Database className="h-4 w-4" />
              Retrieval Augmented Generation
            </h4>
            <div className="grid gap-2 sm:grid-cols-3 text-sm">
              <div><span className="text-muted-foreground">Chunks Retrieved:</span> <span className="ml-2 font-mono">{srs.generation_metadata.retrieved_chunks}</span></div>
              <div><span className="text-muted-foreground">Retrieval Time:</span> <span className="ml-2 font-mono">{srs.generation_metadata.retrieval_time_ms}ms</span></div>
              <div><span className="text-muted-foreground">Generation Time:</span> <span className="ml-2 font-mono">{srs.generation_metadata.generation_time_ms}ms</span></div>
            </div>
            {srs.generation_metadata.retrieval_context && srs.generation_metadata.retrieval_context.length > 0 && (
              <details className="mt-3">
                <summary className="cursor-pointer text-sm text-primary hover:underline">View Retrieval Context</summary>
                <div className="mt-2 p-3 rounded bg-muted/30 font-mono text-xs max-h-40 overflow-y-auto">
                  {srs.generation_metadata.retrieval_context.map((ctx: string, i: number) => (
                    <div key={i} className="mb-2 p-2 bg-card rounded border border-border">{ctx}</div>
                  ))}
                </div>
              </details>
            )}
          </div>
        )}

        {/* Validation Report */}
        {validation && (
          <div className="p-3 rounded-lg bg-muted/50">
            <h4 className="font-medium mb-2 flex items-center gap-2">
              <CheckCircle className="h-4 w-4" />
              Validation Report
            </h4>
            <div className="flex items-center gap-4 mb-3">
              <Badge variant={validation.overall_score >= 80 ? "success" : validation.overall_score >= 60 ? "warning" : "destructive"} className="text-lg px-4 py-2">
                {validation.overall_score}%
              </Badge>
              <div className="text-sm text-muted-foreground">Overall Quality Score</div>
            </div>
            {validation.issues.length > 0 && (
              <div className="space-y-2">
                {validation.issues.map((issue) => (
                  <div key={issue.issue_id} className="p-3 rounded-lg bg-card border border-border">
                    <div className="flex items-start gap-2">
                      {issue.severity === "error" && <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0" />}
                      {issue.severity === "warning" && <AlertCircle className="h-4 w-4 text-warning flex-shrink-0" />}
                      {issue.severity === "info" && <Info className="h-4 w-4 text-primary flex-shrink-0" />}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono text-xs text-muted-foreground">{issue.issue_id}</span>
                          <Badge variant={issue.severity === "error" ? "destructive" : issue.severity === "warning" ? "warning" : "outline"} size="sm">
                            {issue.severity}
                          </Badge>
                          <span className="text-xs text-muted-foreground">{issue.section}</span>
                          {issue.requirement_id && (
                            <span className="font-mono text-xs text-primary">{issue.requirement_id}</span>
                          )}
                        </div>
                        <p className="text-sm">{issue.message}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Requirements Summary */}
        <div className="p-3 rounded-lg bg-muted/50">
          <h4 className="font-medium mb-2 flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Requirements Summary
          </h4>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-6 text-sm">
            {[
              { label: "Functional", count: srs.functional_requirements.length, color: "text-primary", icon: FileText },
              { label: "Security", count: srs.security_requirements.length, color: "text-foreground", icon: Shield },
              { label: "Non-Functional", count: srs.non_functional_requirements.length, color: "text-muted-foreground", icon: FileText },
              { label: "Data", count: srs.data_requirements.length, color: "text-primary", icon: Database },
              { label: "Network", count: srs.network_requirements.length, color: "text-foreground", icon: Globe },
              { label: "Threats", count: srs.threats.length, color: "text-muted-foreground", icon: AlertTriangle },
            ].map(({ label, count, color, icon: Icon }) => (
              <div key={label} className="flex items-center gap-2 p-2 rounded-lg bg-card border border-border">
                <Icon className={`h-4 w-4 ${color}`} />
                <div>
                  <div className={`font-bold ${color}`}>{count}</div>
                  <div className="text-xs text-muted-foreground">{label}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Timing */}
        {srs.generation_metadata && (
          <div className="p-3 rounded-lg bg-muted/50">
            <h4 className="font-medium mb-2 flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Timing
            </h4>
            <div className="grid gap-2 sm:grid-cols-3 text-sm">
              <div><span className="text-muted-foreground">Generation:</span> <span className="ml-2 font-mono">{Math.round((srs.generation_metadata.generation_time_ms || 0) / 1000)}s</span></div>
              <div><span className="text-muted-foreground">Retrieval:</span> <span className="ml-2 font-mono">{srs.generation_metadata.retrieval_time_ms}ms</span></div>
              <div><span className="text-muted-foreground">Total:</span> <span className="ml-2 font-mono">{Math.round(((srs.generation_metadata.generation_time_ms || 0) + srs.generation_metadata.retrieval_time_ms) / 1000)}s</span></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SRSMetadataPanel;
