"use client";

import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { createPortal } from "react-dom";
import { cn } from "../../lib/utils";

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
  title?: string;
  description?: string;
}

export function Dialog({ open, onOpenChange, children, title, description }: DialogProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onOpenChange(false);
    };

    if (open) {
      document.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [open, onOpenChange]);

  if (!open) return null;

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onOpenChange(false);
  };

  const content = (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? "dialog-title" : undefined}
      aria-describedby={description ? "dialog-description" : undefined}
    >
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in"
        aria-hidden="true"
      />
      <div
        ref={contentRef}
        className="relative z-50 w-full max-w-lg rounded-xl bg-card p-6 shadow-elevated animate-in scale-in fade-in slide-up"
        role="document"
      >
        {(title || description) && (
          <div className="mb-4">
            {title && (
              <h2 id="dialog-title" className="text-lg font-semibold">
                {title}
              </h2>
            )}
            {description && (
              <p id="dialog-description" className="text-sm text-muted-foreground mt-1">
                {description}
              </p>
            )}
          </div>
        )}
        <div className="pr-8">{children}</div>
        <button
          onClick={() => onOpenChange(false)}
          className="absolute top-4 right-4 p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          aria-label="Close dialog"
        >
          <X className="h-5 w-5" />
        </button>
      </div>
    </div>
  );

  return createPortal(content, document.body);
}

interface DialogTriggerProps {
  children: React.ReactElement;
}

export function DialogTrigger({ children }: DialogTriggerProps) {
  return children;
}

interface DialogContentProps {
  children: React.ReactNode;
  className?: string;
}

export function DialogContent({ children, className }: DialogContentProps) {
  return <div className={cn("flex flex-col gap-4", className)}>{children}</div>;
}

interface DialogHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export function DialogHeader({ children, className }: DialogHeaderProps) {
  return <div className={cn("flex flex-col space-y-1.5", className)}>{children}</div>;
}

interface DialogTitleProps {
  children: React.ReactNode;
  className?: string;
}

export function DialogTitle({ children, className }: DialogTitleProps) {
  return <h2 className={cn("text-lg font-semibold", className)}>{children}</h2>;
}

interface DialogDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

export function DialogDescription({ children, className }: DialogDescriptionProps) {
  return <p className={cn("text-sm text-muted-foreground", className)}>{children}</p>;
}

interface DialogFooterProps {
  children: React.ReactNode;
  className?: string;
}

export function DialogFooter({ children, className }: DialogFooterProps) {
  return (
    <div className={cn("flex items-center justify-end gap-2 mt-4", className)}>
      {children}
    </div>
  );
}
