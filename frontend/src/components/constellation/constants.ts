/**
 * Constellation Shared Constants
 *
 * Shared configuration for constellation preset types and status values.
 */
import { LucideIcon, Video, Film, Clapperboard } from "lucide-react";

export type ConstellationPreset = "short_drama" | "medium" | "feature_film";
export type StarStatus = "pending" | "generating" | "done" | "error";

export interface PresetConfig {
    label: string;
    Icon: LucideIcon;
    color: string;
    defaultSceneCount: number;
}

export interface StatusConfig {
    label: string;
    color: string;
    bgColor: string;
}

export const PRESET_CONFIG: Record<ConstellationPreset, PresetConfig> = {
    short_drama: {
        label: "단편",
        Icon: Video,
        color: "from-violet-500 to-fuchsia-500",
        defaultSceneCount: 5,
    },
    medium: {
        label: "중편",
        Icon: Film,
        color: "from-cyan-500 to-blue-500",
        defaultSceneCount: 12,
    },
    feature_film: {
        label: "장편",
        Icon: Clapperboard,
        color: "from-amber-500 to-orange-500",
        defaultSceneCount: 30,
    },
};

export const STATUS_CONFIG: Record<StarStatus, StatusConfig> = {
    pending: { label: "대기", color: "text-slate-400", bgColor: "bg-slate-500/20" },
    generating: { label: "생성중", color: "text-amber-400", bgColor: "bg-amber-500/20" },
    done: { label: "완료", color: "text-emerald-400", bgColor: "bg-emerald-500/20" },
    error: { label: "오류", color: "text-red-400", bgColor: "bg-red-500/20" },
};

/**
 * Get preset config safely with fallback to short_drama
 */
export function getPresetConfig(preset: string): PresetConfig {
    return PRESET_CONFIG[preset as ConstellationPreset] || PRESET_CONFIG.short_drama;
}

/**
 * Get status config safely with fallback to pending
 */
export function getStatusConfig(status: string): StatusConfig {
    return STATUS_CONFIG[status as StarStatus] || STATUS_CONFIG.pending;
}
