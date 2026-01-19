"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Sparkles,
    LayoutGrid,
    Image as ImageIcon,
    Film,
    ChevronRight,
    ChevronDown,
    Compass,
    RefreshCw,
    CheckCircle,
    Palette,
    Moon,
    Video,
} from "lucide-react";
import { dimensionIdToCode, getDimensionToken, type DimensionCode } from "@/lib/tokens";
import { useLanguage } from "@/contexts/LanguageContext";
import { getReasonCodeLabel, getConfidenceLabel, scoreToConfidenceLevel } from "@/lib/reason-codes";

interface ConnectionOption {
    id: string;
    label: string;
    description: string;
    recommendedToolId: string;
    icon: string;
    color: string;
    dimension: string;
    dimensionCode: DimensionCode | null;
    confidence: number;
    reasonCodes?: string[];
}

interface ConnectionSelectorProps {
    options: ConnectionOption[];
    onSelect: (optionId: string) => void;
    onReRecommend?: () => void;
    isLoading?: boolean;
    isPrimarySelection?: boolean; // 초기 차원 선택 모드 (1D 강조)
}

const ICON_MAP: Record<string, React.ReactNode> = {
    sparkles: <Sparkles className="h-5 w-5" />,
    "layout-grid": <LayoutGrid className="h-5 w-5" />,
    image: <ImageIcon className="h-5 w-5" />,
    film: <Film className="h-5 w-5" />,
    // Extended Dimension Icons
    "check-circle": <CheckCircle className="h-5 w-5" />,
    palette: <Palette className="h-5 w-5" />,
    moon: <Moon className="h-5 w-5" />,
    video: <Video className="h-5 w-5" />,
};

const getDimensionColorClasses = (dimensionCode?: DimensionCode | null) => {
    if (!dimensionCode) return null;
    const token = getDimensionToken(dimensionCode);
    const key = token.tailwindKey;
    return {
        bg: `bg-${key}/10`,
        border: `border-${key}/30`,
        text: `text-${key}`,
        hover: `hover:bg-${key}/20 hover:border-${key}/50`,
        glow: `shadow-[0_0_15px] shadow-${key}/20`,
    };
};

// 추천 상위 N개
const INITIAL_SHOW_COUNT = 3;

export function ConnectionSelector({
    options,
    onSelect,
    onReRecommend,
    isLoading = false,
    isPrimarySelection = false,
}: ConnectionSelectorProps) {
    const { language, t } = useLanguage();
    const isKo = language === "ko";
    const [hoveredId, setHoveredId] = useState<string | null>(null);
    const [showAll, setShowAll] = useState(false);

    // confidence 기준으로 정렬
    const sortedOptions = [...options].sort((a, b) => b.confidence - a.confidence);

    // 표시할 옵션들 (Primary Selection 모드에서는 더 많이 보여줌)
    const initialShowCount = isPrimarySelection ? 4 : INITIAL_SHOW_COUNT;
    const visibleOptions = showAll ? sortedOptions : sortedOptions.slice(0, initialShowCount);
    const hiddenCount = sortedOptions.length - initialShowCount;

    return (
        <div className="flex flex-col items-center gap-4">
            {/* 차원문 포털 심볼 */}
            <div className="flex items-center gap-2">
                <div className="h-px w-8 bg-gradient-to-r from-transparent via-dimension-1d/50 to-zinc-600" />
                <motion.div
                    animate={{ scale: [1, 1.15, 1], rotate: [0, 180, 360] }}
                    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                    className="h-10 w-10 rounded-full bg-dimension-1d/20 border-2 border-dimension-1d/40 flex items-center justify-center shadow-[0_0_20px] shadow-dimension-1d/30"
                >
                    <Compass className="h-5 w-5 text-dimension-1d" />
                </motion.div>
                <div className="h-px w-8 bg-gradient-to-l from-transparent via-dimension-1d/50 to-zinc-600" />
            </div>

            {/* 추천 라벨 */}
            <div className="text-[10px] uppercase tracking-wider text-gray-500 dark:text-zinc-500 flex items-center gap-1.5">
                <Sparkles className="h-3 w-3 text-dimension-1d" />
                {t("recommendedDimensions")}
            </div>

            {/* 옵션 카드 */}
            <div className="flex flex-col gap-2 w-56">
                <AnimatePresence mode="wait">
                    {isLoading ? (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="flex flex-col gap-2"
                        >
                            {[1, 2, 3].map((i) => (
                                <div
                                    key={i}
                                    className="h-16 rounded-xl bg-zinc-800/50 animate-pulse"
                                />
                            ))}
                        </motion.div>
                    ) : (
                        <>
                            {visibleOptions.map((option, index) => {
                                const resolvedCode = option.dimensionCode ?? dimensionIdToCode(option.dimension);
                                const tokenScheme = getDimensionColorClasses(resolvedCode);
                                const colorScheme = tokenScheme ?? getDimensionColorClasses("1d") ?? {
                                    bg: "bg-gray-800", border: "border-gray-600", text: "text-gray-400",
                                    hover: "hover:bg-gray-700", glow: ""
                                };
                                const IconComponent = ICON_MAP[option.icon] || <Sparkles className="h-5 w-5" />;
                                const isHovered = hoveredId === option.id;
                                const isTopRecommend = index === 0;
                                // Primary Selection 모드에서 1위 옵션은 더 강조
                                const isPrimary = isPrimarySelection && isTopRecommend;
                                const reasonTooltip = option.reasonCodes && option.reasonCodes.length > 0
                                    ? option.reasonCodes.slice(0, 2).map((code) => getReasonCodeLabel(code, language)).join(", ")
                                    : undefined;
                                const confidenceLevel = scoreToConfidenceLevel(option.confidence);
                                const confidenceLabel = getConfidenceLabel(confidenceLevel, language);
                                const confidenceTone = confidenceLevel === "high"
                                    ? "text-emerald-500 bg-emerald-500/10 border-emerald-500/30"
                                    : confidenceLevel === "medium"
                                    ? "text-amber-500 bg-amber-500/10 border-amber-500/30"
                                    : "text-slate-400 bg-slate-500/10 border-slate-500/30";
                                const badgeLabel = t("recommendationTopBadge");

                                return (
                                    <motion.button
                                        key={option.id}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{
                                            opacity: isPrimarySelection && !isTopRecommend ? 0.7 : 1,
                                            x: 0,
                                            scale: isPrimary ? 1.02 : 1,
                                        }}
                                        whileHover={{ scale: 1.02, opacity: 1 }}
                                        transition={{ delay: index * 0.08 }}
                                        onClick={() => onSelect(option.id)}
                                        onMouseEnter={() => setHoveredId(option.id)}
                                        onMouseLeave={() => setHoveredId(null)}
                                        title={reasonTooltip}
                                        className={`
                                            relative flex items-center gap-3 rounded-xl
                                            ${isPrimary ? "p-4" : "p-3"}
                                            ${colorScheme.bg} ${colorScheme.border} border
                                            ${colorScheme.hover}
                                            ${isTopRecommend ? colorScheme.glow : ""}
                                            ${isPrimary ? "shadow-[0_0_30px] shadow-dimension-1d/40 border-2" : ""}
                                            transition-all duration-300
                                            group cursor-pointer
                                        `}
                                    >
                                        {/* 추천 뱃지 (1위만) */}
                                        {isTopRecommend && (
                                            <div className="absolute -top-1.5 -right-1.5 px-1.5 py-0.5 rounded-full bg-dimension-1d text-[8px] font-bold text-white">
                                                {badgeLabel}
                                            </div>
                                        )}

                                        {/* 옵션 번호 */}
                                        <div className={`
                                            absolute -left-3 top-1/2 -translate-y-1/2 h-6 w-6 rounded-full
                                            ${isTopRecommend ? "bg-dimension-1d border-dimension-1d/50 text-white" : "bg-zinc-900 border-zinc-700 text-zinc-400"}
                                            border flex items-center justify-center text-[10px] font-bold
                                        `}>
                                            {index + 1}
                                        </div>

                                        {/* 아이콘 */}
                                        <div className={`${colorScheme.text}`}>
                                            {IconComponent}
                                        </div>

                                        {/* 텍스트 */}
                                        <div className="flex-1 text-left">
                                            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                                {option.label}
                                            </p>
                                            <p className="text-[10px] text-gray-500 dark:text-zinc-500 truncate">
                                                {option.description}
                                            </p>
                                            {option.reasonCodes && option.reasonCodes.length > 0 && (
                                                <div className="mt-1 flex flex-wrap gap-1">
                                                    {option.reasonCodes.slice(0, 2).map((code) => (
                                                        <span
                                                            key={code}
                                                            className="evidence-badge text-[9px]"
                                                        >
                                                            {getReasonCodeLabel(code, language)}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>

                                        {/* 신뢰도 + 화살표 */}
                                        <div className="flex items-center gap-1">
                                            <div className="flex flex-col items-end gap-0.5">
                                                <span
                                                    className={`text-[9px] px-1.5 py-0.5 rounded-full border ${confidenceTone}`}
                                                >
                                                    {confidenceLabel}
                                                </span>
                                                <span className={`text-[10px] ${isTopRecommend ? colorScheme.text : "text-zinc-500"}`}>
                                                    {Math.round(option.confidence * 100)}%
                                                </span>
                                            </div>
                                            <ChevronRight
                                                className={`
                                                    h-4 w-4 text-zinc-500
                                                    transition-transform duration-300
                                                    ${isHovered ? "translate-x-1 text-white" : ""}
                                                `}
                                            />
                                        </div>
                                    </motion.button>
                                );
                            })}
                        </>
                    )}
                </AnimatePresence>
            </div>

            {/* 더 보기 / 접기 버튼 */}
            {hiddenCount > 0 && !isLoading && (
                <motion.button
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    onClick={() => setShowAll(!showAll)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-200/50 dark:bg-zinc-800/30 border border-gray-300/50 dark:border-zinc-700/50 text-gray-600 dark:text-zinc-400 text-xs hover:bg-gray-200 dark:hover:bg-zinc-800/50 hover:text-gray-900 dark:hover:text-white transition-all"
                >
                    <ChevronDown className={`h-3 w-3 transition-transform ${showAll ? "rotate-180" : ""}`} />
                    {showAll
                        ? t("collapseLabel")
                        : (isKo
                            ? `+${hiddenCount}개 ${t("moreLabel")}`
                            : `+${hiddenCount} ${t("moreLabel")}`)}
                </motion.button>
            )}

            {/* 재추천 버튼 */}
            {onReRecommend && !isLoading && (
                <button
                    onClick={onReRecommend}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-200/50 dark:bg-zinc-800/50 border border-gray-300 dark:border-zinc-700 text-gray-600 dark:text-zinc-400 text-xs hover:bg-gray-200 dark:hover:bg-zinc-800 hover:text-gray-900 dark:hover:text-white transition-all"
                >
                    <RefreshCw className="h-3 w-3" />
                    {t("exploreOtherDimensions")}
                </button>
            )}
        </div>
    );
}
