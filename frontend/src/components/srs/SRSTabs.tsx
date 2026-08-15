"use client";

import { cn } from "../../lib/utils";
import { FileText, Shield, Database, Globe, AlertTriangle, Settings, Search } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../../components/ui/Tabs";
import { ScrollArea } from "../../components/ui/ScrollArea";
import { RequirementCard } from "./RequirementCard";
import { SourceChips } from "../rag";
import type { Requirement, SRSSchema, SourceReference } from "../../api/types";

interface SRSTabsProps {
  srs: SRSSchema;
  onRequirementEdit?: (req: Requirement) => void;
  onViewSources?: (source: SourceReference) => void;
  activeTab?: string;
  onTabChange?: (tab: string) => void;
}

const tabs = [
  { id: "overview", label: "Overview", icon: FileText },
  { id: "functional", label: "Functional", icon: FileText },
  { id: "security", label: "Security", icon: Shield },
  { id: "non-functional", label: "Non-Functional", icon: FileText },
  { id: "data", label: "Data", icon: Database },
  { id: "network", label: "Network", icon: Globe },
  { id: "architecture", label: "Architecture", icon: Settings },
  { id: "threats", label: "Threats", icon: AlertTriangle },
  { id: "sources", label: "Sources", icon: Search },
] as const;

export function SRSTabs({
  srs,
  onRequirementEdit,
  onViewSources,
  activeTab = "overview",
  onTabChange,
}: SRSTabsProps) {
  const getRequirementsForTab = (tabId: string) => {
    switch (tabId) {
      case "functional": return srs.functional_requirements;
      case "security": return srs.security_requirements;
      case "non-functional": return srs.non_functional_requirements;
      case "data": return srs.data_requirements;
      case "network": return srs.network_requirements;
      default: return [];
    }
  };

  return (
    <Tabs value={activeTab} onValueChange={onTabChange ?? (() => {})} className="h-full flex flex-col">
      <TabsList className="grid w-full grid-cols-4 sm:grid-cols-5 lg:grid-cols-10 gap-1 p-1 bg-muted/50 rounded-xl">
        {tabs.map((tab) => {
          const count = getRequirementsForTab(tab.id).length;
          return (
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
              {count > 0 && (
                <span className="px-1.5 py-0.5 text-xs rounded-full bg-muted text-muted-foreground">
                  {count}
                </span>
              )}
            </TabsTrigger>
          );
        })}
      </TabsList>

      <TabsContent value="overview" className="flex-1 overflow-hidden">
        <ScrollArea className="h-full p-4 space-y-6">
          <div className="space-y-4 max-w-3xl">
            <section>
              <h3 className="text-lg font-semibold mb-2">Project Overview</h3>
              <div className="prose prose-sm max-w-none text-muted-foreground space-y-3">
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

      {tabs.filter((t) => t.id !== "overview" && t.id !== "architecture" && t.id !== "threats" && t.id !== "sources").map((tab) => (
        <TabsContent key={tab.id} value={tab.id} className="flex-1 overflow-hidden">
          <RequirementList
            requirements={getRequirementsForTab(tab.id)}
            onRequirementEdit={onRequirementEdit}
            onViewSources={onViewSources}
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
        <div className="p-4">
          <SourceChips
            sources={srs.references as SourceReference[]}
            maxVisible={20}
            onClick={onViewSources}
          />
        </div>
      </TabsContent>
    </Tabs>
  );
}

function RequirementList({
  requirements,
  onRequirementEdit,
  onViewSources,
}: {
  requirements: Requirement[];
  onRequirementEdit?: (req: Requirement) => void;
  onViewSources?: (source: SourceReference) => void;
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
          requirement={req}
          onEdit={onRequirementEdit}
          onViewSources={(sources) => {
            const source = sources.find((s) => s.source_id === req.source_references[0]?.source_id);
            if (source) onViewSources?.(source);
          }}
        />
      ))}
    </ScrollArea>
  );
}

export default SRSTabs;
