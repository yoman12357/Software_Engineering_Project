"use client";

import { useCallback, useEffect, useState } from "react";
import { cn } from "../../lib/utils";
import {
  FileText,
  Shield,
  Settings,
  Download,
  Edit,
  Search,
  ExternalLink,
  Eye,
  FileJson,
  History,
  RefreshCw,
  CheckCircle2,
} from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../../components/ui/Tabs";
import { ScrollArea } from "../../components/ui/ScrollArea";
import { Badge } from "../../components/ui/Badge";
import { RequirementCard } from "./RequirementCard";
import { ProvenanceIndicator } from "./ProvenanceIndicator";
import { api } from "../../api/client";
import { buildSrsRoute } from "../../lib/routes";
import { downloadTextFile, srsToMarkdown } from "../../lib/srsExport";
import type {
  ArtifactProvenanceResponse,
  Requirement,
  SourceChunk,
  SourceReference,
  SRSSchema,
  SRSVersionSummary,
  SRSRegeneratableSection,
  SRSValidationResponse,
} from "../../api/types";

interface SRSWorkspaceProps {
  projectId: string;
  srs: SRSSchema;
  versionId: string;
}

type WorkspaceRequirement = SRSWorkspaceProps["srs"]["functional_requirements"][number];

export function SRSWorkspace({ projectId, srs, versionId }: SRSWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<string>("functional");
  const [showSources, setShowSources] = useState(false);
  const [provenance, setProvenance] = useState<ArtifactProvenanceResponse | null>(null);
  const [sources, setSources] = useState<SourceChunk[]>([]);
  const [sourcesLoading, setSourcesLoading] = useState(false);
  const [sourcesError, setSourcesError] = useState<string | null>(null);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [previewPdf, setPreviewPdf] = useState<string | null>(null);
  const [versions, setVersions] = useState<SRSVersionSummary[]>([]);
  const [versionsError, setVersionsError] = useState<string | null>(null);
  const [validation, setValidation] = useState<SRSValidationResponse | null>(null);
  const [validating, setValidating] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  useEffect(() => {
    let active = true;
    api.getSrsProvenance(projectId, versionId)
      .then((result) => {
        if (active) setProvenance(result);
      })
      .catch(() => {
        if (active) setProvenance(null);
      });
    return () => {
      active = false;
    };
  }, [projectId, versionId]);

  useEffect(() => {
    let active = true;
    api.listSrsVersions(projectId)
      .then((result) => {
        if (active) setVersions(result.versions);
      })
      .catch(() => {
        if (active) setVersionsError("Version history could not be loaded.");
      });
    return () => {
      active = false;
    };
  }, [projectId, versionId]);

  const handlePreviewPdf = async () => {
    setExportingPdf(true);
    try {
      const blob = await api.exportSrsPdf(projectId, versionId);
      const url = URL.createObjectURL(blob);
      setPreviewPdf(url);
    } catch (err) {
      setSourcesError(err instanceof Error ? err.message : "PDF preview failed");
    } finally {
      setExportingPdf(false);
    }
  };

  const closePreview = () => {
    if (previewPdf) {
      URL.revokeObjectURL(previewPdf);
      setPreviewPdf(null);
    }
  };

  const loadSources = useCallback(async () => {
    setSourcesLoading(true);
    setSourcesError(null);
    try {
      const result = await api.getSrsSources(projectId, versionId);
      setSources(result.sources);
    } catch {
      setSourcesError("Failed to load source chunks. RAG knowledge base may be unavailable.");
    } finally {
      setSourcesLoading(false);
    }
  }, [projectId, versionId]);

  const handleExportPdf = async () => {
    setExportingPdf(true);
    try {
      const blob = await api.exportSrsPdf(projectId, versionId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      const projectName = (srs.metadata.project_name || "srs")
        .replace(/[^a-z0-9]+/gi, "-")
        .toLowerCase();
      link.download = `srs_${projectName}_v${srs.metadata.version}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      setSourcesError(err instanceof Error ? err.message : "PDF export failed");
    } finally {
      setExportingPdf(false);
    }
  };

  const exportBaseName = (srs.metadata.project_name || "srs")
    .replace(/[^a-z0-9]+/gi, "-")
    .toLowerCase();

  const handleExportMarkdown = () => {
    downloadTextFile(
      srsToMarkdown(srs),
      `srs_${exportBaseName}_v${srs.metadata.version}.md`,
      "text/markdown;charset=utf-8",
    );
  };

  const handleExportJson = () => {
    downloadTextFile(
      JSON.stringify(srs, null, 2),
      `srs_${exportBaseName}_v${srs.metadata.version}.json`,
      "application/json;charset=utf-8",
    );
  };

  const regeneratableSections: Partial<Record<string, SRSRegeneratableSection>> = {
    functional: "functional_requirements",
    security: "security_requirements",
    "non-functional": "non_functional_requirements",
    data: "data_requirements",
    network: "network_requirements",
    architecture: "architecture_summary",
    threats: "threats",
  };

  const handleValidate = async () => {
    setValidating(true);
    setSourcesError(null);
    try {
      setValidation(await api.validateSrsVersion(projectId, versionId));
    } catch (error) {
      setSourcesError(error instanceof Error ? error.message : "Validation failed.");
    } finally {
      setValidating(false);
    }
  };

  const handleRegenerateSection = async () => {
    const section = regeneratableSections[activeTab];
    if (!section) return;
    setRegenerating(true);
    setSourcesError(null);
    try {
      const regenerated = await api.regenerateSrsSection(projectId, versionId, section);
      window.location.hash = buildSrsRoute(projectId, regenerated.id);
    } catch (error) {
      setSourcesError(error instanceof Error ? error.message : "Section regeneration failed.");
    } finally {
      setRegenerating(false);
    }
  };

  useEffect(() => {
    if (activeTab === "sources") {
      loadSources();
    }
  }, [activeTab, loadSources]);

  const tabs = [
    { id: "overview", label: "Overview", icon: FileText },
    { id: "functional", label: "Functional", icon: FileText, count: srs.functional_requirements?.length || 0 },
    { id: "security", label: "Security", icon: Shield, count: srs.security_requirements?.length || 0 },
    { id: "non-functional", label: "Non-Functional", icon: FileText, count: srs.non_functional_requirements?.length || 0 },
    { id: "data", label: "Data", icon: FileText, count: srs.data_requirements?.length || 0 },
    { id: "network", label: "Network", icon: FileText, count: srs.network_requirements?.length || 0 },
    { id: "architecture", label: "Architecture", icon: Settings },
    { id: "threats", label: "Threats", icon: Shield, count: srs.threats?.length || 0 },
    { id: "sources", label: "Sources", icon: Search, count: 0 },
  ];

  const getRequirementsForTab = (tabId: string) => {
    switch (tabId) {
      case "functional":
        return srs.functional_requirements;
      case "security":
        return srs.security_requirements;
      case "non-functional":
        return srs.non_functional_requirements;
      case "data":
        return srs.data_requirements;
      case "network":
        return srs.network_requirements;
      default:
        return [];
    }
  };

  const handleSourceClick = (sourceId: string, requirement: WorkspaceRequirement) => {
    const allSources = requirement.source_references || [];
    const source = allSources.find((s: SourceReference) => s.source_id === sourceId);
    if (source) {
      setShowSources(true);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 p-4 bg-card border border-border rounded-xl">
        <div className="flex items-center gap-4">
          <div className="p-2 rounded-lg bg-primary/10 text-primary">
            <FileText className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">{srs.metadata.project_name}</h1>
            <p className="text-sm text-muted-foreground">
              v{srs.metadata.version} • {new Date(srs.metadata.generated_at).toLocaleString()}
            </p>
          </div>
        </div>

        <div className="flex-1" />

        <div className="flex flex-wrap items-center justify-end gap-2">
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <History className="h-4 w-4" />
            <span className="sr-only">SRS version</span>
            <select
              aria-label="SRS version"
              value={versionId}
              onChange={(event) => {
                window.location.hash = buildSrsRoute(projectId, event.target.value);
              }}
              className="rounded-md border border-border bg-card px-2 py-1.5 text-foreground"
            >
              {versions.length === 0 && <option value={versionId}>Version {srs.metadata.version}</option>}
              {versions.map((version) => (
                <option key={version.id} value={version.id}>
                  Version {version.version_number} · {version.status}
                </option>
              ))}
            </select>
          </label>
          <Button variant="ghost" size="sm" onClick={() => window.location.hash = buildSrsRoute(projectId, versionId, true)}>
            <Edit className="h-4 w-4 mr-2" />
            Edit
          </Button>
          <Button variant="secondary" size="sm" onClick={handlePreviewPdf} loading={exportingPdf} disabled={exportingPdf}>
            <Eye className="h-4 w-4 mr-2" />
            Preview PDF
          </Button>
          <Button data-action="export-pdf" variant="outline" size="sm" onClick={handleExportPdf} loading={exportingPdf} disabled={exportingPdf}>
            <Download className="h-4 w-4 mr-2" />
            Export PDF
          </Button>
          <Button variant="ghost" size="sm" onClick={handleValidate} loading={validating} disabled={validating}>
            <CheckCircle2 className="h-4 w-4 mr-2" />
            Validate
          </Button>
          {regeneratableSections[activeTab] && (
            <Button data-action="regenerate-section" variant="ghost" size="sm" onClick={handleRegenerateSection} loading={regenerating} disabled={regenerating}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Regenerate Section
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={handleExportMarkdown}>
            <Download className="h-4 w-4 mr-2" />
            Markdown
          </Button>
          <Button variant="ghost" size="sm" onClick={handleExportJson}>
            <FileJson className="h-4 w-4 mr-2" />
            JSON
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setShowSources(!showSources)}>
            <Search className="h-4 w-4 mr-2" />
            Sources
          </Button>
        </div>
      </div>

      {/* Metadata bar */}
      <div className="mb-4 border-b border-border pb-3">
        <ProvenanceIndicator provenance={provenance} fallback={srs} />
        {versionsError && <p className="mt-2 text-xs text-red-400">{versionsError}</p>}
        {validation && (
          <p className="mt-2 text-xs text-muted-foreground" role="status">
            Validation score: {validation.overall_score}/100 · {validation.issues.length} issue{validation.issues.length === 1 ? "" : "s"}
          </p>
        )}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
        <TabsList className="grid w-full grid-cols-4 sm:grid-cols-6 lg:grid-cols-10 gap-1 p-1 bg-muted/50 rounded-xl">
          {tabs.map((tab) => (
            <TabsTrigger
              key={tab.id}
              value={tab.id}
              className={cn(
                "flex items-center gap-1.5 justify-center",
                "data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
              )}
            >
              <tab.icon className="h-4 w-4" />
              <span className="hidden sm:inline">{tab.label}</span>
              {tab.count !== undefined && (
                <span className="px-1.5 py-0.5 text-xs rounded-full bg-muted text-muted-foreground">
                  {tab.count}
                </span>
              )}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="overview" className="flex-1 overflow-hidden">
          <ScrollArea className="h-full p-4 space-y-6">
            <div className="space-y-4 max-w-3xl">
              <section>
                <h3 className="text-lg font-semibold mb-2">Project Overview</h3>
                <div className="prose prose-sm max-w-none text-muted-foreground">
                  <p>{srs.project_overview.description}</p>
                  <p>{srs.project_overview.purpose}</p>
                  <p>{srs.project_overview.context}</p>
                </div>
              </section>

              <section>
                <h3 className="text-lg font-semibold mb-2">Scope</h3>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <h4 className="font-medium mb-2">In Scope</h4>
                    <ul className="space-y-1 text-sm text-muted-foreground">
                      {srs.scope.in_scope.map((item) => (
                        <li key={item} className="flex items-start gap-2">
                          <span className="text-primary mt-1">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Out of Scope</h4>
                    <ul className="space-y-1 text-sm text-muted-foreground">
                      {srs.scope.out_of_scope.map((item) => (
                        <li key={item} className="flex items-start gap-2">
                          <span className="text-muted-foreground mt-1">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </section>

              <section>
                <h3 className="text-lg font-semibold mb-2">Assumptions</h3>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  {srs.assumptions.map((a) => (
                    <li key={a} className="flex items-start gap-2">
                      <span className="text-primary mt-1">•</span>
                      <span>{a}</span>
                    </li>
                  ))}
                </ul>
              </section>

              <section>
                <h3 className="text-lg font-semibold mb-2">Stakeholders</h3>
                <div className="flex flex-wrap gap-2">
                  {srs.stakeholders.map((s) => (
                    <span key={s} className="px-2 py-1 text-xs rounded-full bg-muted text-muted-foreground">
                      {s}
                    </span>
                  ))}
                </div>
              </section>

              <section>
                <h3 className="text-lg font-semibold mb-2">User Roles</h3>
                <div className="flex flex-wrap gap-2">
                  {srs.user_roles.map((r) => (
                    <span key={r} className="px-2 py-1 text-xs rounded-full bg-muted text-muted-foreground">
                      {r}
                    </span>
                  ))}
                </div>
              </section>
            </div>
          </ScrollArea>
        </TabsContent>

        {tabs.filter(t => t.id !== "overview" && t.id !== "sources").map((tab) => (
          <TabsContent key={tab.id} value={tab.id} className="flex-1 overflow-hidden">
            <RequirementList
              requirements={getRequirementsForTab(tab.id)}
              onSourceClick={handleSourceClick}
            />
          </TabsContent>
        ))}

        <TabsContent value="architecture" className="flex-1 overflow-hidden">
          <ScrollArea className="h-full p-4 space-y-6">
            <section>
              <h3 className="text-lg font-semibold mb-2">Architecture Overview</h3>
              <p className="text-muted-foreground">{srs.architecture_summary.overview}</p>
            </section>

            <section>
              <h3 className="text-lg font-semibold mb-2">Components</h3>
              <div className="grid gap-4 sm:grid-cols-2">
                {srs.architecture_summary.components.map((comp) => (
                  <div key={comp.name} className="p-4 rounded-lg border border-border bg-card">
                    <h4 className="font-medium mb-2">{comp.name}</h4>
                    <p className="text-sm text-muted-foreground mb-3">{comp.description}</p>
                    <div className="flex flex-wrap gap-2">
                      {comp.responsibilities.map((r) => (
                        <span key={r} className="px-2 py-1 text-xs rounded-full bg-muted text-muted-foreground">
                          {r}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section>
              <h3 className="text-lg font-semibold mb-2">Data Flows</h3>
              <ul className="space-y-1 text-sm text-muted-foreground">
                {srs.architecture_summary.data_flows.map((flow) => (
                  <li key={flow} className="flex items-start gap-2">
                    <span className="text-primary mt-1">→</span>
                    <span>{flow}</span>
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <h3 className="text-lg font-semibold mb-2">Deployment Notes</h3>
              <p className="text-muted-foreground">{srs.architecture_summary.deployment_notes}</p>
            </section>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="threats" className="flex-1 overflow-hidden">
          <ScrollArea className="h-full p-4 space-y-4">
            {srs.threats.map((threat) => (
              <div key={threat.threat_id} className="p-4 rounded-lg border border-border bg-card">
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div>
                    <h4 className="font-semibold">{threat.name}</h4>
                    <span className={cn(
                      "px-2 py-0.5 text-xs rounded-full border",
                      threat.severity === "critical" && "bg-primary text-primary-foreground border-primary",
                      threat.severity === "high" && "bg-secondary-blue text-foreground border-secondary-blue",
                      threat.severity === "medium" && "bg-soft-blue text-foreground border-secondary-blue",
                      threat.severity === "low" && "bg-soft-cyan text-foreground border-secondary-blue",
                    )}>
                      {threat.severity}
                    </span>
                  </div>
                  {threat.category && (
                    <span className="px-2 py-0.5 text-xs rounded-full bg-muted text-muted-foreground">
                      {threat.category}
                    </span>
                  )}
                </div>
                <p className="text-sm text-muted-foreground mb-3">{threat.description}</p>

                {threat.affected_assets.length > 0 && (
                  <div className="mb-3">
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Affected Assets</span>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {threat.affected_assets.map((asset) => (
                        <span key={asset} className="px-2 py-0.5 text-xs rounded-full bg-muted text-muted-foreground">
                          {asset}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {threat.mitigations.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Mitigations</span>
                    <ul className="space-y-2 mt-2">
                      {threat.mitigations.map((mit) => (
                        <li key={mit.mitigation_id} className="text-sm text-muted-foreground flex items-start gap-2">
                          <span className="text-primary mt-1">→</span>
                          <span>{mit.description}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </ScrollArea>
        </TabsContent>

        <TabsContent value="sources" className="flex-1 overflow-hidden">
          <div className="h-full flex flex-col">
            {sourcesLoading && (
              <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
              </div>
            )}
            {sourcesError && (
              <div className="p-4 text-center text-red-500">{sourcesError}</div>
            )}
            <ScrollArea className="flex-1 p-4 space-y-4">
              {!sourcesLoading && !sourcesError && sources.length === 0 && (
                <div className="rounded-xl border border-border bg-muted/30 p-6 text-center text-sm text-muted-foreground">
                  This version has no cited RAG source chunks.
                </div>
              )}
              {sources.map((source) => (
                <article
                  key={source.chunk_id}
                  className="bg-card border border-border rounded-xl overflow-hidden hover:border-primary/50 transition-colors"
                >
                  <div className="p-4 border-b border-border flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <Badge variant="secondary">{source.metadata.source_id}</Badge>
                      <span className="font-medium">{source.metadata.document_title || "Untitled Source"}</span>
                    </div>
                    <a
                      href={source.metadata.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-muted-foreground hover:text-primary transition-colors flex-shrink-0"
                      aria-label="Open original source"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </div>
                  <div className="p-4">
                    <p className="text-sm text-muted-foreground whitespace-pre-wrap">{source.text}</p>
                    {source.metadata.categories && (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {source.metadata.categories.split(",").filter(Boolean).map((cat) => (
                          <Badge key={cat} variant="secondary" size="sm">{cat.trim()}</Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </article>
              ))}
            </ScrollArea>
          </div>
        </TabsContent>
      </Tabs>
        {/* PDF Preview Modal */}
        {previewPdf && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
            onClick={closePreview}
          >
            <div className="relative w-full h-full max-w-4xl max-h-[90vh] bg-white rounded-xl overflow-hidden m-4" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between p-4 border-b border-border">
                <h2 className="text-lg font-semibold">PDF Preview</h2>
                <Button variant="ghost" size="sm" onClick={closePreview}>
                  <Eye className="h-4 w-4" />
                </Button>
              </div>
              <div className="flex-1 overflow-hidden p-4">
                <iframe
                  src={previewPdf}
                  className="w-full h-full border-none rounded-lg"
                  title="SRS PDF Preview"
                />
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

function RequirementList({
  requirements,
  onSourceClick,
}: {
  requirements: WorkspaceRequirement[];
  onSourceClick: (sourceId: string, requirement: WorkspaceRequirement) => void;
}) {
  if (!requirements.length) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        <p>No requirements in this section</p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full p-4 space-y-4">
      {requirements.map((req) => (
        <RequirementCard
          key={req.id}
          requirement={req as unknown as Requirement}
          onViewSources={(sources) => {
            // Find the source in the requirement's sources
            const source = sources.find((s) => s.source_id === req.source_references[0]?.source_id);
            if (source) {
              onSourceClick(source.source_id, req);
            }
          }}
        />
      ))}
    </ScrollArea>
  );
}
