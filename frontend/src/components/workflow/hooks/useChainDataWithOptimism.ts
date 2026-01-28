"use client";

/**
 * useChainDataWithOptimism - Optimistic State Management for Chain Data
 *
 * Wraps DimensionChainContext with optimistic update pattern:
 * - Immediate UI updates (no waiting for sync)
 * - Debounced background synchronization
 * - Automatic retry on failure
 * - Sync status tracking
 *
 * 2026 Pattern: "Offline-First, Sync-Later"
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useDimensionChain, type ChainData } from "@/contexts/DimensionChainContext";

/**
 * Pending sync item
 */
interface PendingSyncItem {
  key: string;
  data: ChainData;
  timestamp: number;
}

/**
 * Options for the optimistic hook
 */
export interface OptimisticOptions {
  /** Debounce delay before syncing (ms) */
  syncDebounceMs?: number;
  /** Maximum retries on sync failure */
  maxRetries?: number;
  /** Retry delay (ms) */
  retryDelayMs?: number;
  /** Callback when sync error occurs */
  onSyncError?: (error: Error, pendingData: PendingSyncItem[]) => void;
  /** Callback when sync succeeds */
  onSyncSuccess?: () => void;
  /** Auto-sync to session storage with this IP slug */
  autoSyncIpSlug?: string;
}

/**
 * Sync status with pending data info
 */
export type OptimisticSyncStatus = "idle" | "syncing" | "error" | "offline";

/**
 * Result interface for the hook
 */
export interface ChainDataWithOptimismResult {
  /** All context methods from useDimensionChain */
  chainData: Record<string, ChainData>;

  /** Optimistic update that immediately reflects in UI */
  updateChainData: (
    key: string,
    data: Record<string, unknown>,
    summary?: string,
    evidenceRefs?: string[]
  ) => void;

  /** Current sync status */
  syncStatus: OptimisticSyncStatus;

  /** Whether there are pending sync items */
  hasPendingSync: boolean;

  /** Number of pending sync items */
  pendingSyncCount: number;

  /** Manually trigger sync */
  retrySync: () => Promise<void>;

  /** Clear all pending syncs */
  clearPendingSync: () => void;

  /** Original context for advanced usage */
  context: ReturnType<typeof useDimensionChain>;
}

/**
 * Optimistic Chain Data Hook
 *
 * @example
 * ```tsx
 * function MyPanel() {
 *   const { updateChainData, syncStatus, hasPendingSync } = useChainDataWithOptimism({
 *     autoSyncIpSlug: ipSlug,
 *     onSyncError: (err) => toast.error("Sync failed: " + err.message),
 *   });
 *
 *   const handleSave = () => {
 *     // Immediately updates UI, syncs in background
 *     updateChainData("vpe", { logicVector: [...], ... }, "VPE analysis complete");
 *   };
 *
 *   return (
 *     <div>
 *       <button onClick={handleSave}>Save</button>
 *       {hasPendingSync && <span>Saving...</span>}
 *     </div>
 *   );
 * }
 * ```
 */
export function useChainDataWithOptimism(
  options: OptimisticOptions = {}
): ChainDataWithOptimismResult {
  const {
    syncDebounceMs = 1000,
    maxRetries = 3,
    retryDelayMs = 2000,
    onSyncError,
    onSyncSuccess,
    autoSyncIpSlug,
  } = options;

  const context = useDimensionChain();
  const [pendingSync, setPendingSync] = useState<PendingSyncItem[]>([]);
  const [syncStatus, setSyncStatus] = useState<OptimisticSyncStatus>("idle");
  const retryCountRef = useRef(0);
  const syncTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Optimistic update - immediately updates context, queues for sync
   */
  const updateChainData = useCallback(
    (
      key: string,
      data: Record<string, unknown>,
      summary?: string,
      evidenceRefs?: string[]
    ) => {
      // 1. Immediately update context (optimistic)
      context.setChainData(key, data, summary, evidenceRefs);

      // 2. Add to pending sync queue
      const pendingItem: PendingSyncItem = {
        key,
        data: {
          dimensionKey: key,
          output: data,
          timestamp: Date.now(),
          summary,
          evidenceRefs,
        },
        timestamp: Date.now(),
      };

      setPendingSync((prev) => {
        // Replace if same key exists
        const filtered = prev.filter((item) => item.key !== key);
        return [...filtered, pendingItem];
      });

      // Reset retry count on new data
      retryCountRef.current = 0;
    },
    [context]
  );

  /**
   * Perform sync to session storage
   */
  const performSync = useCallback(async (): Promise<boolean> => {
    if (!autoSyncIpSlug || pendingSync.length === 0) {
      return true;
    }

    setSyncStatus("syncing");
    context.setSyncStatus("syncing");

    try {
      // Sync to session storage
      context.syncToSession(autoSyncIpSlug);

      // Clear pending items
      setPendingSync([]);
      setSyncStatus("idle");
      context.setSyncStatus("synced");
      retryCountRef.current = 0;

      onSyncSuccess?.();
      return true;
    } catch (error) {
      const err = error instanceof Error ? error : new Error("Sync failed");

      if (retryCountRef.current < maxRetries) {
        retryCountRef.current++;
        setSyncStatus("error");
        context.setSyncStatus("error");

        // Schedule retry
        setTimeout(() => {
          performSync();
        }, retryDelayMs);

        return false;
      }

      // Max retries exceeded
      setSyncStatus("error");
      context.setSyncStatus("error");
      onSyncError?.(err, pendingSync);
      return false;
    }
  }, [
    autoSyncIpSlug,
    pendingSync,
    context,
    maxRetries,
    retryDelayMs,
    onSyncError,
    onSyncSuccess,
  ]);

  /**
   * Manual retry
   */
  const retrySync = useCallback(async () => {
    retryCountRef.current = 0;
    await performSync();
  }, [performSync]);

  /**
   * Clear pending syncs
   */
  const clearPendingSync = useCallback(() => {
    setPendingSync([]);
    setSyncStatus("idle");
    retryCountRef.current = 0;
  }, []);

  /**
   * Debounced sync effect
   */
  useEffect(() => {
    if (pendingSync.length === 0) return;

    // Clear existing timeout
    if (syncTimeoutRef.current) {
      clearTimeout(syncTimeoutRef.current);
    }

    // Schedule debounced sync
    syncTimeoutRef.current = setTimeout(() => {
      performSync();
    }, syncDebounceMs);

    return () => {
      if (syncTimeoutRef.current) {
        clearTimeout(syncTimeoutRef.current);
      }
    };
  }, [pendingSync, syncDebounceMs, performSync]);

  /**
   * Online/offline detection
   */
  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleOnline = () => {
      if (syncStatus === "offline" && pendingSync.length > 0) {
        retrySync();
      }
    };

    const handleOffline = () => {
      setSyncStatus("offline");
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    // Check initial state
    if (!navigator.onLine) {
      setSyncStatus("offline");
    }

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [syncStatus, pendingSync.length, retrySync]);

  return {
    chainData: context.chainData,
    updateChainData,
    syncStatus,
    hasPendingSync: pendingSync.length > 0,
    pendingSyncCount: pendingSync.length,
    retrySync,
    clearPendingSync,
    context,
  };
}
