"use client";

/**
 * DimensionGrid - Grid display of dimension tools
 * 
 * Extracted from /dimension/page.tsx for reuse on unified home.
 * Shows all 10 dimension tools with stage filtering.
 */

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
    Sparkles, LayoutGrid, Image as ImageIcon, Brain, Search, Layers,
    Music, Video, CheckCircle, Palette, ChevronRight, LucideIcon, Wand2
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface DimensionItem {
    href: string;
    icon: LucideIcon;
    stage: "planning" | "pre_production" | "production" | "finishing" | "extended";
    stageOrder: number;
    titleKo: string;
    titleEn: string;
    descKo: string;
    descEn: string;
    portalColor: string;
    borderColor: string;
    textColor: string;
    gradient?: string;
    isNew?: boolean;
}

const WORKFLOW_STAGES = {
    planning: { order: 1, nameKo: "기획", nameEn: "Planning", color: "emerald" },
    pre_production: { order: 2, nameKo: "사전 제작", nameEn: "Pre-production", color: "violet" },
    production: { order: 3, nameKo: "제작", nameEn: "Production", color: "amber" },
    finishing: { order: 4, nameKo: "완성", nameEn: "Finishing", color: "cyan" },
    extended: { order: 5, nameKo: "확장", nameEn: "Extended", color: "fuchsia" },
} as const;

const DIMENSION_ITEMS: DimensionItem[] = [
    // Planning
    { href: "/dimension/abyss", icon: Brain, stage: "planning", stageOrder: 1, titleKo: "심연의 거울", titleEn: "Abyss Mirror", descKo: "나만의 취향과 창작 DNA 분석", descEn: "Analyze your creative DNA", portalColor: "border-indigo-500/50", borderColor: "border-indigo-500", textColor: "text-indigo-400", gradient: "from-indigo-500 via-violet-500 to-blue-500" },
    { href: "/dimension/reference-decoder", icon: Search, stage: "planning", stageOrder: 2, titleKo: "레퍼런스 해석기", titleEn: "Reference Decoder", descKo: "조명, 색감, 연출의 전문가적 분석", descEn: "Expert analysis of lighting, color, direction", portalColor: "border-amber-500/50", borderColor: "border-amber-500", textColor: "text-amber-400", gradient: "from-amber-500 via-orange-500 to-red-500" },
    { href: "/dimension/story-architect", icon: Layers, stage: "planning", stageOrder: 3, titleKo: "시나리오 생성기", titleEn: "Story Architect", descKo: "DNA와 스타일을 결합한 시나리오 작성", descEn: "Write scenarios combining DNA and style", portalColor: "border-emerald-500/50", borderColor: "border-emerald-500", textColor: "text-emerald-400", gradient: "from-emerald-500 via-green-500 to-lime-500", isNew: true },
    // Pre-production
    { href: "/dimension/sound-crafter", icon: Music, stage: "pre_production", stageOrder: 1, titleKo: "사운드 크래프터", titleEn: "Sound Crafter", descKo: "BGM 및 성우 내레이션 생성 (Suno, Udio)", descEn: "Generate BGM and narration (Suno, Udio)", portalColor: "border-pink-500/50", borderColor: "border-pink-500", textColor: "text-pink-400", gradient: "from-pink-500 via-rose-500 to-red-500", isNew: true },
    { href: "/dimension/storyboard", icon: LayoutGrid, stage: "pre_production", stageOrder: 2, titleKo: "스토리보드 스케치", titleEn: "Storyboard Sketch", descKo: "글을 시각적 컷으로 스케치", descEn: "Sketch text into visual cuts", portalColor: "border-cyan-500/50", borderColor: "border-cyan-500", textColor: "text-cyan-400", gradient: "from-cyan-500 via-teal-500 to-emerald-500" },
    { href: "/dimension/prompt", icon: Wand2, stage: "pre_production", stageOrder: 3, titleKo: "프롬프트 연금술", titleEn: "Prompt Alchemy", descKo: "AI가 이해하는 전문 언어로 번역", descEn: "Translate to AI-native language", portalColor: "border-violet-500/50", borderColor: "border-violet-500", textColor: "text-violet-400", gradient: "from-violet-500 via-purple-500 to-indigo-500" },
    // Production
    { href: "/dimension/visual-realizer", icon: ImageIcon, stage: "production", stageOrder: 1, titleKo: "비주얼 리얼라이저", titleEn: "Visual Realizer", descKo: "Key Frame 고품질 생성 (Midjourney)", descEn: "Generate high-quality keyframes", portalColor: "border-orange-500/50", borderColor: "border-orange-500", textColor: "text-orange-400", gradient: "from-orange-500 via-amber-500 to-yellow-500" },
    { href: "/dimension/video-maker", icon: Video, stage: "production", stageOrder: 2, titleKo: "비디오 메이커", titleEn: "Video Maker", descKo: "영상 변환 및 모션 제어 (Veo 3.1, Kling)", descEn: "Video conversion & motion control", portalColor: "border-sky-500/50", borderColor: "border-sky-500", textColor: "text-sky-400", gradient: "from-sky-500 via-blue-500 to-indigo-500" },
    // Finishing
    { href: "/dimension/quality-check", icon: CheckCircle, stage: "finishing", stageOrder: 1, titleKo: "퀄리티 디렉터", titleEn: "Quality Director", descKo: "시각적 일관성 및 동작 자연스러움 검수", descEn: "Check visual consistency & motion smoothness", portalColor: "border-rose-500/50", borderColor: "border-rose-500", textColor: "text-rose-400", gradient: "from-rose-500 via-pink-500 to-red-500" },
    // Extended
    { href: "/dimension/aesthetic", icon: Palette, stage: "extended", stageOrder: 1, titleKo: "미학디렉터", titleEn: "Aesthetic Director", descKo: "거장들의 미학을 적용합니다", descEn: "Apply masters' aesthetics", portalColor: "border-fuchsia-500/50", borderColor: "border-fuchsia-500", textColor: "text-fuchsia-400", gradient: "from-fuchsia-500 via-purple-500 to-pink-500" },
];

type StageKey = keyof typeof WORKFLOW_STAGES;

interface DimensionGridProps {
    showTitle?: boolean;
    showFilters?: boolean;
    compact?: boolean;
}

export function DimensionGrid({ showTitle = true, showFilters = true, compact = false }: DimensionGridProps) {
    const { language } = useLanguage();
    const [selectedStage, setSelectedStage] = useState<StageKey | null>(null);

    const filteredItems = selectedStage
        ? DIMENSION_ITEMS.filter((d) => d.stage === selectedStage)
        : DIMENSION_ITEMS;

    const stageKeys = Object.keys(WORKFLOW_STAGES) as StageKey[];

    const stageColors: Record<string, { bg: string; text: string }> = {
        emerald: { bg: "bg-emerald-500", text: "text-emerald-950" },
        violet: { bg: "bg-violet-500", text: "text-violet-100" },
        amber: { bg: "bg-amber-500", text: "text-amber-950" },
        cyan: { bg: "bg-cyan-500", text: "text-cyan-950" },
        fuchsia: { bg: "bg-fuchsia-500", text: "text-fuchsia-100" },
    };

    return (
        <div className="space-y-4">
            {/* Header */}
            {showTitle && (
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-cyan-500 dark:text-cyan-400" />
                        <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                            {language === "ko" ? "차원 앱" : "Dimension Apps"}
                        </h2>
                    </div>
                    <Link
                        href="/dimension"
                        className="flex items-center gap-1 text-sm text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                    >
                        {language === "ko" ? "전체보기" : "See all"}
                        <ChevronRight className="h-4 w-4" />
                    </Link>
                </div>
            )}

            {/* Stage Filters */}
            {showFilters && (
                <div className="flex flex-wrap gap-2 p-2 rounded-2xl bg-gray-100 dark:bg-white/5 backdrop-blur-sm">
                    <button
                        onClick={() => setSelectedStage(null)}
                        className={`px-4 py-2 rounded-xl text-xs font-bold tracking-wider uppercase transition-all ${selectedStage === null
                            ? "bg-white dark:bg-white text-black shadow-lg"
                            : "text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white"
                            }`}
                    >
                        ALL
                    </button>
                    {stageKeys.map((stageKey) => {
                        const stage = WORKFLOW_STAGES[stageKey];
                        const isSelected = selectedStage === stageKey;
                        const colors = stageColors[stage.color] || stageColors.emerald;

                        return (
                            <button
                                key={stageKey}
                                onClick={() => setSelectedStage(isSelected ? null : stageKey)}
                                className={`px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${isSelected
                                    ? `${colors.bg} ${colors.text} shadow-lg`
                                    : "text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white bg-gray-200/50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10"
                                    }`}
                            >
                                <span className="text-[10px] font-mono opacity-60">{stage.order}</span>
                                <span>{language === "ko" ? stage.nameKo : stage.nameEn}</span>
                            </button>
                        );
                    })}
                </div>
            )}

            {/* Grid */}
            <motion.div
                className={`grid gap-4 ${compact
                    ? "grid-cols-2 sm:grid-cols-3 lg:grid-cols-5"
                    : "sm:grid-cols-2 lg:grid-cols-4"
                    }`}
                layout
            >
                <AnimatePresence mode="popLayout">
                    {filteredItems.map((dimension, idx) => {
                        const Icon = dimension.icon;
                        const stageInfo = WORKFLOW_STAGES[dimension.stage];

                        return (
                            <motion.div
                                key={dimension.href}
                                layout
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.9 }}
                                transition={{ duration: 0.2, delay: idx * 0.03 }}
                            >
                                <Link
                                    href={dimension.href}
                                    className={`group block relative overflow-hidden rounded-2xl border border-gray-200 dark:border-white/10 bg-gray-50/50 dark:bg-white/[0.02] backdrop-blur-sm hover:bg-gray-100/80 dark:hover:bg-white/[0.04] transition-all hover:-translate-y-1 ${compact ? "p-3" : "p-5"
                                        }`}
                                >
                                    {/* NEW Badge */}
                                    {dimension.isNew && (
                                        <div className="absolute top-2 right-2 px-1.5 py-0.5 rounded-full bg-lime-500 text-black text-[9px] font-bold tracking-wider">
                                            NEW
                                        </div>
                                    )}

                                    {/* Hover border */}
                                    <div className={`absolute inset-0 rounded-2xl border-2 ${dimension.borderColor} opacity-0 group-hover:opacity-100 transition-opacity`} />

                                    {/* Gradient background */}
                                    <div className={`absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity bg-gradient-to-br ${dimension.gradient}`} />

                                    <div className={`relative flex items-start gap-3 ${compact ? "flex-col" : ""}`}>
                                        {/* Icon */}
                                        <div className={`flex items-center justify-center rounded-xl bg-gray-100 dark:bg-white/5 border border-gray-200 dark:border-white/10 group-hover:scale-110 transition-transform ${compact ? "h-8 w-8" : "h-10 w-10"
                                            }`}>
                                            <Icon className={`${compact ? "h-4 w-4" : "h-5 w-5"} ${dimension.textColor}`} />
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            {/* Stage label */}
                                            <span className={`text-[10px] font-mono tracking-wider ${dimension.textColor} opacity-60`}>
                                                {stageInfo.order}.{dimension.stageOrder}
                                            </span>
                                            {/* Title */}
                                            <h3 className={`font-semibold text-gray-900 dark:text-white truncate ${compact ? "text-sm" : "text-base"}`}>
                                                {language === "ko" ? dimension.titleKo : dimension.titleEn}
                                            </h3>
                                            {/* Description */}
                                            {!compact && (
                                                <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                                                    {language === "ko" ? dimension.descKo : dimension.descEn}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                </Link>
                            </motion.div>
                        );
                    })}
                </AnimatePresence>
            </motion.div>
        </div>
    );
}
