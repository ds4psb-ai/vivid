"use client";

/**
 * QualityScorecard - 품질 점수 시각화 컴포넌트 for UQSL
 *
 * Features:
 * - 5가지 품질 지표 시각화 (groundedness, relevance, coherence, creativity, safety)
 * - 바 차트 / 레이더 차트 옵션
 * - 총점 강조 표시
 * - 컴팩트/확장 모드
 * - DimensionPanel 토큰 시스템 사용
 * - Framer Motion 애니메이션
 *
 * @see UQSL_SPEC.md - Universal Quality Selection Layer
 */

import { useMemo } from "react";
import { motion } from "framer-motion";
import { Shield, Target, Link2, Sparkles, Lock, TrendingUp } from "lucide-react";
import { type ThemeColor, THEME_COLOR_CLASSES } from "@/lib/dimension-theme";

export interface QualityScores {
    /** 거장 DNA 기반 그라운딩 (0-1) */
    groundedness: number;
    /** RAG 관련도 (0-1) */
    relevance: number;
    /** 일관성 (0-1) */
    coherence: number;
    /** 창의성 (0-1) */
    creativity: number;
    /** 안전성 (0-1) */
    safety: number;
}

export interface QualityScorecardProps {
    /** Quality scores (0-1 for each dimension) */
    scores: QualityScores;
    /** Pre-calculated total score (or will compute weighted average) */
    totalScore?: number;
    /** Custom weights for total score calculation */
    weights?: Partial<QualityScores>;
    /** Theme color */
    themeColor?: ThemeColor;
    /** Compact mode for inline use */
    compact?: boolean;
    /** Chart type */
    chartType?: "bar" | "radar" | "minimal";
    /** Show individual labels */
    showLabels?: boolean;
    /** Animate on mount */
    animate?: boolean;
}

const DIMENSION_META: Record<keyof QualityScores, {
    label: string;
    labelKo: string;
    icon: typeof Shield;
    color: string;
    description: string;
}> = {
    groundedness: {
        label: "Groundedness",
        labelKo: "근거 기반",
        icon: Link2,
        color: "emerald",
        description: "거장 DNA 기반 그라운딩",
    },
    relevance: {
        label: "Relevance",
        labelKo: "관련성",
        icon: Target,
        color: "blue",
        description: "RAG 문맥 관련도",
    },
    coherence: {
        label: "Coherence",
        labelKo: "일관성",
        icon: Link2,
        color: "purple",
        description: "논리적 일관성",
    },
    creativity: {
        label: "Creativity",
        labelKo: "창의성",
        icon: Sparkles,
        color: "amber",
        description: "독창성과 참신함",
    },
    safety: {
        label: "Safety",
        labelKo: "안전성",
        icon: Shield,
        color: "rose",
        description: "콘텐츠 안전성",
    },
};

const DEFAULT_WEIGHTS: QualityScores = {
    groundedness: 0.30,
    relevance: 0.25,
    coherence: 0.20,
    creativity: 0.15,
    safety: 0.10,
};

export default function QualityScorecard({
    scores,
    totalScore,
    weights = DEFAULT_WEIGHTS,
    themeColor = "violet",
    compact = false,
    chartType = "bar",
    showLabels = true,
    animate = true,
}: QualityScorecardProps) {
    const colors = THEME_COLOR_CLASSES[themeColor];

    // Calculate total score if not provided
    const computedTotal = useMemo(() => {
        if (totalScore !== undefined) return totalScore;

        const w = { ...DEFAULT_WEIGHTS, ...weights };
        return (
            scores.groundedness * w.groundedness +
            scores.relevance * w.relevance +
            scores.coherence * w.coherence +
            scores.creativity * w.creativity +
            scores.safety * w.safety
        );
    }, [scores, weights, totalScore]);

    const scorePercent = Math.round(computedTotal * 100);

    // Score grade
    const grade = useMemo(() => {
        if (computedTotal >= 0.9) return { label: "Excellent", color: "emerald", emoji: "🌟" };
        if (computedTotal >= 0.75) return { label: "Good", color: "blue", emoji: "✨" };
        if (computedTotal >= 0.6) return { label: "Fair", color: "amber", emoji: "👍" };
        return { label: "Needs Work", color: "rose", emoji: "💪" };
    }, [computedTotal]);

    // Minimal view
    if (chartType === "minimal") {
        return (
            <div className="flex items-center gap-2">
                <div className={`text-sm font-bold text-${grade.color}-400`}>
                    {scorePercent}%
                </div>
                <div className="w-20 h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <motion.div
                        initial={animate ? { width: 0 } : false}
                        animate={{ width: `${scorePercent}%` }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                        className={`h-full bg-${grade.color}-500 rounded-full`}
                    />
                </div>
            </div>
        );
    }

    // Compact view
    if (compact) {
        return (
            <div className={`rounded-xl ${colors.bg} border ${colors.border} p-3`}>
                <div className="flex items-center justify-between">
                    {/* Total Score */}
                    <div className="flex items-center gap-3">
                        <div className={`w-12 h-12 rounded-xl bg-${grade.color}-500/20 flex items-center justify-center`}>
                            <span className={`text-lg font-bold text-${grade.color}-400`}>
                                {scorePercent}
                            </span>
                        </div>
                        <div>
                            <p className="text-xs text-white/50">품질 점수</p>
                            <p className={`text-sm font-medium text-${grade.color}-400`}>
                                {grade.emoji} {grade.label}
                            </p>
                        </div>
                    </div>

                    {/* Mini bars */}
                    <div className="flex gap-1">
                        {(Object.keys(scores) as (keyof QualityScores)[]).map((key) => (
                            <div key={key} className="flex flex-col items-center gap-1">
                                <div className="w-1.5 h-8 bg-white/10 rounded-full overflow-hidden rotate-180">
                                    <motion.div
                                        initial={animate ? { height: 0 } : false}
                                        animate={{ height: `${scores[key] * 100}%` }}
                                        transition={{ duration: 0.6, delay: 0.1 }}
                                        className={`w-full bg-${DIMENSION_META[key].color}-500`}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    // Full bar chart view
    if (chartType === "bar") {
        return (
            <div className={`rounded-xl ${colors.bg} border ${colors.border} overflow-hidden`}>
                {/* Header with total score */}
                <div className="px-4 py-4 border-b border-white/10">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className={`w-14 h-14 rounded-xl bg-${grade.color}-500/20 flex items-center justify-center`}>
                                <span className={`text-2xl font-bold text-${grade.color}-400`}>
                                    {scorePercent}
                                </span>
                            </div>
                            <div>
                                <p className="text-xs text-white/50 mb-0.5">품질 점수</p>
                                <p className={`text-sm font-semibold text-${grade.color}-400`}>
                                    {grade.emoji} {grade.label}
                                </p>
                            </div>
                        </div>
                        <TrendingUp className={`w-5 h-5 text-${grade.color}-400`} />
                    </div>
                </div>

                {/* Score bars */}
                <div className="p-4 space-y-3">
                    {(Object.keys(scores) as (keyof QualityScores)[]).map((key, index) => {
                        const meta = DIMENSION_META[key];
                        const Icon = meta.icon;
                        const value = scores[key];
                        const percent = Math.round(value * 100);

                        return (
                            <motion.div
                                key={key}
                                initial={animate ? { opacity: 0, x: -10 } : false}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: index * 0.1 }}
                                className="space-y-1.5"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <Icon className={`w-3.5 h-3.5 text-${meta.color}-400`} />
                                        {showLabels && (
                                            <span className="text-xs text-white/70">
                                                {meta.labelKo}
                                            </span>
                                        )}
                                    </div>
                                    <span className={`text-xs font-medium text-${meta.color}-400`}>
                                        {percent}%
                                    </span>
                                </div>
                                <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                                    <motion.div
                                        initial={animate ? { width: 0 } : false}
                                        animate={{ width: `${percent}%` }}
                                        transition={{ duration: 0.8, delay: index * 0.1, ease: "easeOut" }}
                                        className={`h-full bg-${meta.color}-500 rounded-full`}
                                    />
                                </div>
                            </motion.div>
                        );
                    })}
                </div>

                {/* Footer with weights info */}
                <div className="px-4 py-2 border-t border-white/5 bg-white/[0.02]">
                    <p className="text-[10px] text-white/30 text-center">
                        가중치: 근거 {(weights.groundedness ?? DEFAULT_WEIGHTS.groundedness) * 100}% ·
                        관련성 {(weights.relevance ?? DEFAULT_WEIGHTS.relevance) * 100}% ·
                        일관성 {(weights.coherence ?? DEFAULT_WEIGHTS.coherence) * 100}% ·
                        창의성 {(weights.creativity ?? DEFAULT_WEIGHTS.creativity) * 100}% ·
                        안전 {(weights.safety ?? DEFAULT_WEIGHTS.safety) * 100}%
                    </p>
                </div>
            </div>
        );
    }

    // Radar chart view (CSS-based pentagon)
    return (
        <div className={`rounded-xl ${colors.bg} border ${colors.border} overflow-hidden`}>
            {/* Header */}
            <div className="px-4 py-4 border-b border-white/10">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className={`w-14 h-14 rounded-xl bg-${grade.color}-500/20 flex items-center justify-center`}>
                            <span className={`text-2xl font-bold text-${grade.color}-400`}>
                                {scorePercent}
                            </span>
                        </div>
                        <div>
                            <p className="text-xs text-white/50 mb-0.5">품질 점수</p>
                            <p className={`text-sm font-semibold text-${grade.color}-400`}>
                                {grade.emoji} {grade.label}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Radar visualization (simplified pentagon) */}
            <div className="p-6">
                <RadarChart scores={scores} animate={animate} />
            </div>

            {/* Legend */}
            <div className="px-4 pb-4 grid grid-cols-5 gap-2">
                {(Object.keys(scores) as (keyof QualityScores)[]).map((key) => {
                    const meta = DIMENSION_META[key];
                    const Icon = meta.icon;
                    const percent = Math.round(scores[key] * 100);

                    return (
                        <div key={key} className="text-center">
                            <Icon className={`w-4 h-4 mx-auto mb-1 text-${meta.color}-400`} />
                            <p className="text-[10px] text-white/50">{meta.labelKo}</p>
                            <p className={`text-xs font-medium text-${meta.color}-400`}>{percent}%</p>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

/**
 * RadarChart - CSS/SVG based radar chart
 */
function RadarChart({
    scores,
    animate = true,
}: {
    scores: QualityScores;
    animate?: boolean;
}) {
    const size = 160;
    const center = size / 2;
    const radius = size * 0.4;

    // Pentagon vertices (5 points)
    const angleStep = (2 * Math.PI) / 5;
    const startAngle = -Math.PI / 2; // Start from top

    const keys: (keyof QualityScores)[] = ["groundedness", "relevance", "coherence", "creativity", "safety"];

    // Background pentagon
    const bgPoints = keys.map((_, i) => {
        const angle = startAngle + i * angleStep;
        return {
            x: center + radius * Math.cos(angle),
            y: center + radius * Math.sin(angle),
        };
    });

    // Score polygon
    const scorePoints = keys.map((key, i) => {
        const angle = startAngle + i * angleStep;
        const r = radius * scores[key];
        return {
            x: center + r * Math.cos(angle),
            y: center + r * Math.sin(angle),
        };
    });

    const bgPath = bgPoints.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";
    const scorePath = scorePoints.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";

    return (
        <svg width={size} height={size} className="mx-auto">
            {/* Grid lines */}
            {[0.25, 0.5, 0.75, 1].map((scale) => {
                const points = keys.map((_, i) => {
                    const angle = startAngle + i * angleStep;
                    return {
                        x: center + radius * scale * Math.cos(angle),
                        y: center + radius * scale * Math.sin(angle),
                    };
                });
                const path = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";
                return (
                    <path
                        key={scale}
                        d={path}
                        fill="none"
                        stroke="currentColor"
                        strokeWidth={0.5}
                        className="text-white/10"
                    />
                );
            })}

            {/* Axis lines */}
            {bgPoints.map((p, i) => (
                <line
                    key={i}
                    x1={center}
                    y1={center}
                    x2={p.x}
                    y2={p.y}
                    stroke="currentColor"
                    strokeWidth={0.5}
                    className="text-white/10"
                />
            ))}

            {/* Score area */}
            <motion.path
                d={scorePath}
                fill="currentColor"
                fillOpacity={0.2}
                stroke="currentColor"
                strokeWidth={2}
                className="text-violet-500"
                initial={animate ? { opacity: 0 } : false}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
            />

            {/* Score points */}
            {scorePoints.map((p, i) => (
                <motion.circle
                    key={i}
                    cx={p.x}
                    cy={p.y}
                    r={4}
                    fill="currentColor"
                    className={`text-${DIMENSION_META[keys[i]].color}-400`}
                    initial={animate ? { scale: 0 } : false}
                    animate={{ scale: 1 }}
                    transition={{ delay: i * 0.1 }}
                />
            ))}
        </svg>
    );
}

/**
 * QualityBadge - Compact quality indicator badge
 */
export function QualityBadge({
    score,
    size = "md",
}: {
    score: number;
    size?: "sm" | "md" | "lg";
}) {
    const percent = Math.round(score * 100);

    const grade = useMemo(() => {
        if (score >= 0.9) return { color: "emerald", emoji: "🌟" };
        if (score >= 0.75) return { color: "blue", emoji: "✨" };
        if (score >= 0.6) return { color: "amber", emoji: "👍" };
        return { color: "rose", emoji: "💪" };
    }, [score]);

    const sizeClasses = {
        sm: "px-1.5 py-0.5 text-[10px]",
        md: "px-2 py-1 text-xs",
        lg: "px-3 py-1.5 text-sm",
    };

    return (
        <span
            className={`inline-flex items-center gap-1 rounded-full font-medium bg-${grade.color}-500/20 text-${grade.color}-400 ${sizeClasses[size]}`}
        >
            <span>{grade.emoji}</span>
            <span>{percent}%</span>
        </span>
    );
}

/**
 * QualityDot - Minimal quality indicator
 */
export function QualityDot({
    score,
    showLabel = false,
}: {
    score: number;
    showLabel?: boolean;
}) {
    const grade = useMemo(() => {
        if (score >= 0.9) return { color: "emerald", label: "Excellent" };
        if (score >= 0.75) return { color: "blue", label: "Good" };
        if (score >= 0.6) return { color: "amber", label: "Fair" };
        return { color: "rose", label: "Low" };
    }, [score]);

    return (
        <div className="flex items-center gap-1.5">
            <div className={`w-2 h-2 rounded-full bg-${grade.color}-500`} />
            {showLabel && (
                <span className={`text-[10px] text-${grade.color}-400`}>
                    {grade.label}
                </span>
            )}
        </div>
    );
}
