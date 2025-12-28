"use client";

/**
 * SessionContext - Centralized Session State Management
 * 
 * Provides session state across the entire application via React Context.
 * Eliminates duplicate API calls from multiple `useSession` hooks.
 * 
 * @example
 * // In layout.tsx
 * <SessionProvider>
 *   {children}
 * </SessionProvider>
 * 
 * // In any component
 * const { session, isLoading, isAuthenticated, refresh } = useSessionContext();
 */

import { createContext, useContext, useCallback, useEffect, useState, ReactNode } from "react";
import { api, AuthSession } from "@/lib/api";

interface SessionContextValue {
    /** Current session data */
    session: AuthSession | null;
    /** Whether session is being fetched */
    isLoading: boolean;
    /** Convenience boolean for auth status */
    isAuthenticated: boolean;
    /** Error message if session fetch failed */
    error: string | null;
    /** Force refresh session data */
    refresh: () => Promise<void>;
}

const SessionContext = createContext<SessionContextValue | null>(null);

interface SessionProviderProps {
    children: ReactNode;
}

/**
 * SessionProvider wraps the application to provide session state.
 * Place in layout.tsx to ensure single fetch across all components.
 */
export function SessionProvider({ children }: SessionProviderProps) {
    const [session, setSession] = useState<AuthSession | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchSession = useCallback(async () => {
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
    }, []);

    useEffect(() => {
        void fetchSession();
    }, [fetchSession]);

    const isAuthenticated = Boolean(session?.authenticated);

    return (
        <SessionContext.Provider
            value={{
                session,
                isLoading,
                isAuthenticated,
                error,
                refresh: fetchSession,
            }}
        >
            {children}
        </SessionContext.Provider>
    );
}

/**
 * Hook to access session context.
 * Must be used within a SessionProvider.
 * 
 * @throws Error if used outside SessionProvider
 * 
 * @example
 * const { session, isLoading, isAuthenticated } = useSessionContext();
 * if (isLoading) return <Spinner />;
 * if (!isAuthenticated) return <LoginPrompt />;
 */
export function useSessionContext(): SessionContextValue {
    const context = useContext(SessionContext);
    if (!context) {
        throw new Error("useSessionContext must be used within a SessionProvider");
    }
    return context;
}

/**
 * Optional hook that doesn't throw if outside provider.
 * Returns null if no provider is found.
 */
export function useSessionContextOptional(): SessionContextValue | null {
    return useContext(SessionContext);
}
