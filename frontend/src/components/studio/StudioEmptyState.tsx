"use client";

/**
 * StudioEmptyState - Chat-first onboarding for Opal-style Studio
 * 
 * Redesigned with premium aesthetics:
 * - Dynamic Aurora Background
 * - Glassmorphism Cards
 * - Enhanced Typography & Micro-interactions
 */

import { motion } from "framer-motion";
import {
    Sparkles,
    Video,
    FileText,
    MessageSquare,
    Wand2,
    TrendingUp,
    Film,
    ArrowRight,
    Search,
    Zap,
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { useState } from "react";

// Explicit color classes to prevent Tailwind purging
const COLOR_CLASSES = {
    sky: {
        border: "border-sky-500/30",
        bg: "from-sky-500/20 to-sky-600/5",
        iconBorder: "border-sky-500/20",
        text: "text-sky-400",
        textHover: "group-hover:text-sky-300",
        gradient: "from-sky-500",
    },
    emerald: {
        border: "border-emerald-500/30",
        bg: "from-emerald-500/20 to-emerald-600/5",
        iconBorder: "border-emerald-500/20",
        text: "text-emerald-400",
        textHover: "group-hover:text-emerald-300",
        gradient: "from-emerald-500",
    },
    rose: {
        border: "border-rose-500/30",
        bg: "from-rose-500/20 to-rose-600/5",
        iconBorder: "border-rose-500/20",
        text: "text-rose-400",
        textHover: "group-hover:text-rose-300",
        gradient: "from-rose-500",
    },
    amber: {
        border: "border-amber-500/30",
        bg: "from-amber-500/20 to-amber-600/5",
        iconBorder: "border-amber-500/20",
        text: "text-amber-400",
        textHover: "group-hover:text-amber-300",
        gradient: "from-amber-500",
    },
} as const;

type ColorKey = keyof typeof COLOR_CLASSES;

interface PromptSuggestion {
    id: string;
    label: string;
    description: string;
    prompt: string;
    icon: React.ElementType;
    color: ColorKey;
}

interface StudioEmptyStateProps {
    onSendPrompt: (prompt: string) => void;
}

export default function StudioEmptyState({ onSendPrompt }: StudioEmptyStateProps) {
    const { t, language } = useLanguage();
    const [hoveredId, setHoveredId] = useState<string | null>(null);

    const suggestions: PromptSuggestion[] = language === "ko" ? [
        {
            id: "auteur-bong",
            label: "봉준호 스타일 시네마틱",
            description: "수직적 계층 구도와 블랙 코미디 톤의 30초 영상",
            prompt: "봉준호 감독 스타일로 30초 브랜드 영상 워크플로우를 만들어줘. 수직적 계층 구도와 블랙 코미디 톤으로.",
            icon: Film,
            color: "sky",
        },
        {
            id: "youtube-repurpose",
            label: "YouTube 쇼츠 리퍼포징",
            description: "롱폼 영상을 3개의 바이럴 쇼츠로 자동 변환",
            prompt: "긴 YouTube 영상을 3개의 숏폼 클립으로 변환하는 워크플로우 만들어줘. 각각 후크-본문-CTA 구조로.",
            icon: Video,
            color: "emerald",
        },
        {
            id: "trending-content",
            label: "트렌드 인사이트 분석",
            description: "실시간 틱톡 트렌드 기반 콘텐츠 아이디어 도출",
            prompt: "최근 바이럴 틱톡 트렌드를 분석해서 우리 브랜드에 맞는 콘텐츠 아이디어 3개 제안해줘.",
            icon: TrendingUp,
            color: "rose",
        },
        {
            id: "document-video",
            label: "문서 to 스토리보드",
            description: "기획안 문서를 영상 스토리보드로 시각화",
            prompt: "마케팅 기획 문서를 영상 스토리보드로 변환하는 워크플로우 만들어줘.",
            icon: FileText,
            color: "amber",
        },
    ] : [
        {
            id: "auteur-bong",
            label: "Cinematic Branding",
            description: "30s brand video in Bong Joon-ho's signature style",
            prompt: "Create a 30-second brand video workflow in Bong Joon-ho's style with vertical hierarchy composition and dark comedy tone.",
            icon: Film,
            color: "sky",
        },
        {
            id: "youtube-repurpose",
            label: "Shorts Repurposing",
            description: "Convert long-form into 3 viral short clips",
            prompt: "Create a workflow to convert a long YouTube video into 3 short-form clips, each with hook-body-CTA structure.",
            icon: Video,
            color: "emerald",
        },
        {
            id: "trending-content",
            label: "Trend Insights",
            description: "Generate ideas based on real-time TikTok trends",
            prompt: "Analyze recent viral TikTok trends and suggest 3 content ideas that fit our brand.",
            icon: TrendingUp,
            color: "rose",
        },
        {
            id: "document-video",
            label: "Doc to Storyboard",
            description: "Visualize marketing docs as video storyboards",
            prompt: "Create a workflow to convert a marketing document into a video storyboard.",
            icon: FileText,
            color: "amber",
        },
    ];

    const handleSuggestionClick = (suggestion: PromptSuggestion) => {
        onSendPrompt(suggestion.prompt);
    };

    return (
        <div className="absolute inset-0 z-20 flex flex-col items-center justify-center overflow-hidden pt-16" style={{ background: 'linear-gradient(135deg, #0c0c1d 0%, #0a0a14 50%, #0c0c1d 100%)' }}>
            {/* Subtle Aurora Background - More refined, less intense */}
            <div className="absolute inset-0 pointer-events-none">
                {/* Primary glow - top left, cyan */}
                <div className="absolute top-[-10%] left-[-5%] w-[45%] h-[45%] bg-cyan-500/[0.07] rounded-full blur-[100px] animate-pulse-slow" />
                {/* Secondary glow - bottom right, violet */}
                <div className="absolute bottom-[0%] right-[-5%] w-[40%] h-[40%] bg-violet-500/[0.05] rounded-full blur-[100px] animate-pulse-slow" style={{ animationDelay: '2s' }} />
                {/* Accent glow - center, warm */}
                <div className="absolute top-[50%] left-[50%] -translate-x-1/2 -translate-y-1/2 w-[30%] h-[30%] bg-amber-500/[0.03] rounded-full blur-[80px]" />

                {/* Grid texture overlay */}
                <div
                    className="absolute inset-0 opacity-[0.015]"
                    style={{
                        backgroundImage: 'url(/grid.svg)',
                        backgroundSize: '40px 40px',
                        maskImage: 'radial-gradient(ellipse at center, white 0%, transparent 70%)',
                        WebkitMaskImage: 'radial-gradient(ellipse at center, white 0%, transparent 70%)'
                    }}
                />
            </div>

            {/* 2. Main Content Container */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="relative z-10 w-full max-w-4xl px-8 flex flex-col items-center pointer-events-auto"
            >
                {/* Header Section */}
                <div className="text-center mb-12">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.2 }}
                        className="inline-flex items-center gap-2 rounded-full border border-white/5 bg-white/5 px-3 py-1.5 backdrop-blur-md mb-6 hover:bg-white/10 transition-colors cursor-default"
                    >
                        <Wand2 className="h-3.5 w-3.5 text-sky-400" />
                        <span className="text-xs font-medium text-slate-300 tracking-wide">
                            AI WORKFLOW GENERATOR
                        </span>
                    </motion.div>

                    <motion.h1
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight"
                    >
                        {language === "ko" ? (
                            <>
                                무엇을 <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-blue-500">제작</span>하시겠습니까?
                            </>
                        ) : (
                            <>
                                What would you like to <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-blue-500">create</span>?
                            </>
                        )}
                    </motion.h1>

                    <motion.p
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                        className="text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed"
                    >
                        {language === "ko"
                            ? "아이디어만 말씀해 주세요. AI가 기획부터 실행까지, 완벽한 워크플로우를 설계해 드립니다."
                            : "Just describe your idea. AI will design a complete workflow from planning to execution."}
                    </motion.p>
                </div>

                {/* 3. Suggestion Cards Grid */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                    className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full"
                >
                    {suggestions.map((suggestion, index) => {
                        const isHovered = hoveredId === suggestion.id;
                        const colors = COLOR_CLASSES[suggestion.color];

                        return (
                            <motion.button
                                key={suggestion.id}
                                layoutId={suggestion.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.5 + index * 0.1 }}
                                onMouseEnter={() => setHoveredId(suggestion.id)}
                                onMouseLeave={() => setHoveredId(null)}
                                onClick={() => handleSuggestionClick(suggestion)}
                                className={`group relative flex items-start gap-5 rounded-2xl border p-6 text-left transition-all duration-300 bg-white/[0.03] hover:bg-white/[0.06] backdrop-blur-lg ${isHovered
                                    ? `${colors.border} shadow-2xl`
                                    : "border-white/[0.06] hover:border-white/10"
                                    }`}
                            >
                                {/* Icon Container */}
                                <div className={`relative flex h-14 w-14 shrink-0 items-center justify-center rounded-xl transition-all duration-300 group-hover:scale-105 bg-gradient-to-br ${colors.bg} border ${colors.iconBorder}`}>
                                    <suggestion.icon className={`h-7 w-7 transition-colors duration-300 ${colors.text} ${colors.textHover}`} />
                                </div>

                                {/* Text Content */}
                                <div className="flex-1 min-w-0">
                                    <h3 className="font-semibold text-[17px] text-slate-100 group-hover:text-white transition-colors mb-2 flex items-center gap-2">
                                        {suggestion.label}
                                        <ArrowRight className={`h-4 w-4 opacity-0 -translate-x-2 transition-all duration-300 group-hover:opacity-100 group-hover:translate-x-0 ${colors.text}`} />
                                    </h3>
                                    <p className="text-sm text-slate-400 group-hover:text-slate-300 transition-colors leading-relaxed">
                                        {suggestion.description}
                                    </p>
                                </div>

                                {/* Decorative Gradient Blob on Hover */}
                                <div className={`absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-[0.06] transition-opacity duration-500 pointer-events-none bg-gradient-to-br ${colors.gradient} to-transparent`} />
                            </motion.button>
                        );
                    })}
                </motion.div>

                {/* 4. Footer Hint */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1 }}
                    className="mt-12 flex items-center justify-center gap-3 text-sm text-slate-500 bg-black/20 px-4 py-2 rounded-full border border-white/5 backdrop-blur-sm"
                >
                    <div className="flex -space-x-1">
                        <div className="w-2 h-2 rounded-full bg-sky-500 animate-pulse" />
                        <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse delay-150" />
                        <div className="w-2 h-2 rounded-full bg-violet-500 animate-pulse delay-300" />
                    </div>
                    <span>
                        {language === "ko"
                            ? "AI Director가 대기 중입니다. 채팅으로 언제든 말을 걸어주세요."
                            : "AI Director is standing by. Start chatting anytime."}
                    </span>
                </motion.div>
            </motion.div>
        </div>
    );
}
