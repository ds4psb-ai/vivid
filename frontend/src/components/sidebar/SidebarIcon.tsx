"use client";

import type { LucideIcon } from "lucide-react";

interface SidebarIconProps {
  icon: LucideIcon;
  active?: boolean;
  className?: string;
}

export function SidebarIcon({
  icon: Icon,
  active = false,
  className = "",
}: SidebarIconProps) {
  return (
    <Icon
      className={`w-5 h-5 transition-all duration-200 ${
        active
          ? "opacity-100 text-[var(--color-brand-primary)] drop-shadow-[0_0_6px_oklch(0.62_0.28_20_/_0.5)]"
          : "opacity-70 text-[var(--fg-muted)]"
      } ${className}`}
      strokeWidth={active ? 2 : 1.5}
    />
  );
}
