import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type ThemeMode = "light" | "dark" | "system";

interface ThemeState {
  mode: ThemeMode;
  resolvedTheme: "light" | "dark";
  setMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;
  initialize: () => void;
}

function getSystemTheme(): "light" | "dark" {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function resolveTheme(mode: ThemeMode): "light" | "dark" {
  if (mode === "system") return getSystemTheme();
  return mode;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: "system",
      resolvedTheme: "light",

      setMode: (mode: ThemeMode) => {
        const resolved = resolveTheme(mode);
        set({ mode, resolvedTheme: resolved });
        document.documentElement.setAttribute("data-theme", resolved);
        document.documentElement.classList.toggle("dark", resolved === "dark");
      },

      toggleTheme: () => {
        const { mode } = get();
        const nextMode: ThemeMode =
          mode === "light" ? "dark" : mode === "dark" ? "system" : "light";
        get().setMode(nextMode);
      },

      initialize: () => {
        const { mode } = get();
        const resolved = resolveTheme(mode);
        set({ resolvedTheme: resolved });
        document.documentElement.setAttribute("data-theme", resolved);
        document.documentElement.classList.toggle("dark", resolved === "dark");

        // Listen for system theme changes
        const mediaQuery = window.matchMedia(
          "(prefers-color-scheme: dark)"
        );
        const handleChange = () => {
          const { mode } = get();
          if (mode === "system") {
            const resolved = getSystemTheme();
            set({ resolvedTheme: resolved });
            document.documentElement.setAttribute("data-theme", resolved);
            document.documentElement.classList.toggle("dark", resolved === "dark");
          }
        };

        mediaQuery.addEventListener("change", handleChange);
        // Cleanup not needed for persistent store, but good practice
        return () => mediaQuery.removeEventListener("change", handleChange);
      },
    }),
    {
      name: "cybersrs-theme",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ mode: state.mode }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          const resolved = resolveTheme(state.mode);
          state.resolvedTheme = resolved;
          document.documentElement.setAttribute("data-theme", resolved);
          document.documentElement.classList.toggle("dark", resolved === "dark");
        }
      },
    }
  )
);