"use client";

import Link from "next/link";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, LayoutGrid, Image as ImageIcon, Plus, Eye, Fingerprint, LucideIcon } from "lucide-react";
import { AuroraBackground } from "@/components/AuroraBackground";
import { MiniAppSubmitModal } from "@/components/MiniAppSubmitModal";
import { useParallaxScroll, useSmoothScroll } from "@/hooks/useLusionAnimations";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";

interface DimensionItemData {
    href: string;
    icon: LucideIcon;
    dimensionLabel: string;
    sensoryName: string;
    titleKo: string;
    titleEn: string;
    descKo: string;
    descEn: string;
    essenceKo: string;
    essenceEn: string;
    portalColor: string;
    borderColor: string;
    glowClass: string;
    activeBg: string;
    activeText: string;
    textColor: string;
}

// Lusion Style Sensory Dimensions
// 1D Origin (Violet)
// 2D Blueprint (Cyan)
// 3D Ambience (Emerald)
// 4D Moment (Amber)
// 5D Soul (Electric Lime)

const DIMENSION_ITEMS: DimensionItemData[] = [
    {
        href: "/dimension/prompt",
        icon: Sparkles,
        dimensionLabel: "1D",
        sensoryName: "ORIGIN",
        titleKo: "프롬프트 생성기",
        titleEn: "Prompt Generator",
        descKo: "무형의 생각이 언어라는 첫 번째 형태로 응축됩니다.",
        descEn: "Intangible thoughts condense into the first form of language.",
        essenceKo: "본질의 시작",
        essenceEn: "The Seed of Thought",
        portalColor: "border-violet-500/50",
        borderColor: "border-violet-500",
        glowClass: "glow-breathe glow-breathe-violet",
        activeBg: "bg-violet-500",
        activeText: "text-violet-100",
        textColor: "text-violet-400",
    },
    {
        href: "/dimension/storyboard",
        icon: LayoutGrid,
        dimensionLabel: "2D",
        sensoryName: "BLUEPRINT",
        titleKo: "스토리보드 아키텍트",
        titleEn: "Storyboard Architect",
        descKo: "흐릿한 맥락들이 구조화된 계획으로 설계됩니다.",
        descEn: "Vague contexts are designed into structured plans.",
        essenceKo: "구조와 맥락",
        essenceEn: "Context & Structure",
        portalColor: "border-cyan-500/50",
        borderColor: "border-cyan-500",
        glowClass: "glow-breathe glow-breathe-cyan",
        activeBg: "bg-cyan-500",
        activeText: "text-cyan-950",
        textColor: "text-cyan-400",
    },
    {
        href: "/dimension/image-tool",
        icon: ImageIcon,
        dimensionLabel: "3D",
        sensoryName: "AMBIENCE",
        titleKo: "비주얼 스튜디오",
        titleEn: "Visual Studio",
        descKo: "빛과 그림자, 깊이가 더해져 공간이 살아납니다.",
        descEn: "Light, shadow, and depth breathe life into space.",
        essenceKo: "깊이와 실재",
        essenceEn: "Depth & Reality",
        portalColor: "border-emerald-500/50",
        borderColor: "border-emerald-500",
        glowClass: "glow-breathe glow-breathe-emerald",
        activeBg: "bg-emerald-500",
        activeText: "text-emerald-950",
        textColor: "text-emerald-400",
    },
    {
        href: "/dimension/shot-catch",
        icon: Eye,
        dimensionLabel: "4D",
        sensoryName: "MOMENT",
        titleKo: "프레임 캐쳐",
        titleEn: "Frame Catcher",
        descKo: "흐르는 시간 속에서 결정적인 순간을 포착합니다.",
        descEn: "Capturing the decisive moment within the flow of time.",
        essenceKo: "흐름과 타이밍",
        essenceEn: "Flow & Timing",
        portalColor: "border-amber-500/50",
        borderColor: "border-amber-500",
        glowClass: "glow-breathe glow-breathe-amber",
        activeBg: "bg-amber-500",
        activeText: "text-amber-950",
        textColor: "text-amber-400",
    },
    {
        href: "/dimension/soul",
        icon: Fingerprint,
        dimensionLabel: "5D",
        sensoryName: "SOUL",
        titleKo: "장인의 아틀리에",
        titleEn: "Artisan's Atelier",
        descKo: "사주팔자처럼 고유한 운명과 정신을 불어넣습니다.",
        descEn: "Infusing unique destiny and spirit, like a master's touch.",
        essenceKo: "숨결과 초월",
        essenceEn: "Breath & Transcendence",
        portalColor: "border-lime-400/50",
        borderColor: "border-lime-400",
        glowClass: "glow-breathe glow-breathe-lime",
        activeBg: "bg-lime-400",
        activeText: "text-lime-950",
        textColor: "text-lime-400",
    },
];

export default function WorkshopHubPage() {
    const { language } = useLanguage();
    const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
    const [selectedDimension, setSelectedDimension] = useState<string | null>(null);
    useSmoothScroll();
    useParallaxScroll();

    const filteredItems = selectedDimension
        ? DIMENSION_ITEMS.filter(d => d.dimensionLabel === selectedDimension)
        : DIMENSION_ITEMS;

    return (
        <AppShell>
            {/* Aurora Background (Fixed) */}
            <AuroraBackground />

            {/* Mini App Submit Modal */}
            <MiniAppSubmitModal isOpen={isSubmitModalOpen} onClose={() => setIsSubmitModalOpen(false)} />

            {/* Chokki Agent is now global in AppShell */}

            <div className="min-h-screen relative">
                {/* Minimalist Hero Section (Toggle Only) */}
                <section className="relative pt-32 pb-12 flex flex-col items-center justify-center overflow-hidden px-4">

                    {/* Color-Coded Dimension Toggle */}
                    <div className="flex flex-wrap justify-center items-center gap-3 p-2 rounded-full backdrop-blur-sm">
                        <button
                            onClick={() => setSelectedDimension(null)}
                            className={`px-6 py-3 rounded-full text-xs font-bold tracking-widest uppercase transition-all duration-300 ${selectedDimension === null
                                ? "bg-white text-black shadow-lg scale-105"
                                : "text-white/40 hover:text-white"
                                }`}
                        >
                            ALL
                        </button>
                        {DIMENSION_ITEMS.map((dim) => (
                            <button
                                key={dim.dimensionLabel}
                                onClick={() => setSelectedDimension(
                                    selectedDimension === dim.dimensionLabel ? null : dim.dimensionLabel
                                )}
                                className={`px-6 py-3 rounded-full text-xs font-bold tracking-widest transition-all duration-300 flex items-center justify-center ${selectedDimension === dim.dimensionLabel
                                    ? `${dim.activeBg} ${dim.activeText} shadow-lg scale-105`
                                    : "text-white/40 hover:text-white bg-white/5 hover:bg-white/10"
                                    }`}
                            >
                                <span>{dim.dimensionLabel}</span>
                            </button>
                        ))}
                    </div>
                </section>

                {/* Content Section - Cards */}
                <section className="relative z-10 pb-40 px-4 sm:px-6">
                    <div className="mx-auto max-w-7xl">
                        {/* Dimension Portal Grid */}
                        <div className="relative">
                            {/* Background Atmosphere Spot */}
                            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] bg-blue-600/10 blur-[150px] rounded-full pointer-events-none z-0 mix-blend-screen" />

                            <motion.div
                                className={`grid gap-8 relative z-10 ${filteredItems.length === 1 ? "grid-cols-1 max-w-2xl mx-auto" : "sm:grid-cols-2 lg:grid-cols-3"}`}
                                layout
                            >
                                <AnimatePresence mode="popLayout">
                                    {filteredItems.map((dimension) => {
                                        const Icon = dimension.icon;
                                        return (
                                            <motion.div
                                                key={dimension.dimensionLabel}
                                                layout
                                                initial={{ opacity: 0, scale: 0.9 }}
                                                animate={{ opacity: 1, scale: 1 }}
                                                exit={{ opacity: 0, scale: 0.9 }}
                                                transition={{ duration: 0.3 }}
                                                className="group relative"
                                            >
                                                <Link
                                                    href={dimension.href}
                                                    className="block relative overflow-hidden rounded-[2rem] border border-white/5 bg-black/40 p-6 backdrop-blur-2xl hover:bg-white/[0.03] transition-all duration-700 hover:-translate-y-2"
                                                >
                                                    {/* Colored Border Reveal */}
                                                    <div className={`absolute inset-0 rounded-[2rem] border-2 ${dimension.borderColor} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />

                                                    {/* Portal Ring Effect */}
                                                    <div className={`absolute -right-20 -top-20 h-64 w-64 rounded-full border-[1px] ${dimension.portalColor} ${dimension.glowClass} blur-[60px] opacity-20 group-hover:opacity-40 transition-opacity duration-700`} />

                                                    <div className="relative flex items-start justify-between h-full flex-col gap-4 min-h-[180px]">
                                                        <div className="w-full flex items-start justify-between z-10">
                                                            <div className="flex flex-col gap-1">
                                                                <h2 className="text-xl font-bold text-white group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-white/70 transition-all duration-500">
                                                                    {language === 'ko' ? dimension.titleKo : dimension.titleEn}
                                                                </h2>
                                                            </div>
                                                            <div className={`flex h-10 w-10 items-center justify-center rounded-full bg-white/5 border border-white/10 backdrop-blur-md transition-all duration-500 group-hover:scale-110 group-hover:bg-white/10`}>
                                                                <Icon className={`h-4 w-4 ${dimension.textColor}`} aria-hidden="true" />
                                                            </div>
                                                        </div>

                                                        <div className="space-y-6 z-10 mt-auto">
                                                            <div className="space-y-2">
                                                                <p className={`text-xs font-medium uppercase tracking-widest ${dimension.textColor} transition-colors`}>
                                                                    {language === 'ko' ? dimension.essenceKo : dimension.essenceEn}
                                                                </p>
                                                                <p className="text-sm text-[var(--fg-muted)] leading-relaxed line-clamp-2 mix-blend-plus-lighter">
                                                                    {language === 'ko' ? dimension.descKo : dimension.descEn}
                                                                </p>
                                                            </div>
                                                            <div>
                                                                <div className="inline-flex items-center gap-3 px-5 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur-sm group-hover:bg-white group-hover:text-black transition-all duration-300">
                                                                    <span className="text-[10px] font-bold tracking-[0.15em] uppercase">
                                                                        {language === 'ko' ? '차원 진입' : 'EXPLORE'}
                                                                    </span>
                                                                    <div className={`h-1.5 w-1.5 rounded-full ${dimension.activeBg} opacity-80`} />
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
                                    className="group relative overflow-hidden rounded-[2rem] border border-dashed border-white/10 bg-transparent p-6 hover:bg-white/[0.02] hover:border-white/30 transition-all duration-500 flex flex-col items-center justify-center gap-4 min-h-[180px]"
                                >
                                    <div className="relative">
                                        <div className="absolute inset-0 bg-lime-400/20 blur-[30px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                        <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-white/5 border border-white/10 transition-all duration-500 group-hover:scale-110">
                                            <Plus className="h-6 w-6 text-zinc-500 group-hover:text-white transition-colors duration-300" />
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
