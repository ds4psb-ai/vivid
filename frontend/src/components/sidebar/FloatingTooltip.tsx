"use client";

import { useRef } from "react";
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
  const ref = useRef<HTMLDivElement>(null);
  if (typeof document === "undefined" || !visible || !anchorRect) return null;

  const top = anchorRect.top + anchorRect.height / 2;

  return createPortal(
    <div
      ref={ref}
      role="tooltip"
      className="pointer-events-none fixed z-[var(--z-tooltip)] ml-2 -translate-y-1/2 rounded-lg border border-[var(--border-muted)] bg-[var(--surface-2)] px-3 py-1.5 text-sm text-[var(--fg-0)] shadow-sm"
      style={{ top, left: anchorRect.right }}
    >
      {label}
    </div>,
    document.body
  );
}
