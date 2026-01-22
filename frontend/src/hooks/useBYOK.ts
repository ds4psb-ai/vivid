"use client";

/**
 * useBYOK - Bring Your Own Key hook
 *
 * Manages user's personal API key for AI services.
 * Stored encrypted using AES-GCM, never sent to our servers.
 *
 * Security: Uses secure-storage.ts for encrypted storage (P0 hardening)
 */

import { useState, useCallback, useEffect } from "react";
import { secureSet, secureGet, secureRemove, migratePlaintextToSecure } from "@/lib/secure-storage";

const SECURE_KEY = "byok_gemini";
const LEGACY_STORAGE_KEY = "crebit:byok_gemini_key";

interface UseBYOKResult {
    /** Current BYOK key (null if not set) */
    byokKey: string | null;
    /** Whether BYOK is enabled */
    isBYOKEnabled: boolean;
    /** Loading state for async decryption */
    isLoading: boolean;
    /** Set or update BYOK key */
    setBYOKKey: (key: string | null) => Promise<void>;
    /** Clear BYOK key */
    clearBYOKKey: () => void;
    /** Toggle BYOK mode */
    toggleBYOK: () => void;
}

export function useBYOK(): UseBYOKResult {
    const [byokKey, setByokKeyState] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Initialize: migrate plaintext keys and load encrypted value
    useEffect(() => {
        if (typeof window === "undefined") {
            setIsLoading(false);
            return;
        }

        const initializeKey = async () => {
            try {
                // Migrate legacy plaintext key to encrypted storage
                await migratePlaintextToSecure(LEGACY_STORAGE_KEY, SECURE_KEY);

                // Load encrypted key
                const key = await secureGet(SECURE_KEY);
                setByokKeyState(key);
            } catch (error) {
                console.error("[useBYOK] Failed to initialize:", error);
            } finally {
                setIsLoading(false);
            }
        };

        initializeKey();
    }, []);

    const setBYOKKey = useCallback(async (key: string | null) => {
        if (key && key.trim()) {
            await secureSet(SECURE_KEY, key.trim());
            setByokKeyState(key.trim());
        } else {
            secureRemove(SECURE_KEY);
            setByokKeyState(null);
        }
    }, []);

    const clearBYOKKey = useCallback(() => {
        secureRemove(SECURE_KEY);
        setByokKeyState(null);
    }, []);

    const toggleBYOK = useCallback(() => {
        // Not really a toggle, just a convenience to focus on the input
        // Actual toggle would depend on UI implementation
    }, []);

    return {
        byokKey,
        isBYOKEnabled: Boolean(byokKey),
        isLoading,
        setBYOKKey,
        clearBYOKKey,
        toggleBYOK,
    };
}

/**
 * Get headers for API requests with BYOK support and demo user ID
 */
export function getBYOKHeaders(byokKey: string | null): Record<string, string> {
    // Always include x-user-id for demo mode (backend requires auth)
    const userId = typeof window !== "undefined"
        ? localStorage.getItem("userId") || "demo-user"
        : "demo-user";

    const headers: Record<string, string> = {
        "x-user-id": userId,
    };

    if (byokKey) {
        headers["X-Gemini-API-Key"] = byokKey;
    }

    return headers;
}
