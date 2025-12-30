'use client';

import { useState, useCallback, useEffect } from 'react';
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
    /** Update scene overrides */
    updateSceneOverrides: (overrides: Record<string, SceneOverride>) => void;
    /** Clear all state */
    reset: () => void;
    /** Get payload for API request (returns serializable types for API compatibility) */
    getApiPayload: () => {
        director_pack?: Record<string, unknown>;
        scene_overrides?: Record<string, Record<string, unknown>>;
    };
}

export interface UseDirectorPackStateReturn extends DirectorPackState, DirectorPackActions { }

// =============================================================================
// Hook Implementation
// =============================================================================

export function useDirectorPackState(capsuleId?: string): UseDirectorPackStateReturn {
    // State
    const [pack, setPack] = useState<DirectorPack | null>(null);
    const [isEnabled, setIsEnabled] = useState(false);
    const [sceneOverrides, setSceneOverrides] = useState<Record<string, SceneOverride>>({});
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Reset when disabled
    const setEnabled = useCallback((enabled: boolean) => {
        setIsEnabled(enabled);
        if (!enabled) {
            setPack(null);
            setSceneOverrides({});
        }
    }, []);

    // Select a pack
    const selectPack = useCallback((newPack: DirectorPack | null) => {
        setPack(newPack);
        setSceneOverrides({});
        if (newPack) {
            setIsEnabled(true);
        }
    }, []);

    // Load pack by ID
    const loadPackById = useCallback(async (packId: string) => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`/api/v1/director-packs/${packId}`);
            if (!response.ok) throw new Error(`Failed to load pack: ${packId}`);

            const data = await response.json();
            setPack(data.data);
            setIsEnabled(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load pack');
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Load pack by pattern (e.g., auteur.bong-joon-ho -> bong)
    const loadPackByPattern = useCallback(async (patternId: string) => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`/api/v1/director-packs/by-pattern/${encodeURIComponent(patternId)}`);
            if (!response.ok) throw new Error(`No pack for pattern: ${patternId}`);

            const data = await response.json();
            setPack(data.data);
            setIsEnabled(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load pack');
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
        setIsEnabled(false);
        setSceneOverrides({});
        setError(null);
    }, []);

    // Get payload for API request (returns serializable records for API compatibility)
    const getApiPayload = useCallback((): {
        director_pack?: Record<string, unknown>;
        scene_overrides?: Record<string, Record<string, unknown>>;
    } => {
        if (!isEnabled || !pack) {
            return {};
        }

        // Filter only enabled overrides
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

    // Auto-load pack when capsuleId changes
    useEffect(() => {
        if (capsuleId && isEnabled && !pack) {
            // Extract pattern from capsule ID
            const pattern = capsuleId.split('.').pop() || '';
            if (pattern) {
                loadPackByPattern(pattern).catch(() => {
                    // Silently fail - user can manually select
                });
            }
        }
    }, [capsuleId, isEnabled, pack, loadPackByPattern]);

    return {
        // State
        pack,
        isEnabled,
        sceneOverrides,
        isLoading,
        error,
        // Actions
        setEnabled,
        selectPack,
        loadPackById,
        loadPackByPattern,
        updateSceneOverrides,
        reset,
        getApiPayload,
    };
}

export default useDirectorPackState;
