"use client";

/**
 * MobileWorkflowCarousel - Touch-Friendly Step Navigation for Mobile
 *
 * Phase 10: Workflow UX Innovation
 *
 * Provides mobile-optimized workflow step navigation with:
 * - Swipe gestures (left/right to navigate)
 * - Responsive layout (carousel on mobile, grid on tablet+)
 * - Pagination indicators
 * - Keyboard accessibility
 * - Reduced motion support
 *
 * 2026 Pattern: "Mobile-First, Gesture-Driven"
 */

import {
  useState,
  useRef,
  useCallback,
  useMemo,
  useEffect,
  type ReactNode,
  type TouchEvent,
  type KeyboardEvent,
} from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import type { WorkflowStepMetadata, StepState } from "./types";

// =============================================================================
// Types
// =============================================================================

export interface MobileWorkflowCarouselProps {
  /** Workflow steps to display */
  steps: WorkflowStepMetadata[];
  /** Step states for status display */
  stepStates: Record<string, StepState>;
  /** Currently active step index */
  activeIndex?: number;
  /** Callback when step is selected */
  onStepSelect: (stepId: string, index: number) => void;
  /** Render function for each step card */
  renderCard: (step: WorkflowStepMetadata, state: StepState, index: number) => ReactNode;
  /** Show pagination dots */
  showPagination?: boolean;
  /** Show navigation arrows (for accessibility) */
  showArrows?: boolean;
  /** Enable auto-scroll to active step */
  autoScrollToActive?: boolean;
  /** Custom className */
  className?: string;
}

// =============================================================================
// Constants
// =============================================================================

/** Minimum swipe distance to trigger navigation (pixels) */
const MIN_SWIPE_DISTANCE = 50;

/** Animation spring physics */
const SPRING_CONFIG = {
  type: "spring" as const,
  stiffness: 300,
  damping: 30,
};

// =============================================================================
// Sub-Components
// =============================================================================

/**
 * Pagination dots indicator
 */
function PaginationDots({
  total,
  current,
  onSelect,
  className,
}: {
  total: number;
  current: number;
  onSelect: (index: number) => void;
  className?: string;
}) {
  return (
    <div
      className={cn("flex items-center justify-center gap-2", className)}
      role="tablist"
      aria-label="Carousel navigation"
    >
      {Array.from({ length: total }).map((_, index) => (
        <button
          key={index}
          type="button"
          role="tab"
          aria-selected={index === current}
          aria-label={`Go to step ${index + 1}`}
          onClick={() => onSelect(index)}
          className={cn(
            "transition-all duration-200 rounded-full",
            index === current
              ? "w-6 h-2 bg-white"
              : "w-2 h-2 bg-white/30 hover:bg-white/50"
          )}
        />
      ))}
    </div>
  );
}

/**
 * Navigation arrow button
 */
function NavArrow({
  direction,
  onClick,
  disabled,
  className,
}: {
  direction: "prev" | "next";
  onClick: () => void;
  disabled: boolean;
  className?: string;
}) {
  const Icon = direction === "prev" ? ChevronLeft : ChevronRight;
  const label = direction === "prev" ? "Previous step" : "Next step";

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      className={cn(
        "absolute top-1/2 -translate-y-1/2 z-10",
        "w-10 h-10 rounded-full flex items-center justify-center",
        "bg-stitch-surface backdrop-blur-sm border border-white/10",
        "text-white/70 hover:text-white hover:bg-[var(--stitch-card-dark)]",
        "transition-all duration-200",
        "disabled:opacity-30 disabled:cursor-not-allowed",
        direction === "prev" ? "left-2" : "right-2",
        className
      )}
    >
      <Icon className="w-5 h-5" />
    </button>
  );
}

/**
 * Step counter badge
 */
function StepCounter({
  current,
  total,
  className,
}: {
  current: number;
  total: number;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "absolute top-3 right-3 z-10",
        "px-2.5 py-1 rounded-full",
        "bg-stitch-surface backdrop-blur-sm text-white/70 text-xs font-medium",
        className
      )}
    >
      {current + 1} / {total}
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

/**
 * MobileWorkflowCarousel - Touch-friendly step navigation
 *
 * @example
 * ```tsx
 * <MobileWorkflowCarousel
 *   steps={DNA_LAB_STEPS}
 *   stepStates={stepStates}
 *   activeIndex={currentIndex}
 *   onStepSelect={(stepId, index) => navigateToStep(stepId)}
 *   renderCard={(step, state, index) => (
 *     <StepPreviewCard
 *       step={step}
 *       status={state.status}
 *       mode="expanded"
 *     />
 *   )}
 *   showPagination
 *   showArrows
 * />
 * ```
 */
export function MobileWorkflowCarousel({
  steps,
  stepStates,
  activeIndex = 0,
  onStepSelect,
  renderCard,
  showPagination = true,
  showArrows = true,
  autoScrollToActive = true,
  className,
}: MobileWorkflowCarouselProps) {
  const prefersReducedMotion = useReducedMotion();
  const [currentIndex, setCurrentIndex] = useState(activeIndex);
  const [direction, setDirection] = useState(0); // -1 = prev, 1 = next

  // Touch tracking refs
  const touchStartX = useRef<number>(0);
  const touchEndX = useRef<number>(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // Sync with external activeIndex
  useEffect(() => {
    if (autoScrollToActive && activeIndex !== currentIndex) {
      setDirection(activeIndex > currentIndex ? 1 : -1);
      setCurrentIndex(activeIndex);
    }
  }, [activeIndex, autoScrollToActive, currentIndex]);

  // Navigation handlers
  const goToIndex = useCallback(
    (index: number) => {
      if (index < 0 || index >= steps.length) return;

      setDirection(index > currentIndex ? 1 : -1);
      setCurrentIndex(index);

      const step = steps[index];
      if (step) {
        onStepSelect(step.id, index);
      }
    },
    [currentIndex, steps, onStepSelect]
  );

  const goToPrev = useCallback(() => {
    goToIndex(currentIndex - 1);
  }, [currentIndex, goToIndex]);

  const goToNext = useCallback(() => {
    goToIndex(currentIndex + 1);
  }, [currentIndex, goToIndex]);

  // Touch event handlers
  const handleTouchStart = useCallback((e: TouchEvent) => {
    touchStartX.current = e.touches[0]?.clientX ?? 0;
    touchEndX.current = touchStartX.current;
  }, []);

  const handleTouchMove = useCallback((e: TouchEvent) => {
    touchEndX.current = e.touches[0]?.clientX ?? touchEndX.current;
  }, []);

  const handleTouchEnd = useCallback(() => {
    const distance = touchStartX.current - touchEndX.current;
    const isLeftSwipe = distance > MIN_SWIPE_DISTANCE;
    const isRightSwipe = distance < -MIN_SWIPE_DISTANCE;

    if (isLeftSwipe) {
      goToNext();
    } else if (isRightSwipe) {
      goToPrev();
    }

    // Reset touch tracking
    touchStartX.current = 0;
    touchEndX.current = 0;
  }, [goToNext, goToPrev]);

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      switch (e.key) {
        case "ArrowLeft":
          e.preventDefault();
          goToPrev();
          break;
        case "ArrowRight":
          e.preventDefault();
          goToNext();
          break;
        case "Home":
          e.preventDefault();
          goToIndex(0);
          break;
        case "End":
          e.preventDefault();
          goToIndex(steps.length - 1);
          break;
      }
    },
    [goToPrev, goToNext, goToIndex, steps.length]
  );

  // Current step data
  const currentStep = steps[currentIndex];
  const currentState = currentStep ? stepStates[currentStep.id] : null;

  // Animation variants
  const variants = useMemo(
    () => ({
      enter: (dir: number) => ({
        x: dir > 0 ? "100%" : "-100%",
        opacity: 0,
      }),
      center: {
        x: 0,
        opacity: 1,
      },
      exit: (dir: number) => ({
        x: dir < 0 ? "100%" : "-100%",
        opacity: 0,
      }),
    }),
    []
  );

  // Disable animations if reduced motion is preferred
  const transition = prefersReducedMotion
    ? { duration: 0 }
    : SPRING_CONFIG;

  return (
    <div
      ref={containerRef}
      className={cn("relative w-full", className)}
      role="region"
      aria-roledescription="carousel"
      aria-label="Workflow steps"
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {/* Step counter */}
      <StepCounter current={currentIndex} total={steps.length} />

      {/* Navigation arrows */}
      {showArrows && (
        <>
          <NavArrow
            direction="prev"
            onClick={goToPrev}
            disabled={currentIndex === 0}
          />
          <NavArrow
            direction="next"
            onClick={goToNext}
            disabled={currentIndex === steps.length - 1}
          />
        </>
      )}

      {/* Carousel container */}
      <div
        className="overflow-hidden rounded-xl"
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <AnimatePresence initial={false} custom={direction} mode="wait">
          <motion.div
            key={currentIndex}
            custom={direction}
            variants={variants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={transition}
            className="w-full"
            aria-live="polite"
            aria-atomic="true"
          >
            {currentStep && currentState && (
              <div
                role="tabpanel"
                aria-label={`Step ${currentIndex + 1}: ${currentStep.label}`}
              >
                {renderCard(currentStep, currentState, currentIndex)}
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Pagination dots */}
      {showPagination && (
        <PaginationDots
          total={steps.length}
          current={currentIndex}
          onSelect={goToIndex}
          className="mt-4"
        />
      )}

      {/* Screen reader announcements */}
      <div className="sr-only" aria-live="polite">
        {currentStep && `Showing step ${currentIndex + 1} of ${steps.length}: ${currentStep.label}`}
      </div>
    </div>
  );
}

// =============================================================================
// Responsive Wrapper
// =============================================================================

export interface ResponsiveWorkflowCarouselProps extends MobileWorkflowCarouselProps {
  /** Breakpoint for switching to grid (default: md = 768px) */
  gridBreakpoint?: "sm" | "md" | "lg";
  /** Number of grid columns on tablet+ */
  gridColumns?: 2 | 3 | 4;
  /** Grid gap */
  gridGap?: "sm" | "md" | "lg";
}

/**
 * ResponsiveWorkflowCarousel - Carousel on mobile, grid on tablet+
 *
 * Uses CSS to hide/show appropriate layout based on viewport.
 *
 * @example
 * ```tsx
 * <ResponsiveWorkflowCarousel
 *   steps={steps}
 *   stepStates={stepStates}
 *   onStepSelect={handleSelect}
 *   renderCard={renderCard}
 *   gridBreakpoint="md"
 *   gridColumns={4}
 * />
 * ```
 */
export function ResponsiveWorkflowCarousel({
  gridBreakpoint = "md",
  gridColumns = 4,
  gridGap = "md",
  className,
  ...carouselProps
}: ResponsiveWorkflowCarouselProps) {
  const { steps, stepStates, renderCard } = carouselProps;

  // Breakpoint classes
  const hideOnMobile = `hidden ${gridBreakpoint}:grid`;
  const showOnMobile = `${gridBreakpoint}:hidden`;

  // Grid columns class
  const gridColsClass =
    gridColumns === 2
      ? "grid-cols-2"
      : gridColumns === 3
      ? "grid-cols-3"
      : "grid-cols-4";

  // Gap class
  const gapClass =
    gridGap === "sm" ? "gap-2" : gridGap === "lg" ? "gap-6" : "gap-4";

  return (
    <div className={className}>
      {/* Mobile: Carousel */}
      <div className={showOnMobile}>
        <MobileWorkflowCarousel {...carouselProps} />
      </div>

      {/* Tablet+: Grid */}
      <div className={cn(hideOnMobile, gridColsClass, gapClass)}>
        {steps.map((step, index) => {
          const state = stepStates[step.id];
          if (!state) return null;

          return (
            <div
              key={step.id}
              onClick={() => carouselProps.onStepSelect(step.id, index)}
              className="cursor-pointer"
            >
              {renderCard(step, state, index)}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default MobileWorkflowCarousel;
