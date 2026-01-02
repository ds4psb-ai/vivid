"use client";

/**
 * TeachingSettingsContext - Manages Teaching App settings sync with backend.
 * 
 * Provides centralized API key and project data management for Teaching Apps.
 * Syncs with backend API and communicates with iframe apps via postMessage.
 */

import { createContext, useContext, useCallback, useEffect, useState, ReactNode, useRef } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

export interface TeachingSettings {
    hasApiKey: boolean;
    apiKeyPreview: string | null;
    promptData: Record<string, unknown>;
    storyboardData: Record<string, unknown>;
    imageToolData: Record<string, unknown>;
    shotCatchData: Record<string, unknown>;
    language: string;
    selectedModel: string;
}

interface TeachingSettingsContextValue {
    settings: TeachingSettings | null;
    isLoading: boolean;
    error: string | null;
    /** Save API key to backend */
    saveApiKey: (apiKey: string) => Promise<void>;
    /** Clear API key from backend */
    clearApiKey: () => Promise<void>;
    /** Get full API key (for iframe injection) */
    getFullApiKey: () => Promise<string | null>;
    /** Update project data for a specific app */
    updateAppData: (appType: "prompt" | "storyboard" | "imageTool" | "shotCatch", data: Record<string, unknown>) => Promise<void>;
    /** Force refresh settings from backend */
    refresh: () => Promise<void>;
}

const TeachingSettingsContext = createContext<TeachingSettingsContextValue | null>(null);

interface TeachingSettingsProviderProps {
    children: ReactNode;
}

export function TeachingSettingsProvider({ children }: TeachingSettingsProviderProps) {
    const [settings, setSettings] = useState<TeachingSettings | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const fetchSettings = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/api/user/teaching-settings`, {
                credentials: "include",
            });
            if (!res.ok) {
                if (res.status === 401) {
                    // Not authenticated, return empty settings
                    setSettings({
                        hasApiKey: false,
                        apiKeyPreview: null,
                        promptData: {},
                        storyboardData: {},
                        imageToolData: {},
                        shotCatchData: {},
                        language: "ko",
                        selectedModel: "gemini-2.5-flash",
                    });
                    return;
                }
                throw new Error("Failed to fetch settings");
            }
            const data = await res.json();
            setSettings({
                hasApiKey: data.has_api_key,
                apiKeyPreview: data.api_key_preview,
                promptData: data.prompt_data || {},
                storyboardData: data.storyboard_data || {},
                imageToolData: data.image_tool_data || {},
                shotCatchData: data.shot_catch_data || {},
                language: data.language || "ko",
                selectedModel: data.selected_model || "gemini-2.5-flash",
            });
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load settings");
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        void fetchSettings();
    }, [fetchSettings]);

    const saveApiKey = useCallback(async (apiKey: string) => {
        const res = await fetch(`${API_BASE_URL}/api/user/teaching-settings`, {
            method: "PUT",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_key: apiKey }),
        });
        if (!res.ok) throw new Error("Failed to save API key");
        await fetchSettings();
    }, [fetchSettings]);

    const clearApiKey = useCallback(async () => {
        const res = await fetch(`${API_BASE_URL}/api/user/teaching-settings`, {
            method: "PUT",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_key: "" }),
        });
        if (!res.ok) throw new Error("Failed to clear API key");
        await fetchSettings();
    }, [fetchSettings]);

    const getFullApiKey = useCallback(async (): Promise<string | null> => {
        try {
            const res = await fetch(`${API_BASE_URL}/api/user/teaching-settings/api-key`, {
                credentials: "include",
            });
            if (!res.ok) return null;
            const data = await res.json();
            return data.api_key || null;
        } catch {
            return null;
        }
    }, []);

    const updateAppData = useCallback(async (
        appType: "prompt" | "storyboard" | "imageTool" | "shotCatch",
        data: Record<string, unknown>
    ) => {
        // Debounce updates
        if (debounceTimerRef.current) {
            clearTimeout(debounceTimerRef.current);
        }

        debounceTimerRef.current = setTimeout(async () => {
            const fieldMap: Record<string, string> = {
                prompt: "prompt_data",
                storyboard: "storyboard_data",
                imageTool: "image_tool_data",
                shotCatch: "shot_catch_data",
            };

            const res = await fetch(`${API_BASE_URL}/api/user/teaching-settings`, {
                method: "PUT",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ [fieldMap[appType]]: data }),
            });
            if (!res.ok) {
                console.error("Failed to save app data");
            }
        }, 1000); // 1 second debounce
    }, []);

    return (
        <TeachingSettingsContext.Provider
            value={{
                settings,
                isLoading,
                error,
                saveApiKey,
                clearApiKey,
                getFullApiKey,
                updateAppData,
                refresh: fetchSettings,
            }}
        >
            {children}
        </TeachingSettingsContext.Provider>
    );
}

export function useTeachingSettings(): TeachingSettingsContextValue {
    const context = useContext(TeachingSettingsContext);
    if (!context) {
        throw new Error("useTeachingSettings must be used within a TeachingSettingsProvider");
    }
    return context;
}
