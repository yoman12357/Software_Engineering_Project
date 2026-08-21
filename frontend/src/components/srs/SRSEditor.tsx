"use client";

import { useEffect, useState } from "react";
import { ArrowLeft, CheckCircle2, FileText, Save, XCircle } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Textarea } from "../../components/ui/Textarea";
import { Badge } from "../../components/ui/Badge";
import { ScrollArea } from "../../components/ui/ScrollArea";
import { api } from "../../api/client";
import type {
  Requirement,
  SRSEditRequest,
  SRSVersionRead,
  ValidationIssue,
} from "../../api/types";

interface SRSEditorProps {
  projectId: string;
  versionId: string;
  srs: SRSVersionRead["srs"];
  onBack: () => void;
  onSaved?: (version: SRSVersionRead) => void;
}

interface EditDraft {
  section: string;
  requirementId: string;
  field: string;
  value: string;
}

const EDITABLE_SECTIONS: { key: string; label: string; plural: string }[] = [
  { key: "functional", label: "Functional", plural: "functional_requirements" },
  { key: "security", label: "Security", plural: "security_requirements" },
  { key: "non-functional", label: "Non-Functional", plural: "non_functional_requirements" },
  { key: "data", label: "Data", plural: "data_requirements" },
  { key: "network", label: "Network", plural: "network_requirements" },
];

const EDITABLE_FIELDS: { key: string; label: string }[] = [
  { key: "statement", label: "Statement" },
  { key: "title", label: "Title" },
  { key: "rationale", label: "Rationale" },
  { key: "acceptance_criteria", label: "Acceptance Criteria" },
];

export function SRSEditor({ projectId, versionId, srs, onBack, onSaved }: SRSEditorProps) {
  const [drafts, setDrafts] = useState<Record<string, EditDraft>>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveResult, setSaveResult] = useState<SRSVersionRead | null>(null);
  const [issues, setIssues] = useState<ValidationIssue[]>([]);
  const [activeSection, setActiveSection] = useState("functional");

  useEffect(() => {
    // Load issues from the SRS validation_report if present
    const report = (srs as unknown as { validation_report?: { issues?: ValidationIssue[] } | null })
      ?.validation_report;
    if (report?.issues) {
      setIssues(report.issues);
    }
  }, [srs]);

  const getRequirements = (section: string): Requirement[] => {
    if (!srs) return [];
    switch (section) {
      case "functional":
        return srs.functional_requirements || [];
      case "security":
        return srs.security_requirements || [];
      case "non-functional":
        return srs.non_functional_requirements || [];
      case "data":
        return srs.data_requirements || [];
      case "network":
        return srs.network_requirements || [];
      default:
        return [];
    }
  };

  const requirements = getRequirements(activeSection);

  const draftKey = (section: string, reqId: string, field: string) =>
    `${section}:${reqId}:${field}`;

  const updateDraft = (section: string, reqId: string, field: string, value: string) => {
    const key = draftKey(section, reqId, field);
    setDrafts((current) => ({
      ...current,
      [key]: { section, requirementId: reqId, field, value },
    }));
  };

  const draftCount = Object.keys(drafts).length;

  const handleSave = async () => {
    if (draftCount === 0 || !srs) return;
    setSaving(true);
    setSaveError(null);
    setSaveResult(null);

    const updates = Object.values(drafts).map((d) => ({
      section: d.section,
      requirement_id: d.requirementId,
      field: d.field,
      new_value: d.value,
    }));

    const payload: SRSEditRequest = { updates };

    try {
      let updated = await api.editSrsVersion(projectId, versionId, payload);
      try {
        const validation = await api.validateSrsVersion(projectId, versionId);
        setIssues(validation.issues);
        updated = await api.getSrsVersion(projectId, versionId);
      } catch {
        // The edit is already safely persisted; validation can be retried in the workspace.
      }
      setSaveResult(updated);
      onSaved?.(updated);
      setDrafts({});
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save edits");
    } finally {
      setSaving(false);
    }
  };

  if (saveResult) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <div className="max-w-md w-full text-center">
          <div className="mx-auto mb-4 h-14 w-14 rounded-full bg-success/10 text-success flex items-center justify-center">
            <CheckCircle2 className="h-7 w-7" />
          </div>
          <h2 className="text-xl font-semibold mb-2">Edits Applied</h2>
          <p className="text-muted-foreground mb-6">
            Your changes have been saved. The SRS version {saveResult.version_number} is now in{" "}
            <span className="font-medium">draft</span> status and pending re-validation.
          </p>
          <div className="flex justify-center gap-3">
            <Button onClick={onBack}>
              <FileText className="h-4 w-4 mr-2" />
              Back to SRS
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-3 mb-4 p-4 bg-card border border-border rounded-xl">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div className="flex-1">
          <h1 className="text-lg font-semibold">Edit SRS</h1>
          <p className="text-xs text-muted-foreground">
            {srs?.metadata.project_name} v{srs?.metadata.version} • Select requirements to edit
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={draftCount > 0 ? "default" : "secondary"}>
            {draftCount} pending change{draftCount === 1 ? "" : "s"}
          </Badge>
          <Button onClick={handleSave} disabled={draftCount === 0 || saving} loading={saving}>
            <Save className="h-4 w-4 mr-2" />
            Save Changes
          </Button>
        </div>
      </div>

      {saveError && (
        <div className="mb-4 p-3 rounded-lg border border-destructive/20 bg-destructive/10 text-destructive flex items-center gap-2" role="alert">
          <XCircle className="h-4 w-4 flex-shrink-0" />
          {saveError}
        </div>
      )}

      <div className="flex-1 flex gap-4 min-h-0">
        {/* Section navigation */}
        <div className="w-52 flex-shrink-0">
          <ScrollArea className="h-full rounded-xl border border-border bg-card">
            <div className="p-2 space-y-1">
              {EDITABLE_SECTIONS.map((section) => {
                const reqs = getRequirements(section.key);
                const hasDrafts = Object.values(drafts).some((d) => d.section === section.key);
                return (
                  <button
                    key={section.key}
                    onClick={() => setActiveSection(section.key)}
                    className={cn(
                      "w-full text-left px-3 py-2 rounded-lg text-sm transition-colors",
                      activeSection === section.key
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-muted"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span>{section.label}</span>
                      <span className="text-xs opacity-70">{reqs.length}</span>
                    </div>
                    {hasDrafts && (
                      <div className="flex items-center gap-1 mt-1">
                        <span className="h-1.5 w-1.5 rounded-full bg-warning" />
                        <span className="text-xs opacity-70">has edits</span>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </ScrollArea>
        </div>

        {/* Requirements */}
        <ScrollArea className="flex-1">
          <div className="space-y-4 pr-1">
            {requirements.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                <p>No requirements in this section.</p>
              </div>
            ) : (
              requirements.map((req) => (
                <RequirementEditorCard
                  key={req.id}
                  requirement={req}
                  section={activeSection}
                  drafts={drafts}
                  draftKey={draftKey}
                  onUpdate={updateDraft}
                />
              ))
            )}
          </div>
        </ScrollArea>

        {/* Validation issues sidebar */}
        <div className="w-64 flex-shrink-0">
          <ScrollArea className="h-full rounded-xl border border-border bg-card">
            <div className="p-4">
              <h3 className="font-medium mb-3">Validation Issues</h3>
              {issues.length === 0 ? (
                <p className="text-xs text-muted-foreground">
                  No validation issues recorded for this version.
                </p>
              ) : (
                <div className="space-y-2">
                  {issues.map((issue, idx) => (
                    <div
                      key={idx}
                      className={cn(
                        "p-2 rounded-lg border text-xs",
                        issue.severity === "error" && "border-destructive/20 bg-destructive/5 text-destructive",
                        issue.severity === "warning" && "border-warning/20 bg-warning/5 text-warning-foreground",
                        issue.severity === "info" && "border-border bg-muted/50 text-muted-foreground"
                      )}
                    >
                      <div className="flex items-center gap-1 mb-1">
                        <Badge variant={issue.severity === "error" ? "destructive" : "secondary"} size="sm">
                          {issue.severity}
                        </Badge>
                        {issue.requirement_id && (
                          <span className="font-mono">{issue.requirement_id}</span>
                        )}
                      </div>
                      <p>{issue.message}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  );
}

interface RequirementEditorCardProps {
  requirement: Requirement;
  section: string;
  drafts: Record<string, EditDraft>;
  draftKey: (section: string, reqId: string, field: string) => string;
  onUpdate: (section: string, reqId: string, field: string, value: string) => void;
}

function RequirementEditorCard({
  requirement,
  section,
  drafts,
  draftKey,
  onUpdate,
}: RequirementEditorCardProps) {
  const [expanded, setExpanded] = useState(false);

  const hasDrafts = EDITABLE_FIELDS.some((f) => draftKey(section, requirement.id, f.key) in drafts);

  return (
    <article className="rounded-xl border border-border bg-card overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-start gap-3 p-4 text-left hover:bg-muted/30 transition-colors"
      >
        <div className="p-2 rounded-lg bg-primary/10 text-primary flex-shrink-0">
          <FileText className="h-4 w-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-sm text-muted-foreground">{requirement.id}</span>
            <Badge variant="outline" size="sm">{requirement.priority}</Badge>
            <Badge variant="outline" size="sm">{requirement.confidence}</Badge>
            {hasDrafts && (
              <Badge variant="warning" size="sm">Edited</Badge>
            )}
          </div>
          <h4 className="font-medium mt-1">{requirement.title}</h4>
          <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{requirement.statement}</p>
        </div>
        <span className="text-muted-foreground text-xs">{expanded ? "▲" : "▼"}</span>
      </button>

      {expanded && (
        <div className="p-4 pt-0 space-y-4 border-t border-border">
          {EDITABLE_FIELDS.map((field) => {
            const key = draftKey(section, requirement.id, field.key);
            const draft = drafts[key];
            const currentValue = (requirement as unknown as Record<string, unknown>)[field.key] as string;
            const value = draft ? draft.value : currentValue;

            return (
              <div key={field.key}>
                <label className="block text-sm font-medium text-muted-foreground uppercase tracking-wider mb-2">
                  {field.label}
                </label>
                <Textarea
                  value={value}
                  onChange={(e) => onUpdate(section, requirement.id, field.key, e.target.value)}
                  rows={field.key === "acceptance_criteria" ? 3 : 2}
                  className={cn(
                    draft && "border-primary/50 focus-visible:ring-primary/30"
                  )}
                />
                {draft && draft.value !== currentValue && (
                  <p className="text-xs text-muted-foreground mt-1">
                    <span className="text-primary">Modified.</span>{" "}
                    <button
                      type="button"
                      onClick={() => onUpdate(section, requirement.id, field.key, currentValue)}
                      className="underline hover:text-foreground"
                    >
                      Revert
                    </button>
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </article>
  );
}

function cn(...classes: (string | false | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}
