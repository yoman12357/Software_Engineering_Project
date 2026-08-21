"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { createPortal } from "react-dom";
import { cn } from "../../lib/utils";
import { Button } from "../../components/ui/Button";
import { ArrowRight, X, Check, ArrowLeft } from "lucide-react";

interface TourStep {
  id: string;
  title: string;
  content: React.ReactNode;
  target?: string;
  position?: "top" | "bottom" | "left" | "right" | "center";
  action?: () => void;
}

interface TourProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: () => void;
}

const DEFAULT_STEPS: TourStep[] = [
  {
    id: "welcome",
    title: "Welcome to CyberSRS",
    content: (
      <div className="space-y-4">
        <p className="text-lg">Welcome to CyberSRS! This quick tour will show you the key features.</p>
        <p className="text-sm text-muted-foreground">CyberSRS helps you generate professional Software Requirements Specifications for cybersecurity projects using AI.</p>
      </div>
    ),
    position: "center",
  },
  {
    id: "sidebar",
    title: "Navigation Sidebar",
    content: (
      <div className="space-y-4">
        <p className="text-lg">The sidebar on the left is your main navigation.</p>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li>• <strong>New Chat</strong> - Start a fresh conversation</li>
          <li>• <strong>Chat History</strong> - Browse and resume previous sessions</li>
          <li>• <strong>Search</strong> - Filter conversations</li>
        </ul>
      </div>
    ),
    target: "[data-tour-sidebar]",
    position: "right",
  },
  {
    id: "chat",
    title: "Chat Interface",
    content: (
      <div className="space-y-4">
        <p className="text-lg">The main chat area is where you interact with CyberSRS.</p>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li>• Type your project description to start</li>
          <li>• CyberSRS will ask clarifying questions</li>
          <li>• Generate a complete SRS document</li>
        </ul>
      </div>
    ),
    target: "[data-tour-chat]",
    position: "top",
  },
  {
    id: "composer",
    title: "Message Composer",
    content: (
      <div className="space-y-4">
        <p className="text-lg">Use the composer at the bottom to send messages.</p>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li>• Type your project description or questions</li>
          <li>• Press <kbd className="px-1.5 py-0.5 bg-muted rounded text-xs">Enter</kbd> to send</li>
          <li>• Press <kbd className="px-1.5 py-0.5 bg-muted rounded text-xs">Ctrl+Enter</kbd> for new line</li>
        </ul>
      </div>
    ),
    target: "[data-tour-composer]",
    position: "top",
  },
  {
    id: "shortcuts",
    title: "Keyboard Shortcuts",
    content: (
      <div className="space-y-4">
        <p className="text-lg">Boost your productivity with keyboard shortcuts:</p>
        <div className="grid gap-2 text-sm">
          <div className="flex items-center gap-3 p-2 bg-muted/50 rounded">
            <kbd className="px-2 py-1 bg-muted rounded border border-border text-xs font-mono">Ctrl+N</kbd>
            <span className="text-muted-foreground">New Chat</span>
          </div>
          <div className="flex items-center gap-3 p-2 bg-muted/50 rounded">
            <kbd className="px-2 py-1 bg-muted rounded border border-border text-xs font-mono">Ctrl+K</kbd>
            <span className="text-muted-foreground">Focus chat search</span>
          </div>
          <div className="flex items-center gap-3 p-2 bg-muted/50 rounded">
            <kbd className="px-2 py-1 bg-muted rounded border border-border text-xs font-mono">Ctrl+E</kbd>
            <span className="text-muted-foreground">Export the open SRS as PDF</span>
          </div>
          <div className="flex items-center gap-3 p-2 bg-muted/50 rounded">
            <kbd className="px-2 py-1 bg-muted rounded border border-border text-xs font-mono">Esc</kbd>
            <span className="text-muted-foreground">Close dialogs / Cancel</span>
          </div>
        </div>
      </div>
    ),
    position: "center",
  },
  {
    id: "srs",
    title: "SRS Workspace",
    content: (
      <div className="space-y-4">
        <p className="text-lg">After generating an SRS, you can view and edit it in the SRS Workspace.</p>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li>• View functional, security, and non-functional requirements</li>
          <li>• Edit requirements inline</li>
          <li>• Export to PDF</li>
          <li>• View source citations and provenance</li>
        </ul>
      </div>
    ),
    target: "[data-tour-srs]",
    position: "left",
  },
  {
    id: "settings",
    title: "Settings",
    content: (
      <div className="space-y-4">
        <p className="text-lg">Customize your experience in Settings:</p>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li>• <strong>Theme</strong> - Light, Dark, or System</li>
          <li>• <strong>Appearance</strong> - Compact mode, animations</li>
          <li>• <strong>AI Runtime</strong> - Local Ollama configuration</li>
        </ul>
      </div>
    ),
    target: "[data-tour-settings]",
    position: "left",
  },
  {
    id: "complete",
    title: "You're Ready!",
    content: (
      <div className="space-y-4 text-center">
        <div className="mx-auto p-4 rounded-full bg-green-500/10 text-green-500">
          <svg className="mx-auto h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <p className="text-lg font-medium">You're all set! Start by describing your cybersecurity project.</p>
        <p className="text-sm text-muted-foreground">Type a project description in the chat to begin.</p>
      </div>
    ),
    position: "center",
  },
];

interface TourProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: () => void;
}

export function Tour({ isOpen, onClose, onComplete }: TourProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const steps = DEFAULT_STEPS;

  const updateTargetRect = useCallback(() => {
    if (currentStep < steps.length && steps[currentStep].target) {
      const target = document.querySelector(steps[currentStep].target!);
      if (target) {
        setTargetRect(target.getBoundingClientRect());
      } else {
        setTargetRect(null);
      }
    } else {
      setTargetRect(null);
    }
  }, [currentStep, steps]);

  useEffect(() => {
    updateTargetRect();
    window.addEventListener("resize", updateTargetRect);
    window.addEventListener("scroll", updateTargetRect, true);
    return () => {
      window.removeEventListener("resize", updateTargetRect);
      window.removeEventListener("scroll", updateTargetRect, true);
    };
  }, [updateTargetRect]);

  useEffect(() => {
    if (currentStep < steps.length && steps[currentStep].action) {
      steps[currentStep].action!();
    }
    updateTargetRect();
  }, [currentStep, steps, updateTargetRect]);

  useEffect(() => {
    if (!isOpen) {
      setCurrentStep(0);
      return;
    }
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  if (!isOpen) return null;

  const current = steps[currentStep];

  const renderTargetHighlight = () => {
    if (!targetRect || !current.target) return null;
    return (
      <div
        className="fixed pointer-events-none z-40"
        style={{
          top: targetRect.top - 8,
          left: targetRect.left - 8,
          width: targetRect.width + 16,
          height: targetRect.height + 16,
        }}
      >
        <div
          className="absolute inset-0 rounded-lg border-2 border-primary/50 bg-primary/5 animate-pulse"
          style={{
            top: -8,
            left: -8,
            width: `calc(100% + 16px)`,
            height: `calc(100% + 16px)`,
          }}
        />
      </div>
    );
  };

  const renderTooltip = () => {
    if (!targetRect) return null;

    const tooltipStyle: React.CSSProperties = {
      top: targetRect.bottom + 12,
      left: targetRect.left + targetRect.width / 2,
      transform: "translateX(-50%)",
    };

    return (
      <div
        ref={tooltipRef}
        className="fixed z-50 max-w-md w-full pointer-events-auto animate-in slide-in-from-bottom-4"
        style={tooltipStyle}
      >
        <div className="bg-card border border-border rounded-xl shadow-elevated p-6 max-w-md w-full">
          {/* Progress indicator */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              {steps.map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    "h-1.5 w-8 rounded-full transition-colors",
                    i <= currentStep ? "bg-primary" : "bg-muted"
                  )}
                />
              ))}
            </div>
            <span className="text-xs text-muted-foreground">
              Step {currentStep + 1} of {steps.length}
            </span>
          </div>

          {/* Content */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">{current.title}</h3>
            <div className="text-muted-foreground">{current.content}</div>
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between pt-4 border-t border-border">
            <Button
              variant="ghost"
              size="sm"
              onClick={prevStep}
              disabled={currentStep === 0}
            >
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back
            </Button>
            <div className="flex items-center gap-2">
              {currentStep < steps.length - 1 ? (
                <Button size="sm" onClick={() => setCurrentStep(currentStep + 1)}>
                  Next
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Button>
              ) : (
                <Button size="sm" onClick={() => { onComplete?.(); onClose(); }}>
                  <Check className="h-4 w-4 mr-1" />
                  Get Started
                </Button>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCurrentStep(0)}
              className="ml-auto"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    );
  };

  if (!isOpen) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 animate-in fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Target highlight */}
      {renderTargetHighlight()}

      {/* Tooltip */}
      {renderTooltip()}
    </div>,
    document.body
  );
}

export default Tour;
