"use client";

/**
 * DimensionChainContext - Workflow Chain Data Management
 *
 * Manages data flow between dimension panels in the 4-Stage Video Workflow.
 * Stores outputs from each dimension and provides navigation to next dimensions.
 *
 * Enhanced Features (4-D DNA Architecture):
 * - Evidence refs accumulation across workflow
 * - SessionStorage synchronization for cross-MegaApp persistence
 * - MegaApp awareness for intelligent routing
 */

import { createContext, useContext, useCallback, useState, useEffect, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import {
    DIMENSION_DISPLAY_NAMES,
    DIMENSION_STAGES,
    DIMENSION_CONNECTIONS,
} from "@/lib/dimension-theme";
import { DIMENSION_TO_MEGA_APP, type MegaAppId } from "@/lib/dimension-mega-app-map";

/** Chain data stored for each dimension */
export interface ChainData {
    /** Dimension route key */
    dimensionKey: string;
    /** Output data from the dimension */
    output: Record<string, unknown>;
    /** Timestamp of when data was generated */
    timestamp: number;
    /** Summary text for display */
    summary?: string;
    /** Evidence references from this dimension */
    evidenceRefs?: string[];
}

/** Navigation history entry */
export interface NavigationEntry {
    dimensionKey: string;
    timestamp: number;
}

/** Session storage key prefix */
const SESSION_STORAGE_PREFIX = "vivid_chain_";

interface DimensionChainContextValue {
    /** Chain data indexed by dimension route key */
    chainData: Record<string, ChainData>;
    /** Navigation history */
    history: NavigationEntry[];
    /** Current active dimension */
    currentDimension: string | null;

    /** Store output from a dimension */
    setChainData: (dimensionKey: string, output: Record<string, unknown>, summary?: string, evidenceRefs?: string[]) => void;
    /** Bulk set chain data (for loading from server/storage) */
    setChainDataBulk: (data: Record<string, ChainData>) => void;
    /** Get input data available for a dimension (from its input_dimensions) */
    getInputData: (dimensionKey: string) => Record<string, ChainData>;
    /** Get next dimensions available from current dimension */
    getNextDimensions: (dimensionKey: string) => Array<{ key: string; name: string; hasData: boolean }>;
    /** Navigate to a dimension with chain data */
    navigateToDimension: (dimensionKey: string) => void;
    /** Set current active dimension */
    setCurrentDimension: (dimensionKey: string) => void;
    /** Clear all chain data */
    clearChain: () => void;
    /** Clear specific dimension data */
    clearDimensionData: (dimensionKey: string) => void;
    /** Check if dimension has chain data */
    hasChainData: (dimensionKey: string) => boolean;
    /** Get display name for a dimension */
    getDimensionName: (dimensionKey: string) => string;
    /** Get summary of current chain */
    getChainSummary: () => Array<{ key: string; name: string; summary?: string; timestamp: number }>;

    // Evidence refs accumulation (4-D DNA)
    /** Accumulated evidence refs across all dimensions */
    accumulatedEvidenceRefs: string[];
    /** Append new evidence refs (deduped) */
    appendEvidenceRefs: (refs: string[]) => void;
    /** Set accumulated evidence refs (for loading from server) */
    setAccumulatedEvidenceRefsBulk: (refs: string[]) => void;

    // SessionStorage synchronization
    /** Sync current chain to sessionStorage for IP/project persistence */
    syncToSession: (ipSlug: string) => void;
    /** Load chain from sessionStorage */
    loadFromSession: (ipSlug: string) => boolean;
    /** Check if session data exists */
    hasSessionData: (ipSlug: string) => boolean;

    // MegaApp awareness
    /** Current MegaApp context */
    currentMegaApp: MegaAppId | null;
    /** Get MegaApp for a dimension */
    getMegaAppForDimension: (dimensionKey: string) => MegaAppId | null;

    // P7+: Server persistence
    /** Server session ID (null if not synced) */
    serverSessionId: string | null;
    /** Set server session ID */
    setServerSessionId: (id: string | null) => void;
    /** Current server sync version */
    version: number;
    /** Set server sync version */
    setVersion: (v: number) => void;
    /** Sync status */
    syncStatus: "idle" | "syncing" | "synced" | "error" | "conflict";
    /** Set sync status */
    setSyncStatus: (status: "idle" | "syncing" | "synced" | "error" | "conflict") => void;
}

const DimensionChainContext = createContext<DimensionChainContextValue | null>(null);

interface DimensionChainProviderProps {
    children: ReactNode;
}

export function DimensionChainProvider({ children }: DimensionChainProviderProps) {
    const router = useRouter();
    const pathname = usePathname();
    const [chainData, setChainDataState] = useState<Record<string, ChainData>>({});
    const [history, setHistory] = useState<NavigationEntry[]>([]);
    const [currentDimension, setCurrentDimensionState] = useState<string | null>(null);
    const [accumulatedEvidenceRefs, setAccumulatedEvidenceRefs] = useState<string[]>([]);

    // P7+: Server persistence state
    const [serverSessionId, setServerSessionIdState] = useState<string | null>(null);
    const [version, setVersionState] = useState<number>(1);
    const [syncStatus, setSyncStatusState] = useState<"idle" | "syncing" | "synced" | "error" | "conflict">("idle");

    // Derive current MegaApp from pathname
    const currentMegaApp: MegaAppId | null = (() => {
        if (pathname?.startsWith("/dna-lab")) return "dna-lab";
        if (pathname?.startsWith("/story-engine")) return "story-engine";
        if (pathname?.startsWith("/production")) return "production";
        // Also check dimension routes
        const dimensionMatch = pathname?.match(/^\/dimension\/([^/]+)/);
        if (dimensionMatch) {
            const dimKey = dimensionMatch[1];
            return DIMENSION_TO_MEGA_APP[dimKey as keyof typeof DIMENSION_TO_MEGA_APP] || null;
        }
        return null;
    })();

    const getMegaAppForDimension = useCallback((dimensionKey: string): MegaAppId | null => {
        return DIMENSION_TO_MEGA_APP[dimensionKey as keyof typeof DIMENSION_TO_MEGA_APP] || null;
    }, []);

    const setChainData = useCallback((
        dimensionKey: string,
        output: Record<string, unknown>,
        summary?: string,
        evidenceRefs?: string[]
    ) => {
        const newData: ChainData = {
            dimensionKey,
            output,
            timestamp: Date.now(),
            summary,
            evidenceRefs,
        };
        setChainDataState(prev => ({
            ...prev,
            [dimensionKey]: newData,
        }));

        // Auto-accumulate evidence refs if provided
        if (evidenceRefs && evidenceRefs.length > 0) {
            setAccumulatedEvidenceRefs(prev => {
                const combined = new Set([...prev, ...evidenceRefs]);
                return Array.from(combined);
            });
        }
    }, []);

    const appendEvidenceRefs = useCallback((refs: string[]) => {
        if (refs.length === 0) return;
        setAccumulatedEvidenceRefs(prev => {
            const combined = new Set([...prev, ...refs]);
            return Array.from(combined);
        });
    }, []);

    // P7+: Bulk setters for loading from server/storage
    const setChainDataBulk = useCallback((data: Record<string, ChainData>) => {
        setChainDataState(data);
    }, []);

    const setAccumulatedEvidenceRefsBulk = useCallback((refs: string[]) => {
        setAccumulatedEvidenceRefs(refs);
    }, []);

    const setServerSessionId = useCallback((id: string | null) => {
        setServerSessionIdState(id);
    }, []);

    const setVersion = useCallback((v: number) => {
        setVersionState(v);
    }, []);

    const setSyncStatus = useCallback((status: "idle" | "syncing" | "synced" | "error" | "conflict") => {
        setSyncStatusState(status);
    }, []);

    const getInputData = useCallback((dimensionKey: string): Record<string, ChainData> => {
        /**
         * 워크플로우 입력 의존성 맵
         *
         * 거장 RAG + 페르소나 → 차원 조합 → 세계관 컨텐츠 생성
         *
         * - 4D(reference-decoder)는 시작점 (입력 없음 또는 외부 레퍼런스)
         * - Story는 4D 분석 결과 또는 직접 입력
         * - AI(abyss-mirror)는 독립적 - 다른 앱에 컨텍스트로 주입
         */
        const inputMap: Record<string, string[]> = {
            // 4D는 시작점 (입력 없음 또는 외부 레퍼런스)
            "reference-decoder": [],
            // Story는 4D 분석 결과 또는 직접 입력
            "story-architect": ["reference-decoder"],
            "aesthetic-director": ["reference-decoder"],
            // 이하 순차 연결
            "storyboard-sketch": ["story-architect", "reference-decoder"],
            "sound-crafter": ["story-architect", "storyboard-sketch"],
            "prompt-alchemy": ["story-architect", "storyboard-sketch"],
            "visual-realizer": ["prompt-alchemy", "storyboard-sketch"],
            "video-maker": ["visual-realizer", "prompt-alchemy", "sound-crafter"],
            "quality-director": ["video-maker", "visual-realizer"],
            // AI는 독립 - 다른 앱에 컨텍스트로 주입
            "abyss-mirror": [],
        };

        const inputDimensions = inputMap[dimensionKey] || [];
        const result: Record<string, ChainData> = {};

        inputDimensions.forEach(inputKey => {
            if (chainData[inputKey]) {
                result[inputKey] = chainData[inputKey];
            }
        });

        return result;
    }, [chainData]);

    const getNextDimensions = useCallback((dimensionKey: string): Array<{ key: string; name: string; hasData: boolean }> => {
        const nextKeys = DIMENSION_CONNECTIONS[dimensionKey] || [];
        return nextKeys.map(key => ({
            key,
            name: DIMENSION_DISPLAY_NAMES[key] || key,
            hasData: !!chainData[key],
        }));
    }, [chainData]);

    const navigateToDimension = useCallback((dimensionKey: string) => {
        // Add to history
        setHistory(prev => [
            ...prev,
            { dimensionKey, timestamp: Date.now() },
        ]);
        setCurrentDimensionState(dimensionKey);

        // Navigate using Next.js router
        const route = `/dimension/${dimensionKey}`;
        router.push(route);
    }, [router]);

    const setCurrentDimension = useCallback((dimensionKey: string) => {
        setCurrentDimensionState(dimensionKey);
    }, []);

    const clearChain = useCallback(() => {
        setChainDataState({});
        setHistory([]);
        setCurrentDimensionState(null);
    }, []);

    const clearDimensionData = useCallback((dimensionKey: string) => {
        setChainDataState(prev => {
            const newData = { ...prev };
            delete newData[dimensionKey];
            return newData;
        });
    }, []);

    const hasChainData = useCallback((dimensionKey: string): boolean => {
        return !!chainData[dimensionKey];
    }, [chainData]);

    const getDimensionName = useCallback((dimensionKey: string): string => {
        return DIMENSION_DISPLAY_NAMES[dimensionKey] || dimensionKey;
    }, []);

    const getChainSummary = useCallback((): Array<{ key: string; name: string; summary?: string; timestamp: number }> => {
        return Object.values(chainData)
            .sort((a, b) => a.timestamp - b.timestamp)
            .map(data => ({
                key: data.dimensionKey,
                name: DIMENSION_DISPLAY_NAMES[data.dimensionKey] || data.dimensionKey,
                summary: data.summary,
                timestamp: data.timestamp,
            }));
    }, [chainData]);

    // SessionStorage synchronization
    const syncToSession = useCallback((ipSlug: string) => {
        if (typeof window === "undefined") return;

        const sessionData = {
            chainData,
            accumulatedEvidenceRefs,
            history,
            currentDimension,
            syncedAt: Date.now(),
        };

        try {
            sessionStorage.setItem(
                `${SESSION_STORAGE_PREFIX}${ipSlug}`,
                JSON.stringify(sessionData)
            );
        } catch (e) {
            // SessionStorage might be full or disabled
            console.warn("[DimensionChain] Failed to sync to session:", e);
        }
    }, [chainData, accumulatedEvidenceRefs, history, currentDimension]);

    const loadFromSession = useCallback((ipSlug: string): boolean => {
        if (typeof window === "undefined") return false;

        try {
            const stored = sessionStorage.getItem(`${SESSION_STORAGE_PREFIX}${ipSlug}`);
            if (!stored) return false;

            const sessionData = JSON.parse(stored);

            // Validate data structure
            if (!sessionData.chainData || typeof sessionData.chainData !== "object") {
                return false;
            }

            // Restore state
            setChainDataState(sessionData.chainData);
            setAccumulatedEvidenceRefs(sessionData.accumulatedEvidenceRefs || []);
            setHistory(sessionData.history || []);
            setCurrentDimensionState(sessionData.currentDimension || null);

            return true;
        } catch (e) {
            console.warn("[DimensionChain] Failed to load from session:", e);
            return false;
        }
    }, []);

    const hasSessionData = useCallback((ipSlug: string): boolean => {
        if (typeof window === "undefined") return false;

        try {
            const stored = sessionStorage.getItem(`${SESSION_STORAGE_PREFIX}${ipSlug}`);
            return !!stored;
        } catch {
            return false;
        }
    }, []);

    return (
        <DimensionChainContext.Provider
            value={{
                chainData,
                history,
                currentDimension,
                setChainData,
                setChainDataBulk,
                getInputData,
                getNextDimensions,
                navigateToDimension,
                setCurrentDimension,
                clearChain,
                clearDimensionData,
                hasChainData,
                getDimensionName,
                getChainSummary,
                // Evidence refs
                accumulatedEvidenceRefs,
                appendEvidenceRefs,
                setAccumulatedEvidenceRefsBulk,
                // SessionStorage
                syncToSession,
                loadFromSession,
                hasSessionData,
                // MegaApp awareness
                currentMegaApp,
                getMegaAppForDimension,
                // P7+: Server persistence
                serverSessionId,
                setServerSessionId,
                version,
                setVersion,
                syncStatus,
                setSyncStatus,
            }}
        >
            {children}
        </DimensionChainContext.Provider>
    );
}

/**
 * Hook to access dimension chain context.
 * Must be used within a DimensionChainProvider.
 */
export function useDimensionChain(): DimensionChainContextValue {
    const context = useContext(DimensionChainContext);
    if (!context) {
        throw new Error("useDimensionChain must be used within a DimensionChainProvider");
    }
    return context;
}

/**
 * Optional hook that doesn't throw if outside provider.
 */
export function useDimensionChainOptional(): DimensionChainContextValue | null {
    return useContext(DimensionChainContext);
}

// Re-export constants for use in components (from shared utility)
export { DIMENSION_DISPLAY_NAMES, DIMENSION_STAGES, DIMENSION_CONNECTIONS };
