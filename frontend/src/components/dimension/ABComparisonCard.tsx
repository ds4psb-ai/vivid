"use client";

/**
 * ABComparisonCard - A/B 비교 카드 컴포넌트 for UQSL Quality Selection
 *
 * Features:
 * - 2개 후보 나란히 비교 (side-by-side)
 * - 선택 버튼 (A/B)
 * - 선택적 메트릭 표시 (latency, confidence)
 * - DimensionPanel 토큰 시스템 사용
 * - Framer Motion 애니메이션
 * - 반응형 (모바일: 세로 스택)
 *
 * @see UQSL_SPEC.md - Universal Quality Selection Layer
 */

import { useState, useCallback } from "react";
import { Check, Loader2, Clock, Sparkles, HelpCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { type ThemeColor, THEME_COLOR_CLASSES } from "@/lib/dimension-theme";

export interface CandidateData {
    /** Unique identifier */
    id: string;
    /** Content to display (text or React node) */
    content: string | React.ReactNode;
    /** Optional metadata (latency, confidence, etc.) */
    metadata?: {
        latencyMs?: number;
        confidence?: number;
        backendUsed?: string;
        [key: string]: unknown;
    };
}

export interface ABComparisonCardProps {
    /** Two candidates to compare */
    candidates: [CandidateData, CandidateData];
    /** Callback when a candidate is selected */
    onSelect: (selectedId: string, selectedIndex: 0 | 1) => Promise<void>;
    /** Callback when user skips selection */
    onSkip?: () => void;
    /** Show metrics (latency, confidence) */
    showMetrics?: boolean;
    /** Custom labels for A/B */
    labels?: { a: string; b: string };
    /** Theme color */
    themeColor?: ThemeColor;
    /** Disabled state */
    disabled?: boolean;
    /** Initially selected index (if any) */
    initialSelected?: 0 | 1 | null;
    /** Compact mode for smaller displays */
    compact?: boolean;
}

export default function ABComparisonCard({
    candidates,
    onSelect,
    onSkip,
    showMetrics = true,
    labels = { a: "옵션 A", b: "옵션 B" },
    themeColor = "violet",
    disabled = false,
    initialSelected = null,
    compact = false,
}: ABComparisonCardProps) {
    const [selectedIndex, setSelectedIndex] = useState<0 | 1 | null>(initialSelected);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [hasSubmitted, setHasSubmitted] = useState(false);
    const colors = THEME_COLOR_CLASSES[themeColor];

    const handleSelect = useCallback(
        async (index: 0 | 1) => {
            if (disabled || isSubmitting || hasSubmitted) return;

            setSelectedIndex(index);
            setIsSubmitting(true);

            try {
                await onSelect(candidates[index].id, index);
                setHasSubmitted(true);
            } catch (error) {
                console.error("Selection failed:", error);
                setSelectedIndex(null);
            } finally {
                setIsSubmitting(false);
            }
        },
        [disabled, isSubmitting, hasSubmitted, candidates, onSelect]
    );

    const handleSkip = useCallback(() => {
        if (disabled || isSubmitting) return;
        onSkip?.();
    }, [disabled, isSubmitting, onSkip]);

    const formatLatency = (ms?: number) => {
        if (ms === undefined) return null;
        if (ms < 1000) return `${ms}ms`;
        return `${(ms / 1000).toFixed(1)}s`;
    };

    const formatConfidence = (confidence?: number) => {
        if (confidence === undefined) return null;
        return `${Math.round(confidence * 100)}%`;
    };

    // Submitted state
    if (hasSubmitted && selectedIndex !== null) {
        return (
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className={`rounded-xl ${colors.bg} border ${colors.border} p-6`}
            >
                <div className="flex items-center justify-center gap-3">
                    <div className={`p-2 rounded-full ${colors.bg}`}>
                        <Check className={`w-5 h-5 ${colors.text}`} />
                    </div>
                    <span className={`text-sm font-medium ${colors.text}`}>
                        {labels[selectedIndex === 0 ? "a" : "b"]}를 선택했습니다
                    </span>
                </div>
            </motion.div>
        );
    }

    return (
        <div className={`rounded-xl ${colors.bg} border ${colors.border} overflow-hidden`}>
            {/* Header */}
            <div className="px-4 py-3 border-b border-white/10">
                <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-white">
                        어떤 결과가 더 좋나요?
                    </h3>
                    {onSkip && (
                        <button
                            onClick={handleSkip}
                            disabled={disabled || isSubmitting}
                            className="flex items-center gap-1 px-2 py-1 text-xs text-white/50 hover:text-white/70 transition-colors disabled:opacity-50"
                        >
                            <HelpCircle className="w-3 h-3" />
                            <span>잘 모르겠어요</span>
                        </button>
                    )}
                </div>
            </div>

            {/* Comparison Grid */}
            <div className={`grid ${compact ? "grid-cols-1 gap-2" : "grid-cols-2 gap-0"}`}>
                {candidates.map((candidate, index) => {
                    const isA = index === 0;
                    const label = isA ? labels.a : labels.b;
                    const isSelected = selectedIndex === index;
                    const isOtherSelected = selectedIndex !== null && selectedIndex !== index;

                    return (
                        <motion.div
                            key={candidate.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className={`relative p-4 ${
                                !compact && isA ? "border-r border-white/10" : ""
                            } ${isOtherSelected ? "opacity-50" : ""}`}
                        >
                            {/* Label Badge */}
                            <div className="flex items-center justify-between mb-3">
                                <span
                                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                        isA
                                            ? "bg-blue-500/20 text-blue-400"
                                            : "bg-purple-500/20 text-purple-400"
                                    }`}
                                >
                                    {label}
                                </span>

                                {/* Metrics */}
                                {showMetrics && candidate.metadata && (
                                    <div className="flex items-center gap-2 text-xs text-white/40">
                                        {candidate.metadata.latencyMs !== undefined && (
                                            <span className="flex items-center gap-1">
                                                <Clock className="w-3 h-3" />
                                                {formatLatency(candidate.metadata.latencyMs)}
                                            </span>
                                        )}
                                        {candidate.metadata.confidence !== undefined && (
                                            <span className="flex items-center gap-1">
                                                <Sparkles className="w-3 h-3" />
                                                {formatConfidence(candidate.metadata.confidence)}
                                            </span>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Content */}
                            <div className="mb-4">
                                {typeof candidate.content === "string" ? (
                                    <p className="text-sm text-white/80 leading-relaxed line-clamp-6">
                                        {candidate.content}
                                    </p>
                                ) : (
                                    candidate.content
                                )}
                            </div>

                            {/* Select Button */}
                            <button
                                onClick={() => handleSelect(index as 0 | 1)}
                                disabled={disabled || isSubmitting || hasSubmitted}
                                className={`w-full py-2.5 rounded-lg font-medium text-sm transition-all ${
                                    isSelected
                                        ? colors.buttonActive
                                        : `${colors.button} hover:${colors.buttonActive}`
                                } disabled:opacity-50 disabled:cursor-not-allowed`}
                            >
                                {isSubmitting && isSelected ? (
                                    <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                                ) : isSelected ? (
                                    <span className="flex items-center justify-center gap-2">
                                        <Check className="w-4 h-4" />
                                        선택됨
                                    </span>
                                ) : (
                                    `이것 선택`
                                )}
                            </button>
                        </motion.div>
                    );
                })}
            </div>
        </div>
    );
}

/**
 * CandidateCard - Individual candidate display component
 *
 * Can be used standalone for custom layouts
 */
export function CandidateCard({
    candidate,
    label,
    isSelected,
    isDisabled,
    isLoading,
    onSelect,
    showMetrics,
    themeColor = "violet",
}: {
    candidate: CandidateData;
    label: string;
    isSelected: boolean;
    isDisabled: boolean;
    isLoading: boolean;
    onSelect: () => void;
    showMetrics?: boolean;
    themeColor?: ThemeColor;
}) {
    const colors = THEME_COLOR_CLASSES[themeColor];

    const formatLatency = (ms?: number) => {
        if (ms === undefined) return null;
        if (ms < 1000) return `${ms}ms`;
        return `${(ms / 1000).toFixed(1)}s`;
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`rounded-xl ${colors.bg} border ${colors.border} p-4 transition-all ${
                isSelected ? "ring-2 ring-offset-2 ring-offset-black" : ""
            }`}
            style={{ "--tw-ring-color": isSelected ? colors.text : "transparent" } as React.CSSProperties}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
                <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors.bg} ${colors.text}`}
                >
                    {label}
                </span>

                {showMetrics && candidate.metadata && (
                    <div className="flex items-center gap-2 text-xs text-white/40">
                        {candidate.metadata.latencyMs !== undefined && (
                            <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {formatLatency(candidate.metadata.latencyMs)}
                            </span>
                        )}
                    </div>
                )}
            </div>

            {/* Content */}
            <div className="mb-4">
                {typeof candidate.content === "string" ? (
                    <p className="text-sm text-white/80 leading-relaxed line-clamp-6">
                        {candidate.content}
                    </p>
                ) : (
                    candidate.content
                )}
            </div>

            {/* Select Button */}
            <button
                onClick={onSelect}
                disabled={isDisabled || isLoading}
                className={`w-full py-2.5 rounded-lg font-medium text-sm transition-all ${
                    isSelected ? colors.buttonActive : colors.button
                } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
                {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                ) : isSelected ? (
                    <span className="flex items-center justify-center gap-2">
                        <Check className="w-4 h-4" />
                        선택됨
                    </span>
                ) : (
                    "이것 선택"
                )}
            </button>
        </motion.div>
    );
}
