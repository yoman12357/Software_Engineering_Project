"use client";

import { useState } from "react";
import { cn } from "../../lib/utils";
import { AlertCircle, HelpCircle, CheckCircle, X } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Textarea } from "../../components/ui/Textarea";
import { Badge } from "../../components/ui/Badge";
import type { ClarificationQuestionRead } from "../../api/types";

interface ClarificationCardProps {
  question: ClarificationQuestionRead;
  value?: string;
  onChange?: (questionId: string, value: string) => void;
  onSkip?: (questionId: string) => void;
  disabled?: boolean;
  showActions?: boolean;
  compact?: boolean;
}

export function ClarificationCard({
  question,
  value = "",
  onChange,
  onSkip,
  disabled = false,
  showActions = true,
  compact = false,
}: ClarificationCardProps) {
  const [localValue, setLocalValue] = useState(value);
  const [showSkipConfirm, setShowSkipConfirm] = useState(false);

  const handleChange = (val: string) => {
    setLocalValue(val);
    onChange?.(question.id, val);
  };

  const handleSkip = () => {
    if (question.is_critical) {
      setShowSkipConfirm(true);
    } else {
      setLocalValue("");
      onChange?.(question.id, "");
      onSkip?.(question.id);
    }
  };

  if (compact) {
    return (
      <div className="p-3 rounded-lg border border-border bg-card">
        <div className="flex items-start gap-2">
          <div className="flex-shrink-0 mt-0.5">
            {question.is_critical ? (
              <span className="p-1 rounded-full bg-destructive/10 text-destructive" aria-label="Required">
                <AlertCircle className="h-3 w-3" />
              </span>
            ) : (
              <span className="p-1 rounded-full bg-muted text-muted-foreground" aria-label="Optional">
                <HelpCircle className="h-3 w-3" />
              </span>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-sm">{question.question_text}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{question.reason}</p>
          </div>
          {showActions && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSkip}
              disabled={disabled}
              className="text-muted-foreground hover:text-destructive"
              aria-label="Skip question"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 rounded-xl border border-border bg-card">
      <div className="flex items-start gap-3 mb-3">
        <div className="flex-shrink-0 mt-0.5">
          {question.is_critical ? (
            <span className="p-1.5 rounded-full bg-destructive/10 text-destructive" aria-label="Required">
              <AlertCircle className="h-4 w-4" />
            </span>
          ) : (
            <span className="p-1.5 rounded-full bg-muted text-muted-foreground" aria-label="Optional">
              <HelpCircle className="h-4 w-4" />
            </span>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium">{question.question_text}</span>
            {question.is_critical && (
              <Badge variant="destructive" size="sm">Required</Badge>
            )}
            {!question.is_critical && (
              <Badge variant="secondary" size="sm">Optional</Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground">{question.reason}</p>
        </div>
      </div>

      <Textarea
        value={localValue}
        onChange={(e) => handleChange(e.target.value)}
        placeholder={question.expected_answer_type === "number" ? "Enter a number..." : question.expected_answer_type === "boolean" ? "Yes/No" : "Your answer..."}
        disabled={disabled}
        rows={3}
        aria-label={question.question_text}
      />

      {showActions && (
        <div className="flex items-center justify-end gap-2 mt-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleSkip}
            disabled={disabled || !!localValue.trim()}
            className={cn("text-muted-foreground", !!localValue.trim() && "opacity-50")}
            aria-label="Skip question"
          >
            <X className="h-4 w-4 mr-1" />
            Skip
          </Button>
          {localValue.trim() && (
            <Button variant="outline" size="sm" disabled={disabled} className="text-success border-success hover:bg-success/5">
              <CheckCircle className="h-4 w-4 mr-1" />
              Answered
            </Button>
          )}
        </div>
      )}

      {showSkipConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowSkipConfirm(false)} role="dialog" aria-modal="true" aria-labelledby="skip-confirm-title">
          <div className="bg-card rounded-lg p-4 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 id="skip-confirm-title" className="font-semibold mb-2">Skip required question?</h3>
            <p className="text-sm text-muted-foreground mb-4">
              This question is marked as required. Skipping it may affect the quality of the generated SRS.
            </p>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={() => setShowSkipConfirm(false)}>
                Keep Answering
              </Button>
              <Button variant="destructive" size="sm" onClick={() => { setLocalValue(""); onChange?.(question.id, ""); onSkip?.(question.id); setShowSkipConfirm(false); }}>
                Skip Anyway
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ClarificationCard;