"use client";

import { useEffect } from "react";
import { useThemeStore } from "../stores/themeStore";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const initialize = useThemeStore((state) => state.initialize);

  useEffect(() => {
    const cleanup = initialize();
    return cleanup;
  }, [initialize]);

  return <>{children}</>;
}

export function useTheme() {
  const mode = useThemeStore((state) => state.mode);
  const resolvedTheme = useThemeStore((state) => state.resolvedTheme);
  const setMode = useThemeStore((state) => state.setMode);
  const toggleTheme = useThemeStore((state) => state.toggleTheme);

  return {
    theme: mode,
    resolvedTheme,
    setTheme: setMode,
    toggleTheme,
    isDark: resolvedTheme === "dark",
    isSystem: mode === "system",
  };
}