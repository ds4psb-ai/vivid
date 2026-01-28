import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLElement> {
  variant?: "default" | "secondary" | "destructive" | "outline";
  /** Semantic element type - defaults to "span" for inline, use "div" for block */
  as?: "span" | "div";
}

function Badge({ className, variant = "default", as: Component = "span", ...props }: BadgeProps) {
  const variants: Record<string, string> = {
    default: "badge",
    secondary: "badge badge-secondary",
    destructive: "badge badge-destructive",
    outline: "badge badge-outline",
  };

  return (
    <Component
      className={cn(
        variants[variant],
        className
      )}
      {...props}
    />
  );
}

export { Badge };
