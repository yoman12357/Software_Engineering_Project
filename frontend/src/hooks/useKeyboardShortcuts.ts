import { useEffect, useCallback } from "react";

interface KeyboardShortcutsOptions {
  onNewChat?: () => void;
  onSearch?: () => void;
  onExport?: () => void;
  onEscape?: () => void;
  onRegenerate?: () => void;
  onToggleSidebar?: () => void;
}

export function useKeyboardShortcuts({
  onNewChat,
  onSearch,
  onExport,
  onEscape,
  onRegenerate,
  onToggleSidebar,
}: KeyboardShortcutsOptions) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in input/textarea
      const target = event.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) {
        // Allow Escape to close dialogs even in inputs
        if (event.key !== "Escape") return;
      }

      const isCtrlOrMeta = event.ctrlKey || event.metaKey;

      switch (event.key) {
        case "n":
          if (isCtrlOrMeta) {
            event.preventDefault();
            onNewChat?.();
          }
          break;

        case "k":
          if (isCtrlOrMeta) {
            event.preventDefault();
            onSearch?.();
          }
          break;

        case "e":
          if (isCtrlOrMeta) {
            event.preventDefault();
            onExport?.();
          }
          break;

        case "r":
          if (isCtrlOrMeta && event.shiftKey) {
            event.preventDefault();
            onRegenerate?.();
          }
          break;

        case "Escape":
          event.preventDefault();
          onEscape?.();
          break;

        case "b":
          if (isCtrlOrMeta) {
            event.preventDefault();
            onToggleSidebar?.();
          }
          break;
      }
    },
    [onNewChat, onSearch, onExport, onEscape, onRegenerate, onToggleSidebar]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);
}