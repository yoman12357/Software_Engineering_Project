"use client";

import { useState } from "react";
import { cn } from "../../lib/utils";
import { CheckCircle, FileText, Shield, Download, Edit, ExternalLink, Eye } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { api } from "../../api/client";
import type { SRSSchema } from "../../api/types";
import { buildSrsRoute } from "../../lib/routes";

interface SRSCompletionCardProps {
  srs: SRSSchema;
  versionId: string;
  projectId: string;
  onOpen?: () => void;
}

export function SRSCompletionCard({ srs, versionId, projectId, onOpen }: SRSCompletionCardProps) {
  const stats = [
    { label: "Functional", count: srs.functional_requirements?.length || 0, icon: FileText, color: "text-primary" },
    { label: "Security", count: srs.security_requirements?.length || 0, icon: Shield, color: "text-foreground" },
    { label: "Non-Functional", count: srs.non_functional_requirements?.length || 0, icon: FileText, color: "text-muted-foreground" },
    { label: "Threats", count: srs.threats?.length || 0, icon: Shield, color: "text-primary" },
  ];

  const [previewOpen, setPreviewOpen] = useState(false);
  const [pdfDownloading, setPdfDownloading] = useState(false);

  const handlePreview = async () => {
    try {
      const response = await api.getSrsVersion(projectId, versionId);
      if (response.srs) {
        setPreviewOpen(true);
      }
    } catch (error) {
      console.error("Failed to load SRS for preview:", error);
    }
  };

  const handleDownloadPdf = async () => {
    setPdfDownloading(true);
    try {
      const blob = await api.exportSrsPdf(projectId, versionId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `srs_v${srs.metadata.version}_${new Date().toISOString().split("T")[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Failed to download PDF:", error);
    } finally {
      setPdfDownloading(false);
    }
  };

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
        <Button className="flex-1 sm:flex-none" onClick={onOpen ?? (() => { window.location.hash = buildSrsRoute(projectId, versionId); })}>
          <ExternalLink className="h-4 w-4 mr-2" />
          View Full SRS
        </Button>
        <Button variant="outline" onClick={() => { window.location.hash = buildSrsRoute(projectId, versionId, true); }}>
          <Edit className="h-4 w-4 mr-2" />
          Edit Requirements
        </Button>
        <Button variant="ghost" onClick={handlePreview} disabled={previewOpen}>
          <Eye className="h-4 w-4 mr-2" />
          Preview SRS
        </Button>
        <Button variant="secondary" onClick={handleDownloadPdf} disabled={pdfDownloading} loading={pdfDownloading}>
          <Download className="h-4 w-4 mr-2" />
          {pdfDownloading ? "Generating PDF..." : "Export PDF"}
        </Button>
      </div>

      {/* Preview Modal */}
      {previewOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold">SRS Preview - v{srs.metadata.version}</h3>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={() => setPreviewOpen(false)}>
                  <Eye className="h-4 w-4 mr-1" />
                  Close
                </Button>
              </div>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <pre className="whitespace-pre-wrap text-sm font-mono">
                {JSON.stringify(srs, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SRSCompletionCard;
