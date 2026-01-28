"use client";

/**
 * NetworkStatusBadge - Visual indicator for offline state
 *
 * Displays a prominent badge when the user is offline.
 * Auto-hides when connectivity is restored.
 *
 * 2026 UX Pattern: Transparent system state communication
 */

import { WifiOff, RefreshCw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useNetworkStatus } from "@/hooks/useNetworkStatus";
import { useReducedMotion } from "@/hooks/useReducedMotion";

export interface NetworkStatusBadgeProps {
  /** Show even when online (for debugging) */
  forceShow?: boolean;
  /** Custom offline message */
  message?: string;
  /** Show retry button */
  showRetry?: boolean;
}

/**
 * NetworkStatusBadge - Offline indicator component
 *
 * Place this near the top of your layout to show offline status.
 *
 * @example
 * ```tsx
 * // In layout.tsx
 * <NetworkStatusBadge />
 * ```
 */
export function NetworkStatusBadge({
  forceShow = false,
  message = "오프라인",
  showRetry = true,
}: NetworkStatusBadgeProps) {
  const { isOnline, isChecking, checkConnectivity } = useNetworkStatus({
    showToasts: false, // Badge handles visual feedback
  });
  const prefersReducedMotion = useReducedMotion();

  const shouldShow = forceShow || !isOnline;

  if (!shouldShow) return null;

  const animationProps = prefersReducedMotion
    ? {}
    : {
        initial: { opacity: 0, y: -20 },
        animate: { opacity: 1, y: 0 },
        exit: { opacity: 0, y: -20 },
      };

  return (
    <AnimatePresence>
      {shouldShow && (
        <motion.div
          {...animationProps}
          className="fixed top-4 left-1/2 -translate-x-1/2 z-50"
        >
          <div className="flex items-center gap-2 px-4 py-2 bg-gray-800/90 backdrop-blur-sm border border-gray-600/50 rounded-full shadow-lg">
            <WifiOff className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-300 font-medium">{message}</span>

            {showRetry && (
              <button
                onClick={() => checkConnectivity()}
                disabled={isChecking}
                className="ml-2 p-1 rounded-full hover:bg-white/10 transition-colors disabled:opacity-50"
                aria-label="연결 재시도"
              >
                <RefreshCw
                  className={`w-3.5 h-3.5 text-gray-400 ${
                    isChecking ? "animate-spin" : ""
                  }`}
                />
              </button>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/**
 * Compact inline offline indicator
 *
 * Use this for smaller spaces or inline status.
 */
export function NetworkStatusInline({ className = "" }: { className?: string }) {
  const { isOnline } = useNetworkStatus({ showToasts: false });

  if (isOnline) return null;

  return (
    <span
      className={`inline-flex items-center gap-1 text-xs text-gray-400 ${className}`}
    >
      <WifiOff className="w-3 h-3" />
      <span>오프라인</span>
    </span>
  );
}
