"use client";

import * as React from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { cn } from "@/lib/utils";

interface ModeToggleProps {
  iconClassName?: string;
}

export function ModeToggle({ iconClassName }: ModeToggleProps) {
  const { setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <button
        type="button"
        className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)]"
      >
        <span className="sr-only">테마 전환</span>
        <div className="h-4 w-4" />
      </button>
    );
  }

  const isDark = resolvedTheme === "dark";
  const iconColor = iconClassName ?? "text-[var(--fg-0)]";

  return (
    <button
      type="button"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="relative inline-flex h-11 w-11 items-center justify-center rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] transition-colors hover:bg-[var(--surface-3)]"
      title={isDark ? "라이트 모드" : "다크 모드"}
      aria-label={isDark ? "라이트 모드로 전환" : "다크 모드로 전환"}
    >
      <Sun
        className={cn(
          "h-4 w-4 transition-all duration-200",
          iconColor,
          isDark ? "rotate-90 scale-0 opacity-0" : "rotate-0 scale-100 opacity-100"
        )}
      />
      <Moon
        className={cn(
          "absolute h-4 w-4 transition-all duration-200",
          iconColor,
          isDark ? "rotate-0 scale-100 opacity-100" : "rotate-90 scale-0 opacity-0"
        )}
      />
    </button>
  );
}
