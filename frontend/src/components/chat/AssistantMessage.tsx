"use client";

import { useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Check, Shield, RefreshCw, Edit, Trash2 } from "lucide-react";
import { ProjectAnalysisCard } from "./ProjectAnalysisCard";
import { ClarificationForm } from "./ClarificationForm";
import { GenerationStatus } from "./GenerationStatus";
import { SRSCompletionCard } from "./SRSCompletionCard";
import type { ChatCitation, ProjectAnalysis, ClarificationQuestionRead, SRSSchema } from "../../api/types";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";

interface AssistantMessageProps {
  content: string;
  type?: string;
  metadata?: {
    analysis?: ProjectAnalysis;
    questions?: ClarificationQuestionRead[];
    srs?: SRSSchema;
    versionId?: string;
    projectId?: string;
    citations?: ChatCitation[];
    ragEnabled?: boolean;
    warnings?: string[];
    modelName?: string;
  };
  timestamp: string;
  onSubmitClarifications?: (answers: Array<{ question_id: string; answer_text: string; skipped: boolean }>) => void | Promise<void>;
  onOpenSRS?: () => void;
}

export function AssistantMessage({
  content,
  type,
  metadata,
  onSubmitClarifications,
  onOpenSRS,
  onRegenerate,
  onEdit,
  onDelete,
}: AssistantMessageProps & {
  onRegenerate?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
  messageId?: string;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const renderContent = () => {
    switch (type) {
      case "analysis":
        return metadata?.analysis ? (
          <ProjectAnalysisCard analysis={metadata.analysis} />
        ) : (
          <MarkdownContent content={content} />
        );
      case "clarification":
        return metadata?.questions ? (
          <ClarificationForm
            questions={metadata.questions}
            onSubmit={onSubmitClarifications ?? (() => {})}
            disabled={false}
          />
        ) : (
          <MarkdownContent content={content} />
        );
      case "generation":
        return <GenerationStatus />;
      case "srs":
        return metadata?.srs ? (
          <SRSCompletionCard
            srs={metadata.srs}
            versionId={metadata.versionId || ""}
            projectId={metadata.projectId || ""}
            onOpen={onOpenSRS}
          />
        ) : (
          <MarkdownContent content={content} />
        );
      case "error":
        return (
          <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm">
            {content}
          </div>
        );
      default:
        return content ? <MarkdownContent content={content} /> : null;
    }
  };

  return (
    <div className="animate-in slide-in-left">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-[#19c37d] flex items-center justify-center mt-0.5">
          <Shield className="h-4 w-4 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          {renderContent()}
          {metadata?.citations && metadata.citations.length > 0 && (
            <div className="mt-3 rounded-lg border border-[#3f3f3f] bg-[#252525] p-3">
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-[#8e8e8e]">Sources</p>
              <ul className="space-y-1.5">
                {metadata.citations.map((citation) => (
                  <li key={`${citation.source_id}-${citation.chunk_index}`} className="text-xs text-[#b4b4b4]">
                    <span className="font-medium text-[#d1d5db]">{citation.document_title}</span>
                    {citation.page_or_section ? ` — ${citation.page_or_section}` : ""}
                    <span className="ml-1 text-[#737373]">({Math.round(citation.relevance_score * 100)}% match)</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {metadata?.warnings && metadata.warnings.length > 0 && (
            <p className="mt-2 text-xs text-amber-400">{metadata.warnings.join(" ")}</p>
          )}
          {content && (
            <div className="flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={handleCopy}
                className="p-1.5 rounded-md hover:bg-muted text-muted-foreground transition-colors"
                title="Copy"
              >
                {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
              </button>
              {onRegenerate && (
                <button
                  onClick={onRegenerate}
                  className="p-1.5 rounded-md hover:bg-muted text-muted-foreground transition-colors"
                  title="Regenerate"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                </button>
              )}
              {onEdit && (
                <button
                  onClick={onEdit}
                  className="p-1.5 rounded-md hover:bg-muted text-muted-foreground transition-colors"
                  title="Edit"
                >
                  <Edit className="h-3.5 w-3.5" />
                </button>
              )}
              {onDelete && (
                <button
                  onClick={onDelete}
                  className="p-1.5 rounded-md hover:bg-muted text-muted-foreground transition-colors"
                  title="Delete"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="prose prose-invert prose-sm max-w-none prose-p:my-1 prose-headings:my-2 prose-ul:my-1 prose-ol:my-1 prose-li:my-0">
      <Markdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => <p className="text-[15px] leading-relaxed text-[#d1d5db]">{children}</p>,
          h1: ({ children }) => <h1 className="text-xl font-semibold text-white mt-4 mb-2">{children}</h1>,
          h2: ({ children }) => <h2 className="text-lg font-semibold text-white mt-3 mb-1.5">{children}</h2>,
          h3: ({ children }) => <h3 className="text-base font-semibold text-white mt-2 mb-1">{children}</h3>,
          ul: ({ children }) => <ul className="list-disc pl-6 space-y-0.5 text-[#d1d5db]">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-6 space-y-0.5 text-[#d1d5db]">{children}</ol>,
          li: ({ children }) => <li className="text-[15px] leading-relaxed">{children}</li>,
          code: ({ className, children }) => {
            const isBlock = className?.includes("language-");
            if (isBlock && className) {
              const language = className.replace("language-", "");
              return (
                <SyntaxHighlighter
                  language={language}
                  style={atomDark}
                  className="my-2 rounded-lg"
                  customStyle={{
                    padding: "1rem",
                    fontSize: "0.875rem",
                    lineHeight: "1.5",
                    borderRadius: "0.5rem",
                    overflowX: "auto",
                  }}
                >
                  {String(children).trimEnd()}
                </SyntaxHighlighter>
              );
            }
            return (
              <code className="bg-[#2a2a2a] px-1.5 py-0.5 rounded text-sm text-[#e879f9]">{children}</code>
            );
          },
          strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
          em: ({ children }) => <em className="italic text-[#d1d5db]">{children}</em>,
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-[#19c37d] pl-3 text-[#d1d5db] italic">{children}</blockquote>
          ),
          a: ({ href, children }) => (
            <a href={href} className="text-[#19c37d] hover:underline" target="_blank" rel="noopener noreferrer">{children}</a>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-2"><table className="w-full text-sm text-left">{children}</table></div>
          ),
          thead: ({ children }) => <thead className="bg-[#2a2a2a] text-white">{children}</thead>,
          th: ({ children }) => <th className="px-3 py-2 font-medium">{children}</th>,
          td: ({ children }) => <td className="px-3 py-2 border-t border-[#333]">{children}</td>,
          hr: () => <hr className="border-[#333] my-4" />,
        }}
      >
        {content}
      </Markdown>
    </div>
  );
}

export default AssistantMessage;
