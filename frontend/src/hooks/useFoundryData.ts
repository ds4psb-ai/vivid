"use client";

import { useState, useEffect, useCallback, useRef } from "react";

interface UseFoundryDataReturn<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
  lastUpdated: Date | null;
}

export function useFoundryData<T>(
  fetcher: () => Promise<T>,
  options?: { refreshInterval?: number; enabled?: boolean }
): UseFoundryDataReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const doFetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await fetcherRef.current();
      setData(result);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (options?.enabled === false) return;
    doFetch();
    if (options?.refreshInterval) {
      const interval = setInterval(doFetch, options.refreshInterval);
      return () => clearInterval(interval);
    }
  }, [doFetch, options?.enabled, options?.refreshInterval]);

  return { data, isLoading, error, refresh: doFetch, lastUpdated };
}
