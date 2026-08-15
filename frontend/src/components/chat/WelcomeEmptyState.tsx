"use client";

import { cn } from "../../lib/utils";
import { Shield, Sparkles, MessageSquare, Zap, FileText, ArrowRight } from "lucide-react";

interface WelcomeEmptyStateProps {
  onPromptClick?: (prompt: string) => void;
}

const suggestedPrompts = [
  {
    title: "Network Firewall",
    description: "Build a firewall and monitoring system for a college campus network",
    prompt: "I want to build a firewall and network-monitoring system for my college campus with 500+ nodes.",
    icon: Shield,
  },
  {
    title: "API Security Gateway",
    description: "Create an API gateway with authentication, rate limiting, and threat detection",
    prompt: "Design an API security gateway with OAuth2, rate limiting, and real-time threat detection for microservices.",
    icon: Zap,
  },
  {
    title: "SIEM Platform",
    description: "Develop a Security Information and Event Management system",
    prompt: "Create a SIEM platform for log aggregation, correlation, and incident response automation.",
    icon: FileText,
  },
  {
    title: "Zero Trust Architecture",
    description: "Implement zero trust network access with continuous verification",
    prompt: "Design a zero trust architecture with identity-based access, device trust, and micro-segmentation.",
    icon: Sparkles,
  },
];

export function WelcomeEmptyState({ onPromptClick }: WelcomeEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-4 text-center">
      <div className="max-w-2xl space-y-8">
        {/* Brand */}
        <div className="space-y-4">
          <div className="mx-auto p-4 rounded-2xl bg-primary/10 text-primary">
            <Shield className="h-12 w-12 mx-auto" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">CyberSRS</h1>
            <p className="mt-2 text-lg text-muted-foreground">
              AI-assisted Software Requirements Specification generator for cybersecurity projects
            </p>
          </div>
        </div>

        {/* Description */}
        <div className="space-y-3 p-6 rounded-xl bg-card border border-border">
          <p className="text-foreground">
            Describe your cybersecurity project in plain language. CyberSRS will analyze your requirements,
            ask clarifying questions, retrieve relevant security guidance, and generate a complete,
            structured SRS document with traceable requirements and citations.
          </p>
        </div>

        {/* Suggested prompts */}
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Try an example
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {suggestedPrompts.map(({ title, description, prompt, icon: Icon }) => (
              <button
                key={title}
                onClick={() => onPromptClick?.(prompt)}
                className={cn(
                  "relative p-4 rounded-xl border border-border bg-card",
                  "hover:border-primary/50 hover:bg-primary/5 transition-all duration-200",
                  "text-left group"
                )}
              >
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium truncate">{title}</h3>
                    <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{description}</p>
                  </div>
                </div>
                <ArrowRight className="absolute bottom-3 right-3 h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
            ))}
          </div>
        </div>

        {/* Features */}
        <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1 px-3 py-1 rounded-full bg-muted">
            <MessageSquare className="h-3 w-3" />
            Conversational
          </span>
          <span className="flex items-center gap-1 px-3 py-1 rounded-full bg-muted">
            <Sparkles className="h-3 w-3" />
            AI-powered
          </span>
          <span className="flex items-center gap-1 px-3 py-1 rounded-full bg-muted">
            <FileText className="h-3 w-3" />
            Export PDF/JSON
          </span>
          <span className="flex items-center gap-1 px-3 py-1 rounded-full bg-muted">
            <Shield className="h-3 w-3" />
            Security-focused
          </span>
        </div>
      </div>
    </div>
  );
}

export default WelcomeEmptyState;
