import { forwardRef } from "react";
import { cn } from "../../lib/utils";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
  autoResize?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, hint, autoResize = true, id, ...props }, ref) => {
    const textareaId = id || `textarea-${Math.random().toString(36).slice(2, 9)}`;
    const errorId = `${textareaId}-error`;
    const hintId = `${textareaId}-hint`;

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={textareaId}
            className="block text-sm font-medium text-foreground mb-1.5"
          >
            {label}
          </label>
        )}
        <div className="relative">
          <textarea
            ref={ref}
            id={textareaId}
            className={cn(
              "flex min-h-[100px] w-full rounded-lg border border-input bg-background px-3 py-3 text-sm",
              "placeholder:text-muted-foreground",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              "disabled:cursor-not-allowed disabled:opacity-50",
              "transition-colors duration-200 resize-none",
              error && "border-destructive focus-visible:ring-destructive",
              className
            )}
            aria-invalid={error ? "true" : "false"}
            aria-describedby={`${error ? errorId : ""} ${hint ? hintId : ""}`}
            {...props}
          />
          {autoResize && (
            <textarea
              aria-hidden="true"
              className="absolute invisible h-0 w-full pointer-events-none"
              defaultValue={props.defaultValue || props.value || ""}
              readOnly
              tabIndex={-1}
            />
          )}
        </div>
        {error && (
          <p id={errorId} className="mt-1.5 text-sm text-destructive" role="alert">
            {error}
          </p>
        )}
        {hint && !error && (
          <p id={hintId} className="mt-1.5 text-sm text-muted-foreground">
            {hint}
          </p>
        )}
      </div>
    );
  },
);
Textarea.displayName = "Textarea";