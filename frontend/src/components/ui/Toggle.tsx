"use client";

import { forwardRef } from "react";
import { cn } from "../../lib/utils";

export interface ToggleProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  pressed?: boolean;
  onPressedChange?: (pressed: boolean) => void;
  variant?: "default" | "outline";
  size?: "sm" | "md" | "lg";
}

export const Toggle = forwardRef<HTMLButtonElement, ToggleProps>(
  ({ className, pressed, onPressedChange, variant = "default", size = "md", children, ...props }, ref) => {
    const handleClick = () => {
      onPressedChange?.(!pressed);
    };

    const variants = {
      default: "bg-muted hover:bg-muted/80 data-[state=on]:bg-primary data-[state=on]:text-primary-foreground",
      outline: "border border-border bg-transparent hover:bg-muted data-[state=on]:bg-primary data-[state=on]:text-primary-foreground data-[state=on]:border-primary",
    };

    const sizes = {
      sm: "h-8 px-2.5 text-xs",
      md: "h-10 px-3 text-sm",
      lg: "h-12 px-4 text-base",
    };

    return (
      <button
        ref={ref}
        onClick={handleClick}
        aria-pressed={pressed}
        data-state={pressed ? "on" : "off"}
        className={cn(
          "inline-flex items-center justify-center font-medium rounded-lg transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:pointer-events-none disabled:opacity-50",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Toggle.displayName = "Toggle";