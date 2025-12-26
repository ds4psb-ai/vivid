import { useCallback, useEffect, useState } from "react";
import { api, type CreditBalance } from "@/lib/api";
import { normalizeApiError } from "@/lib/errors";

interface UseCreditBalanceResult {
  balance: number;
  details: CreditBalance | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useCreditBalance(
  userId?: string,
  enabled: boolean = true
): UseCreditBalanceResult {
  const resolvedUserId =
    userId || process.env.NEXT_PUBLIC_USER_ID || "demo-user";
  const [details, setDetails] = useState<CreditBalance | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const next = await api.getCreditsBalance(resolvedUserId);
      setDetails(next);
    } catch (err) {
      setError(normalizeApiError(err, "Unable to load credits."));
    } finally {
      setIsLoading(false);
    }
  }, [resolvedUserId]);

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
  };
}
