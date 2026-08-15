"use client";

import { cn } from "../../lib/utils";
import { CheckCircle, FileText, Shield, Download, Edit, ExternalLink } from "lucide-react";
import { Button } from "../../components/ui/Button";
import type { SRSSchema } from "../../api/types";

interface SRSCompletionCardProps {
  srs: SRSSchema;
  versionId: string;
  onOpen?: () => void;
}

export function SRSCompletionCard({ srs, versionId, onOpen }: SRSCompletionCardProps) {
  const stats = [
    { label: "Functional", count: srs.functional_requirements?.length || 0, icon: FileText, color: "text-primary" },
    { label: "Security", count: srs.security_requirements?.length || 0, icon: Shield, color: "text-foreground" },
    { label: "Non-Functional", count: srs.non_functional_requirements?.length || 0, icon: FileText, color: "text-muted-foreground" },
    { label: "Threats", count: srs.threats?.length || 0, icon: Shield, color: "text-primary" },
  ];

  return (
    <div className="animate-in slide-up">
      <div className="flex items-center gap-3 mb-4 p-4 rounded-xl bg-success/5 border border-success/20">
        <div className="p-3 rounded-xl bg-success text-success-foreground">
          <CheckCircle className="h-6 w-6" />
        </div>
        <div>
          <h3 className="text-lg font-semibold">Software Requirements Specification Generated</h3>
          <p className="text-sm text-muted-foreground">
            Version {srs.metadata.version} • {new Date(srs.metadata.generated_at).toLocaleString()}
          </p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 mb-4">
        {stats.map((stat) => (
          <div key={stat.label} className="p-4 rounded-xl bg-card border border-border/50 text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <stat.icon className={cn("h-5 w-5", stat.color)} />
              <span className="text-lg font-bold">{stat.count}</span>
            </div>
            <span className="text-sm text-muted-foreground">{stat.label}</span>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-3">
        <Button className="flex-1 sm:flex-none" onClick={onOpen ?? (() => { window.location.hash = `srs/${versionId}`; })}>
          <ExternalLink className="h-4 w-4 mr-2" />
          View Full SRS
        </Button>
        <Button variant="outline" onClick={() => { window.location.hash = `srs/${versionId}/edit`; }}>
          <Edit className="h-4 w-4 mr-2" />
          Edit Requirements
        </Button>
        <Button variant="ghost" disabled title="PDF export coming soon">
          <Download className="h-4 w-4 mr-2" />
          Export PDF
        </Button>
      </div>
    </div>
  );
}

export default SRSCompletionCard;
