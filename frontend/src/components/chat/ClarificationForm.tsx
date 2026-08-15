"use client";

import { useState, FormEvent } from "react";
import { AlertCircle, CheckCircle, HelpCircle } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Textarea } from "../../components/ui/Textarea";
import { Badge } from "../../components/ui/Badge";
import { Skeleton } from "../../components/ui/Skeleton";
import type { ClarificationQuestionRead } from "../../api/types";

interface ClarificationFormProps {
  questions: ClarificationQuestionRead[];
  onSubmit: (answers: Array<{ question_id: string; answer_text: string; skipped: boolean }>) => void | Promise<void>;
  disabled?: boolean;
  isLoading?: boolean;
}

export function ClarificationForm({
  questions,
  onSubmit,
  disabled = false,
  isLoading = false,
}: ClarificationFormProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const updateAnswer = (questionId: string, value: string) => {
    setAnswers((current) => ({ ...current, [questionId]: value }));
    if (errors[questionId]) {
      setErrors((current) => {
        const next = { ...current };
        delete next[questionId];
        return next;
      });
    }
  };

  const validateAnswers = () => {
    const newErrors: Record<string, string> = {};
    questions.forEach((q) => {
      if (q.is_critical && !(answers[q.id] ?? "").trim()) {
        newErrors[q.id] = "This question is required";
      }
    });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!validateAnswers()) return;

    setSubmitting(true);
    try {
      const payload = questions.map((question) => {
        const text = (answers[question.id] ?? "").trim();
        return {
          question_id: question.id,
          answer_text: text,
          skipped: text.length === 0,
        };
      });
      await onSubmit(payload);
    } catch {
      // Error handled by parent
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4" role="status" aria-label="Loading clarification questions">
        {questions.slice(0, 3).map((q, i) => (
          <div key={q.id || i} className="space-y-2 p-4 rounded-xl border border-border bg-card">
            <Skeleton variant="text" width="80%" />
            <Skeleton variant="rectangular" height={80} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" role="form" aria-label="Clarification questions">
      <div className="flex items-center gap-2 mb-4">
        <HelpCircle className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-semibold">Clarification Questions</h2>
      </div>
      <p className="text-sm text-muted-foreground">
        Answer the questions below to help the system build a more accurate specification.
        <span className="font-medium">Required</span> questions must be answered; others may be skipped.
      </p>

      {questions.map((question) => (
        <div key={question.id} className="p-4 rounded-xl border border-border bg-card">
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
              <label htmlFor={`answer-${question.id}`} className="block">
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
              </label>
            </div>
          </div>

          <Textarea
            id={`answer-${question.id}`}
            value={answers[question.id] ?? ""}
            onChange={(e) => updateAnswer(question.id, e.target.value)}
            placeholder={question.expected_answer_type === "number" ? "Enter a number..." : question.expected_answer_type === "boolean" ? "Yes/No" : "Your answer..."}
            disabled={disabled || submitting}
            rows={3}
            error={errors[question.id]}
            aria-describedby={question.reason ? `${question.id}-reason` : undefined}
            aria-invalid={!!errors[question.id]}
          />
        </div>
      ))}

      <div className="flex justify-end gap-3 pt-4 border-t border-border">
        <Button
          type="button"
          variant="ghost"
          onClick={() => onSubmit(questions.map(q => ({ question_id: q.id, answer_text: "", skipped: true })))}
          disabled={disabled || submitting}
        >
          Skip All
        </Button>
        <Button
          type="submit"
          disabled={disabled || submitting}
          loading={submitting}
        >
          {submitting ? "Submitting answers…" : "Submit Answers"}
          <CheckCircle className="h-4 w-4" />
        </Button>
      </div>
    </form>
  );
}

export default ClarificationForm;
