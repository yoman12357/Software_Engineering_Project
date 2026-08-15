import { Sun, Moon, Monitor } from "lucide-react";
import { cn } from "../../lib/utils";
import { useTheme } from "../../hooks/useTheme";

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();

  return (
    <div className={cn("flex items-center gap-1 rounded-lg bg-muted p-1", className)} role="group" aria-label="Theme selection">
      <button
        onClick={() => setTheme("light")}
        className={cn(
          "p-2 rounded-md transition-all duration-200",
          "hover:bg-muted-foreground/10",
          theme === "light"
            ? "bg-primary text-primary-foreground shadow-sm"
            : "text-muted-foreground"
        )}
        aria-label="Light mode"
        aria-pressed={theme === "light"}
      >
        <Sun className="h-4 w-4" aria-hidden="true" />
      </button>
      <button
        onClick={() => setTheme("system")}
        className={cn(
          "p-2 rounded-md transition-all duration-200",
          "hover:bg-muted-foreground/10",
          theme === "system"
            ? "bg-primary text-primary-foreground shadow-sm"
            : "text-muted-foreground"
        )}
        aria-label="System mode"
        aria-pressed={theme === "system"}
      >
        <Monitor className="h-4 w-4" aria-hidden="true" />
      </button>
      <button
        onClick={() => setTheme("dark")}
        className={cn(
          "p-2 rounded-md transition-all duration-200",
          "hover:bg-muted-foreground/10",
          theme === "dark"
            ? "bg-primary text-primary-foreground shadow-sm"
            : "text-muted-foreground"
        )}
        aria-label="Dark mode"
        aria-pressed={theme === "dark"}
      >
        <Moon className="h-4 w-4" aria-hidden="true" />
      </button>
    </div>
  );
}

export function ThemeToggleCompact({ className }: { className?: string }) {
  const { toggleTheme, isDark } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={cn(
        "p-2 rounded-lg transition-all duration-200",
        "hover:bg-muted-foreground/10",
        "focus-ring",
        className
      )}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      aria-pressed={isDark}
    >
      {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </button>
  );
}
