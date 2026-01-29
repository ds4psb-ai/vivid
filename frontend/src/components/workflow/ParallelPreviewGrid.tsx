"use client";

/**
 * ParallelPreviewGrid - Responsive Grid for Step Preview Cards
 *
 * Phase 5: Workflow UX Innovation
 *
 * Features:
 * - Responsive grid layout (1/2/3/4 columns based on screen size)
 * - App-specific column configuration (DNA Lab: 4, Story Engine: 3, Production: 3)
 * - Individual card expansion state management
 * - Stagger animation with AnimatePresence
 * - Auto input source generation from chain data
 *
 * 2026 Pattern: "Overview First, Details on Demand"
 * - Show all steps at a glance
 * - Allow drilling down into specific steps
 */

import { useState, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import {
  StepPreviewCard,
  type InputSourceInfo,
  type InputSourceOrigin,
  type StepPreviewMode,
} from "./StepPreviewCard";
import { CHAIN_DATA_SOURCE_MAP, STEP_LABELS } from "./workflow-configs";
import type {
  WorkflowStepMetadata,
  StepState,
  ChainDataEntry,
  MegaAppId,
} from "./types";

// =============================================================================
// Types
// =============================================================================

/** Column count configuration */
export type GridColumns = 2 | 3 | 4 | "auto";

/** Gap size options */
export type GridGap = "compact" | "normal" | "spacious";

export interface ParallelPreviewGridProps {
  // Data
  /** Workflow steps metadata */
  steps: WorkflowStepMetadata[];
  /** Current state of each step */
  stepStates: Record<string, StepState>;
  /** Chain data entries */
  chainData?: Record<string, ChainDataEntry>;
  /** Input sources (optional - auto-generated if not provided) */
  inputSources?: Record<string, InputSourceInfo[]>;

  // Layout
  /** Number of columns (auto = based on step count) */
  columns?: GridColumns;
  /** Gap between cards */
  gap?: GridGap;

  // Card Mode
  /** Default card display mode */
  cardMode?: StepPreviewMode;
  /** Allow individual card expansion */
  allowExpand?: boolean;

  // Events
  /** Callback when step card is clicked */
  onStepClick?: (stepId: string) => void;
  /** Callback when step edit is requested */
  onStepEdit?: (stepId: string) => void;

  // Styling
  /** Additional CSS class */
  className?: string;
  /** Enable stagger animation */
  animate?: boolean;

  // Context
  /** Current app ID for source detection */
  currentApp?: MegaAppId;
}

// =============================================================================
// Constants
// =============================================================================

/** Gap class mapping */
const GAP_CLASSES: Record<GridGap, string> = {
  compact: "gap-3",
  normal: "gap-4",
  spacious: "gap-6",
};

/** Animation stagger delay (ms) per card */
const STAGGER_DELAY = 50;

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Get responsive grid classes based on column count
 */
function getGridColsClass(columns: GridColumns, stepCount: number): string {
  const cols = columns === "auto" ? Math.min(stepCount, 4) : columns;

  switch (cols) {
    case 2:
      return "grid-cols-1 sm:grid-cols-2";
    case 3:
      return "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3";
    case 4:
    default:
      return "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4";
  }
}

/**
 * Determine input source origin from chain data source map
 */
function getInputSourceOrigin(
  dataKey: string,
  currentApp: MegaAppId
): InputSourceOrigin {
  const source = CHAIN_DATA_SOURCE_MAP[dataKey];
  if (!source) return "internal";

  // If the source app matches current app, it's internal
  if (source.app === currentApp) return "internal";

  // Otherwise, return the source app as origin
  return source.app as InputSourceOrigin;
}

/**
 * Build input sources from step inputs and chain data
 */
function buildInputSources(
  step: WorkflowStepMetadata,
  chainData: Record<string, ChainDataEntry>,
  currentApp: MegaAppId
): InputSourceInfo[] {
  return step.inputs.map((inputKey) => ({
    dataKey: inputKey,
    source: getInputSourceOrigin(inputKey, currentApp),
    available: !!chainData[inputKey],
    label: STEP_LABELS[inputKey] || inputKey,
  }));
}

// =============================================================================
// Animation Variants
// =============================================================================

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: STAGGER_DELAY / 1000,
    },
  },
};

const itemVariants = {
  hidden: {
    opacity: 0,
    scale: 0.95,
    y: 10,
  },
  show: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      type: "spring" as const,
      stiffness: 300,
      damping: 24,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    y: -10,
    transition: {
      duration: 0.2,
    },
  },
};

// =============================================================================
// Main Component
// =============================================================================

/**
 * ParallelPreviewGrid - Responsive grid layout for workflow step preview cards
 *
 * @example
 * ```tsx
 * <ParallelPreviewGrid
 *   steps={DNA_LAB_STEPS}
 *   stepStates={stepStates}
 *   chainData={chainData}
 *   columns={4}
 *   onStepClick={(stepId) => router.push(`/dna-lab?step=${stepId}`)}
 * />
 * ```
 */
export function ParallelPreviewGrid({
  steps,
  stepStates,
  chainData = {},
  inputSources: providedInputSources,
  columns = "auto",
  gap = "normal",
  cardMode = "compact",
  allowExpand = true,
  onStepClick,
  onStepEdit,
  className,
  animate = true,
  currentApp = "dna-lab",
}: ParallelPreviewGridProps) {
  const prefersReducedMotion = useReducedMotion();
  const shouldAnimate = animate && !prefersReducedMotion;

  // Track individually expanded cards
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());

  // Toggle card expansion
  const toggleExpand = useCallback((stepId: string) => {
    if (!allowExpand) return;
    setExpandedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(stepId)) {
        next.delete(stepId);
      } else {
        next.add(stepId);
      }
      return next;
    });
  }, [allowExpand]);

  // Compute input sources for each step
  const computedInputSources = useMemo(() => {
    if (providedInputSources) return providedInputSources;

    const sources: Record<string, InputSourceInfo[]> = {};
    for (const step of steps) {
      sources[step.id] = buildInputSources(step, chainData, currentApp);
    }
    return sources;
  }, [steps, chainData, currentApp, providedInputSources]);

  // Build grid class names
  const gridClassName = cn(
    "grid",
    getGridColsClass(columns, steps.length),
    GAP_CLASSES[gap],
    className
  );

  // Handle step click
  const handleStepClick = useCallback(
    (stepId: string) => {
      if (cardMode === "collapsed" || allowExpand) {
        toggleExpand(stepId);
      }
      onStepClick?.(stepId);
    },
    [cardMode, allowExpand, toggleExpand, onStepClick]
  );

  // Determine effective mode for each card
  const getEffectiveMode = useCallback(
    (stepId: string): StepPreviewMode => {
      if (allowExpand && expandedSteps.has(stepId)) {
        return "expanded";
      }
      return cardMode;
    },
    [allowExpand, expandedSteps, cardMode]
  );

  // Non-animated render
  if (!shouldAnimate) {
    return (
      <div className={gridClassName}>
        {steps.map((step) => {
          const stepState = stepStates[step.id];
          if (!stepState) return null;

          const chainEntry = chainData[step.id];
          const sources = computedInputSources[step.id] || [];
          const effectiveMode = getEffectiveMode(step.id);

          return (
            <StepPreviewCard
              key={step.id}
              step={step}
              stepState={stepState}
              chainEntry={chainEntry}
              inputSources={sources}
              mode={effectiveMode}
              onClick={() => handleStepClick(step.id)}
              onEdit={onStepEdit ? () => onStepEdit(step.id) : undefined}
            />
          );
        })}
      </div>
    );
  }

  // Animated render
  return (
    <motion.div
      layout
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className={gridClassName}
    >
      <AnimatePresence mode="popLayout">
        {steps.map((step) => {
          const stepState = stepStates[step.id];
          if (!stepState) return null;

          const chainEntry = chainData[step.id];
          const sources = computedInputSources[step.id] || [];
          const effectiveMode = getEffectiveMode(step.id);

          return (
            <motion.div
              key={step.id}
              layout
              variants={itemVariants}
              exit="exit"
            >
              <StepPreviewCard
                step={step}
                stepState={stepState}
                chainEntry={chainEntry}
                inputSources={sources}
                mode={effectiveMode}
                onClick={() => handleStepClick(step.id)}
                onEdit={onStepEdit ? () => onStepEdit(step.id) : undefined}
              />
            </motion.div>
          );
        })}
      </AnimatePresence>
    </motion.div>
  );
}

// =============================================================================
// Utility Exports
// =============================================================================

export { buildInputSources, getInputSourceOrigin, getGridColsClass };

export default ParallelPreviewGrid;
