"use client";

/**
 * SyncStatusIndicator - Visual Sync Status Display
 *
 * Shows the current synchronization status for chain data.
 * Displays as a small badge/indicator in the corner of the screen.
 *
 * 2026 Pattern: "Status at a Glance"
 */

import { Loader2, AlertTriangle, CheckCircle2, WifiOff, Cloud, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { OptimisticSyncStatus } from "./hooks/useChainDataWithOptimism";

interface SyncStatusIndicatorProps {
  /** Current sync status */
  status: OptimisticSyncStatus;
  /** Whether there are pending items */
  hasPending?: boolean;
  /** Number of pending items */
  pendingCount?: number;
  /** Retry handler */
  onRetry?: () => void;
  /** Position on screen */
  position?: "bottom-right" | "bottom-left" | "top-right" | "top-left";
  /** Size variant */
  size?: "sm" | "default";
  /** Additional class name */
  className?: string;
  /** Show even when idle (default: false) */
  showWhenIdle?: boolean;
}

/**
 * Position class mapping
 */
const POSITION_CLASSES: Record<NonNullable<SyncStatusIndicatorProps["position"]>, string> = {
  "bottom-right": "fixed bottom-4 right-4",
  "bottom-left": "fixed bottom-4 left-4",
  "top-right": "fixed top-4 right-4",
  "top-left": "fixed top-4 left-4",
};

/**
 * SyncStatusIndicator Component
 *
 * @example
 * ```tsx
 * const { syncStatus, hasPendingSync, pendingSyncCount, retrySync } = useChainDataWithOptimism();
 *
 * return (
 *   <SyncStatusIndicator
 *     status={syncStatus}
 *     hasPending={hasPendingSync}
 *     pendingCount={pendingSyncCount}
 *     onRetry={retrySync}
 *   />
 * );
 * ```
 */
export function SyncStatusIndicator({
  status,
  hasPending = false,
  pendingCount = 0,
  onRetry,
  position = "bottom-right",
  size = "default",
  className,
  showWhenIdle = false,
}: SyncStatusIndicatorProps) {
  // Don't show when idle and nothing pending (unless explicitly requested)
  if (status === "idle" && !hasPending && !showWhenIdle) {
    return null;
  }

  const isSmall = size === "sm";

  return (
    <div
      className={cn(
        POSITION_CLASSES[position],
        "z-50 transition-all duration-300",
        className
      )}
    >
      {status === "syncing" && (
        <Badge
          variant="secondary"
          className={cn(
            "gap-1.5 animate-pulse",
            isSmall ? "text-xs px-2 py-0.5" : "text-sm px-3 py-1"
          )}
        >
          <Loader2 className={cn("animate-spin", isSmall ? "w-3 h-3" : "w-4 h-4")} />
          <span>저장 중...</span>
          {pendingCount > 1 && <span className="text-muted-foreground">({pendingCount})</span>}
        </Badge>
      )}

      {status === "error" && (
        <div className="flex items-center gap-2">
          <Badge
            variant="destructive"
            className={cn(
              "gap-1.5",
              isSmall ? "text-xs px-2 py-0.5" : "text-sm px-3 py-1"
            )}
          >
            <AlertTriangle className={isSmall ? "w-3 h-3" : "w-4 h-4"} />
            <span>동기화 실패</span>
          </Badge>
          {onRetry && (
            <Button
              variant="outline"
              size={isSmall ? "sm" : "default"}
              onClick={onRetry}
              className={cn(
                "gap-1",
                isSmall ? "h-6 px-2 text-xs" : "h-8 px-3 text-sm"
              )}
            >
              <RefreshCw className={isSmall ? "w-3 h-3" : "w-4 h-4"} />
              재시도
            </Button>
          )}
        </div>
      )}

      {status === "offline" && (
        <Badge
          variant="outline"
          className={cn(
            "gap-1.5 bg-background/80 backdrop-blur",
            isSmall ? "text-xs px-2 py-0.5" : "text-sm px-3 py-1"
          )}
        >
          <WifiOff className={isSmall ? "w-3 h-3" : "w-4 h-4"} />
          <span>오프라인</span>
          {pendingCount > 0 && (
            <span className="text-muted-foreground">({pendingCount} 대기중)</span>
          )}
        </Badge>
      )}

      {status === "idle" && hasPending && (
        <Badge
          variant="secondary"
          className={cn(
            "gap-1.5",
            isSmall ? "text-xs px-2 py-0.5" : "text-sm px-3 py-1"
          )}
        >
          <Cloud className={isSmall ? "w-3 h-3" : "w-4 h-4"} />
          <span>저장 대기중</span>
          {pendingCount > 1 && <span className="text-muted-foreground">({pendingCount})</span>}
        </Badge>
      )}

      {status === "idle" && !hasPending && showWhenIdle && (
        <Badge
          variant="outline"
          className={cn(
            "gap-1.5 bg-background/50",
            isSmall ? "text-xs px-2 py-0.5" : "text-sm px-3 py-1"
          )}
        >
          <CheckCircle2 className={cn(isSmall ? "w-3 h-3" : "w-4 h-4", "text-green-500")} />
          <span>저장됨</span>
        </Badge>
      )}
    </div>
  );
}

/**
 * Inline sync status for embedding in other components
 */
interface InlineSyncStatusProps {
  status: OptimisticSyncStatus;
  className?: string;
}

export function InlineSyncStatus({ status, className }: InlineSyncStatusProps) {
  if (status === "idle") return null;

  return (
    <span className={cn("inline-flex items-center gap-1 text-xs", className)}>
      {status === "syncing" && (
        <>
          <Loader2 className="w-3 h-3 animate-spin" />
          <span className="text-muted-foreground">저장 중</span>
        </>
      )}
      {status === "error" && (
        <>
          <AlertTriangle className="w-3 h-3 text-destructive" />
          <span className="text-destructive">동기화 실패</span>
        </>
      )}
      {status === "offline" && (
        <>
          <WifiOff className="w-3 h-3 text-muted-foreground" />
          <span className="text-muted-foreground">오프라인</span>
        </>
      )}
    </span>
  );
}
