"use client";

import { Download, FileText } from "lucide-react";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator } from "../../components/ui/DropdownMenu";
import { useToast } from "../../components/ui/Toast";
import type { Requirement, SRSSchema, Threat } from "../../api/types";

interface SRSExportActionsProps {
  srs: SRSSchema;
  versionId: string;
  onExport?: (format: "pdf" | "json" | "markdown") => void;
  disabled?: boolean;
}

export function SRSExportActions({ srs, onExport, disabled = false }: SRSExportActionsProps) {
  const { toast } = useToast();

  const handleExport = async (format: "pdf" | "json" | "markdown") => {
    try {
      if (format === "pdf") {
        toast({
          type: "warning",
          title: "PDF Export Unavailable",
          message: "PDF export is not yet implemented. Please use JSON or Markdown export.",
        });
        return;
      }

      let content: string;
      let filename: string;
      let mimeType: string;

      if (format === "json") {
        content = JSON.stringify(srs, null, 2);
        filename = `${srs.metadata.project_name.replace(/\s+/g, "_")}_v${srs.metadata.version}.json`;
        mimeType = "application/json";
      } else {
        content = generateMarkdown(srs);
        filename = `${srs.metadata.project_name.replace(/\s+/g, "_")}_v${srs.metadata.version}.md`;
        mimeType = "text/markdown";
      }

      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        type: "success",
        title: "Export Successful",
        message: `${format.toUpperCase()} file downloaded`,
      });

      onExport?.(format);
    } catch (err) {
      toast({
        type: "error",
        title: "Export Failed",
        message: err instanceof Error ? err.message : "Failed to export file",
      });
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="h-8 border border-border bg-transparent px-3 text-sm hover:bg-muted"
        disabled={disabled}
      >
        <Download className="h-4 w-4 mr-2" />
        Export
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>Export SRS</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => handleExport("json")} disabled={disabled}>
          <FileText className="h-4 w-4 mr-2" />
          JSON
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleExport("markdown")} disabled={disabled}>
          <FileText className="h-4 w-4 mr-2" />
          Markdown
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => handleExport("pdf")} disabled={true}>
          <FileText className="h-4 w-4 mr-2" />
          PDF <span className="ml-auto text-xs text-muted-foreground">Coming soon</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function generateMarkdown(srs: SRSSchema): string {
  const lines: string[] = [];
  lines.push(`# ${srs.metadata.project_name}`);
  lines.push("");
  lines.push(`**Version:** ${srs.metadata.version}`);
  lines.push(`**Generated:** ${new Date(srs.metadata.generated_at).toLocaleString()}`);
  lines.push(`**Model:** ${srs.metadata.model_name}`);
  lines.push("");

  lines.push("## Project Overview");
  lines.push("");
  lines.push(`**Description:** ${srs.project_overview.description}`);
  lines.push(`**Purpose:** ${srs.project_overview.purpose}`);
  lines.push(`**Context:** ${srs.project_overview.context}`);
  lines.push("");

  lines.push("## Scope");
  lines.push("");
  lines.push("### In Scope");
  srs.scope.in_scope.forEach((item: string) => lines.push(`- ${item}`));
  lines.push("");
  lines.push("### Out of Scope");
  srs.scope.out_of_scope.forEach((item: string) => lines.push(`- ${item}`));
  lines.push("");

  const addRequirements = (title: string, reqs: Requirement[]) => {
    if (reqs.length === 0) return;
    lines.push(`## ${title}`);
    lines.push("");
    reqs.forEach((req) => {
      lines.push(`### ${req.id}: ${req.title}`);
      lines.push(`**Priority:** ${req.priority} | **Confidence:** ${req.confidence}`);
      lines.push("");
      lines.push(`**Statement:** ${req.statement}`);
      lines.push(`**Rationale:** ${req.rationale}`);
      lines.push(`**Acceptance Criteria:** ${req.acceptance_criteria}`);
      if (req.dependencies.length > 0) {
        lines.push(`**Dependencies:** ${req.dependencies.join(", ")}`);
      }
      lines.push("");
    });
  };

  addRequirements("Functional Requirements", srs.functional_requirements);
  addRequirements("Non-Functional Requirements", srs.non_functional_requirements);
  addRequirements("Security Requirements", srs.security_requirements);
  addRequirements("Data Requirements", srs.data_requirements);
  addRequirements("Network Requirements", srs.network_requirements);

  if (srs.threats.length > 0) {
    lines.push("## Threats");
    lines.push("");
    srs.threats.forEach((threat: Threat) => {
      lines.push(`### ${threat.threat_id}: ${threat.name}`);
      lines.push(`**Severity:** ${threat.severity}`);
      lines.push(`**Description:** ${threat.description}`);
      if (threat.affected_assets.length > 0) {
        lines.push(`**Affected Assets:** ${threat.affected_assets.join(", ")}`);
      }
      lines.push("");
    });
  }

  return lines.join("\n");
}

export default SRSExportActions;
