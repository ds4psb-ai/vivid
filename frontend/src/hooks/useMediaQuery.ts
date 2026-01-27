"use client";

import { useCallback, useSyncExternalStore } from "react";

/**
 * Responsive media query hook using useSyncExternalStore for SSR compatibility
 * @param query CSS media query string (e.g., "(max-width: 767px)")
 * @returns boolean indicating if the query matches
 */
export function useMediaQuery(query: string): boolean {
  const subscribe = useCallback(
    (callback: () => void) => {
      const mediaQuery = window.matchMedia(query);
      mediaQuery.addEventListener("change", callback);
      return () => mediaQuery.removeEventListener("change", callback);
    },
    [query]
  );

  const getSnapshot = useCallback(
    () => window.matchMedia(query).matches,
    [query]
  );

  const getServerSnapshot = useCallback(() => false, []);

  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

/**
 * Convenience hook for mobile detection
 * @returns boolean indicating if viewport is mobile (<768px)
 */
export function useIsMobile(): boolean {
  return useMediaQuery("(max-width: 767px)");
}

/**
 * Convenience hook for desktop detection
 * @returns boolean indicating if viewport is desktop (>=768px)
 */
export function useIsDesktop(): boolean {
  return useMediaQuery("(min-width: 768px)");
}
