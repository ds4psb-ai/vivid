"use client";

/**
 * AnimatedList - Stagger animation for list items
 *
 * Features:
 * - Staggered fade-in/slide-up animation
 * - Respects prefers-reduced-motion
 * - Accessible (semantic ul/li)
 * - Composable with any list content
 *
 * 2026 UX Pattern: Delightful micro-interactions
 */

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/utils";

// =============================================================================
// Types
// =============================================================================

export interface AnimatedListProps {
  /** List items */
  children: React.ReactNode;
  /** Additional className */
  className?: string;
  /** Stagger delay between items (ms) */
  staggerDelay?: number;
  /** Animation direction */
  direction?: "up" | "down" | "left" | "right";
  /** Whether to animate on mount */
  animateOnMount?: boolean;
}

export interface AnimatedListItemProps {
  /** Item content */
  children: React.ReactNode;
  /** Additional className */
  className?: string;
  /** Custom index for stagger timing */
  index?: number;
}

// =============================================================================
// Animation Variants
// =============================================================================

const getContainerVariants = (staggerDelay: number) => ({
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: staggerDelay / 1000, // Convert ms to seconds
    },
  },
  exit: {
    opacity: 0,
    transition: {
      staggerChildren: staggerDelay / 2000,
      staggerDirection: -1,
    },
  },
});

const getItemVariants = (direction: AnimatedListProps["direction"] = "up") => {
  const offsets = {
    up: { x: 0, y: 20 },
    down: { x: 0, y: -20 },
    left: { x: 20, y: 0 },
    right: { x: -20, y: 0 },
  };

  const offset = offsets[direction];

  return {
    hidden: {
      opacity: 0,
      x: offset.x,
      y: offset.y,
    },
    show: {
      opacity: 1,
      x: 0,
      y: 0,
      transition: {
        type: "spring" as const,
        stiffness: 300,
        damping: 24,
      },
    },
    exit: {
      opacity: 0,
      x: offset.x,
      y: offset.y,
      transition: {
        duration: 0.2,
      },
    },
  };
};

// =============================================================================
// AnimatedList Component
// =============================================================================

/**
 * Animated list container with staggered children
 *
 * @example
 * ```tsx
 * <AnimatedList staggerDelay={50}>
 *   {items.map((item) => (
 *     <AnimatedListItem key={item.id}>
 *       <ItemComponent data={item} />
 *     </AnimatedListItem>
 *   ))}
 * </AnimatedList>
 * ```
 */
export function AnimatedList({
  children,
  className,
  staggerDelay = 50,
  direction = "up",
  animateOnMount = true,
}: AnimatedListProps) {
  const prefersReducedMotion = useReducedMotion();

  // No animation for reduced motion preference
  if (prefersReducedMotion) {
    return <ul className={className}>{children}</ul>;
  }

  const containerVariants = getContainerVariants(staggerDelay);

  return (
    <AnimatePresence mode="wait">
      <motion.ul
        variants={containerVariants}
        initial={animateOnMount ? "hidden" : "show"}
        animate="show"
        exit="exit"
        className={className}
      >
        {React.Children.map(children, (child, index) => {
          if (React.isValidElement(child)) {
            return React.cloneElement(child as React.ReactElement<AnimatedListItemProps>, {
              index,
            });
          }
          return child;
        })}
      </motion.ul>
    </AnimatePresence>
  );
}

// =============================================================================
// AnimatedListItem Component
// =============================================================================

/**
 * Animated list item - must be used inside AnimatedList
 *
 * @example
 * ```tsx
 * <AnimatedListItem className="p-2 bg-white/5 rounded-lg">
 *   <span>Item content</span>
 * </AnimatedListItem>
 * ```
 */
export function AnimatedListItem({
  children,
  className,
}: AnimatedListItemProps) {
  const prefersReducedMotion = useReducedMotion();
  const itemVariants = getItemVariants("up");

  // No animation for reduced motion preference
  if (prefersReducedMotion) {
    return <li className={className}>{children}</li>;
  }

  return (
    <motion.li variants={itemVariants} className={className}>
      {children}
    </motion.li>
  );
}

// =============================================================================
// Animated Inline List (for horizontal tags/badges)
// =============================================================================

export interface AnimatedTagListProps {
  /** Tag items */
  children: React.ReactNode;
  /** Additional className */
  className?: string;
  /** Stagger delay between items (ms) */
  staggerDelay?: number;
}

/**
 * Animated inline list for tags/badges
 *
 * @example
 * ```tsx
 * <AnimatedTagList className="flex flex-wrap gap-1">
 *   {tags.map((tag) => (
 *     <AnimatedListItem key={tag}>
 *       <Badge>{tag}</Badge>
 *     </AnimatedListItem>
 *   ))}
 * </AnimatedTagList>
 * ```
 */
export function AnimatedTagList({
  children,
  className,
  staggerDelay = 30,
}: AnimatedTagListProps) {
  const prefersReducedMotion = useReducedMotion();

  if (prefersReducedMotion) {
    return <div className={cn("flex flex-wrap", className)}>{children}</div>;
  }

  const containerVariants = getContainerVariants(staggerDelay);

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className={cn("flex flex-wrap", className)}
    >
      {children}
    </motion.div>
  );
}

// =============================================================================
// Animated Tag Item
// =============================================================================

/**
 * Animated tag item - for use in AnimatedTagList
 */
export function AnimatedTagItem({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const prefersReducedMotion = useReducedMotion();
  const itemVariants = {
    hidden: { opacity: 0, scale: 0.8 },
    show: {
      opacity: 1,
      scale: 1,
      transition: { type: "spring" as const, stiffness: 400, damping: 20 },
    },
  };

  if (prefersReducedMotion) {
    return <span className={className}>{children}</span>;
  }

  return (
    <motion.span variants={itemVariants} className={className}>
      {children}
    </motion.span>
  );
}
