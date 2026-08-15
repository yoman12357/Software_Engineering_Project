"use client";

import { forwardRef } from "react";
import { cn } from "../../lib/utils";

interface TabsProps {
  value: string;
  onValueChange: (value: string) => void;
  children: React.ReactNode;
  className?: string;
  defaultValue?: string;
  orientation?: "horizontal" | "vertical";
}

export const Tabs = forwardRef<HTMLDivElement, TabsProps>(
  ({ className, children, value, onValueChange, defaultValue, orientation = "horizontal", ...props }, ref) => {
    const [activeValue, setActiveValue] = useState(value || defaultValue || "");

    const handleValueChange = (newValue: string) => {
      setActiveValue(newValue);
      onValueChange?.(newValue);
    };

    return (
      <div ref={ref} className={cn("flex", orientation === "vertical" ? "flex-col" : "flex-row", className)} {...props}>
        <TabsContext.Provider value={{ activeValue, onValueChange: handleValueChange, orientation }}>
          {children}
        </TabsContext.Provider>
      </div>
    );
  },
);

Tabs.displayName = "Tabs";

import { useState, createContext, useContext } from "react";

const TabsContext = createContext<{
  activeValue: string;
  onValueChange: (value: string) => void;
  orientation: "horizontal" | "vertical";
} | null>(null);

function useTabs() {
  const context = useContext(TabsContext);
  if (!context) {
    throw new Error("Tabs components must be used within Tabs");
  }
  return context;
}

type TabsListProps = React.HTMLAttributes<HTMLDivElement>;

export const TabsList = forwardRef<HTMLDivElement, TabsListProps>(
  ({ className, children, ...props }, ref) => {
    const { orientation } = useTabs();
    return (
      <div
        ref={ref}
        role="tablist"
        aria-orientation={orientation}
        className={cn(
          "inline-flex items-center justify-center gap-1 p-1 bg-muted/50 rounded-xl",
          orientation === "vertical" ? "flex-col" : "flex-row",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  },
);
TabsList.displayName = "TabsList";

interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
  disabled?: boolean;
}

export const TabsTrigger = forwardRef<HTMLButtonElement, TabsTriggerProps>(
  ({ className, value, disabled, children, ...props }, ref) => {
    const { activeValue, onValueChange, orientation } = useTabs();

    return (
      <button
        ref={ref}
        role="tab"
        aria-selected={activeValue === value}
        aria-disabled={disabled}
        data-state={activeValue === value ? "active" : "inactive"}
        data-orientation={orientation}
        onClick={() => !disabled && onValueChange(value)}
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-md font-medium transition-all duration-200",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:pointer-events-none disabled:opacity-50",
          "data-[state=active]:bg-primary data-[state=active]:text-primary-foreground",
          "data-[state=inactive]:hover:bg-muted/50 data-[state=inactive]:hover:text-foreground",
          orientation === "vertical"
            ? "w-full justify-start py-2 px-3 text-left"
            : "h-9 px-3 py-1",
          className
        )}
        disabled={disabled}
        {...props}
      >
        {children}
      </button>
    );
  },
);
TabsTrigger.displayName = "TabsTrigger";

interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string;
  forceMount?: boolean;
}

export const TabsContent = forwardRef<HTMLDivElement, TabsContentProps>(
  ({ className, value, forceMount, children, ...props }, ref) => {
    const { activeValue } = useTabs();

    if (!forceMount && activeValue !== value) {
      return null;
    }

    return (
      <div
        ref={ref}
        role="tabpanel"
        id={`tabs-${value}`}
        aria-labelledby={`tab-${value}`}
        hidden={activeValue !== value && !forceMount}
        className={cn(
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "animate-in fade-in-200",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  },
);
TabsContent.displayName = "TabsContent";
