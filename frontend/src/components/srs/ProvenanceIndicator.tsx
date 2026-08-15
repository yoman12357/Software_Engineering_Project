import { BookOpen, Bot, Database, History } from "lucide-react";

import type { ArtifactProvenanceResponse, SRSSchema } from "../../api/types";
import { Badge } from "../ui/Badge";

interface ProvenanceIndicatorProps {
  provenance: ArtifactProvenanceResponse | null;
  fallback: SRSSchema;
}

function modelLabel(variant: string, modelName: string): string {
  if (variant === "finetuned") return "Fine-tuned CyberSRS";
  if (variant === "base") return "Base Qwen";
  return modelName || "Unknown model";
}

export function ProvenanceIndicator({
  provenance,
  fallback,
}: ProvenanceIndicatorProps) {
  if (provenance?.provenance_status === "legacy_unknown") {
    return (
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <History className="h-3.5 w-3.5" />
        Legacy provenance unavailable
      </div>
    );
  }

  const run = provenance?.model_run;
  const ragEnabled = run?.rag_enabled ?? fallback.generation_metadata?.rag_enabled ?? false;
  const chunks = run?.retrieved_chunk_ids.length ?? fallback.generation_metadata?.retrieved_chunks ?? 0;
  const documents = run?.retrieved_document_ids.length ?? 0;
  const sourceText = `${documents} source${documents === 1 ? "" : "s"}`;
  const label = run
    ? modelLabel(run.model_variant, run.model_name)
    : fallback.metadata.model_name;

  return (
    <div
      className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground"
      aria-label="Generation provenance"
    >
      <Badge variant="outline" className="gap-1 font-normal">
        <Bot className="h-3.5 w-3.5" />
        {label}
      </Badge>
      <Badge variant="outline" className="gap-1 font-normal">
        <Database className="h-3.5 w-3.5" />
        RAG {ragEnabled ? "enabled" : "disabled"}
      </Badge>
      {ragEnabled && (
        <Badge variant="outline" className="gap-1 font-normal">
          <BookOpen className="h-3.5 w-3.5" />
          {documents > 0 ? `${sourceText} / ${chunks} chunks` : `${chunks} chunks retrieved`}
        </Badge>
      )}
    </div>
  );
}
