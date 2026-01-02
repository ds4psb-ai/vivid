"use client";

/**
 * CreditContext - Unified Credit Balance Management
 * 
 * Provides credit balance state across Teaching apps and future AI tools.
 * Supports real-time updates and integration with BYOK.
 */

import { createContext, useContext, useCallback, useEffect, useState, ReactNode } from "react";
import { api, CreditBalance } from "@/lib/api";

interface CreditContextValue {
    /** Current credit balance (total) */
    balance: number;
    /** Detailed breakdown */
    breakdown: {
        subscription: number;
        topup: number;
        promo: number;
    } | null;
    /** Loading state */
    isLoading: boolean;
    /** Error message */
    error: string | null;
    /** Force refresh balance */
    refresh: () => Promise<void>;
    /** Check if user has enough credits */
    hasEnoughCredits: (cost: number) => boolean;
}

const CreditContext = createContext<CreditContextValue | null>(null);

interface CreditProviderProps {
    children: ReactNode;
    /** Polling interval in ms (default: 30000) */
    pollingInterval?: number;
}

export function CreditProvider({ children, pollingInterval = 30000 }: CreditProviderProps) {
    const [balance, setBalance] = useState<number>(0);
    const [breakdown, setBreakdown] = useState<CreditContextValue["breakdown"]>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchBalance = useCallback(async () => {
        try {
            const data: CreditBalance = await api.getCreditsBalance();
            const total = data.balance ?? (
                (data.subscription_credits ?? 0) +
                (data.topup_credits ?? 0) +
                (data.promo_credits ?? 0)
            );
            setBalance(total);
            setBreakdown({
                subscription: data.subscription_credits ?? 0,
                topup: data.topup_credits ?? 0,
                promo: data.promo_credits ?? 0,
            });
            setError(null);
        } catch (err) {
            // Don't reset balance on error (keep last known value)
            setError(err instanceof Error ? err.message : "Failed to load credits");
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Initial fetch
    useEffect(() => {
        void fetchBalance();
    }, [fetchBalance]);

    // Polling
    useEffect(() => {
        if (pollingInterval <= 0) return;
        const interval = setInterval(() => {
            void fetchBalance();
        }, pollingInterval);
        return () => clearInterval(interval);
    }, [fetchBalance, pollingInterval]);

    const hasEnoughCredits = useCallback((cost: number): boolean => {
        return balance >= cost;
    }, [balance]);

    return (
        <CreditContext.Provider
            value={{
                balance,
                breakdown,
                isLoading,
                error,
                refresh: fetchBalance,
                hasEnoughCredits,
            }}
        >
            {children}
        </CreditContext.Provider>
    );
}

/**
 * Hook to access credit context.
 * Must be used within a CreditProvider.
 */
export function useCreditContext(): CreditContextValue {
    const context = useContext(CreditContext);
    if (!context) {
        throw new Error("useCreditContext must be used within a CreditProvider");
    }
    return context;
}

/**
 * Optional hook that doesn't throw if outside provider.
 */
export function useCreditContextOptional(): CreditContextValue | null {
    return useContext(CreditContext);
}
