"use client";

/**
 * ThreeWayComparison - Ensemble++ 3-Way 비교 컴포넌트 for UQSL
 *
 * NeurIPS 2025 Ensemble++ 프레임워크 기반 (arXiv:2407.13195)
 *
 * Features:
 * - 3가지 결과 비교 (A: Qdrant, B: NotebookLM, AB: Ensemble)
 * - 권장 옵션 하이라이트
 * - 탭/카드 레이아웃 전환
 * - "잘 모르겠어요" 스킵 옵션
 * - DimensionPanel 토큰 시스템 사용
 * - Framer Motion 애니메이션
 * - 반응형 (모바일: 스와이프)
 *
 * @see UQSL_SPEC.md - Universal Quality Selection Layer
 */

import { useState, useCallback, useMemo } from "react";
import { Check, Loader2, Sparkles, HelpCircle, ChevronLeft, ChevronRight, Layers } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { type ThemeColor, THEME_COLOR_CLASSES } from "@/lib/dimension-theme";

export interface ThreeWayCandidateData {
    /** Unique identifier */
    id: string;
    /** Content to display */
    content: string | React.ReactNode;
    /** Confidence score (0-1) */
    confidence?: number;
    /** Backend used */
    backendUsed?: string;
    /** Additional metadata */
    metadata?: Record<string, unknown>;
}

export type ThreeWaySelection = "a" | "b" | "ab" | "skip";

export interface ThreeWayComparisonProps {
    /** Three candidates to compare */
    candidates: {
        a: ThreeWayCandidateData;   // Backend A (e.g., Qdrant)
        b: ThreeWayCandidateData;   // Backend B (e.g., NotebookLM)
        ab: ThreeWayCandidateData;  // Ensemble (A+B merged)
    };
    /** Callback when a candidate is selected */
    onSelect: (selected: ThreeWaySelection) => Promise<void>;
    /** Custom labels */
    labels?: { a: string; b: string; ab: string };
    /** Show confidence scores */
    showConfidence?: boolean;
    /** Recommended option (will be highlighted) */
    recommended?: "a" | "b" | "ab";
    /** Theme color */
    themeColor?: ThemeColor;
    /** Disabled state */
    disabled?: boolean;
    /** Initial selected (if any) */
    initialSelected?: ThreeWaySelection | null;
    /** Layout mode */
    layout?: "tabs" | "cards" | "auto";
}

const DEFAULT_LABELS = {
    a: "옵션 A",
    b: "옵션 B",
    ab: "앙상블 (A+B)",
};

const OPTION_COLORS = {
    a: "blue",
    b: "purple",
    ab: "emerald",
} as const;

export default function ThreeWayComparison({
    candidates,
    onSelect,
    labels = DEFAULT_LABELS,
    showConfidence = true,
    recommended,
    themeColor = "violet",
    disabled = false,
    initialSelected = null,
    layout = "auto",
}: ThreeWayComparisonProps) {
    const [selectedOption, setSelectedOption] = useState<ThreeWaySelection | null>(initialSelected);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [hasSubmitted, setHasSubmitted] = useState(false);
    const [activeTab, setActiveTab] = useState<"a" | "b" | "ab">("ab");
    const colors = THEME_COLOR_CLASSES[themeColor];

    // Responsive layout detection
    const effectiveLayout = useMemo(() => {
        if (layout !== "auto") return layout;
        // In production, use window width or CSS media queries
        return "cards";
    }, [layout]);

    const handleSelect = useCallback(
        async (option: ThreeWaySelection) => {
            if (disabled || isSubmitting || hasSubmitted) return;

            setSelectedOption(option);

            if (option === "skip") {
                setIsSubmitting(true);
                try {
                    await onSelect("skip");
                    setHasSubmitted(true);
                } catch (error) {
                    console.error("Skip failed:", error);
                    setSelectedOption(null);
                } finally {
                    setIsSubmitting(false);
                }
                return;
            }

            setIsSubmitting(true);
            try {
                await onSelect(option);
                setHasSubmitted(true);
            } catch (error) {
                console.error("Selection failed:", error);
                setSelectedOption(null);
            } finally {
                setIsSubmitting(false);
            }
        },
        [disabled, isSubmitting, hasSubmitted, onSelect]
    );

    const formatConfidence = (confidence?: number) => {
        if (confidence === undefined) return null;
        return `${Math.round(confidence * 100)}%`;
    };

    // Submitted state
    if (hasSubmitted && selectedOption !== null) {
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
                        {selectedOption === "skip"
                            ? "선택을 건너뛰었습니다"
                            : `${labels[selectedOption]}를 선택했습니다`}
                    </span>
                </div>
            </motion.div>
        );
    }

    // Tab layout for mobile
    if (effectiveLayout === "tabs") {
        return (
            <div className={`rounded-xl ${colors.bg} border ${colors.border} overflow-hidden`}>
                {/* Tab Header */}
                <div className="flex border-b border-white/10">
                    {(["a", "b", "ab"] as const).map((key) => (
                        <button
                            key={key}
                            onClick={() => setActiveTab(key)}
                            className={`flex-1 px-4 py-3 text-sm font-medium transition-all relative ${
                                activeTab === key
                                    ? "text-white"
                                    : "text-white/50 hover:text-white/70"
                            }`}
                        >
                            {key === recommended && (
                                <Sparkles className="w-3 h-3 absolute top-2 right-2 text-amber-400" />
                            )}
                            {labels[key]}
                            {activeTab === key && (
                                <motion.div
                                    layoutId="activeTab"
                                    className={`absolute bottom-0 left-0 right-0 h-0.5 bg-${OPTION_COLORS[key]}-500`}
                                />
                            )}
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeTab}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="p-4"
                    >
                        <CandidateContent
                            candidate={candidates[activeTab]}
                            label={labels[activeTab]}
                            optionKey={activeTab}
                            isRecommended={recommended === activeTab}
                            showConfidence={showConfidence}
                            formatConfidence={formatConfidence}
                        />

                        <button
                            onClick={() => handleSelect(activeTab)}
                            disabled={disabled || isSubmitting}
                            className={`w-full mt-4 py-3 rounded-xl font-medium text-sm transition-all ${
                                selectedOption === activeTab
                                    ? `bg-${OPTION_COLORS[activeTab]}-500 text-white`
                                    : `bg-${OPTION_COLORS[activeTab]}-500/20 text-${OPTION_COLORS[activeTab]}-400 hover:bg-${OPTION_COLORS[activeTab]}-500/30`
                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                        >
                            {isSubmitting && selectedOption === activeTab ? (
                                <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                            ) : (
                                "이것 선택"
                            )}
                        </button>
                    </motion.div>
                </AnimatePresence>

                {/* Navigation arrows for mobile swipe hint */}
                <div className="flex justify-between px-4 py-2 text-white/30">
                    <button
                        onClick={() => setActiveTab(activeTab === "a" ? "ab" : activeTab === "ab" ? "b" : "a")}
                        className="p-1 hover:text-white/50 transition-colors"
                    >
                        <ChevronLeft className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => setActiveTab(activeTab === "a" ? "b" : activeTab === "b" ? "ab" : "a")}
                        className="p-1 hover:text-white/50 transition-colors"
                    >
                        <ChevronRight className="w-4 h-4" />
                    </button>
                </div>

                {/* Skip button */}
                <div className="px-4 pb-4">
                    <button
                        onClick={() => handleSelect("skip")}
                        disabled={disabled || isSubmitting}
                        className="w-full flex items-center justify-center gap-2 py-2 text-xs text-white/40 hover:text-white/60 transition-colors disabled:opacity-50"
                    >
                        <HelpCircle className="w-3 h-3" />
                        <span>잘 모르겠어요</span>
                    </button>
                </div>
            </div>
        );
    }

    // Card layout (default)
    return (
        <div className={`rounded-xl ${colors.bg} border ${colors.border} overflow-hidden`}>
            {/* Header */}
            <div className="px-4 py-3 border-b border-white/10">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Layers className="w-4 h-4 text-white/50" />
                        <h3 className="text-sm font-medium text-white">
                            세 가지 결과 중 선택하세요
                        </h3>
                    </div>
                    <button
                        onClick={() => handleSelect("skip")}
                        disabled={disabled || isSubmitting}
                        className="flex items-center gap-1 px-2 py-1 text-xs text-white/50 hover:text-white/70 transition-colors disabled:opacity-50"
                    >
                        <HelpCircle className="w-3 h-3" />
                        <span>잘 모르겠어요</span>
                    </button>
                </div>
            </div>

            {/* Three-way Grid */}
            <div className="grid grid-cols-3 gap-0">
                {(["a", "b", "ab"] as const).map((key, index) => {
                    const candidate = candidates[key];
                    const label = labels[key];
                    const isSelected = selectedOption === key;
                    const isOtherSelected = selectedOption !== null && selectedOption !== key && selectedOption !== "skip";
                    const isRecommended = recommended === key;

                    return (
                        <motion.div
                            key={key}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className={`relative p-4 ${
                                index < 2 ? "border-r border-white/10" : ""
                            } ${isOtherSelected ? "opacity-50" : ""}`}
                        >
                            {/* Recommended badge */}
                            {isRecommended && (
                                <div className="absolute -top-0 left-1/2 -translate-x-1/2 -translate-y-1/2">
                                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 text-[10px] font-medium">
                                        <Sparkles className="w-2.5 h-2.5" />
                                        추천
                                    </span>
                                </div>
                            )}

                            {/* Label Badge */}
                            <div className="flex items-center justify-between mb-3">
                                <span
                                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${OPTION_COLORS[key]}-500/20 text-${OPTION_COLORS[key]}-400`}
                                >
                                    {label}
                                </span>

                                {/* Confidence */}
                                {showConfidence && candidate.confidence !== undefined && (
                                    <span className="flex items-center gap-1 text-xs text-white/40">
                                        <Sparkles className="w-3 h-3" />
                                        {formatConfidence(candidate.confidence)}
                                    </span>
                                )}
                            </div>

                            {/* Content */}
                            <div className="mb-4 min-h-[120px]">
                                {typeof candidate.content === "string" ? (
                                    <p className="text-sm text-white/80 leading-relaxed line-clamp-6">
                                        {candidate.content}
                                    </p>
                                ) : (
                                    candidate.content
                                )}
                            </div>

                            {/* Backend indicator */}
                            {candidate.backendUsed && (
                                <p className="text-[10px] text-white/30 mb-2">
                                    via {candidate.backendUsed}
                                </p>
                            )}

                            {/* Select Button */}
                            <button
                                onClick={() => handleSelect(key)}
                                disabled={disabled || isSubmitting || hasSubmitted}
                                className={`w-full py-2.5 rounded-lg font-medium text-sm transition-all ${
                                    isSelected
                                        ? `bg-${OPTION_COLORS[key]}-500 text-white shadow-lg shadow-${OPTION_COLORS[key]}-500/20`
                                        : `bg-${OPTION_COLORS[key]}-500/20 text-${OPTION_COLORS[key]}-400 hover:bg-${OPTION_COLORS[key]}-500/30`
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
                                    "선택"
                                )}
                            </button>
                        </motion.div>
                    );
                })}
            </div>

            {/* Ensemble explanation */}
            <div className="px-4 py-3 border-t border-white/10 bg-white/[0.02]">
                <p className="text-[11px] text-white/40 text-center">
                    💡 <strong className="text-white/50">앙상블(A+B)</strong>는 두 시스템의 결과를 결합하여 더 정확한 답변을 제공합니다
                </p>
            </div>
        </div>
    );
}

/**
 * CandidateContent - Internal component for candidate display
 */
function CandidateContent({
    candidate,
    label,
    optionKey,
    isRecommended,
    showConfidence,
    formatConfidence,
}: {
    candidate: ThreeWayCandidateData;
    label: string;
    optionKey: "a" | "b" | "ab";
    isRecommended: boolean;
    showConfidence: boolean;
    formatConfidence: (c?: number) => string | null;
}) {
    return (
        <div>
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${OPTION_COLORS[optionKey]}-500/20 text-${OPTION_COLORS[optionKey]}-400`}
                    >
                        {label}
                    </span>
                    {isRecommended && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 text-[10px] font-medium">
                            <Sparkles className="w-2.5 h-2.5" />
                            추천
                        </span>
                    )}
                </div>

                {showConfidence && candidate.confidence !== undefined && (
                    <span className="flex items-center gap-1 text-xs text-white/40">
                        <Sparkles className="w-3 h-3" />
                        {formatConfidence(candidate.confidence)}
                    </span>
                )}
            </div>

            {/* Content */}
            <div className="min-h-[150px]">
                {typeof candidate.content === "string" ? (
                    <p className="text-sm text-white/80 leading-relaxed">
                        {candidate.content}
                    </p>
                ) : (
                    candidate.content
                )}
            </div>

            {/* Backend indicator */}
            {candidate.backendUsed && (
                <p className="text-[10px] text-white/30 mt-2">
                    via {candidate.backendUsed}
                </p>
            )}
        </div>
    );
}

/**
 * CompactThreeWay - Simplified version for inline use
 */
export function CompactThreeWay({
    options,
    onSelect,
    recommended,
    disabled = false,
}: {
    options: { a: string; b: string; ab: string };
    onSelect: (selected: "a" | "b" | "ab") => void;
    recommended?: "a" | "b" | "ab";
    disabled?: boolean;
}) {
    return (
        <div className="flex gap-2">
            {(["a", "b", "ab"] as const).map((key) => (
                <button
                    key={key}
                    onClick={() => onSelect(key)}
                    disabled={disabled}
                    className={`flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                        recommended === key
                            ? `bg-${OPTION_COLORS[key]}-500 text-white ring-2 ring-${OPTION_COLORS[key]}-400/50`
                            : `bg-${OPTION_COLORS[key]}-500/20 text-${OPTION_COLORS[key]}-400 hover:bg-${OPTION_COLORS[key]}-500/30`
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                    {options[key]}
                    {recommended === key && (
                        <Sparkles className="w-3 h-3 inline ml-1" />
                    )}
                </button>
            ))}
        </div>
    );
}
