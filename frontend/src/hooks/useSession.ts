"use client";

import { useCallback, useEffect, useState } from "react";
import { api, AuthSession } from "@/lib/api";

export const useSession = (enabled = true) => {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isLoading, setIsLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);

  const fetchSession = useCallback(async () => {
    if (!enabled) return Promise.resolve();
    setIsLoading(true);
    try {
      const data = await api.getSession();
      setSession(data);
      setError(null);
    } catch (err) {
      setSession({ authenticated: false });
      setError(err instanceof Error ? err.message : "Failed to load session");
    } finally {
      setIsLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    void fetchSession();
  }, [fetchSession]);

  return { session, isLoading, error, refresh: fetchSession };
};
