"use client";

import { useState } from "react";
import { forwardRef } from "react";
import { cn } from "../../lib/utils";

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string;
  alt?: string;
  fallback?: string;
  size?: "sm" | "md" | "lg" | "xl";
}

export const Avatar = forwardRef<HTMLDivElement, AvatarProps>(
  ({ className, src, alt, fallback, size = "md", ...props }, ref) => {
    const sizes = {
      sm: "h-8 w-8 text-xs",
      md: "h-10 w-10 text-sm",
      lg: "h-12 w-12 text-base",
      xl: "h-16 w-16 text-lg",
    };

    const [showFallback, setShowFallback] = useState(false);

    if (!src || showFallback) {
      return (
        <div
          ref={ref}
          className={cn(
            "inline-flex items-center justify-center rounded-full bg-muted font-medium",
            sizes[size],
            className
          )}
          {...props}
        >
          {fallback || alt?.charAt(0).toUpperCase() || "?"}
        </div>
      );
    }

    return (
      <div
        ref={ref}
        className={cn("inline-flex items-center justify-center rounded-full overflow-hidden", sizes[size], className)}
        {...props}
      >
        <img
          src={src}
          alt={alt || ""}
          onError={() => setShowFallback(true)}
          className="w-full h-full object-cover"
        />
      </div>
    );
  }
);

Avatar.displayName = "Avatar";