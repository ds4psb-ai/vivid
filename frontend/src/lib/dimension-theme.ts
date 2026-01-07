/**
 * Dimension Theme & Constants - Shared utilities for dimension components
 *
 * Single source of truth for dimension display names, colors, and workflow configuration.
 */

// Align with DimensionPanelLayout ThemeColor
export type ThemeColor = "violet" | "cyan" | "emerald" | "amber" | "rose" | "fuchsia" | "indigo" | "sky";

// =============================================================================
// DIMENSION DISPLAY NAMES - SSoT for route_key → display name mapping
// =============================================================================
export const DIMENSION_DISPLAY_NAMES: Record<string, string> = {
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

// English display names
export const DIMENSION_DISPLAY_NAMES_EN: Record<string, string> = {
    "abyss-mirror": "Abyss Mirror",
    "reference-decoder": "Reference Decoder",
    "story-architect": "Story Architect",
    "aesthetic-director": "Aesthetic Director",
    "storyboard-sketch": "Storyboard Sketch",
    "sound-crafter": "Sound Crafter",
    "prompt-alchemy": "Prompt Alchemy",
    "visual-realizer": "Visual Realizer",
    "video-maker": "Video Maker",
    "quality-director": "Quality Director",
};

// =============================================================================
// DIMENSION STAGES - Stage metadata for ordering
// =============================================================================
export const DIMENSION_STAGES: Record<string, { stage: string; order: number }> = {
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

// =============================================================================
// DIMENSION CONNECTIONS - Workflow connection map
// =============================================================================
export const DIMENSION_CONNECTIONS: Record<string, string[]> = {
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

export interface ThemeColorClasses {
    bg: string;
    border: string;
    text: string;
    button: string;
    buttonActive: string;
}

export const THEME_COLOR_CLASSES: Record<ThemeColor, ThemeColorClasses> = {
    emerald: {
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/20",
        text: "text-emerald-400",
        button: "bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400",
        buttonActive: "bg-emerald-500 text-black",
    },
    violet: {
        bg: "bg-violet-500/10",
        border: "border-violet-500/20",
        text: "text-violet-400",
        button: "bg-violet-500/20 hover:bg-violet-500/30 text-violet-400",
        buttonActive: "bg-violet-500 text-black",
    },
    amber: {
        bg: "bg-amber-500/10",
        border: "border-amber-500/20",
        text: "text-amber-400",
        button: "bg-amber-500/20 hover:bg-amber-500/30 text-amber-400",
        buttonActive: "bg-amber-500 text-black",
    },
    cyan: {
        bg: "bg-cyan-500/10",
        border: "border-cyan-500/20",
        text: "text-cyan-400",
        button: "bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400",
        buttonActive: "bg-cyan-500 text-black",
    },
    rose: {
        bg: "bg-rose-500/10",
        border: "border-rose-500/20",
        text: "text-rose-400",
        button: "bg-rose-500/20 hover:bg-rose-500/30 text-rose-400",
        buttonActive: "bg-rose-500 text-black",
    },
    fuchsia: {
        bg: "bg-fuchsia-500/10",
        border: "border-fuchsia-500/20",
        text: "text-fuchsia-400",
        button: "bg-fuchsia-500/20 hover:bg-fuchsia-500/30 text-fuchsia-400",
        buttonActive: "bg-fuchsia-500 text-black",
    },
    indigo: {
        bg: "bg-indigo-500/10",
        border: "border-indigo-500/20",
        text: "text-indigo-400",
        button: "bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-400",
        buttonActive: "bg-indigo-500 text-black",
    },
    sky: {
        bg: "bg-sky-500/10",
        border: "border-sky-500/20",
        text: "text-sky-400",
        button: "bg-sky-500/20 hover:bg-sky-500/30 text-sky-400",
        buttonActive: "bg-sky-500 text-black",
    },
};

/**
 * Get theme color classes for a given theme color
 */
export function getThemeColors(color: ThemeColor): ThemeColorClasses {
    return THEME_COLOR_CLASSES[color];
}
