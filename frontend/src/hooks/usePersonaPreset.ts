"use client";

/**
 * usePersonaPreset - 페르소나 프리셋 저장/로드/동기화 훅
 * 
 * Phase 2: Implementation Plan v2
 * - localStorage 저장/로드
 * - 서버 동기화 (백그라운드)
 * - trace_id 히스토리 관리
 * - 워크플로우 재진입 지원
 */

import { useState, useCallback, useEffect, useRef } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8100';
const STORAGE_PREFIX = 'vivid:mirror:preset';
const SCHEMA_VERSION = '2026-01-14';

// ============================================================================
// Types
// ============================================================================

export interface EvidenceRef {
    ref_id: string;
    source: string;
    content_preview: string;
    dataset_id: string;
    dataset_label: string;
    score: number;
}

export interface TraceEntry {
    trace_id: string;
    session_id?: string;  // Link to preset meta.id (optional for backward compatibility)
    timestamp: string;
    stage: string;
    evidence_refs: EvidenceRef[];
    user_message_preview: string;
}

export interface PersonaPresetMeta {
    id: string;
    created_at: string;
    version: string;
    completion_rate: number;
    schema_version: string;
    source_hash?: string;
    rag_policy_version?: string;
}

export interface PersonaPreset {
    meta: PersonaPresetMeta;
    input?: {
        mbti?: string;
        blood_type?: string;
        birth_datetime?: string;
        gender?: string;
    };
    saju?: Record<string, unknown>;
    psychology?: Record<string, unknown>;
    creativity?: Record<string, unknown>;
    persona?: Record<string, unknown>;
    [key: string]: unknown;
}

export interface UsePersonaPresetReturn {
    preset: PersonaPreset | null;
    presets: PersonaPreset[];
    traces: TraceEntry[];
    isLoading: boolean;
    isSyncing: boolean;
    error: string | null;
    // Actions
    saveLocal: (preset: PersonaPreset) => void;
    loadLocal: (id: string) => PersonaPreset | null;
    updatePreset: (update: Partial<PersonaPreset>) => void;
    deleteLocal: (id: string) => void;
    clearLocal: () => void;
    syncToServer: () => Promise<void>;
    addTrace: (trace: TraceEntry) => void;
    // Workflow
    resumeSession: (presetId: string) => PersonaPreset | null;
    listPresets: () => PersonaPreset[];
}

// ============================================================================
// Utilities
// ============================================================================

function generateStorageKey(userId: string): string {
    return `${STORAGE_PREFIX}:${userId}`;
}

function generateHash(input: Record<string, unknown>): string {
    const str = JSON.stringify(input);
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    return Math.abs(hash).toString(16);
}

function _createEmptyPreset(): PersonaPreset {
    return {
        meta: {
            id: crypto.randomUUID(),
            created_at: new Date().toISOString(),
            version: '1.0',
            completion_rate: 0,
            schema_version: SCHEMA_VERSION,
        },
    };
}

// ============================================================================
// Hook
// ============================================================================

interface UsePersonaPresetOptions {
    userId?: string;
    autoLoad?: boolean;
}

export function usePersonaPreset(options: UsePersonaPresetOptions = {}): UsePersonaPresetReturn {
    const { userId = 'anonymous', autoLoad = true } = options;

    // State
    const [preset, setPreset] = useState<PersonaPreset | null>(null);
    const [presets, setPresets] = useState<PersonaPreset[]>([]);
    const [traces, setTraces] = useState<TraceEntry[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSyncing, setIsSyncing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const storageKey = useRef(generateStorageKey(userId));

    // Load from localStorage on mount
    useEffect(() => {
        if (autoLoad) {
            loadAllPresets();
        }
        setIsLoading(false);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [userId, autoLoad]);

    // Load all presets from localStorage
    const loadAllPresets = useCallback(() => {
        try {
            const stored = localStorage.getItem(storageKey.current);
            if (stored) {
                const parsed = JSON.parse(stored) as { presets: PersonaPreset[]; traces: TraceEntry[] };
                setPresets(parsed.presets || []);
                setTraces(parsed.traces || []);
                // Set current preset to most recent
                if (parsed.presets?.length > 0) {
                    const sorted = [...parsed.presets].sort(
                        (a, b) => new Date(b.meta.created_at).getTime() - new Date(a.meta.created_at).getTime()
                    );
                    setPreset(sorted[0]);
                }
            }
        } catch (e) {
            console.error('[usePersonaPreset] Load error:', e);
            setError('프리셋 로드 실패');
        }
    }, []);

    // Save to localStorage
    const persistToStorage = useCallback((newPresets: PersonaPreset[], newTraces: TraceEntry[]) => {
        try {
            localStorage.setItem(storageKey.current, JSON.stringify({
                presets: newPresets,
                traces: newTraces,
                updated_at: new Date().toISOString(),
            }));
        } catch (e) {
            console.error('[usePersonaPreset] Save error:', e);
            setError('프리셋 저장 실패');
        }
    }, []);

    // Save current preset
    const saveLocal = useCallback((newPreset: PersonaPreset) => {
        // Ensure schema version
        const presetToSave: PersonaPreset = {
            ...newPreset,
            meta: {
                ...newPreset.meta,
                schema_version: SCHEMA_VERSION,
                source_hash: generateHash(newPreset.input || {}),
            },
        };

        setPreset(presetToSave);

        // Update presets list
        setPresets(prev => {
            const existing = prev.findIndex(p => p.meta.id === presetToSave.meta.id);
            let updated: PersonaPreset[];
            if (existing >= 0) {
                updated = [...prev];
                updated[existing] = presetToSave;
            } else {
                updated = [presetToSave, ...prev];
            }
            persistToStorage(updated, traces);
            return updated;
        });
    }, [traces, persistToStorage]);

    // Load specific preset by ID
    const loadLocal = useCallback((id: string): PersonaPreset | null => {
        const found = presets.find(p => p.meta.id === id);
        if (found) {
            setPreset(found);
            return found;
        }
        return null;
    }, [presets]);

    // Update current preset (merge)
    const updatePreset = useCallback((update: Partial<PersonaPreset>) => {
        setPreset(prev => {
            if (!prev) return prev;
            const updated = {
                ...prev,
                ...update,
                meta: {
                    ...prev.meta,
                    ...update.meta,
                },
            };
            saveLocal(updated);
            return updated;
        });
    }, [saveLocal]);

    // Delete preset
    const deleteLocal = useCallback((id: string) => {
        setPresets(prev => {
            const updated = prev.filter(p => p.meta.id !== id);
            persistToStorage(updated, traces);
            return updated;
        });
        if (preset?.meta.id === id) {
            setPreset(null);
        }
    }, [preset, traces, persistToStorage]);

    // Clear all
    const clearLocal = useCallback(() => {
        localStorage.removeItem(storageKey.current);
        setPresets([]);
        setTraces([]);
        setPreset(null);
    }, []);

    // Add trace entry
    const addTrace = useCallback((trace: TraceEntry) => {
        setTraces(prev => {
            const updated = [trace, ...prev].slice(0, 100); // Keep max 100 traces
            persistToStorage(presets, updated);
            return updated;
        });
    }, [presets, persistToStorage]);

    // Server sync (background)
    const syncToServer = useCallback(async () => {
        if (!preset) return;

        setIsSyncing(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE}/api/dimension/mirror/export`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(preset),
            });

            if (!response.ok) {
                throw new Error(`Sync failed: ${response.status}`);
            }

            console.log('[usePersonaPreset] Synced to server');
        } catch (e) {
            console.error('[usePersonaPreset] Sync error:', e);
            setError('서버 동기화 실패');
        } finally {
            setIsSyncing(false);
        }
    }, [preset]);

    // Resume session (workflow re-entry)
    const resumeSession = useCallback((presetId: string): PersonaPreset | null => {
        const found = loadLocal(presetId);
        if (found) {
            // Filter traces for this preset
            const presetTraces = traces.filter(t =>
                t.timestamp >= found.meta.created_at
            );
            console.log(`[usePersonaPreset] Resumed session with ${presetTraces.length} traces`);
        }
        return found;
    }, [loadLocal, traces]);

    // List all presets
    const listPresets = useCallback((): PersonaPreset[] => {
        return [...presets].sort(
            (a, b) => new Date(b.meta.created_at).getTime() - new Date(a.meta.created_at).getTime()
        );
    }, [presets]);

    return {
        preset,
        presets,
        traces,
        isLoading,
        isSyncing,
        error,
        saveLocal,
        loadLocal,
        updatePreset,
        deleteLocal,
        clearLocal,
        syncToServer,
        addTrace,
        resumeSession,
        listPresets,
    };
}

export default usePersonaPreset;
