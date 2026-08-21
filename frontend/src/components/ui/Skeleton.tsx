"use client";

import { cn } from "../../lib/utils";

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  variant?: "text" | "circular" | "rectangular";
}

export function Skeleton({ className, width, height, variant = "text" }: SkeletonProps) {
  const baseStyles = "animate-pulse bg-gradient-to-r from-[#2a2a2a] via-[#333333] to-[#2a2a2a] bg-[length:200%_100%] rounded";

  const variantStyles = {
    text: "rounded",
    circular: "rounded-full",
    rectangular: "rounded-lg",
  };

  const widthStyle = width ? { width: typeof width === "number" ? `${width}px` : width } : {};
  const heightStyle = height ? { height: typeof height === "number" ? `${height}px` : height } : {};

  return (
    <div
      className={cn(baseStyles, variantStyles[variant], className)}
      style={{ ...widthStyle, ...heightStyle }}
    />
  );
}

export function MessageSkeleton({ isUser = false }: { isUser?: boolean }) {
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} animate-in slide-in-${isUser ? "right" : "left"}`}>
      <div className="max-w-[70%] flex items-start gap-3">
        {isUser ? (
          <div className="flex flex-col items-end flex-1">
            <div className="bg-[#2f2f2f] text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm">
              <Skeleton className="h-4 w-3/4" variant="text" />
              <Skeleton className="h-4 w-1/2 mt-2" variant="text" />
              <Skeleton className="h-4 w-1/2 mt-2" variant="text" />
            </div>
          </div>
        ) : (
          <>
            <div className="flex-shrink-0 w-7 h-7 rounded-full bg-[#19c37d] flex items-center justify-center mt-0.5">
              <div className="h-4 w-4 rounded-full bg-[#19c37d]/20 animate-pulse" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="bg-[#2f2f2f] text-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                <Skeleton className="h-4 w-3/4" variant="text" />
                <Skeleton className="h-4 w-1/2 mt-2" variant="text" />
                <Skeleton className="h-4 w-1/2 mt-2" variant="text" />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export function SkeletonLoader({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-6">
      {Array.from({ length: count }).map((_, i) => (
        <MessageSkeleton key={i} isUser={i % 2 === 0} />
      ))}
    </div>
  );
}

function StatCardSkeleton() {
  return (
    <div className="bg-[#171717] border border-white/10 rounded-xl p-6">
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-4 w-24" variant="text" />
          <Skeleton className="h-8 w-16 mt-2" variant="text" />
        </div>
        <div className="p-3 rounded-xl bg-[#19c37d]/10">
          <Skeleton className="h-6 w-6" variant="circular" />
        </div>
      </div>
    </div>
  );
}

function RecentSessionsSkeleton() {
  return (
    <div className="lg:col-span-2 bg-[#171717] border border-white/10 rounded-xl overflow-hidden">
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <Skeleton className="h-5 w-24" variant="text" />
      </div>
      <div className="divide-y divide-white/10">
        {[1, 2, 3].map((i) => (
          <div key={i} className="p-4 hover:bg-white/5 transition-colors flex items-center justify-between border-b border-white/5">
            <div className="flex items-center gap-3">
              <Skeleton className="h-5 w-5" variant="circular" />
              <div>
                <Skeleton className="h-5 w-32" variant="text" />
                <Skeleton className="h-3 w-24 mt-1" variant="text" />
              </div>
            </div>
            <Skeleton className="h-5 w-20" variant="text" />
          </div>
        ))}
      </div>
    </div>
  );
}

function ProjectsListSkeleton() {
  return (
    <div className="bg-[#171717] border border-white/10 rounded-xl overflow-hidden">
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <Skeleton className="h-5 w-24" variant="text" />
      </div>
      <div className="divide-y divide-white/5">
        {[1, 2, 3].map((i) => (
          <div key={i} className="p-4 hover:bg-white/5 transition-colors flex items-center justify-between border-b border-white/5">
            <div className="flex items-center gap-3">
              <Skeleton className="h-5 w-5" variant="circular" />
              <div>
                <Skeleton className="h-5 w-32" variant="text" />
                <Skeleton className="h-3 w-24 mt-1" variant="text" />
              </div>
            </div>
            <Skeleton className="h-5 w-20" variant="text" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="h-full flex flex-col bg-[#212121]">
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center gap-4">
          <Skeleton className="h-6 w-6 rounded-xl bg-[#19c37d]/10" variant="circular" />
          <div>
            <Skeleton className="h-6 w-32" variant="text" />
            <Skeleton className="h-4 w-48 mt-2" variant="text" />
          </div>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-6">
        {[1, 2, 3, 4].map((i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>
      <div className="flex-1 p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <RecentSessionsSkeleton />
          <ProjectsListSkeleton />
        </div>
      </div>
    </div>
  );
}

export default Skeleton;