import { cn } from "../../lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "destructive" | "success" | "warning" | "outline";
  size?: "sm" | "md" | "lg";
}

export function Badge({
  className,
  variant = "default",
  size = "md",
  children,
  ...props
}: BadgeProps) {
  const variants = {
    default: "bg-primary text-primary-foreground",
    secondary: "bg-secondary text-secondary-foreground",
    destructive: "bg-destructive text-destructive-foreground",
    success: "bg-success text-success-foreground",
    warning: "bg-warning text-warning-foreground",
    outline: "border border-border bg-transparent",
  };

  const sizes = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-xs",
    lg: "px-3 py-1 text-sm",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center font-medium rounded-full transition-colors",
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}

export function PriorityBadge({ priority }: { priority: "must" | "should" | "could" }) {
  const variants = {
    must: "bg-destructive/10 text-destructive border-destructive/20",
    should: "bg-warning/10 text-warning border-warning/20",
    could: "bg-muted text-muted-foreground border-border",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border",
        variants[priority]
      )}
    >
      {priority}
    </span>
  );
}

export function CategoryBadge({ category }: { category: string }) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-soft-blue text-primary border border-primary/20">
      {category}
    </span>
  );
}

export function ConfidenceBadge({ confidence }: { confidence: "high" | "medium" | "low" }) {
  const variants = {
    high: "bg-success/10 text-success border-success/20",
    medium: "bg-warning/10 text-warning border-warning/20",
    low: "bg-muted text-muted-foreground border-border",
  };

  return (
    <span className={cn("inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border", variants[confidence])}>
      {confidence}
    </span>
  );
}
