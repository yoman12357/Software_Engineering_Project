"use client";

import { Shield, Zap, FileText, Globe, Lock, Server } from "lucide-react";

interface WelcomeEmptyStateProps {
  onPromptClick?: (prompt: string) => void;
}

const suggestedPrompts = [
  {
    title: "Zero-Trust VPN",
    prompt: "I want to build a secure zero-trust VPN gateway for a mid-size company with MFA, device attestation, and audit logging.",
    icon: Lock,
  },
  {
    title: "Network Firewall",
    prompt: "Build a firewall and monitoring system for a college campus network with 500+ nodes and real-time intrusion detection.",
    icon: Shield,
  },
  {
    title: "API Security Gateway",
    prompt: "Design an API security gateway with OAuth2, rate limiting, and real-time threat detection for microservices.",
    icon: Zap,
  },
  {
    title: "SIEM Platform",
    prompt: "Create a SIEM platform for log aggregation, correlation, and incident response automation for a healthcare organization.",
    icon: FileText,
  },
  {
    title: "Cloud Security Posture",
    prompt: "Build a cloud security posture management tool for multi-cloud environments (AWS, Azure, GCP) with compliance checks.",
    icon: Globe,
  },
  {
    title: "Endpoint Protection",
    prompt: "Design an endpoint detection and response (EDR) system with behavioral analysis and automated threat containment.",
    icon: Server,
  },
];

export function WelcomeEmptyState({ onPromptClick }: WelcomeEmptyStateProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4">
      <div className="max-w-[600px] w-full space-y-8">
        {/* Logo + Title */}
        <div className="text-center space-y-3">
          <div className="mx-auto w-12 h-12 rounded-full bg-[#19c37d] flex items-center justify-center">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-2xl font-semibold text-white">CyberSRS</h1>
          <p className="text-[#8e8e8e] text-sm">
            Describe your cybersecurity project and I will generate a complete Software Requirements Specification.
          </p>
        </div>

        {/* Prompt Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {suggestedPrompts.map((prompt) => (
            <button
              key={prompt.title}
              onClick={() => onPromptClick?.(prompt.prompt)}
              className="flex items-start gap-3 p-3 rounded-xl border border-[#424242] bg-[#2f2f2f] hover:bg-[#3a3a3a] transition-colors text-left group"
            >
              <prompt.icon className="h-5 w-5 text-[#8e8e8e] mt-0.5 flex-shrink-0 group-hover:text-[#d1d5db] transition-colors" />
              <span className="text-sm text-[#d1d5db] group-hover:text-white transition-colors">
                {prompt.title}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default WelcomeEmptyState;
