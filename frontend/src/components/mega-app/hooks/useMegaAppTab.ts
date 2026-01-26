"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import type { MegaAppTab } from "../types";

interface UseMegaAppTabOptions {
  tabs: MegaAppTab[];
  defaultTab?: string;
  paramName?: string;
}

interface UseMegaAppTabReturn {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

/**
 * Custom hook for URL-synchronized tab state
 *
 * Features:
 * - Syncs tab state with URL search params
 * - Validates tab value against available tabs
 * - Falls back to default tab if invalid
 * - Updates URL without page reload
 */
export function useMegaAppTab({
  tabs,
  defaultTab,
  paramName = "tab",
}: UseMegaAppTabOptions): UseMegaAppTabReturn {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  // Get initial tab from URL or default
  const getInitialTab = useCallback(() => {
    const urlTab = searchParams.get(paramName);
    if (urlTab && tabs.some((t) => t.value === urlTab && !t.isDisabled)) {
      return urlTab;
    }
    return defaultTab || tabs[0]?.value || "";
  }, [searchParams, paramName, tabs, defaultTab]);

  const [activeTab, setActiveTabState] = useState(getInitialTab);

  // Sync state with URL changes
  useEffect(() => {
    const urlTab = searchParams.get(paramName);
    if (urlTab && tabs.some((t) => t.value === urlTab && !t.isDisabled)) {
      setActiveTabState(urlTab);
    }
  }, [searchParams, paramName, tabs]);

  // Update URL when tab changes
  const setActiveTab = useCallback(
    (tab: string) => {
      // Validate tab
      if (!tabs.some((t) => t.value === tab && !t.isDisabled)) {
        return;
      }

      setActiveTabState(tab);

      // Update URL
      const params = new URLSearchParams(searchParams.toString());
      params.set(paramName, tab);
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [tabs, searchParams, paramName, router, pathname]
  );

  return { activeTab, setActiveTab };
}
