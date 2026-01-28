"use client";

/**
 * Button - Core button component with accessibility and motion
 *
 * Features:
 * - WCAG 2.1 compliant touch targets (44px minimum)
 * - Press feedback with scale animation
 * - Respects prefers-reduced-motion
 * - Variant and size system
 */

import * as React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  size?: "default" | "sm" | "lg" | "icon";
  /** Disable press animation */
  disableAnimation?: boolean;
}

// Touch target utility class - 44px minimum (WCAG 2.1)
export const TOUCH_TARGET = "min-h-[44px] min-w-[44px]";

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", disableAnimation = false, ...props }, ref) => {
    const baseStyles = "btn";

    const variants: Record<string, string> = {
      default: "btn-primary",
      destructive: "btn-destructive",
      outline: "btn-outline",
      secondary: "btn-secondary",
      ghost: "btn-ghost",
      link: "btn-link",
    };

    // Updated sizes with WCAG-compliant touch targets
    const sizes: Record<string, string> = {
      default: "btn-size-default min-h-[44px]",  // 44px minimum (WCAG)
      sm: "btn-size-sm min-h-[36px]",            // Smaller for desktop contexts
      lg: "btn-size-lg min-h-[48px]",            // Larger touch target
      icon: "btn-size-icon min-h-[44px] min-w-[44px]", // Square 44x44px
    };

    const buttonClassName = cn(baseStyles, variants[variant], sizes[size], className);

    // Extract safe props for motion.button (exclude conflicting drag handlers)
    const {
      onDrag,
      onDragEnd,
      onDragStart,
      onAnimationStart,
      onAnimationEnd,
      ...safeProps
    } = props;

    // Use motion button for press feedback (respects reduced-motion via CSS)
    if (!disableAnimation && !props.disabled) {
      return (
        <motion.button
          className={cn(buttonClassName, "motion-safe:active:scale-[0.98]")}
          ref={ref as React.Ref<HTMLButtonElement>}
          whileTap={{ scale: 0.98 }}
          transition={{ duration: 0.1 }}
          {...safeProps}
        />
      );
    }

    return (
      <button
        className={buttonClassName}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };
