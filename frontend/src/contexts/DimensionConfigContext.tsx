"use client";

import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from "react";
import { api, DimensionToolConfig, DimensionToolsConfig } from "@/lib/api";
import {
    getInputFieldsByDimension as getInputFields,
    getDefaultInputValues as getDefaults,
    type InputFieldConfig,
} from "@/lib/dimension-input-schemas";

// =============================================================================
// Types
// =============================================================================

interface ConnectionOption {
    id: string;
    label: string;
    description: string;
    recommendedToolId: string;
    icon: string;
    color: string;
    confidence: number;
}

interface DimensionConfigContextType {
    // Loading state
    isLoading: boolean;
    error: string | null;

    // Raw data from API
    config: DimensionToolsConfig | null;

    // Derived data for components
    tools: DimensionToolConfig[];
    toolsById: Record<string, DimensionToolConfig>;
    stageOrder: string[];

    // Helper functions
    getToolByDimension: (dimension: string) => DimensionToolConfig | undefined;
    getToolById: (toolId: string) => DimensionToolConfig | undefined;
    getInitialOptions: () => ConnectionOption[];
    getConnectionOptions: (excludeToolIds?: string[]) => ConnectionOption[];
    getInputFieldsByDimension: (dimension: string) => InputFieldConfig[];
    getDefaultInputValues: (dimension: string) => Record<string, string>;

    // Refresh function
    refresh: () => Promise<void>;
}

// =============================================================================
// Fallback data (used while loading or on error)
// =============================================================================

const FALLBACK_TOOLS: DimensionToolConfig[] = [
    { toolId: "prompt_generator", dimension: "1D", displayName: "프롬프트 연금술", displayNameEn: "Prompt Alchemy", description: "AI가 이해하는 전문 언어로 번역", icon: "sparkles", color: "violet", stage: "pre_production", capsuleKey: "teaching.prompt.generate", endpoint: "/api/dimension/1d/generate", creditCost: 5 },
    { toolId: "storyboard", dimension: "2D", displayName: "스토리보드 스케치", displayNameEn: "Storyboard Sketch", description: "글을 시각적 컷으로 스케치", icon: "layout-grid", color: "emerald", stage: "pre_production", capsuleKey: "teaching.storyboard.create", endpoint: "/api/dimension/2d/create", creditCost: 10 },
    { toolId: "image_tool", dimension: "3D", displayName: "비주얼 리얼라이저", displayNameEn: "Visual Realizer", description: "Key Frame 고품질 생성", icon: "image", color: "amber", stage: "production", capsuleKey: "teaching.image.generate", endpoint: "/api/dimension/3d/generate", creditCost: 5 },
    { toolId: "reference_analyzer", dimension: "4D", displayName: "레퍼런스 해석기", displayNameEn: "Reference Decoder", description: "조명, 색감, 연출의 전문가적 분석", icon: "film", color: "cyan", stage: "planning", capsuleKey: "teaching.reference.analyze", endpoint: "/api/dimension/4d/analyze", creditCost: 8 },
    { toolId: "quality_check", dimension: "QC", displayName: "퀄리티 디렉터", displayNameEn: "Quality Director", description: "시각적 일관성 및 품질 검수", icon: "check-circle", color: "rose", stage: "finishing", capsuleKey: "dimension.quality.check", endpoint: "/api/dimension/quality/check", creditCost: 8 },
    { toolId: "aesthetic_direct", dimension: "AD", displayName: "미학디렉터", displayNameEn: "Aesthetic Director", description: "시각적 스타일 가이드라인 생성", icon: "palette", color: "fuchsia", stage: "planning", capsuleKey: "dimension.aesthetic.direct", endpoint: "/api/dimension/aesthetic/direct", creditCost: 10 },
    { toolId: "persona_analyze", dimension: "AI", displayName: "심연의 거울", displayNameEn: "Abyss Mirror", description: "내면의 욕구와 감정 해석", icon: "moon", color: "indigo", stage: "planning", capsuleKey: "dimension.persona.analyze", endpoint: "/api/dimension/persona/analyze", creditCost: 5 },
    { toolId: "veo_generate", dimension: "VEO", displayName: "비디오 메이커", displayNameEn: "Video Maker", description: "최종 AI 영상 생성", icon: "video", color: "sky", stage: "production", capsuleKey: "veo.video.generate", endpoint: "/api/dimension/veo/generate", creditCost: 200 },
];

const FALLBACK_STAGE_ORDER = ["planning", "pre_production", "production", "finishing"];

// =============================================================================
// Context
// =============================================================================

const DimensionConfigContext = createContext<DimensionConfigContextType | undefined>(undefined);

export function DimensionConfigProvider({ children }: { children: React.ReactNode }) {
    const [config, setConfig] = useState<DimensionToolsConfig | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchConfig = useCallback(async (retryCount = 0) => {
        const MAX_RETRIES = 2;
        try {
            setIsLoading(true);
            setError(null);
            const data = await api.getDimensionToolsConfig();
            setConfig(data);
        } catch (err) {
            // Retry on timeout or network errors
            if (retryCount < MAX_RETRIES && err instanceof Error &&
                (err.message.includes("시간이 초과") || err.message.includes("연결"))) {
                console.warn(`[DimensionConfig] Retry ${retryCount + 1}/${MAX_RETRIES}...`);
                await new Promise(r => setTimeout(r, 1000 * (retryCount + 1)));
                return fetchConfig(retryCount + 1);
            }
            console.error("[DimensionConfig] Failed to fetch config:", err);
            setError(err instanceof Error ? err.message : "Failed to load dimension config");
            // Use fallback on error
            setConfig(null);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchConfig();
    }, [fetchConfig]);

    // Derived data
    const tools = useMemo(() => config?.tools ?? FALLBACK_TOOLS, [config]);
    const stageOrder = useMemo(() => config?.stageOrder ?? FALLBACK_STAGE_ORDER, [config]);

    const toolsById = useMemo(() => {
        if (config?.toolsById) return config.toolsById;
        // Build from fallback
        return FALLBACK_TOOLS.reduce((acc, tool) => {
            acc[tool.toolId] = tool;
            return acc;
        }, {} as Record<string, DimensionToolConfig>);
    }, [config]);

    // Helper functions
    const getToolByDimension = useCallback((dimension: string): DimensionToolConfig | undefined => {
        return tools.find(t => t.dimension === dimension);
    }, [tools]);

    const getToolById = useCallback((toolId: string): DimensionToolConfig | undefined => {
        return toolsById[toolId];
    }, [toolsById]);

    const getInitialOptions = useCallback((): ConnectionOption[] => {
        return tools.map((tool, idx) => ({
            id: `init-${tool.dimension.toLowerCase()}`,
            label: tool.displayName,
            description: tool.description,
            recommendedToolId: tool.toolId,
            icon: tool.icon,
            color: tool.color,
            confidence: 0.95 - (idx * 0.05), // Decreasing confidence by order
        }));
    }, [tools]);

    const getConnectionOptions = useCallback((excludeToolIds: string[] = []): ConnectionOption[] => {
        return tools
            .filter(tool => !excludeToolIds.includes(tool.toolId))
            .map((tool, idx) => ({
                id: `opt-${tool.dimension.toLowerCase()}`,
                label: tool.displayName,
                description: tool.description,
                recommendedToolId: tool.toolId,
                icon: tool.icon,
                color: tool.color,
                confidence: 0.95 - (idx * 0.05),
            }));
    }, [tools]);

    const value: DimensionConfigContextType = {
        isLoading,
        error,
        config,
        tools,
        toolsById,
        stageOrder,
        getToolByDimension,
        getToolById,
        getInitialOptions,
        getConnectionOptions,
        getInputFieldsByDimension: getInputFields,
        getDefaultInputValues: getDefaults,
        refresh: fetchConfig,
    };

    return (
        <DimensionConfigContext.Provider value={value}>
            {children}
        </DimensionConfigContext.Provider>
    );
}

export function useDimensionConfig(): DimensionConfigContextType {
    const context = useContext(DimensionConfigContext);
    if (context === undefined) {
        throw new Error("useDimensionConfig must be used within a DimensionConfigProvider");
    }
    return context;
}

// =============================================================================
// Export types
// =============================================================================

export type { DimensionToolConfig, ConnectionOption, InputFieldConfig };
