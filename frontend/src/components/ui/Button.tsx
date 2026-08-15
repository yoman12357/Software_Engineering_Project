import { forwardRef } from "react";
import { cn } from "../../lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "destructive";
  size?: "sm" | "md" | "lg" | "icon";
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", loading, disabled, children, ...props }, ref) => {
    const baseStyles = "inline-flex items-center justify-center font-medium transition-all duration-200 rounded-lg focus-ring disabled:opacity-50 disabled:cursor-not-allowed";

    const variants = {
      primary: "bg-primary text-primary-foreground hover:bg-primary-hover shadow-sm",
      secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
      outline: "border border-border bg-transparent hover:bg-muted",
      ghost: "hover:bg-muted",
      destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
    };

    const sizes = {
      sm: "h-8 px-3 text-sm gap-1.5",
      md: "h-10 px-4 text-sm gap-2",
      lg: "h-12 px-6 text-base gap-2",
      icon: "h-10 w-10",
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled || loading}
        aria-busy={loading}
        {...props}
      >
        {loading ? (
          <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" aria-hidden="true">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        ) : (
          children
        )}
      </button>
    );
  },
);

Button.displayName = "Button";