"use client";

import Link from "next/link";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Sparkles, LayoutGrid, Image as ImageIcon, Plus, Eye, LucideIcon,
    CheckCircle, Palette, Moon, Film, ChevronRight, Link2, X, Trash2,
    Brain, Search, Layers, Music, Video, Wand2
} from "lucide-react";
import { AuroraBackground } from "@/components/AuroraBackground";
import { MiniAppSubmitModal } from "@/components/MiniAppSubmitModal";
import { useParallaxScroll } from "@/hooks/useLusionAnimations";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";
import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";

interface DimensionItemData {
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
    glowClass: string;
    activeBg: string;
    activeText: string;
    textColor: string;
    gradient?: string;
    isNew?: boolean;
}

// 4-Stage Workflow Structure
const WORKFLOW_STAGES = {
    planning: { order: 1, nameKo: "기획", nameEn: "Planning", color: "emerald" },
    pre_production: { order: 2, nameKo: "사전 제작", nameEn: "Pre-production", color: "violet" },
    production: { order: 3, nameKo: "제작", nameEn: "Production", color: "amber" },
    finishing: { order: 4, nameKo: "완성", nameEn: "Finishing", color: "cyan" },
    extended: { order: 5, nameKo: "확장", nameEn: "Extended", color: "fuchsia" },
};

const DIMENSION_ITEMS: DimensionItemData[] = [
    // ========== Stage 1: 기획 (Planning) ==========
    {
        href: "/dimension/abyss",
        icon: Brain,
        stage: "planning",
        stageOrder: 1,
        titleKo: "심연의 거울",
        titleEn: "Abyss Mirror",
        descKo: "나만의 취향과 창작 DNA 분석",
        descEn: "Analyze your creative DNA",
        portalColor: "border-indigo-500/50",
        borderColor: "border-indigo-500",
        glowClass: "glow-breathe glow-breathe-indigo",
        activeBg: "bg-indigo-500",
        activeText: "text-indigo-100",
        textColor: "text-indigo-400",
        gradient: "from-indigo-500 via-violet-500 to-blue-500",
    },
    {
        href: "/dimension/reference-decoder",
        icon: Search,
        stage: "planning",
        stageOrder: 2,
        titleKo: "레퍼런스 해석기",
        titleEn: "Reference Decoder",
        descKo: "조명, 색감, 연출의 전문가적 분석",
        descEn: "Expert analysis of lighting, color, direction",
        portalColor: "border-amber-500/50",
        borderColor: "border-amber-500",
        glowClass: "glow-breathe glow-breathe-amber",
        activeBg: "bg-amber-500",
        activeText: "text-amber-950",
        textColor: "text-amber-400",
        gradient: "from-amber-500 via-orange-500 to-red-500",
    },
    {
        href: "/dimension/story-architect",
        icon: Layers,
        stage: "planning",
        stageOrder: 3,
        titleKo: "시나리오 생성기",
        titleEn: "Story Architect",
        descKo: "DNA와 스타일을 결합한 시나리오 작성",
        descEn: "Write scenarios combining DNA and style",
        portalColor: "border-emerald-500/50",
        borderColor: "border-emerald-500",
        glowClass: "glow-breathe glow-breathe-emerald",
        activeBg: "bg-emerald-500",
        activeText: "text-emerald-950",
        textColor: "text-emerald-400",
        gradient: "from-emerald-500 via-green-500 to-lime-500",
        isNew: true,
    },

    // ========== Stage 2: 사전 제작 (Pre-production) ==========
    {
        href: "/dimension/sound-crafter",
        icon: Music,
        stage: "pre_production",
        stageOrder: 1,
        titleKo: "사운드 크래프터",
        titleEn: "Sound Crafter",
        descKo: "BGM 및 성우 내레이션 생성 (Suno, Udio)",
        descEn: "Generate BGM and narration (Suno, Udio)",
        portalColor: "border-pink-500/50",
        borderColor: "border-pink-500",
        glowClass: "glow-breathe glow-breathe-pink",
        activeBg: "bg-pink-500",
        activeText: "text-pink-100",
        textColor: "text-pink-400",
        gradient: "from-pink-500 via-rose-500 to-red-500",
        isNew: true,
    },
    {
        href: "/dimension/storyboard",
        icon: LayoutGrid,
        stage: "pre_production",
        stageOrder: 2,
        titleKo: "스토리보드 스케치",
        titleEn: "Storyboard Sketch",
        descKo: "글을 시각적 컷으로 스케치",
        descEn: "Sketch text into visual cuts",
        portalColor: "border-cyan-500/50",
        borderColor: "border-cyan-500",
        glowClass: "glow-breathe glow-breathe-cyan",
        activeBg: "bg-cyan-500",
        activeText: "text-cyan-950",
        textColor: "text-cyan-400",
        gradient: "from-cyan-500 via-teal-500 to-emerald-500",
    },
    {
        href: "/dimension/prompt",
        icon: Wand2,
        stage: "pre_production",
        stageOrder: 3,
        titleKo: "프롬프트 연금술",
        titleEn: "Prompt Alchemy",
        descKo: "AI가 이해하는 전문 언어로 번역",
        descEn: "Translate to AI-native language",
        portalColor: "border-violet-500/50",
        borderColor: "border-violet-500",
        glowClass: "glow-breathe glow-breathe-violet",
        activeBg: "bg-violet-500",
        activeText: "text-violet-100",
        textColor: "text-violet-400",
        gradient: "from-violet-500 via-purple-500 to-indigo-500",
    },

    // ========== Stage 3: 제작 (Production) ==========
    {
        href: "/dimension/visual-realizer",
        icon: ImageIcon,
        stage: "production",
        stageOrder: 1,
        titleKo: "비주얼 리얼라이저",
        titleEn: "Visual Realizer",
        descKo: "Key Frame 고품질 생성 (Midjourney)",
        descEn: "Generate high-quality keyframes",
        portalColor: "border-orange-500/50",
        borderColor: "border-orange-500",
        glowClass: "glow-breathe glow-breathe-orange",
        activeBg: "bg-orange-500",
        activeText: "text-orange-950",
        textColor: "text-orange-400",
        gradient: "from-orange-500 via-amber-500 to-yellow-500",
    },
    {
        href: "/dimension/video-maker",
        icon: Video,
        stage: "production",
        stageOrder: 2,
        titleKo: "비디오 메이커",
        titleEn: "Video Maker",
        descKo: "영상 변환 및 모션 제어 (Veo 3.1, Kling)",
        descEn: "Video conversion & motion control",
        portalColor: "border-sky-500/50",
        borderColor: "border-sky-500",
        glowClass: "glow-breathe glow-breathe-sky",
        activeBg: "bg-sky-500",
        activeText: "text-sky-100",
        textColor: "text-sky-400",
        gradient: "from-sky-500 via-blue-500 to-indigo-500",
    },

    // ========== Stage 4: 완성 (Finishing) ==========
    {
        href: "/dimension/quality-check",
        icon: CheckCircle,
        stage: "finishing",
        stageOrder: 1,
        titleKo: "퀄리티 디렉터",
        titleEn: "Quality Director",
        descKo: "시각적 일관성 및 동작 자연스러움 검수",
        descEn: "Check visual consistency & motion smoothness",
        portalColor: "border-rose-500/50",
        borderColor: "border-rose-500",
        glowClass: "glow-breathe glow-breathe-rose",
        activeBg: "bg-rose-500",
        activeText: "text-rose-100",
        textColor: "text-rose-400",
        gradient: "from-rose-500 via-pink-500 to-red-500",
    },

    // ========== Extended Tools ==========
    {
        href: "/dimension/aesthetic",
        icon: Palette,
        stage: "extended",
        stageOrder: 1,
        titleKo: "미학디렉터",
        titleEn: "Aesthetic Director",
        descKo: "거장들의 미학을 적용합니다",
        descEn: "Apply masters' aesthetics",
        portalColor: "border-fuchsia-500/50",
        borderColor: "border-fuchsia-500",
        glowClass: "glow-breathe glow-breathe-fuchsia",
        activeBg: "bg-fuchsia-500",
        activeText: "text-fuchsia-100",
        textColor: "text-fuchsia-400",
        gradient: "from-fuchsia-500 via-purple-500 to-pink-500",
    },
];

type StageKey = keyof typeof WORKFLOW_STAGES;

// Route key mapping for chain context
const ROUTE_KEYS: Record<string, string> = {
    "/dimension/abyss": "abyss-mirror",
    "/dimension/reference-decoder": "reference-decoder",
    "/dimension/story-architect": "story-architect",
    "/dimension/sound-crafter": "sound-crafter",
    "/dimension/storyboard": "storyboard-sketch",
    "/dimension/prompt": "prompt-alchemy",
    "/dimension/visual-realizer": "visual-realizer",
    "/dimension/video-maker": "video-maker",
    "/dimension/quality-check": "quality-director",
    "/dimension/aesthetic": "aesthetic-director",
};

export default function WorkshopHubPage() {
    const { language } = useLanguage();
    const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
    const [selectedStage, setSelectedStage] = useState<StageKey | null>(null);
    const [showChainPanel, setShowChainPanel] = useState(false);
    const chainCtx = useDimensionChainOptional();
    useParallaxScroll();

    const filteredItems = selectedStage
        ? DIMENSION_ITEMS.filter(d => d.stage === selectedStage)
        : DIMENSION_ITEMS;

    const stageKeys = Object.keys(WORKFLOW_STAGES) as StageKey[];

    // Chain data summary
    const chainSummary = chainCtx?.getChainSummary() || [];
    const hasChainData = chainSummary.length > 0;

    // Check if a dimension has chain data
    const hasDimensionData = (href: string): boolean => {
        const routeKey = ROUTE_KEYS[href];
        return routeKey ? chainCtx?.hasChainData(routeKey) || false : false;
    };

    return (
        <AppShell showTopBar={false}>
            {/* Aurora Background (Fixed) */}
            <AuroraBackground />

            {/* Mini App Submit Modal */}
            <MiniAppSubmitModal isOpen={isSubmitModalOpen} onClose={() => setIsSubmitModalOpen(false)} />

            {/* Chokki Agent is now global in AppShell */}

            <div className="min-h-screen relative">
                {/* Minimalist Hero Section (Toggle Only) */}
                <section className="relative pt-32 pb-12 flex flex-col items-center justify-center overflow-hidden px-4">

                    {/* 4-Stage Workflow Toggle */}
                    <div className="flex flex-wrap justify-center items-center gap-2 p-2 rounded-2xl backdrop-blur-sm bg-black/5 dark:bg-white/5">
                        <button
                            onClick={() => setSelectedStage(null)}
                            className={`px-5 py-2.5 rounded-xl text-xs font-bold tracking-widest uppercase transition-all duration-300 ${selectedStage === null
                                ? "bg-black dark:bg-white text-white dark:text-black shadow-lg scale-105"
                                : "text-black/40 dark:text-white/40 hover:text-black dark:hover:text-white"
                                }`}
                        >
                            ALL
                        </button>
                        {stageKeys.map((stageKey) => {
                            const stage = WORKFLOW_STAGES[stageKey];
                            const isSelected = selectedStage === stageKey;
                            const stageColors: Record<string, { bg: string; text: string }> = {
                                emerald: { bg: "bg-emerald-500", text: "text-emerald-950" },
                                violet: { bg: "bg-violet-500", text: "text-violet-100" },
                                amber: { bg: "bg-amber-500", text: "text-amber-950" },
                                cyan: { bg: "bg-cyan-500", text: "text-cyan-950" },
                                fuchsia: { bg: "bg-fuchsia-500", text: "text-fuchsia-100" },
                            };
                            const colors = stageColors[stage.color] || stageColors.emerald;

                            return (
                                <button
                                    key={stageKey}
                                    onClick={() => setSelectedStage(isSelected ? null : stageKey)}
                                    className={`px-4 py-2.5 rounded-xl text-xs font-bold tracking-wide transition-all duration-300 flex items-center gap-2 ${isSelected
                                        ? `${colors.bg} ${colors.text} shadow-lg scale-105`
                                        : "text-black/50 dark:text-white/50 hover:text-black dark:hover:text-white bg-black/5 dark:bg-white/5 hover:bg-black/10 dark:hover:bg-white/10"
                                        }`}
                                >
                                    <span className="text-[10px] font-mono opacity-60">{stage.order}</span>
                                    <span>{language === 'ko' ? stage.nameKo : stage.nameEn}</span>
                                </button>
                            );
                        })}
                    </div>

                    {/* Chain Status Bar */}
                    <AnimatePresence>
                        {hasChainData && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="mt-4 w-full max-w-2xl"
                            >
                                <div className="relative p-3 rounded-xl backdrop-blur-md bg-gradient-to-r from-emerald-500/10 via-violet-500/10 to-amber-500/10 border border-white/10">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <Link2 className="w-4 h-4 text-emerald-400" />
                                            <span className="text-sm font-medium text-white/80">
                                                {language === 'ko' ? '워크플로우 진행 중' : 'Workflow in progress'}
                                            </span>
                                            <span className="text-xs text-white/40">
                                                ({chainSummary.length} {language === 'ko' ? '단계 완료' : 'steps done'})
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => setShowChainPanel(!showChainPanel)}
                                                className="text-xs text-white/60 hover:text-white px-2 py-1 rounded-lg hover:bg-white/10 transition-colors"
                                            >
                                                {showChainPanel ? (language === 'ko' ? '숨기기' : 'Hide') : (language === 'ko' ? '상세보기' : 'Details')}
                                            </button>
                                            <button
                                                onClick={() => chainCtx?.clearChain()}
                                                className="p-1 rounded-lg text-white/40 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                                                title={language === 'ko' ? '초기화' : 'Clear'}
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>

                                    {/* Expanded Chain Details */}
                                    <AnimatePresence>
                                        {showChainPanel && (
                                            <motion.div
                                                initial={{ height: 0, opacity: 0 }}
                                                animate={{ height: "auto", opacity: 1 }}
                                                exit={{ height: 0, opacity: 0 }}
                                                className="overflow-hidden"
                                            >
                                                <div className="pt-3 mt-3 border-t border-white/10 space-y-2">
                                                    {chainSummary.map((item, idx) => (
                                                        <div
                                                            key={item.key}
                                                            className="flex items-center gap-2 text-sm"
                                                        >
                                                            <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs font-bold">
                                                                {idx + 1}
                                                            </span>
                                                            <span className="text-white/80 font-medium">{item.name}</span>
                                                            {item.summary && (
                                                                <span className="text-white/40 text-xs truncate max-w-[200px]">
                                                                    - {item.summary}
                                                                </span>
                                                            )}
                                                        </div>
                                                    ))}
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </section>

                {/* Content Section - Cards */}
                <section className="relative z-10 pb-40 px-4 sm:px-6">
                    <div className="mx-auto max-w-7xl">
                        {/* Dimension Portal Grid */}
                        <div className="relative">
                            {/* Background Atmosphere Spot */}
                            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] bg-blue-600/10 blur-[150px] rounded-full pointer-events-none z-0 mix-blend-screen" />

                            <motion.div
                                className={`grid gap-6 relative z-10 ${filteredItems.length === 1 ? "grid-cols-1 max-w-2xl mx-auto" : "sm:grid-cols-2 lg:grid-cols-4"}`}
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
                                                transition={{ duration: 0.3, delay: idx * 0.05 }}
                                                className="group relative"
                                            >
                                                <Link
                                                    href={dimension.href}
                                                    className="block relative overflow-hidden rounded-[2rem] border border-black/5 dark:border-white/5 bg-white/60 dark:bg-black/40 p-6 backdrop-blur-2xl hover:bg-white/80 dark:hover:bg-white/[0.03] transition-all duration-700 hover:-translate-y-2 shadow-lg dark:shadow-none"
                                                >
                                                    {/* NEW Badge */}
                                                    {dimension.isNew && (
                                                        <div className="absolute top-4 right-4 z-20 px-2 py-1 rounded-full bg-lime-500 text-black text-[10px] font-bold tracking-wider animate-pulse">
                                                            NEW
                                                        </div>
                                                    )}

                                                    {/* Chain Data Indicator */}
                                                    {hasDimensionData(dimension.href) && (
                                                        <div className="absolute top-4 left-4 z-20 flex items-center gap-1 px-2 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/30">
                                                            <CheckCircle className="w-3 h-3 text-emerald-400" />
                                                            <span className="text-[10px] text-emerald-400 font-medium">
                                                                {language === 'ko' ? '데이터' : 'Data'}
                                                            </span>
                                                        </div>
                                                    )}

                                                    {/* Colored Border Reveal */}
                                                    <div className={`absolute inset-0 rounded-[2rem] border-2 ${dimension.borderColor} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />

                                                    {/* Gradient Background */}
                                                    <div className={`
                                                        absolute inset-0 opacity-0 group-hover:opacity-20 transition-opacity duration-700
                                                        bg-gradient-to-br ${dimension.gradient || "from-white/10 to-transparent"}
                                                    `} />

                                                    {/* Portal Ring Effect */}
                                                    <div className={`absolute -right-20 -top-20 h-64 w-64 rounded-full border-[1px] ${dimension.portalColor} ${dimension.glowClass} blur-[60px] opacity-20 group-hover:opacity-40 transition-opacity duration-700`} />

                                                    <div className="relative flex items-start justify-between h-full flex-col gap-4 min-h-[140px]">
                                                        <div className="w-full flex items-start justify-between z-10">
                                                            <div className="flex flex-col gap-1">
                                                                {/* Stage Label */}
                                                                <span className={`text-[10px] font-mono tracking-wider ${dimension.textColor} opacity-60`}>
                                                                    {stageInfo.order}.{dimension.stageOrder}
                                                                </span>
                                                                <h2 className="text-lg font-bold text-gray-900 dark:text-white group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-gray-900 group-hover:to-gray-600 dark:group-hover:from-white dark:group-hover:to-white/70 transition-all duration-500">
                                                                    {language === 'ko' ? dimension.titleKo : dimension.titleEn}
                                                                </h2>
                                                            </div>
                                                            <div className={`flex h-10 w-10 items-center justify-center rounded-full bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 backdrop-blur-md transition-all duration-500 group-hover:scale-110 group-hover:bg-black/10 dark:group-hover:bg-white/10`}>
                                                                <Icon className={`h-4 w-4 ${dimension.textColor}`} aria-hidden="true" />
                                                            </div>
                                                        </div>

                                                        <div className="space-y-6 z-10 mt-auto">
                                                            <div className="space-y-2">
                                                                <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed line-clamp-2">
                                                                    {language === 'ko' ? dimension.descKo : dimension.descEn}
                                                                </p>
                                                            </div>
                                                            {/* Arrow Action */}
                                                            <div className="flex justify-end mt-4">
                                                                <div className={`
                                                                    flex items-center justify-center w-8 h-8 rounded-full
                                                                    border border-black/10 dark:border-white/10 bg-black/5 dark:bg-white/5 backdrop-blur-sm
                                                                    text-black/40 dark:text-white/40 group-hover:text-black dark:group-hover:text-white group-hover:bg-black/10 dark:group-hover:bg-white/20
                                                                    transition-all duration-300 group-hover:scale-110
                                                                `}>
                                                                    <ChevronRight className="w-4 h-4" />
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </Link>
                                            </motion.div>
                                        );
                                    })}
                                </AnimatePresence>

                                {/* Propose Button - Minimalist */}
                                <button
                                    onClick={() => setIsSubmitModalOpen(true)}
                                    className="group relative overflow-hidden rounded-[2rem] border border-dashed border-black/10 dark:border-white/10 bg-transparent p-6 hover:bg-black/[0.02] dark:hover:bg-white/[0.02] hover:border-black/30 dark:hover:border-white/30 transition-all duration-500 flex flex-col items-center justify-center gap-4 min-h-[140px]"
                                >
                                    <div className="relative">
                                        <div className="absolute inset-0 bg-lime-400/20 blur-[30px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                        <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 transition-all duration-500 group-hover:scale-110">
                                            <Plus className="h-6 w-6 text-zinc-500 group-hover:text-black dark:group-hover:text-white transition-colors duration-300" />
                                        </div>
                                    </div>

                                    <div className="text-center space-y-2">
                                        <span className="text-xs font-bold tracking-[0.2em] text-zinc-600 uppercase group-hover:text-lime-400 transition-colors">
                                            ∞D INFINITE
                                        </span>
                                        <p className="text-sm text-zinc-500 group-hover:text-zinc-300 transition-colors max-w-[200px]">
                                            {language === "ko" ? "새로운 차원을 제안하세요" : "Propose a new dimension"}
                                        </p>
                                    </div>
                                </button>
                            </motion.div>
                        </div>
                    </div>
                </section>
            </div>
        </AppShell>
    );
}
