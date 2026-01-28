"use client";

/**
 * SuccessAnimation - Visual feedback for successful operations
 *
 * Provides animated success indicators:
 * - Check mark animation
 * - Overlay variant
 * - Inline variant
 *
 * 2026 UX Pattern: Micro-interactions for positive feedback
 */

import { CheckCircle, Check } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/utils";

export interface SuccessAnimationProps {
  /** Whether to show the animation */
  show: boolean;
  /** Variant: overlay covers parent, inline shows in flow */
  variant?: "overlay" | "inline" | "icon";
  /** Success message */
  message?: string;
  /** Auto-hide after duration (ms), 0 to disable */
  autoHide?: number;
  /** Callback when animation completes */
  onComplete?: () => void;
  /** Additional className */
  className?: string;
}

/**
 * SuccessAnimation - Animated success indicator
 *
 * @example
 * ```tsx
 * // Overlay mode (covers parent)
 * <div className="relative">
 *   <Content />
 *   <SuccessAnimation show={success} variant="overlay" />
 * </div>
 *
 * // Inline mode
 * {success && <SuccessAnimation show variant="inline" message="저장됨" />}
 * ```
 */
export function SuccessAnimation({
  show,
  variant = "overlay",
  message,
  autoHide = 2000,
  onComplete,
  className,
}: SuccessAnimationProps) {
  const prefersReducedMotion = useReducedMotion();

  // Auto-hide effect
  if (autoHide > 0 && show) {
    setTimeout(() => {
      onComplete?.();
    }, autoHide);
  }

  if (variant === "icon") {
    return (
      <AnimatePresence>
        {show && (
          <motion.div
            initial={prefersReducedMotion ? {} : { scale: 0, opacity: 0 }}
            animate={prefersReducedMotion ? {} : { scale: 1, opacity: 1 }}
            exit={prefersReducedMotion ? {} : { scale: 0, opacity: 0 }}
            transition={{ type: "spring", damping: 15, stiffness: 300 }}
            className={cn("text-green-500", className)}
          >
            <CheckCircle className="w-5 h-5" />
          </motion.div>
        )}
      </AnimatePresence>
    );
  }

  if (variant === "inline") {
    return (
      <AnimatePresence>
        {show && (
          <motion.div
            initial={prefersReducedMotion ? {} : { opacity: 0, y: -10 }}
            animate={prefersReducedMotion ? {} : { opacity: 1, y: 0 }}
            exit={prefersReducedMotion ? {} : { opacity: 0, y: -10 }}
            className={cn(
              "flex items-center gap-2 text-green-400",
              className
            )}
          >
            <CheckCircle className="w-4 h-4" />
            {message && <span className="text-sm">{message}</span>}
          </motion.div>
        )}
      </AnimatePresence>
    );
  }

  // Overlay variant
  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0 }}
          animate={prefersReducedMotion ? {} : { opacity: 1 }}
          exit={prefersReducedMotion ? {} : { opacity: 0 }}
          className={cn(
            "absolute inset-0 flex flex-col items-center justify-center bg-green-500/10 rounded-xl z-10",
            className
          )}
        >
          <motion.div
            initial={prefersReducedMotion ? {} : { scale: 0 }}
            animate={prefersReducedMotion ? {} : { scale: 1 }}
            transition={{ type: "spring", damping: 12, stiffness: 200, delay: 0.1 }}
          >
            <CheckCircle className="w-16 h-16 text-green-500" />
          </motion.div>
          {message && (
            <motion.p
              initial={prefersReducedMotion ? {} : { opacity: 0, y: 10 }}
              animate={prefersReducedMotion ? {} : { opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mt-3 text-sm text-green-400 font-medium"
            >
              {message}
            </motion.p>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/**
 * ErrorShake - Shake animation for error feedback
 *
 * @example
 * ```tsx
 * <ErrorShake trigger={hasError}>
 *   <Input value={value} error={error} />
 * </ErrorShake>
 * ```
 */
export function ErrorShake({
  children,
  trigger,
  className,
}: {
  children: React.ReactNode;
  trigger: boolean;
  className?: string;
}) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div
      animate={
        trigger && !prefersReducedMotion
          ? { x: [-10, 10, -10, 10, 0] }
          : {}
      }
      transition={{ duration: 0.4 }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/**
 * PulseOnUpdate - Pulse animation when content updates
 */
export function PulseOnUpdate({
  children,
  trigger,
  className,
}: {
  children: React.ReactNode;
  trigger: unknown; // Changes to this value trigger the pulse
  className?: string;
}) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div
      key={String(trigger)} // Re-mount on change
      initial={prefersReducedMotion ? {} : { scale: 1.05, opacity: 0.8 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.2 }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
