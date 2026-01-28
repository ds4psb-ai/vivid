"use client";

/**
 * CopyButton - Copy to clipboard with feedback
 *
 * Features:
 * - Visual feedback on copy
 * - Tooltip integration
 * - Accessible (aria-label)
 * - Touch-friendly (44px targets)
 *
 * 2026 UX Pattern: Immediate feedback for actions
 */

import { useState, useCallback } from "react";
import { Copy, Check } from "lucide-react";
import { copyToClipboard } from "@/lib/clipboard";
import { Tooltip } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

export interface CopyButtonProps {
  /** Text to copy to clipboard */
  text: string;
  /** Tooltip label (default: "복사") */
  label?: string;
  /** Success message (default: "복사됨!") */
  successLabel?: string;
  /** Button size */
  size?: "sm" | "md" | "lg";
  /** Color variant */
  variant?: "default" | "amber" | "red" | "gray";
  /** Additional className */
  className?: string;
  /** Callback after successful copy */
  onCopy?: () => void;
}

const SIZE_CLASSES = {
  sm: "p-1 min-h-[32px] min-w-[32px]",
  md: "p-1.5 min-h-[44px] min-w-[44px]",
  lg: "p-2 min-h-[48px] min-w-[48px]",
};

const ICON_SIZES = {
  sm: "w-3 h-3",
  md: "w-4 h-4",
  lg: "w-5 h-5",
};

const VARIANT_CLASSES = {
  default: "text-white/60 hover:text-white hover:bg-white/10",
  amber: "text-amber-400/60 hover:text-amber-400 hover:bg-amber-500/10",
  red: "text-red-400/60 hover:text-red-400 hover:bg-red-500/10",
  gray: "text-gray-400/60 hover:text-gray-400 hover:bg-gray-500/10",
};

const SUCCESS_CLASSES = {
  default: "text-emerald-400",
  amber: "text-emerald-400",
  red: "text-emerald-400",
  gray: "text-emerald-400",
};

/**
 * Copy button with tooltip and feedback
 *
 * @example
 * ```tsx
 * <CopyButton text="Hello world" label="메시지 복사" />
 *
 * <CopyButton
 *   text={errorMessage}
 *   label="에러 메시지 복사"
 *   variant="red"
 *   size="sm"
 * />
 * ```
 */
export function CopyButton({
  text,
  label = "복사",
  successLabel = "복사됨!",
  size = "md",
  variant = "default",
  className,
  onCopy,
}: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    const success = await copyToClipboard(text);
    if (success) {
      setCopied(true);
      onCopy?.();
      setTimeout(() => setCopied(false), 1500);
    }
  }, [text, onCopy]);

  return (
    <Tooltip content={copied ? successLabel : label}>
      <button
        onClick={handleCopy}
        className={cn(
          "rounded-lg transition-colors flex items-center justify-center",
          SIZE_CLASSES[size],
          copied ? SUCCESS_CLASSES[variant] : VARIANT_CLASSES[variant],
          className
        )}
        aria-label={label}
      >
        {copied ? (
          <Check className={ICON_SIZES[size]} />
        ) : (
          <Copy className={ICON_SIZES[size]} />
        )}
      </button>
    </Tooltip>
  );
}
