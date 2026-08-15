"use client";

import { useState, useEffect } from "react";
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from "lucide-react";
import { cn } from "../../lib/utils";

export interface Toast {
  id: string;
  type: "success" | "error" | "warning" | "info";
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastState {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, "id">) => string;
  removeToast: (id: string) => void;
}

let toastStore: ToastState = {
  toasts: [],
  addToast: () => "",
  removeToast: () => {},
};

const listeners: Set<() => void> = new Set();

function notify() {
  listeners.forEach((listener) => listener());
}

toastStore = {
  toasts: [],
  addToast: (toast) => {
    const id = Math.random().toString(36).slice(2, 11);
    toastStore.toasts = [...toastStore.toasts, { ...toast, id }];
    notify();
    if (toast.duration !== 0) {
      setTimeout(() => {
        toastStore.removeToast(id);
      }, toast.duration ?? 5000);
    }
    return id;
  },
  removeToast: (id) => {
    toastStore.toasts = toastStore.toasts.filter((t) => t.id !== id);
    notify();
  },
};

export function useToast() {
  const [, setTick] = useState(0);

  useEffect(() => {
    const listener = () => setTick((t) => t + 1);
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  }, []);

  return {
    toasts: toastStore.toasts,
    toast: toastStore.addToast,
    dismiss: toastStore.removeToast,
  };
}

export function Toast({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  const icons = {
    success: <CheckCircle className="h-5 w-5 text-success" />,
    error: <AlertCircle className="h-5 w-5 text-destructive" />,
    warning: <AlertTriangle className="h-5 w-5 text-warning" />,
    info: <Info className="h-5 w-5 text-primary" />,
  };

  return (
    <div
      className={cn(
        "flex items-start gap-3 p-4 rounded-lg border shadow-elevated animate-in slide-in-right",
        "bg-card border-border",
        "min-w-[300px] max-w-md"
      )}
      role="alert"
    >
      <div className="flex-shrink-0 mt-0.5">{icons[toast.type]}</div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-foreground">{toast.title}</p>
        {toast.message && (
          <p className="mt-1 text-sm text-muted-foreground">{toast.message}</p>
        )}
        {toast.action && (
          <button
            onClick={() => {
              toast.action!.onClick();
              onClose();
            }}
            className="mt-2 text-sm font-medium text-primary hover:underline"
          >
            {toast.action.label}
          </button>
        )}
      </div>
      <button
        onClick={onClose}
        className="flex-shrink-0 p-1 text-muted-foreground hover:text-foreground transition-colors"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

export function Toaster() {
  const { toasts, dismiss } = useToast();

  return (
    <div
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none"
      aria-live="polite"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          toast={toast}
          onClose={() => dismiss(toast.id)}
        />
      ))}
    </div>
  );
}