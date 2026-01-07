"use client";

/**
 * AI Video Workflow Master Course Page
 * 
 * Refactored based on the new curriculum design.
 * @see ai_video_course_design.md
 */

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
    ArrowRight,
    Brain,
    Sparkles,
    Zap,
    Film,
    Layers,
    Music,
    Image as ImageIcon,
    Video,
    CheckCircle,
    Search,
    ChevronDown,
    Users,
    Eye,
    Clock,
    type LucideIcon
} from "lucide-react";
import AppShell from "@/components/AppShell";
import ApplicationModal from "@/components/ApplicationModal";
import { AuroraBackground } from "@/components/AuroraBackground";
import { CrebitGuideBadge } from "@/components/CrebitGuideBadge";
import { useParallaxScroll } from "@/hooks/useLusionAnimations";
import { trackEvent, EVENTS } from "@/lib/analytics";

// Local components
import {
    SectionHeader,
    StatItem,
    CurriculumBox,
} from "./_components";

// ============================================================================
// Types & Constants
// ============================================================================

interface TimeLeft {
    days: number;
    hours: number;
    minutes: number;
    seconds: number;
}

interface WorkflowStep {
    icon: LucideIcon;
    title: string;
    desc: string;
}

interface WorkflowStage {
    number: string;
    title: string;
    subtitle: string;
    color: "emerald" | "violet" | "amber" | "cyan";
    steps: WorkflowStep[];
    tip?: string;
}

const DEADLINE = new Date("2026-02-01T23:59:59").getTime();

const WORKFLOW_STAGES: WorkflowStage[] = [
    {
        number: "01",
        title: "기획",
        subtitle: "아이디어를 구체화하는 첫걸음",
        color: "emerald",
        steps: [
            { icon: Brain, title: "심연의 거울", desc: "나만의 취향과 창작 DNA 분석 (Gemini, NotebookLM)" },
            { icon: Search, title: "레퍼런스 해석기", desc: "조명, 색감, 연출의 전문가적 분석" },
            { icon: Layers, title: "시나리오 생성기", desc: "DNA와 스타일을 결합한 시나리오 작성" },
        ],
    },
    {
        number: "02",
        title: "사전 제작",
        subtitle: "시나리오를 시청각 설계도로 변환",
        color: "violet",
        steps: [
            { icon: Music, title: "사운드 크래프터", desc: "BGM 및 성우 내레이션 생성 (Suno, Udio)" },
            { icon: ImageIcon, title: "스토리보드 스케치", desc: "글을 시각적 컷으로 스케치" },
            { icon: Sparkles, title: "프롬프트 연금술", desc: "AI가 이해하는 전문 언어로 번역" },
        ],
    },
    {
        number: "03",
        title: "제작",
        subtitle: "상상을 현실로 구현",
        color: "amber",
        steps: [
            { icon: ImageIcon, title: "비주얼 리얼라이저", desc: "Key Frame 고품질 생성 (Midjourney)" },
            { icon: Video, title: "비디오 메이커", desc: "영상 변환 및 모션 제어 (Veo 3.1, Kling)" },
        ],
    },
    {
        number: "04",
        title: "완성",
        subtitle: "프로페셔널 퀄리티로 마무리",
        color: "cyan",
        steps: [
            { icon: CheckCircle, title: "퀄리티 디렉터", desc: "시각적 일관성 및 동작 자연스러움 검수" },
        ],
        tip: "AI가 90%를 완성하고, 당신은 미학적 판단 10%에 집중합니다.",
    },
];

const BEFORE_ITEMS = [
    '"AI로 영상 만들 수 있다던데..."',
    "유튜브 보면서 무작정 따라하기",
    "남의 프롬프트 복붙하기",
    '"이거 어떻게 만들었어요?" 질문하기',
];

const AFTER_ITEMS = [
    { text: '"내 영상 스타일은 이거야"', bold: true },
    { text: "내 미학에 맞는 레퍼런스 직접 분석", bold: false },
    { text: "프롬프트의 원리와 작동 방식 이해", bold: false },
    { text: "다른 사람들이 질문하는 Creator", bold: true },
];

const CURRICULUM_DATA = [
    {
        section: "01",
        title: "Week 1: 워크플로우 전체 체험",
        items: [
            "오리엔테이션 & 워크플로우 소개",
            "나만의 창작 DNA 찾기 (심연의 거울)",
            "과제: 30초 감성 영상 완성",
            "목표: 전체 흐름 빠르게 이해하기",
        ],
    },
    {
        section: "02",
        title: "Week 2: 광고처럼 임팩트 있게",
        items: [
            "프롬프트 연금술 마스터 & 스타일 프리셋",
            "비주얼 & 비디오 심화 (카메라 워크 제어)",
            "과제: 30초 프로덕션급 광고 만들기",
            "목표: 레퍼런스 분석 및 미학적 선택 훈련",
        ],
    },
    {
        section: "03",
        title: "Week 3: 이야기가 있는 영상",
        items: [
            "시나리오 & 스토리보드 심화 (장면 전환)",
            "사운드 & 편집 리듬 (Suno AI, 믹싱)",
            "과제: 3분 뮤직비디오 OR 숏드라마",
            "목표: 내러티브와 호흡 조절",
        ],
    },
    {
        section: "04",
        title: "Week 4: 나만의 작품 (Capstone)",
        items: [
            "개인 프로젝트 심화 작업 (1:1 피드백)",
            "최종 발표 & 시사회 (크리틱)",
            "결과물: 3분 자유 주제 영상 (Final Portfolio)",
            "목표: 독립적인 AI 영상 크리에이터로 데뷔",
        ],
    },
];

// Coloso-style social proof & pricing
const SOCIAL_PROOF = {
    totalStudents: 127,
    recentViews: 23,
    price: {
        original: 890000,
        discounted: 490000,
        discountPercent: 45,
    },
    badges: ["입문~중급", "4주 완성", "한국어"],
};

// Color mappings for workflow stages
const COLOR_CLASSES = {
    emerald: {
        text: "text-emerald-500",
        border: "hover:border-emerald-500/50",
        bar: "bg-emerald-500",
        iconText: "text-emerald-400",
        tipBg: "bg-emerald-900/20",
        tipBorder: "border-emerald-500/20",
        tipText: "text-emerald-300",
    },
    violet: {
        text: "text-violet-500",
        border: "hover:border-violet-500/50",
        bar: "bg-violet-500",
        iconText: "text-violet-400",
        tipBg: "bg-violet-900/20",
        tipBorder: "border-violet-500/20",
        tipText: "text-violet-300",
    },
    amber: {
        text: "text-amber-500",
        border: "hover:border-amber-500/50",
        bar: "bg-amber-500",
        iconText: "text-amber-400",
        tipBg: "bg-amber-900/20",
        tipBorder: "border-amber-500/20",
        tipText: "text-amber-300",
    },
    cyan: {
        text: "text-cyan-500",
        border: "hover:border-cyan-500/50",
        bar: "bg-cyan-500",
        iconText: "text-cyan-400",
        tipBg: "bg-cyan-900/20",
        tipBorder: "border-cyan-500/20",
        tipText: "text-cyan-300",
    },
} as const;

// ============================================================================
// Custom Hooks
// ============================================================================

function useCountdown(deadline: number): TimeLeft {
    const [timeLeft, setTimeLeft] = useState<TimeLeft>({ days: 0, hours: 0, minutes: 0, seconds: 0 });

    useEffect(() => {
        const calculateTimeLeft = () => {
            const now = Date.now();
            const distance = deadline - now;

            if (distance < 0) {
                return { days: 0, hours: 0, minutes: 0, seconds: 0 };
            }

            return {
                days: Math.floor(distance / (1000 * 60 * 60 * 24)),
                hours: Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
                minutes: Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60)),
                seconds: Math.floor((distance % (1000 * 60)) / 1000),
            };
        };

        setTimeLeft(calculateTimeLeft());

        const interval = setInterval(() => {
            const newTimeLeft = calculateTimeLeft();
            setTimeLeft(newTimeLeft);

            if (newTimeLeft.days === 0 && newTimeLeft.hours === 0 &&
                newTimeLeft.minutes === 0 && newTimeLeft.seconds === 0) {
                clearInterval(interval);
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [deadline]);

    return timeLeft;
}

// ============================================================================
// Sub-Components
// ============================================================================

interface WorkflowItemProps {
    Icon: LucideIcon;
    title: string;
    desc: string;
    colorClass?: string;
}

function WorkflowItem({ Icon, title, desc, colorClass = "text-slate-300" }: WorkflowItemProps) {
    return (
        <div className="flex items-start gap-4 group/item">
            <div className={`p-2.5 rounded-xl bg-white/5 border border-white/5 
                           group-hover/item:bg-white/10 group-hover/item:border-white/10 
                           transition-all duration-300 ${colorClass}`}>
                <Icon size={18} aria-hidden="true" />
            </div>
            <div className="flex-1 min-w-0">
                <h4 className="text-white font-semibold text-[15px] mb-1 
                              group-hover/item:text-emerald-50 transition-colors">
                    {title}
                </h4>
                <p className="text-slate-400 text-xs leading-relaxed 
                             group-hover/item:text-slate-300 transition-colors">
                    {desc}
                </p>
            </div>
        </div>
    );
}

interface WorkflowCardProps {
    stage: WorkflowStage;
}

function WorkflowCard({ stage }: WorkflowCardProps) {
    const colors = COLOR_CLASSES[stage.color];

    return (
        <article
            className={`group relative p-8 rounded-3xl bg-white/[0.02] backdrop-blur-sm
                       border border-white/10 ${colors.border} 
                       transition-all duration-500 hover:bg-white/[0.04]`}
            role="article"
            aria-labelledby={`stage-${stage.number}-title`}
        >
            {/* Animated top bar */}
            <div
                className={`absolute top-0 left-0 w-full h-1 rounded-t-3xl ${colors.bar} 
                           transform origin-left scale-x-0 group-hover:scale-x-100 
                           transition-transform duration-500`}
                aria-hidden="true"
            />

            {/* Stage header */}
            <header className="mb-8">
                <h3
                    id={`stage-${stage.number}-title`}
                    className="text-2xl font-black text-white mb-2 flex items-center gap-3"
                >
                    <span className={`${colors.text} text-lg font-mono tabular-nums`}>
                        {stage.number}
                    </span>
                    {stage.title}
                </h3>
                <p className="text-slate-400 text-sm">{stage.subtitle}</p>
            </header>

            {/* Workflow steps */}
            <div className="space-y-5">
                {stage.steps.map((step, idx) => (
                    <WorkflowItem
                        key={idx}
                        Icon={step.icon}
                        title={step.title}
                        desc={step.desc}
                        colorClass={colors.iconText}
                    />
                ))}
            </div>

            {/* Optional tip */}
            {stage.tip && (
                <aside
                    className={`mt-6 p-4 rounded-xl ${colors.tipBg} border ${colors.tipBorder}`}
                    role="note"
                >
                    <p className={`${colors.tipText} text-xs font-bold mb-1 uppercase tracking-wider`}>
                        Pro Tip
                    </p>
                    <p className="text-slate-300 text-xs leading-relaxed">
                        {stage.tip}
                    </p>
                </aside>
            )}
        </article>
    );
}

interface CountdownDisplayProps {
    timeLeft: TimeLeft;
}

const CountdownDisplay = React.memo(function CountdownDisplay({ timeLeft }: CountdownDisplayProps) {
    const formatNumber = (n: number) => String(n).padStart(2, "0");

    return (
        <div
            className="font-mono text-xl text-white font-bold tracking-widest"
            role="timer"
            aria-label="마감까지 남은 시간"
        >
            <span className="tabular-nums">{formatNumber(timeLeft.days)}</span>
            <span className="text-slate-500">일 </span>
            <span className="tabular-nums">{formatNumber(timeLeft.hours)}</span>
            <span className="text-slate-500">시간 </span>
            <span className="tabular-nums">{formatNumber(timeLeft.minutes)}</span>
            <span className="text-slate-500">분 </span>
            <span className="tabular-nums">{formatNumber(timeLeft.seconds)}</span>
            <span className="text-slate-500">초</span>
        </div>
    );
});

/**
 * Coloso-style Social Proof Banner
 * Shows student count and recent interest
 */
function SocialProofBanner() {
    return (
        <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6">
            {/* Total Students */}
            <div className="flex items-center gap-2 px-4 py-2 rounded-full
                           bg-amber-500/10 border border-amber-500/20">
                <Users className="w-4 h-4 text-amber-400" />
                <span className="text-sm text-amber-300 font-medium">
                    <span className="font-bold text-amber-400">{SOCIAL_PROOF.totalStudents}명</span> 수강 중
                </span>
            </div>

            {/* Recent Views - Pulsing with CSS animation (GPU friendly) */}
            <div
                className="flex items-center gap-2 px-4 py-2 rounded-full
                           bg-emerald-500/10 border border-emerald-500/20 animate-pulse"
            >
                <Eye className="w-4 h-4 text-emerald-400" />
                <span className="text-sm text-emerald-300 font-medium">
                    최근 <span className="font-bold text-emerald-400">{SOCIAL_PROOF.recentViews}명</span>이 관심
                </span>
            </div>

            {/* Pill Badges */}
            {SOCIAL_PROOF.badges.map((badge, idx) => (
                <span
                    key={idx}
                    className="px-3 py-1.5 rounded-full text-xs font-medium
                              bg-white/5 border border-white/10 text-slate-300"
                >
                    {badge}
                </span>
            ))}
        </div>
    );
}

/**
 * Coloso-style Accordion Curriculum Item
 */
interface AccordionCurriculumProps {
    section: string;
    title: string;
    items: string[];
    isOpen: boolean;
    onToggle: () => void;
}

function AccordionCurriculum({ section, title, items, isOpen, onToggle }: AccordionCurriculumProps) {
    return (
        <div
            className={`rounded-2xl border transition-all duration-300 overflow-hidden
                       ${isOpen
                    ? 'bg-white/[0.04] border-emerald-500/30'
                    : 'bg-white/[0.02] border-white/10 hover:border-white/20'}`}
        >
            <button
                onClick={onToggle}
                className="w-full px-6 py-5 flex items-center justify-between gap-4
                          text-left group"
                aria-expanded={isOpen}
            >
                <div className="flex items-center gap-4">
                    <span className="text-emerald-500 font-mono text-sm font-bold
                                   tabular-nums min-w-[2rem]">
                        {section}
                    </span>
                    <span className="text-white font-semibold text-base sm:text-lg">
                        {title}
                    </span>
                </div>
                <motion.div
                    animate={{ rotate: isOpen ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                    className="text-slate-400 group-hover:text-white transition-colors"
                >
                    <ChevronDown className="w-5 h-5" />
                </motion.div>
            </button>

            <AnimatePresence initial={false}>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                    >
                        <div className="px-6 pb-5 pt-2 border-t border-white/5">
                            <ul className="space-y-3">
                                {items.map((item, idx) => (
                                    <li
                                        key={idx}
                                        className="flex gap-3 text-slate-300 text-sm"
                                    >
                                        <span className="text-emerald-500 flex-shrink-0">•</span>
                                        <span>{item}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

/**
 * Price Display with Discount (Coloso style)
 */
function PriceDisplay() {
    const { original, discounted, discountPercent } = SOCIAL_PROOF.price;
    const formatPrice = (n: number) => n.toLocaleString();

    return (
        <div className="flex items-center gap-3">
            {/* Discount Badge */}
            <span className="px-2 py-1 rounded-md bg-amber-500 text-black
                           text-xs font-bold">
                {discountPercent}% OFF
            </span>

            {/* Prices */}
            <div className="flex items-baseline gap-2">
                <span className="text-slate-500 line-through text-sm">
                    ₩{formatPrice(original)}
                </span>
                <span className="text-white font-bold text-xl">
                    ₩{formatPrice(discounted)}
                </span>
            </div>
        </div>
    );
}

// ============================================================================
// Main Component
// ============================================================================

export default function AIVideoWorkflowMasterPage() {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [openSection, setOpenSection] = useState<string | null>("01"); // First section open by default
    const timeLeft = useCountdown(DEADLINE);


    useParallaxScroll();

    const handleToggleSection = (section: string) => {
        setOpenSection(openSection === section ? null : section);
    };

    const handleCTAClick = (location: string) => {
        trackEvent(EVENTS.CTA_CLICK, { location });
        setIsModalOpen(true);
    };

    return (
        <AppShell showTopBar={false}>
            {/* Background Effects */}
            <AuroraBackground />
            <CrebitGuideBadge />

            <div className="min-h-screen relative overflow-x-hidden selection:bg-emerald-500/30 font-sans text-slate-200">

                {/* ==================== HERO SECTION ==================== */}
                <section
                    className="relative min-h-screen flex flex-col items-center justify-center 
                               overflow-hidden px-6 lg:px-[--base-padding-x] py-20"
                    aria-labelledby="hero-title"
                >
                    <div className="relative z-30 max-w-7xl mx-auto text-center flex flex-col items-center">
                        <div className="parallax-medium">
                            <motion.div
                                initial={{ opacity: 0, y: 30 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 1.0, ease: "easeOut" }}
                                className="space-y-10"
                            >
                                {/* Badge */}
                                <div className="stagger-reveal inline-flex items-center gap-3 px-6 py-2.5 
                                               rounded-full border border-emerald-500/30 
                                               bg-gradient-to-r from-emerald-900/40 to-black/60 
                                               backdrop-blur-md">
                                    <span className="text-sm font-medium tracking-[0.12em] text-emerald-300">
                                        신세대 AI 영상 프로덕션 가이드
                                    </span>
                                </div>

                                {/* Main Title */}
                                <div className="space-y-6">
                                    <h1
                                        id="hero-title"
                                        className="stagger-reveal stagger-1 text-4xl sm:text-5xl lg:text-6xl xl:text-7xl 
                                                  font-black text-white leading-[1.1] tracking-tight"
                                    >
                                        프롬프트 하나로 완성하는
                                        <br />
                                        <span className="text-transparent bg-clip-text 
                                                        bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
                                            AI 영상 제작 워크플로우
                                        </span>
                                    </h1>
                                    <p className="text-xl md:text-2xl lg:text-3xl font-light text-slate-300 
                                                 tracking-tight max-w-4xl mx-auto leading-relaxed">
                                        "매주 하나의 완성된 영상을 만들면서, AI 도구를 자연스럽게 체득합니다."
                                    </p>
                                </div>

                                {/* Stats */}
                                <div className="stagger-reveal stagger-3 flex flex-wrap justify-center 
                                               gap-8 md:gap-12 lg:gap-16 py-10 mt-12 
                                               border-t border-white/5 px-4">
                                    <StatItem
                                        label="커리큘럼"
                                        value="4주"
                                        icon={<Layers className="w-5 h-5 text-emerald-400" />}
                                    />
                                    <StatItem
                                        label="학습 도구"
                                        value="8+"
                                        badge="All-in-one"
                                        icon={<Zap className="w-5 h-5 text-emerald-400" />}
                                    />
                                    <StatItem
                                        label="결과물"
                                        value="4편"
                                        badge="포트폴리오"
                                        urgent
                                        icon={<Film className="w-5 h-5 text-emerald-400" />}
                                    />
                                </div>

                                {/* CTA Button */}
                                <button
                                    onClick={() => handleCTAClick("hero")}
                                    className="stagger-reveal stagger-3 group relative px-10 py-5 sm:px-12 sm:py-6
                                              bg-white text-black text-base sm:text-lg font-bold rounded-full
                                              hover:bg-emerald-50 transition-all duration-300
                                              transform hover:scale-[1.02] active:scale-[0.98]
                                              shadow-[0_0_40px_rgba(16,185,129,0.3)]
                                              focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:ring-offset-2
                                              focus:ring-offset-black"
                                    aria-label="마스터 클래스 합류 신청"
                                >
                                    <span className="relative z-10 flex items-center gap-3">
                                        마스터 클래스 합류하기
                                        <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                    </span>
                                </button>

                                {/* Coloso-style Social Proof */}
                                <div className="stagger-reveal stagger-4 mt-10">
                                    <SocialProofBanner />
                                </div>
                            </motion.div>
                        </div>
                    </div>
                </section>

                {/* ==================== WORKFLOW SECTION ==================== */}
                <section
                    className="py-20 lg:py-32 relative z-10 px-6 lg:px-[--base-padding-x]"
                    aria-labelledby="workflow-title"
                >
                    <div className="max-w-7xl mx-auto">
                        <SectionHeader
                            title="4단계 워크플로우"
                            subtitle="AI Video Workflow"
                            desc="직관과 영감을 정밀한 엔지니어링으로 전환하는 독보적 프로세스"
                        />

                        <div className="mt-16 lg:mt-20 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                            {WORKFLOW_STAGES.map((stage) => (
                                <WorkflowCard key={stage.number} stage={stage} />
                            ))}
                        </div>
                    </div>
                </section>

                {/* ==================== TRANSFORMATION SECTION ==================== */}
                <section
                    className="py-20 lg:py-32 relative z-10 px-6 lg:px-[--base-padding-x]"
                    aria-labelledby="transformation-title"
                >
                    <div className="max-w-5xl mx-auto">
                        <SectionHeader
                            title="수강 후 변화"
                            subtitle="Transformation"
                            desc="단순한 툴 학습이 아닌, 크리에이터로서의 정체성을 확립합니다."
                        />

                        <div className="mt-12 lg:mt-16 grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8">
                            {/* Before Card */}
                            <div
                                className="p-8 lg:p-10 rounded-3xl bg-red-950/20 border border-red-500/20 
                                          opacity-80 hover:opacity-100 transition-opacity duration-300"
                                role="region"
                                aria-label="수강 전 상태"
                            >
                                <h3 className="text-xl font-bold text-red-400 mb-6">Before</h3>
                                <ul className="space-y-4" role="list">
                                    {BEFORE_ITEMS.map((item, idx) => (
                                        <li key={idx} className="flex gap-3 text-slate-400 text-[15px]">
                                            <span className="text-red-500/60 flex-shrink-0" aria-hidden="true">✕</span>
                                            <span>{item}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            {/* After Card */}
                            <div
                                className="p-8 lg:p-10 rounded-3xl bg-emerald-950/30 border border-emerald-500/30 
                                          relative overflow-hidden"
                                role="region"
                                aria-label="수강 후 상태"
                            >
                                <div
                                    className="absolute inset-0 bg-emerald-500/5 animate-pulse"
                                    style={{ animationDuration: "3s" }}
                                    aria-hidden="true"
                                />
                                <h3 className="text-xl font-bold text-emerald-400 mb-6 relative">After</h3>
                                <ul className="space-y-4 relative" role="list">
                                    {AFTER_ITEMS.map((item, idx) => (
                                        <li key={idx} className="flex gap-3 text-white text-[15px]">
                                            <CheckCircle
                                                className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5"
                                                aria-hidden="true"
                                            />
                                            <span className={item.bold ? "font-semibold" : ""}>
                                                {item.text}
                                            </span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </div>
                </section>

                {/* ==================== CURRICULUM SECTION ==================== */}
                <section
                    id="curriculum"
                    className="py-20 lg:py-32 border-t border-white/5 relative z-10 px-6 lg:px-[--base-padding-x]"
                    aria-labelledby="curriculum-title"
                >
                    <div className="max-w-5xl mx-auto">
                        <header className="text-center mb-12 lg:mb-16 space-y-4">
                            <span className="text-emerald-500 font-bold tracking-[0.2em] text-sm uppercase">
                                Curriculum
                            </span>
                            <h2
                                id="curriculum-title"
                                className="text-3xl sm:text-4xl lg:text-5xl font-black text-white tracking-tight"
                            >
                                4주 마스터 과정
                            </h2>
                            <p className="text-slate-400 text-base lg:text-lg font-light">
                                매주 하나의 포트폴리오를 완성합니다.
                            </p>
                        </header>

                        <div className="space-y-3">
                            {CURRICULUM_DATA.map((week) => (
                                <AccordionCurriculum
                                    key={week.section}
                                    section={week.section}
                                    title={week.title}
                                    items={week.items}
                                    isOpen={openSection === week.section}
                                    onToggle={() => handleToggleSection(week.section)}
                                />
                            ))}
                        </div>
                    </div>
                </section>

                {/* ==================== FOOTER ==================== */}
                <footer
                    className="py-16 lg:py-20 relative z-10 border-t border-white/5 
                              bg-black/40 backdrop-blur-xl"
                    role="contentinfo"
                >
                    <div className="max-w-6xl mx-auto px-6">
                        <div className="flex flex-col md:flex-row justify-between items-center gap-6 text-xs text-slate-500">
                            <p>© 2026 AI Video Master. All rights reserved.</p>
                            <nav className="flex gap-6" aria-label="Footer navigation">
                                <Link
                                    href="/crebit/terms?tab=terms"
                                    className="hover:text-white transition-colors"
                                >
                                    이용약관
                                </Link>
                                <Link
                                    href="/crebit/terms?tab=privacy"
                                    className="hover:text-white transition-colors"
                                >
                                    개인정보처리방침
                                </Link>
                            </nav>
                        </div>
                    </div>
                </footer>

                {/* ==================== STICKY CTA BAR (Coloso-style) ==================== */}
                <div
                    id="apply"
                    className="fixed bottom-0 left-0 right-0 z-50 p-4 sm:p-5
                              border-t border-white/10 bg-black/95 backdrop-blur-xl"
                    role="region"
                    aria-label="수강 신청 바"
                >
                    <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
                        {/* Left: Countdown + Urgency - Desktop only */}
                        <div className="hidden lg:flex items-center gap-6">
                            <div>
                                <p className="text-xs text-amber-400 font-bold mb-1 tracking-widest uppercase
                                             flex items-center gap-2">
                                    <Clock className="w-3.5 h-3.5" />
                                    다음 기수 마감 임박
                                </p>
                                <CountdownDisplay timeLeft={timeLeft} />
                            </div>
                            {/* Urgency indicator */}
                            <div className="h-12 w-px bg-white/10" />
                            <div className="flex items-center gap-2 text-sm text-slate-400">
                                <Users className="w-4 h-4 text-amber-400" />
                                <span><span className="text-amber-400 font-bold">{SOCIAL_PROOF.totalStudents}명</span> 수강 중</span>
                            </div>
                        </div>

                        {/* Right Section */}
                        <div className="flex items-center gap-4 sm:gap-6 w-full lg:w-auto justify-between lg:justify-end">
                            {/* Price Display - Coloso style */}
                            <div className="hidden sm:block">
                                <PriceDisplay />
                            </div>

                            {/* CTA Button with glow */}
                            <button
                                onClick={() => handleCTAClick("sticky_bar")}
                                className="flex-1 sm:flex-none px-6 sm:px-8 py-3 sm:py-4
                                          text-black font-bold text-base sm:text-lg
                                          bg-gradient-to-r from-amber-400 to-amber-500
                                          hover:from-amber-300 hover:to-amber-400
                                          rounded-full transition-all duration-300
                                          shadow-[0_0_20px_rgba(251,191,36,0.4)]
                                          hover:shadow-[0_0_30px_rgba(251,191,36,0.6)]
                                          focus:outline-none focus:ring-2 focus:ring-amber-400
                                          focus:ring-offset-2 focus:ring-offset-black"
                                aria-label="수강 신청하기"
                            >
                                <span className="flex items-center justify-center gap-2">
                                    수강 신청하기
                                    <ArrowRight className="w-4 h-4" aria-hidden="true" />
                                </span>
                            </button>
                        </div>
                    </div>
                </div>

                {/* Spacer for sticky bar */}
                <div className="h-20 sm:h-24" aria-hidden="true" />

                {/* Modal */}
                <ApplicationModal
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                />
            </div>
        </AppShell>
    );
}
