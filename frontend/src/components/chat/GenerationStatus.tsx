"use client";

import { Loader2, Database, FileText, Shield, X } from "lucide-react";
import type { SRSGenerationProgressEvent } from "../../api/types";
import { Button } from "../ui/Button";

const signals = [
  { label: "Local Qwen generation", icon: Shield },
  { label: "Security knowledge retrieval (RAG)", icon: Database },
  { label: "Structured SRS validation", icon: FileText },
] as const;

export function GenerationStatus({
  progress,
  onCancel,
}: {
  progress?: SRSGenerationProgressEvent | null;
  onCancel?: () => void;
}) {
  return (
    <div className="animate-in slide-up">
      <div className="mb-4 flex items-start gap-3 rounded-xl border border-primary/20 bg-primary/5 p-4">
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-medium">Generating your SRS</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {progress?.message ?? "Preparing validated SRS generation with local Qwen."}
          </p>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all duration-300"
              style={{ width: `${progress?.progress ?? 2}%` }}
            />
          </div>
        </div>
        {onCancel && (
          <Button variant="ghost" size="sm" onClick={onCancel} aria-label="Cancel generation">
            <X className="mr-1 h-4 w-4" /> Cancel
          </Button>
        )}
      </div>

      <div className="space-y-3">
        {signals.map((signal) => (
          <div
            key={signal.label}
            className="flex items-center gap-3 rounded-lg border border-border bg-muted/30 p-3 text-muted-foreground"
          >
            <Loader2 className="h-5 w-5 text-primary animate-spin" />
            <span className="text-sm">{signal.label}</span>
            <span className="ml-auto text-xs text-muted-foreground">
              {progress?.phase === "completed" ? "complete" : "in progress"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default GenerationStatus;
