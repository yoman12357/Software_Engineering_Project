"use client";

import { useState } from "react";
import { Database, Search, FileText, Filter } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { ScrollArea } from "../../components/ui/ScrollArea";
import { SourceCard } from "./SourceCard";
import { SourceChipGroup } from "./SourceChip";
import type { SourceReference } from "../../api/types";

interface RetrievalSourcesProps {
  sources: SourceReference[];
  summary?: {
    totalChunks: number;
    sources: Array<{ source_id: string; document_title: string; chunk_count: number }>;
  };
  onSelectSource?: (source: SourceReference) => void;
}

export function RetrievalSources({ sources, summary, onSelectSource }: RetrievalSourcesProps) {
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<string>("");

  const filteredSources = sources.filter((s) =>
    s.document_title.toLowerCase().includes(filter.toLowerCase()) ||
    s.source_id.toLowerCase().includes(filter.toLowerCase()) ||
    (s.section_heading || "").toLowerCase().includes(filter.toLowerCase())
  );

  const toggleExpand = (sourceId: string) => {
    setExpandedSources((prev) => {
      const next = new Set(prev);
      if (next.has(sourceId)) {
        next.delete(sourceId);
      } else {
        next.add(sourceId);
      }
      return next;
    });
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-primary/10 text-primary">
            <Database className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-semibold">Retrieved Sources</h3>
            <p className="text-sm text-muted-foreground">
              {sources.length} chunk{sources.length !== 1 ? "s" : ""} from {summary?.sources.length || 0} document{summary?.sources.length !== 1 ? "s" : ""}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="gap-1">
            <Filter className="h-3.5 w-3.5" />
            Filter
          </Button>
        </div>
      </div>

      {/* Filter */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Filter sources..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="w-full pl-10 pr-4 py-2 rounded-lg border border-border bg-background text-sm"
        />
      </div>

      {/* Summary badges */}
      {summary && summary.sources.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {summary.sources.map((src) => (
            <Badge key={src.source_id} variant="outline" className="gap-1 cursor-pointer hover:bg-primary/5" onClick={() => setFilter(src.source_id)}>
              <FileText className="h-3 w-3" />
              {src.document_title} ({src.chunk_count})
            </Badge>
          ))}
        </div>
      )}

      {/* Sources list */}
      <ScrollArea className="max-h-[60vh] space-y-3">
        {filteredSources.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Database className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
            <p>No sources match your filter</p>
          </div>
        ) : (
          filteredSources.map((source) => (
            <SourceCard
              key={source.source_id}
              source={source}
              expanded={expandedSources.has(source.source_id)}
              onExpand={toggleExpand}
              onClick={onSelectSource}
            />
          ))
        )}
      </ScrollArea>

      {/* Source chips at bottom for quick navigation */}
      {sources.length > 5 && (
        <div className="border-t border-border pt-4">
          <p className="text-xs text-muted-foreground mb-2">Quick navigation:</p>
          <SourceChipGroup sources={sources} maxVisible={10} onClick={onSelectSource} compact />
        </div>
      )}
    </div>
  );
}

interface RetrievalSummaryProps {
  summary: {
    totalChunks: number;
    sources: Array<{ source_id: string; document_title: string; chunk_count: number }>;
    retrievalTimeMs: number;
    ragEnabled: boolean;
  };
}

export function RetrievalSummary({ summary }: RetrievalSummaryProps) {
  if (!summary.ragEnabled) {
    return (
      <div className="p-3 rounded-lg bg-muted/50 border border-border">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Database className="h-4 w-4" />
          RAG was not used for this generation
        </div>
      </div>
    );
  }

  return (
    <div className="p-3 rounded-lg bg-muted/50 border border-border">
      <div className="flex items-center gap-2 mb-3">
        <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
          <Database className="h-4 w-4" />
        </div>
        <h4 className="font-medium">Retrieval Summary</h4>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="p-2 rounded-lg bg-card border border-border text-center">
          <div className="text-2xl font-bold text-primary">{summary.totalChunks}</div>
          <div className="text-xs text-muted-foreground">Total Chunks</div>
        </div>
        <div className="p-2 rounded-lg bg-card border border-border text-center">
          <div className="text-2xl font-bold text-primary">{summary.sources.length}</div>
          <div className="text-xs text-muted-foreground">Documents</div>
        </div>
        <div className="p-2 rounded-lg bg-card border border-border text-center">
          <div className="text-2xl font-bold text-primary">{summary.retrievalTimeMs}ms</div>
          <div className="text-xs text-muted-foreground">Retrieval Time</div>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {summary.sources.map((src) => (
          <Badge key={src.source_id} variant="outline" className="gap-1">
            <FileText className="h-3 w-3" />
            {src.document_title} ({src.chunk_count})
          </Badge>
        ))}
      </div>
    </div>
  );
}

export default RetrievalSources;
