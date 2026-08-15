"use client";

import { cn } from "../../lib/utils";
import { Sun, Moon, Monitor } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { useThemeStore } from "../../stores/themeStore";

interface ThemeSelectorProps {
  className?: string;
  variant?: "buttons" | "dropdown";
}

export function ThemeSelector({ className, variant = "buttons" }: ThemeSelectorProps) {
  const { mode, setMode, resolvedTheme } = useThemeStore();

  const themes = [
    { value: "light" as const, label: "Light", icon: Sun, description: "Always light mode" },
    { value: "dark" as const, label: "Dark", icon: Moon, description: "Always dark mode" },
    { value: "system" as const, label: "System", icon: Monitor, description: `Follows system (${resolvedTheme})` },
  ];

  if (variant === "dropdown") {
    return (
      <div className={cn("relative inline-block", className)}>
        <Button variant="outline" size="sm" className="gap-2">
          {mode === "light" && <Sun className="h-4 w-4" />}
          {mode === "dark" && <Moon className="h-4 w-4" />}
          {mode === "system" && <Monitor className="h-4 w-4" />}
          <span className="capitalize">{mode}</span>
        </Button>
      </div>
    );
  }

  return (
    <div className={cn("flex gap-2", className)} role="radiogroup" aria-label="Theme selection">
      {themes.map(({ value, label, icon: Icon, description }) => (
        <button
          key={value}
          onClick={() => setMode(value)}
          role="radio"
          aria-checked={mode === value}
          className={cn(
            "flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium transition-all",
            mode === value
              ? "border-primary bg-primary/5 text-primary"
              : "border-border hover:border-primary/50"
          )}
        >
          <Icon className="h-4 w-4" />
          <div className="hidden sm:block">
            <p className="font-medium capitalize">{label}</p>
            <p className="text-xs text-muted-foreground">{description}</p>
          </div>
        </button>
      ))}
    </div>
  );
}

export default ThemeSelector;