import { forwardRef } from "react";
import { cn } from "../../lib/utils";

export type CardProps = React.HTMLAttributes<HTMLDivElement>;

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-xl border bg-card text-card-foreground shadow-subtle",
        className
      )}
      {...props}
    >
      {children}
    </div>
  ),
);
Card.displayName = "Card";

export const CardHeader = forwardRef<HTMLDivElement, CardProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex flex-col space-y-1.5 p-6", className)}
      {...props}
    >
      {children}
    </div>
  ),
);
CardHeader.displayName = "CardHeader";

export const CardTitle = forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, children, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn("text-xl font-semibold leading-none tracking-tight", className)}
      {...props}
    >
      {children}
    </h3>
  ),
);
CardTitle.displayName = "CardTitle";

export const CardDescription = forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, children, ...props }, ref) => (
    <p
      ref={ref}
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    >
      {children}
    </p>
  ),
);
CardDescription.displayName = "CardDescription";

export const CardContent = forwardRef<HTMLDivElement, CardProps>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={cn("p-6 pt-0", className)} {...props}>
      {children}
    </div>
  ),
);
CardContent.displayName = "CardContent";

export const CardFooter = forwardRef<HTMLDivElement, CardProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex items-center p-6 pt-0", className)}
      {...props}
    >
      {children}
    </div>
  ),
);
CardFooter.displayName = "CardFooter";
