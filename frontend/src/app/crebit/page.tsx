"use client";

/**
 * ATC Academy (formerly Crebit) Landing Page
 * 
 * Vision: AI Technical Producer (ATC) Academy
 * 2026 Roadmap: 10 Feature Films
 * Core Tech: Abyss Interpreter, Logic Extractor, Saju Propensity, Higgsfield Fine-tuning
 */

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Brain, Calculator, Sparkles, Zap, Film, Users, Globe } from "lucide-react";
import AppShell from "@/components/AppShell";
import ApplicationModal from "@/components/ApplicationModal";
import PortfolioLightbox from "@/components/PortfolioLightbox";
import { AuroraBackground } from "@/components/AuroraBackground";
import { CrebitGuideBadge } from "@/components/CrebitGuideBadge";
import { useParallaxScroll, useSmoothScroll } from "@/hooks/useLusionAnimations";
import { trackEvent, EVENTS } from "@/lib/analytics";

// Local components
import {
    SectionHeader,
    StatItem,
    PortfolioItem,
    PipelineNode,
    CurriculumBox,
    TrackCard,
    MentorProfile,
    AgentVisualization,
} from "./_components";

export default function ATCPage() {
    const [timeLeft, setTimeLeft] = useState<{ days: number, hours: number, minutes: number, seconds: number }>({ days: 0, hours: 0, minutes: 0, seconds: 0 });
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedPortfolio, setSelectedPortfolio] = useState<{ img: string; tag: string; title: string; desc: string } | null>(null);

    useSmoothScroll();
    useParallaxScroll();

    useEffect(() => {
        // Mock deadline for the next recruitment batch
        const deadline = new Date("2026-02-01T23:59:59").getTime();
        const interval = setInterval(() => {
            const now = new Date().getTime();
            const distance = deadline - now;
            if (distance < 0) { clearInterval(interval); return; }
            setTimeLeft({
                days: Math.floor(distance / (1000 * 60 * 60 * 24)),
                hours: Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
                minutes: Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60)),
                seconds: Math.floor((distance % (1000 * 60)) / 1000)
            });
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    return (
        <AppShell showTopBar={false}>
            {/* Aurora Background Layer */}
            <AuroraBackground />

            {/* Guide Badge */}
            <CrebitGuideBadge />

            <div className="min-h-screen relative overflow-x-hidden selection:bg-[#4200FF]/30 font-sans text-slate-200">

                {/* Hero Section */}
                <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden px-[--base-padding-x] py-20">

                    <div className="relative z-30 max-w-7xl mx-auto px-6 text-center flex flex-col items-center">
                        <div className="parallax-medium">
                            <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1.0, ease: "easeOut" }} className="space-y-10">
                                <div className="stagger-reveal inline-flex items-center gap-3 px-6 py-2 rounded-full border border-emerald-500/30 bg-gradient-to-r from-emerald-900/40 to-black backdrop-blur-md mb-8">
                                    <img src="/assets/characters/chokki.png" alt="초끼" className="w-8 h-8 rounded-full border border-emerald-500/50" />
                                    <span className="text-sm font-medium tracking-[0.15em] text-emerald-300">초끼와 떠나는 4차원 크리에이터 여정</span>
                                </div>

                                <div className="space-y-6">
                                    <h1 className="stagger-reveal stagger-1 text-hero font-black text-white leading-[0.9] tracking-tighter mix-blend-screen drop-shadow-2xl">
                                        4개의 차원을 연결하는<br />
                                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-200 to-cyan-400">AI 에이전트 워크플로우</span>
                                    </h1>
                                    <p className="text-2xl md:text-3xl font-light text-slate-300 tracking-tight">
                                        ATC 아카데미: AI 테크니컬 프로듀서 양성 과정
                                    </p>
                                </div>

                                <div className="stagger-reveal stagger-3 flex flex-wrap justify-center gap-8 md:gap-16 py-10 mt-12 border-t border-white/5 w-full md:w-auto px-10">
                                    <StatItem label="글로벌 연계" value="온라인" icon={<Globe className="w-5 h-5 text-emerald-400" />} />
                                    <StatItem label="소수정예" value="20명" badge="오프라인" icon={<Users className="w-5 h-5 text-emerald-400" />} />
                                    <StatItem label="슈퍼 엘리트" value="10명" badge="마스터" urgent icon={<Film className="w-5 h-5 text-emerald-400" />} />
                                </div>

                                <button onClick={() => { trackEvent(EVENTS.CTA_CLICK, { location: 'hero' }); setIsModalOpen(true); }}
                                    className="stagger-reveal stagger-3 button-primary group relative px-12 py-6 bg-white text-black text-lg font-bold rounded-full mt-8 hover:bg-emerald-50 transition-all transform hover:scale-[1.02] shadow-[0_0_40px_rgba(16,185,129,0.3)]">
                                    <span className="relative z-10 flex items-center gap-3">ATC 1기 지원하기 <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" /></span>
                                </button>
                            </motion.div>
                        </div>
                    </div>
                </section>

                {/* Core Dimensions (System Architecture) */}
                <section className="py-[--section-gap] relative z-10 px-[--base-padding-x] mt-10">
                    <div className="max-w-full mx-auto">
                        <SectionHeader
                            title="핵심 차원 (Core Dimensions)"
                            subtitle="ATC 4단계 파이프라인"
                            desc="직관과 영감을 정밀한 엔지니어링으로 전환하는 독보적 아키텍처"
                        />

                        <div className="mt-20 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                            {/* Dimension 1: Abyss Interpreter */}
                            <div className="group relative p-8 rounded-2xl bg-gradient-to-b from-white/[0.03] to-transparent border border-white/10 hover:border-emerald-500/50 transition-all duration-500 overflow-hidden">
                                <div className="absolute top-0 left-0 w-full h-1 bg-emerald-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500" />
                                <div className="mb-6 w-12 h-12 rounded-xl bg-emerald-900/30 flex items-center justify-center border border-emerald-500/20 group-hover:scale-110 transition-transform">
                                    <Brain className="w-6 h-6 text-emerald-400" />
                                </div>
                                <h3 className="text-xl font-bold text-white mb-2">1D. 심연 해석기</h3>
                                <p className="text-emerald-400 text-xs font-mono mb-4 uppercase tracking-wider">Subconscious Analysis</p>
                                <p className="text-slate-400 text-sm leading-relaxed">
                                    잠재의식 수준까지 나를 해석합니다. 추상적인 감정과 꿈을 구체적인 키워드와 시각적 언어로 번역하여 당신만의 고유한 세계관을 발견합니다.
                                </p>
                            </div>

                            {/* Dimension 2: Logic Extractor */}
                            <div className="group relative p-8 rounded-2xl bg-gradient-to-b from-white/[0.03] to-transparent border border-white/10 hover:border-violet-500/50 transition-all duration-500 overflow-hidden">
                                <div className="absolute top-0 left-0 w-full h-1 bg-violet-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500" />
                                <div className="mb-6 w-12 h-12 rounded-xl bg-violet-900/30 flex items-center justify-center border border-violet-500/20 group-hover:scale-110 transition-transform">
                                    <Calculator className="w-6 h-6 text-violet-400" />
                                </div>
                                <h3 className="text-xl font-bold text-white mb-2">2D. 로직 추출기</h3>
                                <p className="text-violet-400 text-xs font-mono mb-4 uppercase tracking-wider">Mathematics of Beauty</p>
                                <p className="text-slate-400 text-sm leading-relaxed">
                                    거장들의 명장면을 수학적 로직으로 추출합니다. 황금비, 앵글, 조명의 수치화를 통해 당신의 작품에 거장의 DNA를 이식합니다.
                                </p>
                            </div>

                            {/* Dimension 3: Saju Propensity */}
                            <div className="group relative p-8 rounded-2xl bg-gradient-to-b from-white/[0.03] to-transparent border border-white/10 hover:border-amber-500/50 transition-all duration-500 overflow-hidden">
                                <div className="absolute top-0 left-0 w-full h-1 bg-amber-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500" />
                                <div className="mb-6 w-12 h-12 rounded-xl bg-amber-900/30 flex items-center justify-center border border-amber-500/20 group-hover:scale-110 transition-transform">
                                    <Sparkles className="w-6 h-6 text-amber-400" />
                                </div>
                                <h3 className="text-xl font-bold text-white mb-2">3D. 사주 성향 분석</h3>
                                <p className="text-amber-400 text-xs font-mono mb-4 uppercase tracking-wider">Destined Content Type</p>
                                <p className="text-slate-400 text-sm leading-relaxed">
                                    사주(Four Pillars) 로직으로 알아보는 나의 콘텐츠 성향. 당신이 타고난 크리에이티브 에너지가 어떤 장르와 포맷에 최적화되어 있는지 분석합니다.
                                </p>
                            </div>

                            {/* Dimension 4: Higgsfield Fine-tuning */}
                            <div className="group relative p-8 rounded-2xl bg-gradient-to-b from-white/[0.03] to-transparent border border-white/10 hover:border-cyan-500/50 transition-all duration-500 overflow-hidden">
                                <div className="absolute top-0 left-0 w-full h-1 bg-cyan-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500" />
                                <div className="mb-6 w-12 h-12 rounded-xl bg-cyan-900/30 flex items-center justify-center border border-cyan-500/20 group-hover:scale-110 transition-transform">
                                    <Zap className="w-6 h-6 text-cyan-400" />
                                </div>
                                <h3 className="text-xl font-bold text-white mb-2">4D. 힉스필드 튜너</h3>
                                <p className="text-cyan-400 text-xs font-mono mb-4 uppercase tracking-wider">Custom Model Training</p>
                                <p className="text-slate-400 text-sm leading-relaxed">
                                    미세 튜닝(Fine-tuning)을 통한 플랫폼의 개인화. 힉스필드와 커스텀 앱 워크플로우를 통해 남들과 다른 독보적인 퀄리티의 결과물을 생성합니다.
                                </p>
                            </div>
                        </div>
                    </div>
                </section>

                {/* 2026 Roadmap Section */}
                <section className="py-[--section-gap] relative overflow-hidden text-left px-[--base-padding-x]">
                    <div className="max-w-full mx-auto relative z-20">
                        <SectionHeader
                            title="2026 비전 스코프"
                            subtitle="AI 장편 영화 10편"
                            desc="단순한 교육이 아닙니다. 실제 극장 개봉과 OTT 배급을 목표로 하는 프로덕션입니다."
                        />

                        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {/* Placeholder for Feature Film Projects */}
                            <div className="lg:col-span-2 relative h-[500px] rounded-3xl overflow-hidden group">
                                <PortfolioItem
                                    img="/images/portfolio_noir.png"
                                    tag="장편 영화 01"
                                    title="The Abyss (심연)"
                                    desc="감독: ATC 팀 알파 | 장르: SF 스릴러 | 상태: 프리 프로덕션"
                                    delay={0.1}
                                    color="emerald"
                                    height="h-full"
                                    onClick={() => setSelectedPortfolio({ img: "/images/portfolio_noir.png", tag: "장편 영화", title: "The Abyss (심연)", desc: "ATC 엘리트 프로젝트 #01" })}
                                />
                            </div>
                            <div className="relative h-[500px] flex flex-col gap-8">
                                <div className="h-1/2 rounded-3xl overflow-hidden">
                                    <PortfolioItem
                                        img="/images/portfolio_anime.png"
                                        tag="장편 영화 02"
                                        title="네온 소울"
                                        desc="사이버펑크 애니메이션 시리즈"
                                        delay={0.2}
                                        color="pink"
                                        height="h-full"
                                    />
                                </div>
                                <div className="h-1/2 p-8 rounded-3xl bg-white/[0.02] border border-white/10 flex flex-col justify-center">
                                    <h4 className="text-2xl font-black text-white mb-4">세 번째 감독은<br /><span className="text-slate-500">당신입니다</span></h4>
                                    <p className="text-slate-400 text-sm mb-6">당신의 시나리오가 2026년의 세 번째 작품이 됩니다.</p>
                                    <button onClick={() => { setIsModalOpen(true); }} className="text-left flex items-center gap-2 text-emerald-400 font-bold hover:gap-4 transition-all">
                                        프로젝트 제안하기 <ArrowRight className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Curriculum Section */}
                <section id="curriculum" className="py-[--section-gap] border-t border-white/5 relative z-10 px-[--base-padding-x]">
                    <div className="max-w-5xl mx-auto">
                        <div className="text-center mb-16 space-y-4">
                            <span className="text-emerald-500 font-bold tracking-[0.2em] text-sm uppercase">Elite Curriculum</span>
                            <h2 className="text-4xl md:text-5xl font-black text-white tracking-tight">ATC 마스터 코스</h2>
                            <p className="text-slate-400 text-lg font-light">AI 기술과 예술적 직관의 완벽한 결합</p>
                        </div>
                        <div className="space-y-4">
                            <CurriculumBox
                                section="01"
                                title="Foundation: 해석과 설계"
                                items={[
                                    "Abyss Interpreter: 잠재의식 및 세계관 추출 실습",
                                    "Saju Content: 나의 창작 성향과 최적 장르 분석",
                                    "Prompt Engineering Pro: 자연어를 넘어선 기계어와의 대화",
                                    "Scenario Structuring: AI와 함께하는 3막 구조 설계"
                                ]}
                            />
                            <CurriculumBox
                                section="02"
                                title="Technology: 로직과 튜닝"
                                items={[
                                    "Logic Extractor: 거장들의 연출 기법 수치화 및 적용",
                                    "Higgsfield & Fine-tuning: 나만의 모델 학습시키기",
                                    "ComfyUI Advanced Workflow: 노드 기반의 복잡한 파이프라인 제어",
                                    "Consistency Control: 롱폼 제작을 위한 캐릭터/배경 일관성 유지"
                                ]}
                            />
                            <CurriculumBox
                                section="03"
                                title="Production: 생성과 합성"
                                items={[
                                    "Multi-Model Generation: Midjourney, Runway, Veo, Sora 복합 활용",
                                    "High-End Compositing: After Effects & Nuke AI Tools",
                                    "Sound Scaping: Suno, Udio를 활용한 프로페셔널 사운드 디자인",
                                    "Final Mastering: 극장 상영을 위한 업스케일링 및 색보정"
                                ]}
                            />
                            <CurriculumBox
                                section="04"
                                title="Business: 배급과 확장"
                                items={[
                                    "Film Festival Strategy: AI 영화제 및 국제 영화제 출품 전략",
                                    "OTT Distribution: 넷플릭스/유튜브 프리미엄 배급 프로세스",
                                    "IP Expansion: 캐릭터 굿즈 및 파생 콘텐츠 기획",
                                    "Human Cloud Network: ATC 졸업생 네트워크 활용법"
                                ]}
                            />
                        </div>
                    </div>
                </section>

                {/* Leaders Section */}
                <section className="py-[--section-gap] border-t border-white/5 relative z-10 px-[--base-padding-x]">
                    <div className="max-w-full mx-auto">
                        <SectionHeader title="마스터" subtitle="ATC 교수진" desc="각 분야 최고의 전문가들이 당신의 멘토가 됩니다." />
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-[--grid-gap] mt-16">
                            <MentorProfile img="/images/mentor_1.png" name="김태은 (Humanizer)" role="총괄 PD / Founder" tags={["AI 심리학", "워크플로우 아키텍트"]} />
                            <MentorProfile img="/images/mentor_2.png" name="박지수 (Tech Director)" role="로직 마스터" tags={["파이프라인 엔지니어링", "파인튜닝"]} />
                            <MentorProfile img="/images/mentor_3.png" name="하소이 (Executive PD)" role="제작 총괄" tags={["Commercial Film", "글로벌 배급"]} />
                        </div>
                    </div>
                </section>

                {/* Footer - Premium Glass Refactor */}
                <footer className="py-20 relative z-10 border-t border-white/5 bg-black/40 backdrop-blur-xl">
                    <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent" />

                    <div className="max-w-6xl mx-auto px-6">
                        <div className="grid grid-cols-1 md:grid-cols-12 gap-12 md:gap-24 mb-16">
                            {/* Brand Column */}
                            <div className="md:col-span-4 space-y-6">
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-600 to-teal-800 flex items-center justify-center shadow-lg shadow-emerald-500/20">
                                        <span className="text-white font-bold text-lg">A</span>
                                    </div>
                                    <span className="text-xl font-bold tracking-tight text-white">ATC 아카데미</span>
                                </div>
                                <p className="text-slate-400 text-sm leading-relaxed font-light">
                                    AI 테크니컬 프로듀서 아카데미<br />
                                    창의적 지능의 미래를 정의합니다.
                                </p>
                                <div className="flex gap-4 pt-2">
                                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                                    <span className="text-xs font-mono text-emerald-500">SYSTEM OPERATIONAL</span>
                                </div>
                            </div>

                            {/* Info Columns */}
                            <div className="md:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/5 hover:border-white/10 transition-colors group">
                                    <div className="flex items-center gap-2 mb-4">
                                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 group-hover:shadow-[0_0_10px_#10B981] transition-shadow" />
                                        <span className="text-xs text-slate-400 uppercase tracking-wider font-bold">판매자 정보</span>
                                    </div>
                                    <h4 className="text-white font-bold mb-3">주식회사 페이지아카데미</h4>
                                    <div className="space-y-2 text-xs text-slate-500 font-mono">
                                        <p>대표자: 이용찬 | 사업자등록번호: 751-88-02370</p>
                                        <p>주소: 서울 성동구 성수이로 113, 801호</p>
                                        <p>이메일: kaylee@page-academy.com</p>
                                    </div>
                                </div>

                                <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/5 hover:border-white/10 transition-colors group">
                                    <div className="flex items-center gap-2 mb-4">
                                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 group-hover:shadow-[0_0_10px_#06B6D4] transition-shadow" />
                                        <span className="text-xs text-slate-400 uppercase tracking-wider font-bold">제작사 정보</span>
                                    </div>
                                    <h4 className="text-white font-bold mb-3">(주)아캐인 ARKAIN Inc.</h4>
                                    <div className="space-y-2 text-xs text-slate-500 font-mono">
                                        <p>대표자: 정의석 | 사업자등록번호: 685-87-03357</p>
                                        <p>주소: 서울 용산구 한남대로 8길 16</p>
                                        <p>사업내용: 디지털 콘텐츠 제작 및 플랫폼</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Bottom Bar */}
                        <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-6 text-xs text-slate-600">
                            <p>© 2026 ATC Academy. All rights reserved.</p>
                            <div className="flex gap-6">
                                <Link href="/crebit/terms?tab=terms" className="hover:text-white transition-colors">이용약관</Link>
                                <Link href="/crebit/terms?tab=privacy" className="hover:text-white transition-colors">개인정보처리방침</Link>
                            </div>
                        </div>
                    </div>
                </footer>

                {/* Sticky Bottom Bar */}
                <div id="apply" className="fixed bottom-0 left-0 right-0 z-30 p-6 border-t border-white/10 bg-black/80 backdrop-blur-xl">
                    <div className="max-w-7xl mx-auto flex items-center justify-between">
                        <div className="hidden md:block">
                            <div className="text-xs text-emerald-400 font-bold mb-1 tracking-widest uppercase">다음 기수 마감까지</div>
                            <div className="font-mono text-xl text-white font-bold tracking-widest">
                                {String(timeLeft.days).padStart(2, '0')}일 {String(timeLeft.hours).padStart(2, '0')}시간 {String(timeLeft.minutes).padStart(2, '0')}분 {String(timeLeft.seconds).padStart(2, '0')}초
                            </div>
                        </div>
                        <div className="flex items-center gap-8 w-full md:w-auto justify-between md:justify-start">
                            <div className="text-right hidden sm:block">
                                <div className="text-xs text-slate-400 mb-1">엘리트 멤버십</div>
                                <div className="text-white font-bold text-xl">글로벌 온라인 / 오프라인</div>
                            </div>
                            <button onClick={() => { trackEvent(EVENTS.CTA_CLICK, { location: 'sticky_bar' }); setIsModalOpen(true); }}
                                className="button-primary magnetic-btn flex-1 md:flex-none text-black font-bold text-lg bg-emerald-400 hover:bg-emerald-300 shadow-lg shadow-emerald-500/20">
                                <span className="relative z-10 flex items-center gap-2">지원하기 <ArrowRight className="w-4 h-4" /></span>
                            </button>
                        </div>
                    </div>
                </div>

                <div className="h-24" />
                <ApplicationModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
                <PortfolioLightbox isOpen={!!selectedPortfolio} onClose={() => setSelectedPortfolio(null)} item={selectedPortfolio} />
            </div>
        </AppShell>
    );
}

