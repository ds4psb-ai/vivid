"use client";

/**
 * useNetworkStatus - Offline Detection & Network Resilience
 *
 * Monitors network connectivity and provides state for:
 * - Offline mode detection
 * - Reconnection events
 * - Toast notifications on status changes
 *
 * 2026 UX Pattern: Resilient UI that gracefully handles connectivity issues
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { useToast } from "@/components/Toast";

export interface NetworkStatusResult {
  /** Whether the browser is currently online */
  isOnline: boolean;
  /** Whether the user was offline at some point in this session */
  wasOffline: boolean;
  /** Whether we're currently checking connectivity */
  isChecking: boolean;
  /** Last time connectivity was confirmed */
  lastOnlineAt: Date | null;
  /** Manually trigger a connectivity check */
  checkConnectivity: () => Promise<boolean>;
}

/**
 * Hook for monitoring network status
 *
 * @param options - Configuration options
 * @returns Network status state and utilities
 *
 * @example
 * ```tsx
 * const { isOnline, wasOffline, checkConnectivity } = useNetworkStatus();
 *
 * if (!isOnline) {
 *   return <OfflineMessage />;
 * }
 *
 * // Retry on reconnect
 * useEffect(() => {
 *   if (wasOffline && isOnline) {
 *     refetchData();
 *   }
 * }, [isOnline, wasOffline]);
 * ```
 */
export function useNetworkStatus(options: {
  /** Show toast notifications on status change (default: true) */
  showToasts?: boolean;
  /** URL to ping for connectivity check (optional) */
  pingUrl?: string;
} = {}): NetworkStatusResult {
  const { showToasts = true } = options;
  const toast = useToast();

  const [isOnline, setIsOnline] = useState(true);
  const [wasOffline, setWasOffline] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [lastOnlineAt, setLastOnlineAt] = useState<Date | null>(null);

  // Track if we've shown the offline toast
  const hasShownOfflineToast = useRef(false);

  // Manual connectivity check
  const checkConnectivity = useCallback(async (): Promise<boolean> => {
    setIsChecking(true);

    try {
      // Try to fetch a small resource to verify actual connectivity
      // navigator.onLine can give false positives
      if (options.pingUrl) {
        const response = await fetch(options.pingUrl, {
          method: "HEAD",
          cache: "no-store",
        });
        const connected = response.ok;
        setIsOnline(connected);
        if (connected) {
          setLastOnlineAt(new Date());
        }
        return connected;
      }

      // Fall back to navigator.onLine
      const connected = navigator.onLine;
      setIsOnline(connected);
      if (connected) {
        setLastOnlineAt(new Date());
      }
      return connected;
    } catch {
      setIsOnline(false);
      return false;
    } finally {
      setIsChecking(false);
    }
  }, [options.pingUrl]);

  // Set up event listeners
  useEffect(() => {
    if (typeof window === "undefined") return;

    // Initial state
    setIsOnline(navigator.onLine);
    if (navigator.onLine) {
      setLastOnlineAt(new Date());
    }

    const handleOnline = () => {
      setIsOnline(true);
      setLastOnlineAt(new Date());

      // Show reconnection toast if we were offline
      if (showToasts && hasShownOfflineToast.current) {
        toast.success("네트워크가 복구되었습니다");
        hasShownOfflineToast.current = false;
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
      setWasOffline(true);

      // Show offline toast
      if (showToasts && !hasShownOfflineToast.current) {
        toast.warning("오프라인 모드 - 일부 기능이 제한됩니다");
        hasShownOfflineToast.current = true;
      }
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [showToasts, toast]);

  return {
    isOnline,
    wasOffline,
    isChecking,
    lastOnlineAt,
    checkConnectivity,
  };
}

/**
 * Hook for offline-first data fetching pattern
 *
 * Provides utilities for handling offline scenarios with queued requests.
 */
export function useOfflineQueue<T>() {
  const { isOnline } = useNetworkStatus({ showToasts: false });
  const [queue, setQueue] = useState<T[]>([]);

  const enqueue = useCallback((item: T) => {
    setQueue((prev) => [...prev, item]);
  }, []);

  const dequeue = useCallback(() => {
    setQueue((prev) => prev.slice(1));
    return queue[0];
  }, [queue]);

  const clearQueue = useCallback(() => {
    setQueue([]);
  }, []);

  return {
    isOnline,
    queue,
    queueLength: queue.length,
    enqueue,
    dequeue,
    clearQueue,
    hasQueuedItems: queue.length > 0,
  };
}
