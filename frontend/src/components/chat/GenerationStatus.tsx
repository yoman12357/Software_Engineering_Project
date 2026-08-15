"use client";

import { cn } from "../../lib/utils";
import { Loader2, CheckCircle, Database, FileText, Shield } from "lucide-react";

const signals = [
  { label: "Local Qwen generation", icon: Shield },
  { label: "Security knowledge retrieval", icon: Database },
  { label: "Structured SRS validation", icon: FileText },
] as const;

export function GenerationStatus() {

  return (
    <div className="animate-in slide-up">
      <div className="mb-4 flex items-start gap-3 rounded-xl border border-primary/20 bg-primary/5 p-4">
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
        <div>
          <h3 className="font-medium">Generating your SRS</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Generating your SRS with Qwen and the security knowledge base...
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {signals.map((signal) => (
          <div
            key={signal.label}
            className={cn(
              "flex items-center gap-3 rounded-lg border border-border bg-muted/30 p-3",
              "text-muted-foreground"
            )}
          >
            <signal.icon className="h-5 w-5 text-primary" />
            <span className="text-sm">{signal.label}</span>
            <CheckCircle className="ml-auto h-4 w-4 text-success" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default GenerationStatus;
