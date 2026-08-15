"use client";

import { useCallback, useState, useRef, useEffect } from "react";
import { cn } from "../../lib/utils";

interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactElement;
  side?: "top" | "bottom" | "left" | "right";
  delay?: number;
}

export function Tooltip({ content, children, side = "top", delay = 200 }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const tooltipRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLElement>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const updatePosition = useCallback(() => {
    if (!triggerRef.current || !tooltipRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    const gap = 8;

    let x = 0;
    let y = 0;

    switch (side) {
      case "top":
        x = triggerRect.left + triggerRect.width / 2 - tooltipRect.width / 2;
        y = triggerRect.top - tooltipRect.height - gap;
        break;
      case "bottom":
        x = triggerRect.left + triggerRect.width / 2 - tooltipRect.width / 2;
        y = triggerRect.bottom + gap;
        break;
      case "left":
        x = triggerRect.left - tooltipRect.width - gap;
        y = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2;
        break;
      case "right":
        x = triggerRect.right + gap;
        y = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2;
        break;
    }

    setPosition({ x, y });
  }, [side]);

  const showTooltip = () => {
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
      requestAnimationFrame(updatePosition);
    }, delay);
  };

  const hideTooltip = () => {
    clearTimeout(timeoutRef.current);
    setIsVisible(false);
  };

  useEffect(() => {
    if (isVisible) {
      updatePosition();
      window.addEventListener("scroll", updatePosition, true);
      window.addEventListener("resize", updatePosition);
    }
    return () => {
      window.removeEventListener("scroll", updatePosition, true);
      window.removeEventListener("resize", updatePosition);
    };
  }, [isVisible, updatePosition]);

  return (
    <>
      <span
        ref={triggerRef}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
      >
        {children}
      </span>
      {isVisible && (
        <div
          ref={tooltipRef}
          className={cn(
            "fixed z-50 px-3 py-1.5 text-sm text-popover-foreground bg-popover border border-border rounded-lg shadow-elevated",
            "animate-in fade-in zoom-in-95 duration-200",
            "max-w-xs"
          )}
          style={{
            left: position.x,
            top: position.y,
          }}
          role="tooltip"
        >
          {content}
        </div>
      )}
    </>
  );
}

export function TooltipProvider({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
