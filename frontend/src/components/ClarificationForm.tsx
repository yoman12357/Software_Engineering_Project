import { useState, type FormEvent } from "react";
import type { ClarificationQuestionRead } from "../api/types";

interface ClarificationFormProps {
  questions: ClarificationQuestionRead[];
  disabled?: boolean;
  onSubmit: (answers: Array<{ question_id: string; answer_text: string; skipped: boolean }>) => void | Promise<void>;
}

export function ClarificationForm({
  questions,
  disabled = false,
  onSubmit,
}: ClarificationFormProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateAnswer(questionId: string, value: string) {
    setAnswers((current) => ({ ...current, [questionId]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    // Validate that all critical questions have an answer.
    const missingCritical = questions.some(
      (q) => q.is_critical && !(answers[q.id] ?? "").trim(),
    );
    if (missingCritical) {
      setError("Please answer all required (critical) questions before continuing.");
      return;
    }

    setError(null);
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit answers.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card">
      <h2>Clarification Questions</h2>
      <p>
        Answer the questions below to help the system build a more accurate
        specification. Critical questions are required; others may be skipped.
      </p>

      {questions.map((question) => (
        <div key={question.id} style={{ marginBottom: "1rem" }}>
          <label htmlFor={`answer-${question.id}`}>
            {question.question_text}
            {question.is_critical ? (
              <span className="badge must">Required</span>
            ) : (
              <span className="badge could">Optional</span>
            )}
          </label>
          <textarea
            id={`answer-${question.id}`}
            value={answers[question.id] ?? ""}
            onChange={(event) => updateAnswer(question.id, event.target.value)}
            disabled={disabled || submitting}
            placeholder={question.reason}
          />
        </div>
      ))}

      {error ? <p className="error-note">{error}</p> : null}

      <button type="submit" className="primary" disabled={disabled || submitting}>
        {submitting ? "Submitting answers…" : "Submit answers"}
      </button>
    </form>
  );
}