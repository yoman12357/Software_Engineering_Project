"use client";

import { forwardRef } from "react";
import { cn } from "../../lib/utils";

export interface ScrollAreaProps extends React.HTMLAttributes<HTMLDivElement> {
  scrollbarWidth?: "thin" | "auto" | "none";
}

export const ScrollArea = forwardRef<HTMLDivElement, ScrollAreaProps>(
  ({ className, children, scrollbarWidth = "thin", ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "overflow-auto",
          scrollbarWidth === "thin" && "scrollbar-thin",
          scrollbarWidth === "none" && "scrollbar-none",
          "scrollbar-track-transparent",
          "scrollbar-thumb-muted-foreground/30",
          "scrollbar-thumb-hover:muted-foreground/50",
          className
        )}
        {...props}
      >
        <div>
          {children}
        </div>
      </div>
    );
  },
);

ScrollArea.displayName = "ScrollArea";
