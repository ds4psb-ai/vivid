"use client";

/**
 * useBYOK - Bring Your Own Key hook
 * 
 * Manages user's personal API key for AI services.
 * Stored in localStorage, never sent to our servers.
 */

import { useState, useCallback, useEffect } from "react";

const STORAGE_KEY = "crebit:byok_gemini_key";

interface UseBYOKResult {
    /** Current BYOK key (null if not set) */
    byokKey: string | null;
    /** Whether BYOK is enabled */
    isBYOKEnabled: boolean;
    /** Set or update BYOK key */
    setBYOKKey: (key: string | null) => void;
    /** Clear BYOK key */
    clearBYOKKey: () => void;
    /** Toggle BYOK mode */
    toggleBYOK: () => void;
}

export function useBYOK(): UseBYOKResult {
    const [byokKey, setByokKeyState] = useState<string | null>(null);
    const [isInitialized, setIsInitialized] = useState(false);

    // Load from localStorage on mount
    useEffect(() => {
        if (typeof window !== "undefined") {
            const stored = localStorage.getItem(STORAGE_KEY);
            setByokKeyState(stored);
            setIsInitialized(true);
        }
    }, []);

    const setBYOKKey = useCallback((key: string | null) => {
        if (key && key.trim()) {
            localStorage.setItem(STORAGE_KEY, key.trim());
            setByokKeyState(key.trim());
        } else {
            localStorage.removeItem(STORAGE_KEY);
            setByokKeyState(null);
        }
    }, []);

    const clearBYOKKey = useCallback(() => {
        localStorage.removeItem(STORAGE_KEY);
        setByokKeyState(null);
    }, []);

    const toggleBYOK = useCallback(() => {
        // Not really a toggle, just a convenience to focus on the input
        // Actual toggle would depend on UI implementation
    }, []);

    return {
        byokKey: isInitialized ? byokKey : null,
        isBYOKEnabled: Boolean(byokKey),
        setBYOKKey,
        clearBYOKKey,
        toggleBYOK,
    };
}

/**
 * Get headers for API requests with BYOK support
 */
export function getBYOKHeaders(byokKey: string | null): Record<string, string> {
    if (byokKey) {
        return { "X-Gemini-API-Key": byokKey };
    }
    return {};
}
