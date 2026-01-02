'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import type { DirectorPack } from '@/types/director-pack';
import type { SceneOverride } from '@/components/SceneDNAEditor';

// =============================================================================
// Types
// =============================================================================

export interface DirectorPackState {
    /** Selected DirectorPack */
    pack: DirectorPack | null;
    /** Whether DNA mode is enabled */
    isEnabled: boolean;
    /** Per-scene overrides */
    sceneOverrides: Record<string, SceneOverride>;
    /** Loading state */
    isLoading: boolean;
    /** Error state */
    error: string | null;
    /** Available packs list */
    availablePacks: DirectorPackSummary[];
    /** Retry count */
    retryCount: number;
}

export interface DirectorPackSummary {
    pack_id: string;
    pattern_id: string;
    version: string;
    invariant_count: number;
    slot_count: number;
    forbidden_count: number;
}

export interface DirectorPackActions {
    /** Enable/disable DNA mode */
    setEnabled: (enabled: boolean) => void;
    /** Select a pack */
    selectPack: (pack: DirectorPack | null) => void;
    /** Load pack by ID */
    loadPackById: (packId: string) => Promise<void>;
    /** Load pack by capsule pattern */
    loadPackByPattern: (patternId: string) => Promise<void>;
    /** Load available packs list */
    loadAvailablePacks: (patternFilter?: string) => Promise<void>;
    /** Update scene overrides */
    updateSceneOverrides: (overrides: Record<string, SceneOverride>) => void;
    /** Clear all state */
    reset: () => void;
    /** Clear error */
    clearError: () => void;
    /** Get payload for API request */
    getApiPayload: () => {
        director_pack?: Record<string, unknown>;
        scene_overrides?: Record<string, Record<string, unknown>>;
    };
    /** Validate shots against current pack */
    validateShots: (shots: Array<{ shot_id: string; prompt: string }>) => Promise<ValidationResult | null>;
}

export interface ValidationResult {
    total_shots: number;
    compliant_shots: number;
    partial_shots: number;
    violation_shots: number;
    overall_compliance_rate: number;
    summary: string;
    shot_reports: Array<{
        shot_id: string;
        overall_level: string;
        overall_confidence: number;
        suggestions: string[];
    }>;
}

export interface UseDirectorPackStateReturn extends DirectorPackState, DirectorPackActions { }

// =============================================================================
// Constants
// =============================================================================

const STORAGE_KEY = 'crebit_director_pack_state';
const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1000;
const API_BASE = '/api/v1/director-packs';

// =============================================================================
// Helper Functions
// =============================================================================

function saveToStorage(packId: string | null, isEnabled: boolean) {
    if (typeof window === 'undefined') return;
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ packId, isEnabled }));
    } catch {
        // Ignore storage errors
    }
}

function loadFromStorage(): { packId: string | null; isEnabled: boolean } | null {
    if (typeof window === 'undefined') return null;
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            return JSON.parse(stored);
        }
    } catch {
        // Ignore storage errors
    }
    return null;
}

async function fetchWithRetry(
    url: string,
    options?: RequestInit,
    maxRetries = MAX_RETRIES
): Promise<Response> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            const response = await fetch(url, options);
            if (response.ok) return response;

            // Don't retry 4xx errors
            if (response.status >= 400 && response.status < 500) {
                throw new Error(`API error: ${response.status}`);
            }

            lastError = new Error(`Server error: ${response.status}`);
        } catch (err) {
            lastError = err instanceof Error ? err : new Error(String(err));
        }

        // Wait before retry (exponential backoff)
        if (attempt < maxRetries - 1) {
            await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS * (attempt + 1)));
        }
    }

    throw lastError || new Error('Request failed');
}

// =============================================================================
// Hook Implementation
// =============================================================================

export function useDirectorPackState(capsuleId?: string): UseDirectorPackStateReturn {
    // State
    const [pack, setPack] = useState<DirectorPack | null>(null);
    const [isEnabled, setIsEnabledState] = useState(false);
    const [sceneOverrides, setSceneOverrides] = useState<Record<string, SceneOverride>>({});
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [availablePacks, setAvailablePacks] = useState<DirectorPackSummary[]>([]);
    const [retryCount, setRetryCount] = useState(0);

    // Refs
    const initialLoadDone = useRef(false);
    const packsCache = useRef<Map<string, DirectorPack>>(new Map());

    // Set enabled with storage persistence
    const setEnabled = useCallback((enabled: boolean) => {
        setIsEnabledState(enabled);
        if (!enabled) {
            setPack(null);
            setSceneOverrides({});
        }
        saveToStorage(pack?.meta.pack_id || null, enabled);
    }, [pack]);

    // Select a pack
    const selectPack = useCallback((newPack: DirectorPack | null) => {
        setPack(newPack);
        setSceneOverrides({});
        setError(null);
        if (newPack) {
            setIsEnabledState(true);
            saveToStorage(newPack.meta.pack_id, true);
            // Cache the pack
            packsCache.current.set(newPack.meta.pack_id, newPack);
        }
    }, []);

    // Load pack by ID with caching
    const loadPackById = useCallback(async (packId: string) => {
        // Check cache first
        const cached = packsCache.current.get(packId);
        if (cached) {
            setPack(cached);
            setIsEnabledState(true);
            saveToStorage(packId, true);
            return;
        }

        setIsLoading(true);
        setError(null);
        setRetryCount(0);

        try {
            const response = await fetchWithRetry(`${API_BASE}/${packId}`);
            const data = await response.json();

            if (data.success && data.data) {
                const loadedPack = data.data as DirectorPack;
                setPack(loadedPack);
                setIsEnabledState(true);
                saveToStorage(packId, true);
                packsCache.current.set(packId, loadedPack);
            } else {
                throw new Error(data.message || 'Failed to load pack');
            }
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Failed to load pack';
            setError(message);
            console.error('[useDirectorPackState] loadPackById error:', message);
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Load pack by pattern
    const loadPackByPattern = useCallback(async (patternId: string) => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetchWithRetry(`${API_BASE}/by-pattern/${encodeURIComponent(patternId)}`);
            const data = await response.json();

            if (data.success && data.data) {
                const loadedPack = data.data as DirectorPack;
                setPack(loadedPack);
                setIsEnabledState(true);
                saveToStorage(loadedPack.meta.pack_id, true);
                packsCache.current.set(loadedPack.meta.pack_id, loadedPack);
            } else {
                throw new Error(data.message || 'No pack found for pattern');
            }
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Failed to load pack';
            setError(message);
            console.error('[useDirectorPackState] loadPackByPattern error:', message);
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Load available packs list
    const loadAvailablePacks = useCallback(async (patternFilter?: string) => {
        setIsLoading(true);

        try {
            const params = new URLSearchParams();
            if (patternFilter) params.set('pattern_id', patternFilter);

            const response = await fetchWithRetry(`${API_BASE}/?${params}`);
            const data = await response.json();

            if (data.success && Array.isArray(data.data)) {
                setAvailablePacks(data.data);
            }
        } catch (err) {
            console.error('[useDirectorPackState] loadAvailablePacks error:', err);
            // Don't set error - this is a background operation
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Update scene overrides
    const updateSceneOverrides = useCallback((overrides: Record<string, SceneOverride>) => {
        setSceneOverrides(overrides);
    }, []);

    // Reset all state
    const reset = useCallback(() => {
        setPack(null);
        setIsEnabledState(false);
        setSceneOverrides({});
        setError(null);
        setRetryCount(0);
        saveToStorage(null, false);
    }, []);

    // Clear error
    const clearError = useCallback(() => {
        setError(null);
    }, []);

    // Get payload for API request
    const getApiPayload = useCallback((): {
        director_pack?: Record<string, unknown>;
        scene_overrides?: Record<string, Record<string, unknown>>;
    } => {
        if (!isEnabled || !pack) {
            return {};
        }

        const enabledOverrides: Record<string, Record<string, unknown>> = {};
        Object.entries(sceneOverrides).forEach(([sceneId, override]) => {
            if (override.enabled) {
                enabledOverrides[sceneId] = override as unknown as Record<string, unknown>;
            }
        });

        return {
            director_pack: pack as unknown as Record<string, unknown>,
            scene_overrides: Object.keys(enabledOverrides).length > 0 ? enabledOverrides : undefined,
        };
    }, [isEnabled, pack, sceneOverrides]);

    // Validate shots against current pack
    const validateShots = useCallback(async (
        shots: Array<{ shot_id: string; prompt: string }>
    ): Promise<ValidationResult | null> => {
        if (!pack) return null;

        try {
            const response = await fetchWithRetry(`${API_BASE}/validate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    pack_id: pack.meta.pack_id,
                    shots,
                }),
            });

            const data = await response.json();
            if (data.success && data.data) {
                return data.data as ValidationResult;
            }
        } catch (err) {
            console.error('[useDirectorPackState] validateShots error:', err);
        }

        return null;
    }, [pack]);

    // Restore state from localStorage on mount
    useEffect(() => {
        if (initialLoadDone.current) return;
        initialLoadDone.current = true;

        const stored = loadFromStorage();
        if (stored?.packId && stored?.isEnabled) {
            loadPackById(stored.packId).catch(() => {
                // Silently fail - user can manually select
            });
        }
    }, [loadPackById]);

    // Auto-load pack when capsuleId changes
    useEffect(() => {
        if (capsuleId && isEnabled && !pack && !isLoading) {
            // Try to find matching pack from pattern
            const pattern = capsuleId.split('.').pop() || '';
            if (pattern) {
                loadPackByPattern(pattern).catch(() => {
                    // Silently fail - user can manually select
                });
            }
        }
    }, [capsuleId, isEnabled, pack, isLoading, loadPackByPattern]);

    // Load available packs when enabled
    useEffect(() => {
        if (isEnabled && availablePacks.length === 0) {
            loadAvailablePacks();
        }
    }, [isEnabled, availablePacks.length, loadAvailablePacks]);

    return {
        // State
        pack,
        isEnabled,
        sceneOverrides,
        isLoading,
        error,
        availablePacks,
        retryCount,
        // Actions
        setEnabled,
        selectPack,
        loadPackById,
        loadPackByPattern,
        loadAvailablePacks,
        updateSceneOverrides,
        reset,
        clearError,
        getApiPayload,
        validateShots,
    };
}

export default useDirectorPackState;
