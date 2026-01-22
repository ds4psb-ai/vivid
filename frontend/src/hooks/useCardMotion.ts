/**
 * Card Motion Hook
 *
 * Provides consistent card hover animations across the application.
 * Based on Lusion-style micro-interactions and 2026 UX trends.
 */

import { useMemo } from "react";
import type { MotionProps, Transition, TargetAndTransition, Easing } from "framer-motion";

// =============================================================================
// Types
// =============================================================================

export type CardMotionPreset = "default" | "subtle" | "lift" | "scale" | "none";

// Lusion-style cubic bezier easing
type CubicBezierEasing = [number, number, number, number];

export interface CardMotionConfig {
  /** Y-axis translation on hover (pixels) */
  hoverY?: number;
  /** Scale factor on hover */
  hoverScale?: number;
  /** Transition duration (seconds) */
  duration?: number;
  /** Custom easing curve */
  ease?: CubicBezierEasing;
}

export interface CardMotionResult {
  /** Props to spread on motion.div */
  motionProps: Pick<MotionProps, "whileHover" | "transition">;
  /** Individual hover state for conditional styling */
  whileHover: TargetAndTransition;
  /** Transition config */
  transition: Transition;
}

// =============================================================================
// Presets
// =============================================================================

// Default Lusion-style easing curve
const LUSION_EASE: CubicBezierEasing = [0.16, 1, 0.3, 1];
const LINEAR_EASE: CubicBezierEasing = [0, 0, 1, 1];

const PRESETS: Record<CardMotionPreset, CardMotionConfig> = {
  /** Default card hover - subtle lift with scale */
  default: {
    hoverY: -3,
    hoverScale: 1.01,
    duration: 0.3,
    ease: LUSION_EASE,
  },
  /** Very subtle hover - minimal movement */
  subtle: {
    hoverY: -2,
    hoverScale: 1.005,
    duration: 0.25,
    ease: LUSION_EASE,
  },
  /** Lift effect - more pronounced vertical movement */
  lift: {
    hoverY: -4,
    hoverScale: 1.01,
    duration: 0.3,
    ease: LUSION_EASE,
  },
  /** Scale only - no vertical movement */
  scale: {
    hoverY: 0,
    hoverScale: 1.02,
    duration: 0.3,
    ease: LUSION_EASE,
  },
  /** No animation */
  none: {
    hoverY: 0,
    hoverScale: 1,
    duration: 0,
    ease: LINEAR_EASE,
  },
};

// =============================================================================
// Hook
// =============================================================================

/**
 * Hook for consistent card hover animations
 *
 * @example
 * ```tsx
 * // Using a preset
 * const { motionProps } = useCardMotion("default");
 * return <motion.div {...motionProps}>Card content</motion.div>;
 *
 * // Custom configuration
 * const { motionProps } = useCardMotion({ hoverY: -5, hoverScale: 1.02 });
 * return <motion.div {...motionProps}>Card content</motion.div>;
 *
 * // Access individual parts
 * const { whileHover, transition } = useCardMotion("lift");
 * return (
 *   <motion.div
 *     whileHover={{ ...whileHover, boxShadow: "0 10px 20px rgba(0,0,0,0.2)" }}
 *     transition={transition}
 *   >
 *     Card content
 *   </motion.div>
 * );
 * ```
 */
export function useCardMotion(
  presetOrConfig: CardMotionPreset | CardMotionConfig = "default"
): CardMotionResult {
  return useMemo(() => {
    // Resolve config from preset or use directly
    const config: CardMotionConfig =
      typeof presetOrConfig === "string"
        ? PRESETS[presetOrConfig]
        : { ...PRESETS.default, ...presetOrConfig };

    const whileHover: TargetAndTransition = {
      y: config.hoverY ?? -3,
      scale: config.hoverScale ?? 1.01,
    };

    const transition: Transition = {
      duration: config.duration ?? 0.3,
      ease: config.ease ?? LUSION_EASE,
    };

    return {
      motionProps: {
        whileHover,
        transition,
      },
      whileHover,
      transition,
    };
  }, [presetOrConfig]);
}

// =============================================================================
// Constants Export (for non-hook usage)
// =============================================================================

/** Standard card hover transition for motion.div */
export const CARD_HOVER_TRANSITION: Transition = {
  duration: 0.3,
  ease: LUSION_EASE,
};

/** Standard card hover state for motion.div */
export const CARD_HOVER_STATE: TargetAndTransition = {
  y: -3,
  scale: 1.01,
};

/** Combined motion props for direct spreading */
export const CARD_MOTION_PROPS: Pick<MotionProps, "whileHover" | "transition"> = {
  whileHover: CARD_HOVER_STATE,
  transition: CARD_HOVER_TRANSITION,
};

export default useCardMotion;
