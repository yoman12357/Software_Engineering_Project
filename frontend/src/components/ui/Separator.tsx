import { cn } from "../../lib/utils";

export interface SeparatorProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: "horizontal" | "vertical";
  decorative?: boolean;
}

export function Separator({
  className,
  orientation = "horizontal",
  decorative = true,
  ...props
}: SeparatorProps) {
  return (
    <div
      role={decorative ? "none" : "separator"}
      aria-orientation={orientation}
      className={cn(
        "bg-border shrink-0 transition-colors",
        orientation === "horizontal" ? "h-px w-full" : "w-px h-full",
        className
      )}
      {...props}
    />
  );
}