"use client";

/**
 * Tooltip - Accessible tooltip component
 *
 * Features:
 * - Keyboard accessible (focus triggers)
 * - Respects reduced motion
 * - Multiple positioning options
 * - Customizable delay
 *
 * 2026 UX Pattern: Progressive disclosure for help text
 */

import React, { useState, useRef, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/utils";

// =============================================================================
// Types
// =============================================================================

export type TooltipPosition = "top" | "bottom" | "left" | "right";

export interface TooltipProps {
  /** Tooltip content */
  content: React.ReactNode;
  /** Trigger element */
  children: React.ReactElement;
  /** Position relative to trigger */
  position?: TooltipPosition;
  /** Delay before showing (ms) */
  delay?: number;
  /** Additional class for tooltip */
  className?: string;
  /** Disable tooltip */
  disabled?: boolean;
  /** Maximum width */
  maxWidth?: number;
}

// =============================================================================
// Tooltip Provider Context (for grouped tooltips)
// =============================================================================

interface TooltipContextValue {
  isGrouped: boolean;
  delayGroup: number;
}

const TooltipContext = React.createContext<TooltipContextValue>({
  isGrouped: false,
  delayGroup: 0,
});

export function TooltipProvider({
  children,
  delayGroup = 300,
}: {
  children: React.ReactNode;
  delayGroup?: number;
}) {
  return (
    <TooltipContext.Provider value={{ isGrouped: true, delayGroup }}>
      {children}
    </TooltipContext.Provider>
  );
}

// =============================================================================
// Tooltip Component
// =============================================================================

/**
 * Tooltip - Show content on hover/focus
 *
 * @example
 * ```tsx
 * <Tooltip content="This is helpful info">
 *   <Button>Hover me</Button>
 * </Tooltip>
 *
 * // With rich content
 * <Tooltip
 *   content={
 *     <div>
 *       <strong>Title</strong>
 *       <p>Description text</p>
 *     </div>
 *   }
 *   position="right"
 * >
 *   <Icon />
 * </Tooltip>
 * ```
 */
export function Tooltip({
  content,
  children,
  position = "top",
  delay = 400,
  className,
  disabled = false,
  maxWidth = 250,
}: TooltipProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const prefersReducedMotion = useReducedMotion();
  const [isMounted, setIsMounted] = useState(false);

  // Handle client-side mounting for portal
  useEffect(() => {
    setIsMounted(true);
  }, []);

  const updatePosition = useCallback(() => {
    if (!triggerRef.current) return;

    const rect = triggerRef.current.getBoundingClientRect();
    const scrollX = window.scrollX;
    const scrollY = window.scrollY;
    const offset = 8;

    let x = 0;
    let y = 0;

    switch (position) {
      case "top":
        x = rect.left + scrollX + rect.width / 2;
        y = rect.top + scrollY - offset;
        break;
      case "bottom":
        x = rect.left + scrollX + rect.width / 2;
        y = rect.bottom + scrollY + offset;
        break;
      case "left":
        x = rect.left + scrollX - offset;
        y = rect.top + scrollY + rect.height / 2;
        break;
      case "right":
        x = rect.right + scrollX + offset;
        y = rect.top + scrollY + rect.height / 2;
        break;
    }

    setCoords({ x, y });
  }, [position]);

  const show = useCallback(() => {
    if (disabled) return;
    timeoutRef.current = setTimeout(() => {
      updatePosition();
      setIsOpen(true);
    }, delay);
  }, [delay, disabled, updatePosition]);

  const hide = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsOpen(false);
  }, []);

  // Clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // Wrap child in a span to attach event handlers
  const trigger = (
    <span
      ref={triggerRef as React.RefObject<HTMLSpanElement>}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
      aria-describedby={isOpen ? "tooltip" : undefined}
      className="inline-flex"
    >
      {children}
    </span>
  );

  // Position styles
  const getTransformOrigin = () => {
    switch (position) {
      case "top":
        return "bottom center";
      case "bottom":
        return "top center";
      case "left":
        return "right center";
      case "right":
        return "left center";
    }
  };

  const getTransform = () => {
    switch (position) {
      case "top":
        return "translateX(-50%) translateY(-100%)";
      case "bottom":
        return "translateX(-50%)";
      case "left":
        return "translateY(-50%) translateX(-100%)";
      case "right":
        return "translateY(-50%)";
    }
  };

  const animationProps = prefersReducedMotion
    ? {}
    : {
        initial: { opacity: 0, scale: 0.95 },
        animate: { opacity: 1, scale: 1 },
        exit: { opacity: 0, scale: 0.95 },
      };

  const tooltipContent = (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          {...animationProps}
          transition={{ duration: 0.15 }}
          id="tooltip"
          role="tooltip"
          className={cn(
            "fixed z-[9999] px-3 py-2 text-sm rounded-lg",
            "bg-[var(--surface-0)] border border-[var(--border-subtle)]",
            "text-[var(--fg-0)] shadow-lg",
            className
          )}
          style={{
            left: coords.x,
            top: coords.y,
            transform: getTransform(),
            transformOrigin: getTransformOrigin(),
            maxWidth,
          }}
        >
          {content}
        </motion.div>
      )}
    </AnimatePresence>
  );

  return (
    <>
      {trigger}
      {isMounted && createPortal(tooltipContent, document.body)}
    </>
  );
}

// =============================================================================
// TooltipTrigger & TooltipContent (Alternative API)
// =============================================================================

export function TooltipTrigger({
  children,
  asChild,
}: {
  children: React.ReactNode;
  asChild?: boolean;
}) {
  // Simple pass-through for alternative API compatibility
  return <>{children}</>;
}

export function TooltipContent({
  children,
  side = "top",
  className,
}: {
  children: React.ReactNode;
  side?: TooltipPosition;
  className?: string;
}) {
  // This is used in compound pattern, wrapped by Tooltip
  return <>{children}</>;
}
