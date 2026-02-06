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
      className={`h-5 w-5 transition-colors ${
        active ? "text-[var(--color-brand-primary)]" : "text-[var(--fg-muted)]"
      } ${className}`}
      strokeWidth={active ? 2 : 1.75}
    />
  );
}
