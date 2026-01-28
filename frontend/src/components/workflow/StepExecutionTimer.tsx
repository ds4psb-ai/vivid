"use client";

/**
 * StepExecutionTimer - Real-time Step Duration Display
 *
 * Shows execution time for workflow steps with live updating
 * when a step is in progress.
 *
 * 2026 Pattern: "Transparent Progress"
 * - Live duration updates
 * - Visual status indicators
 * - Error state handling
 */

import { useEffect, useState } from "react";
import { Loader2, Clock, CheckCircle2, XCircle, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { StepMetrics } from "./hooks/useWorkflowObservability";

/**
 * Format duration in human-readable format
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  }

  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`;
  }

  return `${seconds}s`;
}

/**
 * Format duration with decimal precision
 */
export function formatDurationPrecise(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  }

  const seconds = ms / 1000;

  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = (seconds % 60).toFixed(0);

  return `${minutes}:${remainingSeconds.padStart(2, "0")}`;
}

interface StepExecutionTimerProps {
  /** Step identifier for display */
  stepId: string;
  /** Step metrics (if available) */
  metrics?: StepMetrics;
  /** Current duration in ms (for live updates) */
  duration?: number | null;
  /** Is the step currently running */
  isRunning?: boolean;
  /** Does the step have an error */
  hasError?: boolean;
  /** Retry count (if any) */
  retryCount?: number;
  /** Size variant */
  size?: "sm" | "default";
  /** Show icon */
  showIcon?: boolean;
  /** Additional class name */
  className?: string;
}

/**
 * StepExecutionTimer Component
 *
 * @example
 * ```tsx
 * // Using with observability hook
 * const { getStepDuration, isStepRunning, hasStepError, metrics } = useWorkflowObservability("dna-lab");
 *
 * <StepExecutionTimer
 *   stepId="vpe"
 *   duration={getStepDuration("vpe")}
 *   isRunning={isStepRunning("vpe")}
 *   hasError={hasStepError("vpe")}
 *   metrics={metrics.steps["vpe"]}
 * />
 * ```
 */
export function StepExecutionTimer({
  stepId,
  metrics,
  duration: externalDuration,
  isRunning: externalIsRunning,
  hasError: externalHasError,
  retryCount: externalRetryCount,
  size = "default",
  showIcon = true,
  className,
}: StepExecutionTimerProps) {
  // Support both external control and metrics-based
  const isRunning = externalIsRunning ?? (!metrics?.completedAt && !!metrics?.startedAt);
  const hasError = externalHasError ?? !!metrics?.error;
  const retryCount = externalRetryCount ?? metrics?.retryCount ?? 0;

  // Live duration state (updates every second when running)
  const [liveDuration, setLiveDuration] = useState<number | null>(null);

  // Calculate duration from metrics or external prop
  const baseDuration = externalDuration ?? metrics?.durationMs ?? null;

  // Update live duration when running
  useEffect(() => {
    if (!isRunning) {
      setLiveDuration(null);
      return;
    }

    // Initial calculation
    if (metrics?.startedAt) {
      setLiveDuration(Date.now() - metrics.startedAt);
    }

    // Update every second
    const interval = setInterval(() => {
      if (metrics?.startedAt) {
        setLiveDuration(Date.now() - metrics.startedAt);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [isRunning, metrics?.startedAt]);

  // Use live duration when running, otherwise use base duration
  const displayDuration = isRunning ? liveDuration : baseDuration;

  // Don't render if no duration
  if (displayDuration === null && !isRunning && !hasError) {
    return null;
  }

  // Determine badge variant and icon
  let variant: "default" | "secondary" | "destructive" | "outline" = "outline";
  let Icon = Clock;

  if (isRunning) {
    variant = "secondary";
    Icon = Loader2;
  } else if (hasError) {
    variant = "destructive";
    Icon = XCircle;
  } else if (displayDuration !== null) {
    variant = "default";
    Icon = CheckCircle2;
  }

  const iconSize = size === "sm" ? "w-3 h-3" : "w-4 h-4";
  const textSize = size === "sm" ? "text-xs" : "text-sm";

  return (
    <Badge
      variant={variant}
      className={cn(
        "font-mono gap-1.5",
        textSize,
        isRunning && "animate-pulse",
        className
      )}
    >
      {showIcon && (
        <Icon className={cn(iconSize, isRunning && "animate-spin")} />
      )}
      <span>
        {displayDuration !== null ? formatDurationPrecise(displayDuration) : "—"}
      </span>
      {retryCount > 0 && (
        <span className="flex items-center gap-0.5 text-muted-foreground">
          <RefreshCw className="w-3 h-3" />
          <span>{retryCount}</span>
        </span>
      )}
    </Badge>
  );
}

/**
 * Compact inline timer for step progress indicators
 */
interface InlineTimerProps {
  duration: number | null;
  isRunning?: boolean;
  className?: string;
}

export function InlineTimer({ duration, isRunning, className }: InlineTimerProps) {
  const [liveDuration, setLiveDuration] = useState(duration);

  // Update live duration
  useEffect(() => {
    if (!isRunning || duration === null) {
      setLiveDuration(duration);
      return;
    }

    setLiveDuration(duration);

    const interval = setInterval(() => {
      setLiveDuration((prev) => (prev !== null ? prev + 1000 : null));
    }, 1000);

    return () => clearInterval(interval);
  }, [isRunning, duration]);

  if (liveDuration === null) return null;

  return (
    <span className={cn("font-mono text-xs text-muted-foreground", className)}>
      {formatDuration(liveDuration)}
    </span>
  );
}

/**
 * Summary of workflow timing metrics
 */
interface WorkflowTimingSummaryProps {
  totalDurationMs: number;
  totalCreditsUsed: number;
  completedSteps: number;
  totalSteps: number;
  className?: string;
}

export function WorkflowTimingSummary({
  totalDurationMs,
  totalCreditsUsed,
  completedSteps,
  totalSteps,
  className,
}: WorkflowTimingSummaryProps) {
  return (
    <div className={cn("flex items-center gap-4 text-sm text-muted-foreground", className)}>
      <div className="flex items-center gap-1.5">
        <Clock className="w-4 h-4" />
        <span>{formatDuration(totalDurationMs)}</span>
      </div>
      {totalCreditsUsed > 0 && (
        <div className="flex items-center gap-1.5">
          <span className="text-amber-500">◆</span>
          <span>{totalCreditsUsed.toLocaleString()} credits</span>
        </div>
      )}
      <div className="flex items-center gap-1.5">
        <CheckCircle2 className="w-4 h-4" />
        <span>{completedSteps}/{totalSteps} steps</span>
      </div>
    </div>
  );
}
