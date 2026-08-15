"use client";

import { useState } from "react";
import { cn } from "../../lib/utils";
import { Shield, Users, Server, ShieldCheck, Target, X, ChevronDown } from "lucide-react";

interface ProjectAnalysisCardProps {
  analysis: {
    inferred_categories: string[];
    stakeholders: string[];
    assets: string[];
    users: string[];
    constraints: string[];
    goals: string[];
    missing_information: string[];
    project_summary: string;
  };
}

export function ProjectAnalysisCard({ analysis }: ProjectAnalysisCardProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    summary: true,
    categories: true,
    stakeholders: true,
    assets: true,
    users: true,
    constraints: true,
    goals: true,
    missing: true,
  });

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const Section = ({ title, icon: Icon, children, sectionKey, count }: {
    title: string;
    icon: React.ComponentType<{ className?: string }>;
    children: React.ReactNode;
    sectionKey: string;
    count?: number;
  }) => {
    const isExpanded = expandedSections[sectionKey];
    return (
      <div className="border border-border/50 rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection(sectionKey)}
          className="w-full flex items-center gap-3 p-3 hover:bg-muted/50 transition-colors text-left"
          aria-expanded={isExpanded}
        >
          <div className="p-2 rounded-lg bg-primary/10 text-primary">
            <Icon className="h-5 w-5" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-foreground">{title}</h4>
            {count !== undefined && (
              <span className="text-xs text-muted-foreground">{count} items</span>
            )}
          </div>
          <ChevronDown className={cn("h-4 w-4 text-muted-foreground transition-transform", isExpanded && "rotate-180")} />
        </button>
        {isExpanded && (
          <div className="px-3 pb-3 border-t border-border/50 animate-in slide-down">
            {children}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="animate-in slide-up">
      <div className="flex items-start gap-3 mb-4">
        <div className="p-3 rounded-xl bg-primary/10 text-primary">
          <ShieldCheck className="h-6 w-6" />
        </div>
        <div>
          <h3 className="text-lg font-semibold">Project Analysis Complete</h3>
          <p className="text-sm text-muted-foreground mt-1">
            {analysis.project_summary}
          </p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Section
          title="Categories"
          icon={Shield}
          sectionKey="categories"
          count={analysis.inferred_categories.length}
        >
          <div className="flex flex-wrap gap-2">
            {analysis.inferred_categories.map((cat) => (
              <span key={cat} className="px-2 py-1 text-xs rounded-full bg-soft-blue text-primary border border-primary/20">
                {cat}
              </span>
            ))}
          </div>
        </Section>

        <Section
          title="Stakeholders"
          icon={Users}
          sectionKey="stakeholders"
          count={analysis.stakeholders.length}
        >
          <div className="flex flex-wrap gap-2">
            {analysis.stakeholders.map((s) => (
              <span key={s} className="px-2 py-1 text-xs rounded-full bg-muted text-muted-foreground">
                {s}
              </span>
            ))}
          </div>
        </Section>

        <Section
          title="Assets"
          icon={Server}
          sectionKey="assets"
          count={analysis.assets.length}
        >
          <div className="flex flex-wrap gap-2">
            {analysis.assets.map((a) => (
              <span key={a} className="px-2 py-1 text-xs rounded-full bg-muted text-muted-foreground">
                {a}
              </span>
            ))}
          </div>
        </Section>

        <Section
          title="User Roles"
          icon={ShieldCheck}
          sectionKey="users"
          count={analysis.users.length}
        >
          <div className="flex flex-wrap gap-2">
            {analysis.users.map((u) => (
              <span key={u} className="px-2 py-1 text-xs rounded-full bg-muted text-muted-foreground">
                {u}
              </span>
            ))}
          </div>
        </Section>

        <Section
          title="Constraints"
          icon={X}
          sectionKey="constraints"
          count={analysis.constraints.length}
        >
          <ul className="space-y-1">
            {analysis.constraints.map((c) => (
              <li key={c} className="text-sm text-muted-foreground flex items-start gap-2">
                <span className="text-primary mt-1">•</span>
                <span>{c}</span>
              </li>
            ))}
          </ul>
        </Section>

        <Section
          title="Goals"
          icon={Target}
          sectionKey="goals"
          count={analysis.goals.length}
        >
          <ul className="space-y-1">
            {analysis.goals.map((g) => (
              <li key={g} className="text-sm text-muted-foreground flex items-start gap-2">
                <span className="text-primary mt-1">•</span>
                <span>{g}</span>
              </li>
            ))}
          </ul>
        </Section>

        {analysis.missing_information.length > 0 && (
          <Section
            title="Missing Information"
            icon={X}
            sectionKey="missing"
            count={analysis.missing_information.length}
          >
            <ul className="space-y-1">
              {analysis.missing_information.map((m) => (
                <li key={m} className="text-sm text-warning flex items-start gap-2">
                  <span className="text-warning mt-1">•</span>
                  <span>{m}</span>
                </li>
              ))}
            </ul>
          </Section>
        )}
      </div>
    </div>
  );
}
