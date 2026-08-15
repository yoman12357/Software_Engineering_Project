import type { ReactNode } from "react";

interface ErrorStateProps {
  message: string;
  details?: unknown;
  onRetry?: () => void;
  children?: ReactNode;
}

export function ErrorState({ message, details, onRetry, children }: ErrorStateProps) {
  return (
    <div className="error-box" role="alert">
      <strong>{message}</strong>
      {details !== undefined ? <p>{String(details)}</p> : null}
      {children}
      {onRetry ? (
        <p style={{ marginBottom: 0 }}>
          <button type="button" onClick={onRetry}>
            Retry
          </button>
        </p>
      ) : null}
    </div>
  );
}