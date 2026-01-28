"use client";

/**
 * useWorkflowObservability - Workflow Metrics & Observability Hook
 *
 * Tracks step execution times, credits used, and provides real-time
 * visibility into workflow progress.
 *
 * 2026 Pattern: "Measure Everything"
 * - Automatic step timing
 * - Credits aggregation
 * - Error tracking
 *
 * IMPORTANT: Use WorkflowObservabilityProvider to share state across components.
 * Without the provider, each hook call creates isolated state.
 */

import { createContext, useContext, useCallback, useState, useRef, type ReactNode } from "react";
import type { MegaAppId } from "../types";

/**
 * Metrics for a single workflow step
 */
export interface StepMetrics {
  /** Step identifier */
  stepId: string;
  /** Timestamp when step started (ms since epoch) */
  startedAt?: number;
  /** Timestamp when step completed (ms since epoch) */
  completedAt?: number;
  /** Duration in milliseconds */
  durationMs?: number;
  /** Credits consumed by this step */
  creditsUsed?: number;
  /** Error message if step failed */
  error?: string;
  /** Number of retries attempted */
  retryCount?: number;
}

/**
 * Aggregate metrics for the entire workflow
 */
export interface WorkflowMetrics {
  /** Unique session identifier */
  sessionId: string;
  /** App identifier */
  appId: MegaAppId;
  /** Per-step metrics */
  steps: Record<string, StepMetrics>;
  /** Total duration across all steps */
  totalDurationMs: number;
  /** Total credits used across all steps */
  totalCreditsUsed: number;
  /** Workflow started timestamp */
  workflowStartedAt?: number;
  /** Workflow completed timestamp */
  workflowCompletedAt?: number;
}

/**
 * Result interface for the hook
 */
export interface WorkflowObservabilityResult {
  /** Current metrics state */
  metrics: WorkflowMetrics;

  /** Mark a step as started */
  startStep: (stepId: string) => void;

  /** Mark a step as completed with optional result data */
  completeStep: (stepId: string, result?: { creditsUsed?: number }) => void;

  /** Mark a step as failed */
  failStep: (stepId: string, error: string) => void;

  /** Retry a failed step (increments retry count and resets timer) */
  retryStep: (stepId: string) => void;

  /** Get duration for a specific step (live updating if in progress) */
  getStepDuration: (stepId: string) => number | null;

  /** Check if a step is currently running */
  isStepRunning: (stepId: string) => boolean;

  /** Check if a step has an error */
  hasStepError: (stepId: string) => boolean;

  /** Get error message for a step */
  getStepError: (stepId: string) => string | undefined;

  /** Reset all metrics */
  resetMetrics: () => void;

  /** Get average step duration */
  getAverageStepDuration: () => number;
}

/**
 * Generate a unique session ID
 */
function generateSessionId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback for older environments
  return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Create initial metrics state
 */
function createInitialMetrics(appId: MegaAppId): WorkflowMetrics {
  return {
    sessionId: generateSessionId(),
    appId,
    steps: {},
    totalDurationMs: 0,
    totalCreditsUsed: 0,
  };
}

/**
 * Workflow Observability Hook
 *
 * Provides comprehensive metrics tracking for workflow steps.
 *
 * @example
 * ```tsx
 * function MyPanel() {
 *   const { startStep, completeStep, getStepDuration, isStepRunning } = useWorkflowObservability("dna-lab");
 *
 *   const handleGenerate = async () => {
 *     startStep("vpe");
 *     try {
 *       const result = await generateVPE();
 *       completeStep("vpe", { creditsUsed: result.credits });
 *     } catch (e) {
 *       failStep("vpe", e.message);
 *     }
 *   };
 *
 *   return (
 *     <div>
 *       {isStepRunning("vpe") && <Timer duration={getStepDuration("vpe")} />}
 *     </div>
 *   );
 * }
 * ```
 */
export function useWorkflowObservability(appId: MegaAppId): WorkflowObservabilityResult {
  const [metrics, setMetrics] = useState<WorkflowMetrics>(() =>
    createInitialMetrics(appId)
  );

  // Track if this is the first step (to set workflow start time)
  const isFirstStepRef = useRef(true);

  /**
   * Start tracking a step
   */
  const startStep = useCallback((stepId: string) => {
    const now = Date.now();

    setMetrics((prev) => {
      const existingStep = prev.steps[stepId];

      return {
        ...prev,
        // Set workflow start time on first step
        workflowStartedAt: isFirstStepRef.current ? now : prev.workflowStartedAt,
        steps: {
          ...prev.steps,
          [stepId]: {
            stepId,
            startedAt: now,
            completedAt: undefined,
            durationMs: undefined,
            error: undefined,
            // Preserve retry count if retrying
            retryCount: existingStep?.retryCount,
          },
        },
      };
    });

    isFirstStepRef.current = false;
  }, []);

  /**
   * Mark a step as completed
   */
  const completeStep = useCallback(
    (stepId: string, result?: { creditsUsed?: number }) => {
      const now = Date.now();

      setMetrics((prev) => {
        const step = prev.steps[stepId];
        if (!step?.startedAt) return prev;

        const durationMs = now - step.startedAt;
        const creditsUsed = result?.creditsUsed || 0;

        return {
          ...prev,
          steps: {
            ...prev.steps,
            [stepId]: {
              ...step,
              completedAt: now,
              durationMs,
              creditsUsed,
              error: undefined,
            },
          },
          totalDurationMs: prev.totalDurationMs + durationMs,
          totalCreditsUsed: prev.totalCreditsUsed + creditsUsed,
        };
      });
    },
    []
  );

  /**
   * Mark a step as failed
   */
  const failStep = useCallback((stepId: string, error: string) => {
    const now = Date.now();

    setMetrics((prev) => {
      const step = prev.steps[stepId];
      if (!step) return prev;

      const durationMs = step.startedAt ? now - step.startedAt : undefined;

      return {
        ...prev,
        steps: {
          ...prev.steps,
          [stepId]: {
            ...step,
            completedAt: now,
            durationMs,
            error,
          },
        },
        // Still add to total duration even on failure
        totalDurationMs: prev.totalDurationMs + (durationMs || 0),
      };
    });
  }, []);

  /**
   * Retry a failed step
   */
  const retryStep = useCallback((stepId: string) => {
    setMetrics((prev) => {
      const step = prev.steps[stepId];
      const newRetryCount = (step?.retryCount || 0) + 1;

      return {
        ...prev,
        steps: {
          ...prev.steps,
          [stepId]: {
            stepId,
            startedAt: Date.now(),
            completedAt: undefined,
            durationMs: undefined,
            error: undefined,
            retryCount: newRetryCount,
          },
        },
      };
    });
  }, []);

  /**
   * Get current duration for a step (live for running steps)
   */
  const getStepDuration = useCallback(
    (stepId: string): number | null => {
      const step = metrics.steps[stepId];
      if (!step) return null;

      // If completed, return final duration
      if (step.completedAt && step.durationMs !== undefined) {
        return step.durationMs;
      }

      // If running, return live duration
      if (step.startedAt && !step.completedAt) {
        return Date.now() - step.startedAt;
      }

      return null;
    },
    [metrics.steps]
  );

  /**
   * Check if a step is currently running
   */
  const isStepRunning = useCallback(
    (stepId: string): boolean => {
      const step = metrics.steps[stepId];
      return !!(step?.startedAt && !step?.completedAt);
    },
    [metrics.steps]
  );

  /**
   * Check if a step has an error
   */
  const hasStepError = useCallback(
    (stepId: string): boolean => {
      return !!metrics.steps[stepId]?.error;
    },
    [metrics.steps]
  );

  /**
   * Get error message for a step
   */
  const getStepError = useCallback(
    (stepId: string): string | undefined => {
      return metrics.steps[stepId]?.error;
    },
    [metrics.steps]
  );

  /**
   * Reset all metrics
   */
  const resetMetrics = useCallback(() => {
    setMetrics(createInitialMetrics(appId));
    isFirstStepRef.current = true;
  }, [appId]);

  /**
   * Get average step duration (completed steps only)
   */
  const getAverageStepDuration = useCallback((): number => {
    const completedSteps = Object.values(metrics.steps).filter(
      (s) => s.completedAt && s.durationMs !== undefined && !s.error
    );

    if (completedSteps.length === 0) return 0;

    const totalMs = completedSteps.reduce((sum, s) => sum + (s.durationMs || 0), 0);
    return Math.round(totalMs / completedSteps.length);
  }, [metrics.steps]);

  return {
    metrics,
    startStep,
    completeStep,
    failStep,
    retryStep,
    getStepDuration,
    isStepRunning,
    hasStepError,
    getStepError,
    resetMetrics,
    getAverageStepDuration,
  };
}

// ============================================================================
// CONTEXT & PROVIDER (for shared state across components)
// ============================================================================

/**
 * Context for sharing observability state across components
 */
const WorkflowObservabilityContext = createContext<WorkflowObservabilityResult | null>(null);

/**
 * Provider props
 */
interface WorkflowObservabilityProviderProps {
  appId: MegaAppId;
  children: ReactNode;
}

/**
 * WorkflowObservabilityProvider - Share observability state across components
 *
 * Wrap your workflow shell with this provider to ensure all child components
 * share the same observability state (metrics, timers, etc.).
 *
 * @example
 * ```tsx
 * function WorkflowShell({ appId, children }) {
 *   return (
 *     <WorkflowObservabilityProvider appId={appId}>
 *       {children}
 *     </WorkflowObservabilityProvider>
 *   );
 * }
 *
 * // In child components:
 * function StepPanel() {
 *   const { startStep, completeStep } = useWorkflowObservabilityContext();
 *   // Now shares state with other components!
 * }
 * ```
 */
export function WorkflowObservabilityProvider({
  appId,
  children,
}: WorkflowObservabilityProviderProps) {
  // Use the internal hook to create shared state
  const value = useWorkflowObservabilityInternal(appId);

  return (
    <WorkflowObservabilityContext.Provider value={value}>
      {children}
    </WorkflowObservabilityContext.Provider>
  );
}

/**
 * Internal hook that creates new state (used by provider)
 * This is the original useWorkflowObservability implementation
 */
function useWorkflowObservabilityInternal(appId: MegaAppId): WorkflowObservabilityResult {
  const [metrics, setMetrics] = useState<WorkflowMetrics>(() =>
    createInitialMetrics(appId)
  );

  // Track if this is the first step (to set workflow start time)
  const isFirstStepRef = useRef(true);

  const startStep = useCallback((stepId: string) => {
    const now = Date.now();

    setMetrics((prev) => {
      const existingStep = prev.steps[stepId];

      return {
        ...prev,
        workflowStartedAt: isFirstStepRef.current ? now : prev.workflowStartedAt,
        steps: {
          ...prev.steps,
          [stepId]: {
            stepId,
            startedAt: now,
            completedAt: undefined,
            durationMs: undefined,
            error: undefined,
            retryCount: existingStep?.retryCount,
          },
        },
      };
    });

    isFirstStepRef.current = false;
  }, []);

  const completeStep = useCallback(
    (stepId: string, result?: { creditsUsed?: number }) => {
      const now = Date.now();

      setMetrics((prev) => {
        const step = prev.steps[stepId];
        if (!step?.startedAt) return prev;

        const durationMs = now - step.startedAt;
        const creditsUsed = result?.creditsUsed || 0;

        return {
          ...prev,
          steps: {
            ...prev.steps,
            [stepId]: {
              ...step,
              completedAt: now,
              durationMs,
              creditsUsed,
              error: undefined,
            },
          },
          totalDurationMs: prev.totalDurationMs + durationMs,
          totalCreditsUsed: prev.totalCreditsUsed + creditsUsed,
        };
      });
    },
    []
  );

  const failStep = useCallback((stepId: string, error: string) => {
    const now = Date.now();

    setMetrics((prev) => {
      const step = prev.steps[stepId];
      if (!step) return prev;

      const durationMs = step.startedAt ? now - step.startedAt : undefined;

      return {
        ...prev,
        steps: {
          ...prev.steps,
          [stepId]: {
            ...step,
            completedAt: now,
            durationMs,
            error,
          },
        },
        totalDurationMs: prev.totalDurationMs + (durationMs || 0),
      };
    });
  }, []);

  const retryStep = useCallback((stepId: string) => {
    setMetrics((prev) => {
      const step = prev.steps[stepId];
      const newRetryCount = (step?.retryCount || 0) + 1;

      return {
        ...prev,
        steps: {
          ...prev.steps,
          [stepId]: {
            stepId,
            startedAt: Date.now(),
            completedAt: undefined,
            durationMs: undefined,
            error: undefined,
            retryCount: newRetryCount,
          },
        },
      };
    });
  }, []);

  const getStepDuration = useCallback(
    (stepId: string): number | null => {
      const step = metrics.steps[stepId];
      if (!step) return null;

      if (step.completedAt && step.durationMs !== undefined) {
        return step.durationMs;
      }

      if (step.startedAt && !step.completedAt) {
        return Date.now() - step.startedAt;
      }

      return null;
    },
    [metrics.steps]
  );

  const isStepRunning = useCallback(
    (stepId: string): boolean => {
      const step = metrics.steps[stepId];
      return !!(step?.startedAt && !step?.completedAt);
    },
    [metrics.steps]
  );

  const hasStepError = useCallback(
    (stepId: string): boolean => {
      return !!metrics.steps[stepId]?.error;
    },
    [metrics.steps]
  );

  const getStepError = useCallback(
    (stepId: string): string | undefined => {
      return metrics.steps[stepId]?.error;
    },
    [metrics.steps]
  );

  const resetMetrics = useCallback(() => {
    setMetrics(createInitialMetrics(appId));
    isFirstStepRef.current = true;
  }, [appId]);

  const getAverageStepDuration = useCallback((): number => {
    const completedSteps = Object.values(metrics.steps).filter(
      (s) => s.completedAt && s.durationMs !== undefined && !s.error
    );

    if (completedSteps.length === 0) return 0;

    const totalMs = completedSteps.reduce((sum, s) => sum + (s.durationMs || 0), 0);
    return Math.round(totalMs / completedSteps.length);
  }, [metrics.steps]);

  return {
    metrics,
    startStep,
    completeStep,
    failStep,
    retryStep,
    getStepDuration,
    isStepRunning,
    hasStepError,
    getStepError,
    resetMetrics,
    getAverageStepDuration,
  };
}

/**
 * Hook to access observability context (must be within provider)
 *
 * Use this when you need shared observability state across components.
 * Throws if used outside WorkflowObservabilityProvider.
 */
export function useWorkflowObservabilityContext(): WorkflowObservabilityResult {
  const context = useContext(WorkflowObservabilityContext);
  if (!context) {
    throw new Error(
      "useWorkflowObservabilityContext must be used within a WorkflowObservabilityProvider"
    );
  }
  return context;
}

/**
 * Optional hook that returns null if outside provider
 *
 * Useful for components that can work with or without shared observability.
 */
export function useWorkflowObservabilityOptional(): WorkflowObservabilityResult | null {
  return useContext(WorkflowObservabilityContext);
}
