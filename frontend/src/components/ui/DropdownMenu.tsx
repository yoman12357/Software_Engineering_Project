"use client";

import {
  type ForwardedRef,
  type MutableRefObject,
  useState,
  useRef,
  useEffect,
  createContext,
  useContext,
  forwardRef,
} from "react";
import { createPortal } from "react-dom";
import { ChevronRight } from "lucide-react";
import { cn } from "../../lib/utils";

interface DropdownMenuContextType {
  open: boolean;
  setOpen: (open: boolean) => void;
  triggerRef: MutableRefObject<HTMLButtonElement | null>;
  contentRef: MutableRefObject<HTMLDivElement | null>;
}

const DropdownMenuContext = createContext<DropdownMenuContextType | null>(null);

function useDropdownMenu() {
  const context = useContext(DropdownMenuContext);
  if (!context) {
    throw new Error("DropdownMenu components must be used within DropdownMenu");
  }
  return context;
}

function assignForwardedRef<T>(ref: ForwardedRef<T>, value: T | null) {
  if (!ref) return;
  if (typeof ref === "function") {
    ref(value);
    return;
  }
  (ref as React.MutableRefObject<T | null>).current = value;
}

export interface DropdownMenuProps {
  children: React.ReactNode;
}

export function DropdownMenu({ children }: DropdownMenuProps) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }

    if (open) {
      document.addEventListener("keydown", handleKeyDown);
    }
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open]);

  return (
    <DropdownMenuContext.Provider value={{ open, setOpen, triggerRef, contentRef }}>
      <div className="relative inline-block">{children}</div>
    </DropdownMenuContext.Provider>
  );
}

export type DropdownMenuTriggerProps = React.ButtonHTMLAttributes<HTMLButtonElement>;

export const DropdownMenuTrigger = forwardRef<HTMLButtonElement, DropdownMenuTriggerProps>(
  ({ className, children, ...props }, ref) => {
    const { open, setOpen, triggerRef } = useDropdownMenu();

    return (
      <button
        ref={(el) => {
          triggerRef.current = el;
          assignForwardedRef(ref, el);
        }}
        onClick={() => setOpen(!open)}
        aria-haspopup="true"
        aria-expanded={open}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium",
          "bg-transparent hover:bg-muted transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);
DropdownMenuTrigger.displayName = "DropdownMenuTrigger";

export interface DropdownMenuContentProps extends React.HTMLAttributes<HTMLDivElement> {
  align?: "start" | "end";
  sideOffset?: number;
}

export const DropdownMenuContent = forwardRef<HTMLDivElement, DropdownMenuContentProps>(
  ({ className, children, align = "start", sideOffset = 4, ...props }, ref) => {
    const { open, triggerRef, contentRef } = useDropdownMenu();

    useEffect(() => {
      if (!open || !triggerRef.current || !contentRef.current) return;

      const triggerRect = triggerRef.current.getBoundingClientRect();
      const contentRect = contentRef.current.getBoundingClientRect();
      const viewportWidth = window.innerWidth;

      let left = align === "start" ? triggerRect.left : triggerRect.right - contentRect.width;
      const top = triggerRect.bottom + sideOffset;

      if (left + contentRect.width > viewportWidth - 8) {
        left = viewportWidth - contentRect.width - 8;
      }
      if (left < 8) {
        left = 8;
      }

      contentRef.current.style.left = `${left}px`;
      contentRef.current.style.top = `${top}px`;
    }, [open, align, sideOffset, contentRef, triggerRef]);

    if (!open) return null;

    return createPortal(
      <div
        ref={(el) => {
          contentRef.current = el;
          assignForwardedRef(ref, el);
        }}
        className={cn(
          "fixed z-50 min-w-[200px] rounded-lg border border-border bg-card",
          "shadow-elevated animate-in fade-in-100 zoom-in-95",
          "overflow-hidden",
          className
        )}
        role="menu"
        {...props}
      >
        <div className="p-1">{children}</div>
      </div>,
      document.body
    );
  }
);
DropdownMenuContent.displayName = "DropdownMenuContent";

export interface DropdownMenuItemProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  inset?: boolean;
  disabled?: boolean;
  onSelect?: () => void;
}

export const DropdownMenuItem = forwardRef<HTMLButtonElement, DropdownMenuItemProps>(
  ({ className, inset, disabled, onSelect, children, ...props }, ref) => {
    const { setOpen } = useDropdownMenu();

    return (
      <button
        ref={ref}
        onClick={() => {
          if (!disabled) {
            onSelect?.();
            setOpen(false);
          }
        }}
        disabled={disabled}
        role="menuitem"
        className={cn(
          "relative flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm",
          "hover:bg-muted focus:outline-none focus:bg-muted",
          "disabled:pointer-events-none disabled:opacity-50",
          inset && "pl-8",
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);
DropdownMenuItem.displayName = "DropdownMenuItem";

export type DropdownMenuSeparatorProps = React.HTMLAttributes<HTMLDivElement>;

export function DropdownMenuSeparator({ className, ...props }: DropdownMenuSeparatorProps) {
  return (
    <div
      className={cn("h-px bg-border my-1", className)}
      role="separator"
      {...props}
    />
  );
}

export interface DropdownMenuLabelProps extends React.HTMLAttributes<HTMLDivElement> {
  inset?: boolean;
}

export function DropdownMenuLabel({ className, inset, children, ...props }: DropdownMenuLabelProps) {
  return (
    <div
      className={cn("px-3 py-1.5 text-xs font-semibold text-muted-foreground", inset && "pl-8", className)}
      {...props}
    >
      {children}
    </div>
  );
}

export type DropdownMenuGroupProps = React.HTMLAttributes<HTMLDivElement>;

export function DropdownMenuGroup({ className, children, ...props }: DropdownMenuGroupProps) {
  return <div className={cn("p-1", className)} {...props}>{children}</div>;
}

export interface DropdownMenuSubProps {
  children: React.ReactNode;
}

export function DropdownMenuSub({ children }: DropdownMenuSubProps) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    function handleMouseLeave(e: MouseEvent) {
      if (!contentRef.current?.contains(e.relatedTarget as Node)) {
        setOpen(false);
      }
    }

    const content = contentRef.current;
    content?.addEventListener("mouseleave", handleMouseLeave);
    return () => content?.removeEventListener("mouseleave", handleMouseLeave);
  }, [open]);

  return (
    <div className="relative" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <DropdownMenuSubTrigger ref={triggerRef} open={open} onClick={() => setOpen(!open)}>
        {children}
      </DropdownMenuSubTrigger>
      {open && <DropdownMenuSubContent ref={contentRef} />}
    </div>
  );
}

interface DropdownMenuSubTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  open: boolean;
}

const DropdownMenuSubTrigger = forwardRef<HTMLButtonElement, DropdownMenuSubTriggerProps>(
  ({ className, open, children, ...props }, ref) => (
    <button
      ref={ref}
      aria-haspopup="true"
      aria-expanded={open}
      className={cn(
        "flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm",
        "hover:bg-muted focus:outline-none focus:bg-muted",
        className
      )}
      {...props}
    >
      {children}
      <ChevronRight className="ml-auto h-4 w-4" />
    </button>
  )
);

type DropdownMenuSubContentProps = React.HTMLAttributes<HTMLDivElement>;

const DropdownMenuSubContent = forwardRef<HTMLDivElement, DropdownMenuSubContentProps>(
  ({ className, children, ...props }, ref) =>
    createPortal(
      <div
        ref={ref}
        className={cn(
          "fixed z-50 min-w-[180px] rounded-lg border border-border bg-card",
          "shadow-elevated animate-in fade-in-100 zoom-in-95",
          "p-1 overflow-hidden",
          className
        )}
        {...props}
      >
        {children}
      </div>,
      document.body
    )
);
