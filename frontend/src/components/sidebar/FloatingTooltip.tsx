"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

interface FloatingTooltipProps {
  label: string;
  anchorRect: DOMRect | null;
  visible: boolean;
}

export function FloatingTooltip({
  label,
  anchorRect,
  visible,
}: FloatingTooltipProps) {
  const [mounted, setMounted] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || !visible || !anchorRect) return null;

  const top = anchorRect.top + anchorRect.height / 2;

  return createPortal(
    <div
      ref={ref}
      role="tooltip"
      className="fixed z-[var(--z-tooltip)] pointer-events-none
                 -translate-y-1/2 ml-3
                 px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap
                 bg-[var(--surface-2)] dark:bg-[#222224] text-[var(--fg-0)] dark:text-white
                 border border-[var(--glass-border)]
                 shadow-lg
                 animate-in fade-in slide-in-from-left-1 duration-150"
      style={{ top, left: anchorRect.right }}
    >
      {label}
    </div>,
    document.body
  );
}
