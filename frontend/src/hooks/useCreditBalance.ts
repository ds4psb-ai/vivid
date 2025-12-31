import { useCallback, useEffect, useState } from "react";
import { api, type CreditBalance } from "@/lib/api";
import { normalizeApiError } from "@/lib/errors";

interface UseCreditBalanceResult {
  balance: number;
  details: CreditBalance | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  /** True if user is authenticated and can access credits */
  isAuthenticated: boolean;
}

/**
 * Fetches user credit balance from session-authenticated backend.
 * Returns error if not authenticated.
 */
export function useCreditBalance(
  enabled: boolean = true
): UseCreditBalanceResult {
  const [details, setDetails] = useState<CreditBalance | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(true);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const next = await api.getCreditsBalance();
      setDetails(next);
      setIsAuthenticated(true);
    } catch (err: unknown) {
      const errObj = err as { status?: number };
      if (errObj?.status === 401) {
        setIsAuthenticated(false);
        setError("로그인이 필요합니다.");
      } else {
        setError(normalizeApiError(err, "Unable to load credits."));
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;
    void refresh();
  }, [enabled, refresh]);

  return {
    balance: details?.balance ?? 0,
    details,
    isLoading,
    error,
    refresh,
    isAuthenticated,
  };
}
