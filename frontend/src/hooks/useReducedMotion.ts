"use client";

/**
 * useReducedMotion - Respects user's motion preferences
 *
 * Detects prefers-reduced-motion media query and provides
 * a boolean to conditionally disable animations.
 *
 * 2026 UX Pattern: Mindful UX - respect user preferences
 * WCAG 2.1 SC 2.3.3: Animation from Interactions
 */

import { useState, useEffect } from "react";

/**
 * Check if user prefers reduced motion
 *
 * @returns boolean - true if user prefers reduced motion
 *
 * @example
 * ```tsx
 * const prefersReducedMotion = useReducedMotion();
 *
 * <motion.div
 *   animate={prefersReducedMotion ? {} : { opacity: 1, y: 0 }}
 *   transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.3 }}
 * />
 * ```
 */
export function useReducedMotion(): boolean {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    // Check if running in browser
    if (typeof window === "undefined") return;

    // Get initial value
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(mediaQuery.matches);

    // Listen for changes
    const handler = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches);
    };

    mediaQuery.addEventListener("change", handler);

    return () => {
      mediaQuery.removeEventListener("change", handler);
    };
  }, []);

  return prefersReducedMotion;
}

/**
 * Get motion-safe animation props for Framer Motion
 *
 * Returns animation props that respect reduced motion preference.
 * When reduced motion is preferred, returns instant transitions.
 *
 * @example
 * ```tsx
 * const motionProps = useMotionSafeProps({
 *   animate: { opacity: 1, y: 0 },
 *   initial: { opacity: 0, y: 20 },
 *   transition: { duration: 0.3 }
 * });
 *
 * <motion.div {...motionProps} />
 * ```
 */
export function useMotionSafeProps<T extends Record<string, unknown>>(
  props: T
): T {
  const prefersReducedMotion = useReducedMotion();

  if (!prefersReducedMotion) {
    return props;
  }

  // Remove animation-related props for reduced motion
  return {
    ...props,
    animate: props.animate ? getStaticValues(props.animate as Record<string, unknown>) : undefined,
    initial: undefined,
    exit: undefined,
    transition: { duration: 0 },
    whileHover: undefined,
    whileTap: undefined,
    whileFocus: undefined,
    whileInView: undefined,
  };
}

/**
 * Extract final values from animate object (for reduced motion)
 */
function getStaticValues(
  animate: Record<string, unknown>
): Record<string, unknown> {
  // Return final values without intermediate animation states
  const result: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(animate)) {
    // If it's an array (keyframes), use the last value
    if (Array.isArray(value)) {
      result[key] = value[value.length - 1];
    } else {
      result[key] = value;
    }
  }

  return result;
}

/**
 * Get CSS transition duration based on motion preference
 *
 * @example
 * ```tsx
 * const duration = useMotionDuration(300);
 * // Returns 300 normally, 0 if reduced motion is preferred
 * ```
 */
export function useMotionDuration(normalMs: number): number {
  const prefersReducedMotion = useReducedMotion();
  return prefersReducedMotion ? 0 : normalMs;
}

/**
 * Conditional class helper for reduced motion
 *
 * @example
 * ```tsx
 * const className = useMotionClass(
 *   "transition-all duration-300",
 *   "transition-none"
 * );
 * ```
 */
export function useMotionClass(
  normalClass: string,
  reducedClass = "transition-none"
): string {
  const prefersReducedMotion = useReducedMotion();
  return prefersReducedMotion ? reducedClass : normalClass;
}
