import { useState, useEffect } from "react";

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const media = window.matchMedia(query);
    setMatches(media.matches);

    const listener = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    media.addEventListener("change", listener);
    return () => media.removeEventListener("change", listener);
  }, [query]);

  return matches;
}

export function useBreakpoint() {
  const isMobile = useMediaQuery("(max-width: 639px)");
  const isTablet = useMediaQuery("(min-width: 640px) and (max-width: 1023px)");
  const isLarge = useMediaQuery("(min-width: 1280px)");

  if (isMobile) return "mobile";
  if (isTablet) return "tablet";
  if (isLarge) return "large";
  return "desktop";
}

export function useReducedMotion(): boolean {
  return useMediaQuery("(prefers-reduced-motion: reduce)");
}
