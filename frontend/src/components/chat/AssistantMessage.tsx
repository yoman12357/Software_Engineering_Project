"use client";

import { ProjectAnalysisCard } from "./ProjectAnalysisCard";
import { ClarificationForm } from "./ClarificationForm";
import { GenerationStatus } from "./GenerationStatus";
import { SRSCompletionCard } from "./SRSCompletionCard";
import type { ProjectAnalysis, ClarificationQuestionRead, SRSSchema } from "../../api/types";

interface AssistantMessageProps {
  content: string;
  type?: string;
  metadata?: {
    analysis?: ProjectAnalysis;
    questions?: ClarificationQuestionRead[];
    srs?: SRSSchema;
    versionId?: string;
    projectId?: string;
  };
  timestamp: Date;
  onSubmitClarifications?: (answers: Array<{ question_id: string; answer_text: string; skipped: boolean }>) => void | Promise<void>;
  onOpenSRS?: () => void;
}

export function AssistantMessage({
  content,
  type,
  metadata,
  timestamp,
  onSubmitClarifications,
  onOpenSRS,
}: AssistantMessageProps) {
  const renderContent = () => {
    switch (type) {
      case "analysis":
        return metadata?.analysis ? (
          <ProjectAnalysisCard analysis={metadata.analysis} />
        ) : (
          <div className="prose prose-sm max-w-none">{content}</div>
        );
      case "clarification":
        return metadata?.questions ? (
          <ClarificationForm
            questions={metadata.questions}
            onSubmit={onSubmitClarifications ?? (() => {})}
            disabled={false}
          />
        ) : (
          <div className="prose prose-sm max-w-none">{content}</div>
        );
      case "generation":
        return <GenerationStatus />;
      case "srs":
        return metadata?.srs ? (
          <SRSCompletionCard srs={metadata.srs} versionId={metadata.versionId || ""} onOpen={onOpenSRS} />
        ) : (
          <div className="prose prose-sm max-w-none">{content}</div>
        );
      case "error":
        return (
          <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive">
            {content}
          </div>
        );
      default:
        return <div className="prose prose-sm max-w-none whitespace-pre-wrap">{content}</div>;
    }
  };

  return (
    <div className="animate-in slide-up animate-out fade-out">
      <div className="flex gap-3 max-w-[85%] lg:max-w-[80%]">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
          <svg className="h-4 w-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.5a3.374 3.374 0 00-3.37-3.37V12a5 5 0 1110 0v.5" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <div className="bg-muted/50 rounded-2xl rounded-tl-sm px-4 py-3">
            {renderContent()}
          </div>
          <div className="flex justify-end mt-1">
            <time className="text-xs text-muted-foreground">
              {new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </time>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AssistantMessage;
