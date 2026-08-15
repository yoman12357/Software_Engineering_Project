"use client";

import { cn } from "../../lib/utils";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
}

export function Skeleton({
  className,
  variant = "text",
  width,
  height,
  ...props
}: SkeletonProps) {
  const variants = {
    text: "h-4 rounded",
    circular: "rounded-full",
    rectangular: "rounded-lg",
  };

  return (
    <div
      className={cn(
        "animate-pulse bg-muted",
        variants[variant],
        className
      )}
      style={{
        width: width ? (typeof width === "number" ? `${width}px` : width) : undefined,
        height: height ? (typeof height === "number" ? `${height}px` : height) : undefined,
      }}
      {...props}
    />
  );
}

export function SkeletonText({ lines = 3, className, ...props }: { lines?: number; className?: string }) {
  return (
    <div className={cn("space-y-2", className)} {...props}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} variant="text" width={i === lines - 1 ? "60%" : "100%"} />
      ))}
    </div>
  );
}

export function SkeletonCard({ className, ...props }: { className?: string }) {
  return (
    <div className={cn("rounded-xl border bg-card p-4 space-y-4", className)} {...props}>
      <div className="flex items-center gap-4">
        <Skeleton variant="circular" width={40} height={40} />
        <div className="space-y-2 flex-1">
          <Skeleton variant="text" width="40%" />
          <Skeleton variant="text" width="30%" />
        </div>
      </div>
      <Skeleton variant="rectangular" height={100} />
      <div className="flex gap-2">
        <Skeleton variant="text" width="80px" />
        <Skeleton variant="text" width="80px" />
        <Skeleton variant="text" width="80px" />
      </div>
    </div>
  );
}

export function SkeletonChatMessage({ className, ...props }: { className?: string }) {
  return (
    <div className={cn("flex gap-3 animate-in slide-up", className)} {...props}>
      <Skeleton variant="circular" width={32} height={32} className="flex-shrink-0 mt-1" />
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <Skeleton variant="text" width="80px" height={20} />
          <Skeleton variant="text" width="60px" height={16} />
        </div>
        <SkeletonText lines={3} />
      </div>
    </div>
  );
}