"use client";

/**
 * DimensionChainContext - Workflow Chain Data Management
 *
 * Manages data flow between dimension panels in the 4-Stage Video Workflow.
 * Stores outputs from each dimension and provides navigation to next dimensions.
 */

import { createContext, useContext, useCallback, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";

// Route key to display name mapping
const DIMENSION_DISPLAY_NAMES: Record<string, string> = {
    "abyss-mirror": "심연의 거울",
    "reference-decoder": "레퍼런스 해석기",
    "story-architect": "시나리오 생성기",
    "aesthetic-director": "미학디렉터",
    "storyboard-sketch": "스토리보드 스케치",
    "sound-crafter": "사운드 크래프터",
    "prompt-alchemy": "프롬프트 연금술",
    "visual-realizer": "비주얼 리얼라이저",
    "video-maker": "비디오 메이커",
    "quality-director": "퀄리티 디렉터",
};

// Stage metadata for ordering
const DIMENSION_STAGES: Record<string, { stage: string; order: number }> = {
    "abyss-mirror": { stage: "planning", order: 1 },
    "reference-decoder": { stage: "planning", order: 2 },
    "story-architect": { stage: "planning", order: 3 },
    "aesthetic-director": { stage: "planning", order: 4 },
    "storyboard-sketch": { stage: "pre_production", order: 2 },
    "sound-crafter": { stage: "pre_production", order: 1 },
    "prompt-alchemy": { stage: "pre_production", order: 3 },
    "visual-realizer": { stage: "production", order: 1 },
    "video-maker": { stage: "production", order: 2 },
    "quality-director": { stage: "finishing", order: 1 },
};

// Connection map: dimension -> possible next dimensions
const DIMENSION_CONNECTIONS: Record<string, string[]> = {
    "abyss-mirror": ["reference-decoder", "story-architect", "aesthetic-director"],
    "reference-decoder": ["story-architect", "storyboard-sketch"],
    "story-architect": ["storyboard-sketch", "sound-crafter", "prompt-alchemy"],
    "aesthetic-director": ["story-architect", "visual-realizer"],
    "storyboard-sketch": ["sound-crafter", "prompt-alchemy"],
    "sound-crafter": ["video-maker"],
    "prompt-alchemy": ["visual-realizer", "video-maker"],
    "visual-realizer": ["video-maker", "quality-director"],
    "video-maker": ["quality-director"],
    "quality-director": [],
};

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
}

/** Navigation history entry */
export interface NavigationEntry {
    dimensionKey: string;
    timestamp: number;
}

interface DimensionChainContextValue {
    /** Chain data indexed by dimension route key */
    chainData: Record<string, ChainData>;
    /** Navigation history */
    history: NavigationEntry[];
    /** Current active dimension */
    currentDimension: string | null;

    /** Store output from a dimension */
    setChainData: (dimensionKey: string, output: Record<string, unknown>, summary?: string) => void;
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
}

const DimensionChainContext = createContext<DimensionChainContextValue | null>(null);

interface DimensionChainProviderProps {
    children: ReactNode;
}

export function DimensionChainProvider({ children }: DimensionChainProviderProps) {
    const router = useRouter();
    const [chainData, setChainDataState] = useState<Record<string, ChainData>>({});
    const [history, setHistory] = useState<NavigationEntry[]>([]);
    const [currentDimension, setCurrentDimensionState] = useState<string | null>(null);

    const setChainData = useCallback((
        dimensionKey: string,
        output: Record<string, unknown>,
        summary?: string
    ) => {
        const newData: ChainData = {
            dimensionKey,
            output,
            timestamp: Date.now(),
            summary,
        };
        setChainDataState(prev => ({
            ...prev,
            [dimensionKey]: newData,
        }));
    }, []);

    const getInputData = useCallback((dimensionKey: string): Record<string, ChainData> => {
        // Map dimension to its input sources based on capsule definitions
        const inputMap: Record<string, string[]> = {
            "reference-decoder": ["abyss-mirror"],
            "story-architect": ["abyss-mirror", "reference-decoder"],
            "aesthetic-director": ["abyss-mirror", "reference-decoder"],
            "storyboard-sketch": ["story-architect", "reference-decoder"],
            "sound-crafter": ["story-architect", "storyboard-sketch"],
            "prompt-alchemy": ["story-architect", "storyboard-sketch"],
            "visual-realizer": ["prompt-alchemy", "storyboard-sketch"],
            "video-maker": ["visual-realizer", "prompt-alchemy", "sound-crafter"],
            "quality-director": ["video-maker", "visual-realizer"],
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

    return (
        <DimensionChainContext.Provider
            value={{
                chainData,
                history,
                currentDimension,
                setChainData,
                getInputData,
                getNextDimensions,
                navigateToDimension,
                setCurrentDimension,
                clearChain,
                clearDimensionData,
                hasChainData,
                getDimensionName,
                getChainSummary,
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

// Export constants for use in components
export { DIMENSION_DISPLAY_NAMES, DIMENSION_STAGES, DIMENSION_CONNECTIONS };
