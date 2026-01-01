"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
    Calendar,
    Users,
    PlayCircle,
    ArrowRight,
    ChevronDown,
    Film
} from "lucide-react";
import AppShell from "@/components/AppShell";
import ApplicationModal from "@/components/ApplicationModal";
import PortfolioLightbox from "@/components/PortfolioLightbox";
import { trackEvent, EVENTS } from "@/lib/analytics";

export default function CrebitPage() {
    const [timeLeft, setTimeLeft] = useState<{ days: number, hours: number, minutes: number, seconds: number }>({ days: 0, hours: 0, minutes: 0, seconds: 0 });
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedPortfolio, setSelectedPortfolio] = useState<{ img: string; tag: string; title: string; desc: string } | null>(null);

    useEffect(() => {
        // Early bird deadline: Jan 4, 2026 23:59:59 (더 급박하게!)
        const deadline = new Date("2026-01-04T23:59:59").getTime();

        const interval = setInterval(() => {
            const now = new Date().getTime();
            const distance = deadline - now;

            if (distance < 0) {
                clearInterval(interval);
                return;
            }

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
            <div className="min-h-screen bg-[#050505] text-white overflow-x-hidden selection:bg-[#4200FF]/30 font-sans">

                {/* 1. Hero Section (Cinematic Dark Mode) */}
                <section className="relative h-screen min-h-[900px] flex items-center justify-center overflow-hidden">
                    {/* Background Video/Image Placeholder */}
                    <div className="absolute inset-0 z-0">
                        <div className="absolute inset-0 bg-[#050505]/70 z-10" />
                        <div className="absolute inset-0 bg-gradient-to-t from-[#050505] via-transparent to-[#050505]/40 z-10" />
                        <div className="absolute inset-0 bg-gradient-to-b from-[#050505]/80 via-transparent to-transparent z-10" />
                        <Image
                            src="/images/hero_bg_main.png"
                            alt="Crebit Hero"
                            fill
                            className="object-cover opacity-80"
                            priority
                            quality={100}
                        />
                        {/* Cinematic Grain Overlay */}
                        <div className="absolute inset-0 bg-[url('/images/noise.png')] opacity-[0.03] mix-blend-overlay z-20 pointer-events-none" />
                    </div>

                    <div className="relative z-30 max-w-7xl mx-auto px-6 text-center flex flex-col items-center">
                        <motion.div
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 1.0, ease: "easeOut" }}
                            className="space-y-10"
                        >
                            {/* Top Badge - Dark High-Tech Look */}
                            <div className="inline-flex items-center gap-3 px-6 py-2 rounded-full border border-white/10 bg-black/60 backdrop-blur-md mb-8 hover:bg-black/80 transition-colors cursor-default">
                                <span className="w-2 h-2 rounded-full bg-[#4200FF] animate-pulse shadow-[0_0_10px_#4200FF]" />
                                <span className="text-sm font-medium tracking-[0.2em] text-slate-300 uppercase">Crebit / Season 1</span>
                            </div>

                            {/* Main Heading - Heavy Cinematic Typography */}
                            <div className="space-y-4">
                                <h1 className="text-4xl md:text-7xl font-black text-white leading-[1.05] tracking-tight drop-shadow-2xl">
                                    나만의 세계관을<br />
                                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-200 to-slate-500">불멸의 에셋으로</span>
                                </h1>
                            </div>

                            <p className="text-lg md:text-2xl text-slate-400 font-light tracking-wide max-w-3xl mx-auto leading-relaxed mt-10">
                                영감은 휘발되지만, 시스템은 영원합니다.<br />
                                당신의 세계관을 견고한 IP 자산으로 설계합니다.
                                <span className="text-white font-medium mt-6 block text-sm tracking-[0.2em] uppercase opacity-80">Crebit Night Artist Season 1</span>
                            </p>

                            {/* Stats / Info - Minimalist Tech */}
                            <div className="flex flex-wrap justify-center gap-12 md:gap-24 py-10 mt-16 border-t border-white/5 w-full md:w-auto px-10">
                                <StatItem label="모집 마감" value={`D-${timeLeft.days}`} highlight />
                                <StatItem label="모집 정원" value="40명" badge="선착순" urgent />
                                <StatItem label="교육 장소" value="성수 페이지 아카데미" />
                            </div>

                            {/* Primary CTA - Solid & Strong */}
                            <button
                                onClick={() => { trackEvent(EVENTS.CTA_CLICK, { location: 'hero' }); setIsModalOpen(true); }}
                                className="group relative px-12 py-6 bg-white text-black text-lg font-bold rounded-full mt-8 hover:bg-slate-200 transition-all transform hover:scale-[1.02] shadow-[0_0_30px_rgba(255,255,255,0.2)]"
                            >
                                <span className="relative z-10 flex items-center gap-3">
                                    1기 멤버십 합류하기 <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                </span>
                            </button>
                        </motion.div>
                    </div>
                </section>

                {/* 2. Portfolio (Outcome) - Cinematic Masonry Grid */}
                <section className="py-32 bg-[#0a0a0c]">
                    <div className="max-w-[1400px] mx-auto px-6">
                        <SectionHeader title="Outcomes" subtitle="시네마틱 퀄리티의 정점" desc="이론이 아닙니다. 당신의 이름으로 남을 작품입니다." />

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-24 h-[1200px] md:h-[800px]">
                            {/* Item 1: Cinematic - Large Vertical */}
                            <div className="lg:col-span-1 lg:row-span-2 h-full">
                                <PortfolioItem
                                    img="/images/portfolio_noir.png"
                                    tag="시네마틱 숏필름"
                                    title="The Detective"
                                    desc="Midjourney v6 + Runway Gen-3"
                                    delay={0.1}
                                    color="purple"
                                    height="h-full"
                                    onClick={() => setSelectedPortfolio({ img: "/images/portfolio_noir.png", tag: "시네마틱", title: "누아르 탐정", desc: "Midjourney v6 + Runway Gen-3" })}
                                />
                            </div>
                            {/* Item 2: Anime - Horizontal */}
                            <div className="lg:col-span-2 h-full">
                                <PortfolioItem
                                    img="/images/portfolio_anime.png"
                                    tag="애니메이션 뮤비"
                                    title="Cyberpunk Soul"
                                    desc="Niji Journey + Live2D + After Effects"
                                    delay={0.2}
                                    color="pink"
                                    height="h-full"
                                    onClick={() => setSelectedPortfolio({ img: "/images/portfolio_anime.png", tag: "애니메이션", title: "사이버펑크 소녀", desc: "Niji Journey + Live2D" })}
                                />
                            </div>
                            {/* Item 3: Motion - Square */}
                            <div className="md:col-span-1 h-full">
                                <PortfolioItem
                                    img="/images/portfolio_motion.png"
                                    tag="모션 그래픽"
                                    title="Abstract Loop"
                                    desc="Sora + Topaz Upscale"
                                    delay={0.3}
                                    color="sky"
                                    height="h-full"
                                    onClick={() => setSelectedPortfolio({ img: "/images/portfolio_motion.png", tag: "모션그래픽", title: "추상 3D 루프", desc: "루프 애니메이션 + 업스케일링" })}
                                />
                            </div>
                            {/* Item 4: Extra (Placeholder for layout) */}
                            <div className="md:col-span-1 h-full">
                                <PortfolioItem
                                    img="/images/hero_bg_main.png"
                                    tag="비주얼라이저"
                                    title="Sound Reactive"
                                    desc="TouchDesigner + AI Style Transfer"
                                    delay={0.4}
                                    color="purple"
                                    height="h-full"
                                />
                            </div>
                        </div>
                    </div>
                </section>

                {/* 3. System (Pipeline Blueprint) */}
                <section className="py-40 bg-[#050505] relative overflow-hidden text-left">
                    {/* Architectural Grid Background */}
                    <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f1f1f_1px,transparent_1px),linear-gradient(to_bottom,#1f1f1f_1px,transparent_1px)] bg-[size:40px_40px] opacity-20" />
                    <div className="absolute inset-0 bg-[radial-gradient(circle_800px_at_50%_50%,#000000_0%,transparent_100%)] z-10" />

                    <div className="max-w-7xl mx-auto px-6 relative z-20">
                        <SectionHeader title="System Architecture" subtitle="직관에서 자산으로" desc="추상적인 영감을 구체적인 데이터 파이프라인으로 전환합니다." />

                        <div className="mt-32 relative">
                            {/* Node Graph Container */}
                            <div className="relative grid grid-cols-1 md:grid-cols-4 gap-8 md:gap-4 items-start">

                                {/* Connector Line (Desktop) */}
                                <div className="hidden md:block absolute top-[60px] left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-[#4200FF] to-transparent opacity-30 z-0" />

                                <PipelineNode
                                    step="01"
                                    type="INPUT"
                                    label="Auteur DNA"
                                    desc="사용자의 직관과 세계관을 데이터화하여 추출"
                                    tags={["RAG", "Embeddings"]}
                                />
                                <PipelineNode
                                    step="02"
                                    type="PROCESS"
                                    label="장면 설계도 구현"
                                    desc="LLM 기반 시나리오 구조화 및 프롬프트 엔지니어링"
                                    tags={["LLM", "Prompt Opt"]}
                                    active
                                />
                                <PipelineNode
                                    step="03"
                                    type="GENERATION"
                                    label="에셋 팩토리 가동"
                                    desc="멀티 모델 AI를 활용한 고품질 소스 양산"
                                    tags={["Diffusion", "I2V"]}
                                />
                                <PipelineNode
                                    step="04"
                                    type="OUTPUT"
                                    label="파이널 컴포지팅"
                                    desc="시네마틱 룩뎁 보정 및 최종 렌더링"
                                    tags={["Upscale", "Grading"]}
                                />
                            </div>
                        </div>

                        <div className="mt-24 flex flex-col items-center gap-4">
                            <div className="w-px h-16 bg-gradient-to-b from-transparent via-[#4200FF] to-transparent opacity-50" />
                            <h3 className="text-xl md:text-2xl font-bold text-white tracking-tight flex items-center gap-3">
                                <span className="w-2 h-2 rounded-full bg-[#4200FF] shadow-[0_0_15px_#4200FF]" />
                                대체 불가능한 IP 자산
                            </h3>
                            <p className="text-xs text-slate-600 font-mono tracking-[0.3em] uppercase opacity-50">System Output Verified</p>
                        </div>
                    </div>
                </section>

                {/* 4. Curriculum - Cinematic Roadmap (Dark Mode) */}
                <section id="curriculum" className="py-32 bg-[#050505] border-t border-white/5">
                    <div className="max-w-5xl mx-auto px-6">
                        <div className="text-center mb-16 space-y-4">
                            <span className="text-[#4200FF] font-bold tracking-[0.2em] text-sm uppercase">Roadmap</span>
                            <h2 className="text-4xl md:text-5xl font-black text-white tracking-tight">12주 올인원 커리큘럼</h2>
                            <p className="text-slate-400 text-lg font-light">기초부터 프로덕션 데뷔까지, 빈틈없는 시스템</p>
                        </div>

                        <div className="space-y-4">
                            <CurriculumBox
                                section="01"
                                title="세계관 구축 & 스타일 정립"
                                items={[
                                    "레퍼런스 디깅과 무드보드 설정 (Pinterest/Behance)",
                                    "나만의 프롬프트 딕셔너리 구축 (Notion Template 제공)",
                                    "Midjourney 파라미터 튜닝 (--s, --c, --w 완벽 이해)",
                                    "일관된 캐릭터/배경 생성 노하우 (Seed 고정)"
                                ]}
                            />
                            <CurriculumBox
                                section="02"
                                title="시네마틱 스토리텔링"
                                items={[
                                    "영화적 기승전결 구조 (3막 구성 이론)",
                                    "컷 연결의 미학: 매치 컷, 점프 컷 활용",
                                    "카메라 무브먼트 프롬프트 (Pan, Tilt, Dolly Zoom)",
                                    "ChatGPT를 활용한 시나리오/콘티 자동화"
                                ]}
                            />
                            <CurriculumBox
                                section="03"
                                title="영상 생성 & 모션 그래픽"
                                items={[
                                    "Runway Gen-3 / Veo 심화 테크닉",
                                    "이미지 투 비디오 (I2V) 모션 제어 (Motion Brush)",
                                    "립싱크 & 페이셜 캡처 (Sync Labs)",
                                    "Upscaling & Frame Interpolation (Topaz AI)"
                                ]}
                            />
                            <CurriculumBox
                                section="04"
                                title="사운드 & 파이널 컷"
                                items={[
                                    "AI 음악/효과음 생성 (Suno, Udio)",
                                    "프리미어/다빈치 리졸브 컷 편집 기초",
                                    "색보정(Color Grading)으로 톤앤매너 완성",
                                    "최종 포트폴리오 패키징 및 배포 전략"
                                ]}
                            />
                        </div>
                    </div>
                </section>

                {/* 5. Tracks - REFINED (Blending) */}
                <section className="py-32 bg-[#0a0a0c]">
                    <div className="max-w-6xl mx-auto px-6">
                        <SectionHeader title="Tracks" subtitle="A반 vs B반" desc="당신의 성향에 맞는 트랙을 선택하세요." />

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-16">
                            {/* A Class */}
                            <TrackCard
                                type="A"
                                title="AI 영화반"
                                badge="CINEMATIC"
                                schedule="화/목 or 수 19:00"
                                desc="영화적 연출과 미장센을 추구하는 분"
                                color="#4200FF"
                            />
                            {/* B Class */}
                            <TrackCard
                                type="B"
                                title="AI 애니메이션반"
                                badge="ANIME / MV"
                                schedule="수 or 화/목 19:00"
                                desc="서브컬처/뮤직비디오 스타일을 선호하는 분"
                                color="#EC4899"
                            />
                        </div>
                    </div>
                </section>

                {/* 6. Instructor */}
                <section className="py-32 bg-[#050505] border-t border-white/5">
                    <div className="max-w-6xl mx-auto px-6">
                        <SectionHeader title="Leaders" subtitle="현업 리드 멘토진" />

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-16">
                            <MentroProfile
                                img="/images/mentor_1.png"
                                name="휴머나이저 (김태은)"
                                role="Humanizer 총괄 PD"
                                tags={["AI 커뮤니티 리드", "프롬프트 엔지니어"]}
                            />
                            <MentroProfile
                                img="/images/mentor_2.png"
                                name="극단AI (박지수)"
                                role="Tech Director"
                                tags={["ComfyUI 마스터", "파이프라인 설계"]}
                            />
                            <MentroProfile
                                img="/images/mentor_3.png"
                                name="소이PD (하소이)"
                                role="Commercial PD"
                                tags={["Commercial Film 400여 편", "브랜드 필름 연출"]}
                            />
                        </div>
                    </div>
                </section>

                {/* Business Info Footer (전자상거래법 필수 표기) */}
                <footer className="py-12 bg-[#050505] border-t border-white/5">
                    <div className="max-w-5xl mx-auto px-6">
                        {/* Partnership Header */}
                        <div className="text-center mb-8">
                            <div className="inline-flex items-center gap-3 mb-4">
                                <span className="text-white font-bold">Crebit</span>
                                <span className="text-slate-500">×</span>
                                <span className="text-white font-bold">Page Academy</span>
                            </div>
                            <p className="text-xs text-slate-500 max-w-lg mx-auto">
                                본 교육 프로그램은 <span className="text-slate-400">주식회사 아캐인(Arkain)</span>이 기획・제작하고,
                                <span className="text-slate-400">주식회사 페이지아카데미</span>가 학원업 등록 사업자로서 운영・판매합니다.
                            </p>
                        </div>

                        {/* Business Info Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm">
                            {/* Seller (Page Academy) */}
                            <div className="space-y-3 p-5 rounded-xl bg-white/[0.02] border border-white/5">
                                <div className="flex items-center gap-2 mb-3">
                                    <span className="w-2 h-2 rounded-full bg-[#4200FF]" />
                                    <span className="text-xs text-slate-400 uppercase tracking-wider font-medium">판매자 (학원업 등록 사업자)</span>
                                </div>
                                <p className="text-white font-medium">주식회사 페이지아카데미</p>
                                <div className="space-y-1.5 text-slate-400">
                                    <p><span className="text-slate-500">대표자:</span> 이용찬</p>
                                    <p><span className="text-slate-500">사업자등록번호:</span> 751-88-02370</p>
                                    <p><span className="text-slate-500">통신판매업신고:</span> 2022-서울성동-00228</p>
                                    <p><span className="text-slate-500">주소:</span> 서울특별시 성동구 성수이로 113, 8층 801호</p>
                                    <p><span className="text-slate-500">이메일:</span> <a href="mailto:kaylee@page-academy.com" className="text-[#4200FF] hover:underline">kaylee@page-academy.com</a></p>
                                </div>
                            </div>

                            {/* Producer (Arkain) */}
                            <div className="space-y-3 p-5 rounded-xl bg-white/[0.02] border border-white/5">
                                <div className="flex items-center gap-2 mb-3">
                                    <span className="w-2 h-2 rounded-full bg-[#FF0045]" />
                                    <span className="text-xs text-slate-400 uppercase tracking-wider font-medium">기획・제작</span>
                                </div>
                                <p className="text-white font-medium">(주)아캐인 ARKAIN Inc.</p>
                                <div className="space-y-1.5 text-slate-400">
                                    <p><span className="text-slate-500">대표자:</span> 정의석</p>
                                    <p><span className="text-slate-500">사업자등록번호:</span> 685-87-03357</p>
                                    <p><span className="text-slate-500">법인등록번호:</span> 110111-9081607</p>
                                    <p><span className="text-slate-500">주소:</span> 서울특별시 용산구 한남대로 8길 16 (한남동)</p>
                                    <p><span className="text-slate-500">업종:</span> 디지털 콘텐츠 제작 및 플랫폼 사업</p>
                                </div>
                            </div>
                        </div>

                        {/* Legal Footer */}
                        <div className="mt-8 pt-6 border-t border-white/5 text-center text-xs text-slate-500 space-y-3">
                            {/* Quick Links */}
                            <div className="flex items-center justify-center gap-4 text-slate-400">
                                <Link href="/crebit/terms?tab=terms" className="hover:text-white transition-colors">이용약관</Link>
                                <span className="text-slate-600">|</span>
                                <Link href="/crebit/terms?tab=privacy" className="hover:text-white transition-colors">개인정보처리방침</Link>
                                <span className="text-slate-600">|</span>
                                <Link href="/crebit/terms?tab=refund" className="hover:text-white transition-colors">환불정책</Link>
                            </div>
                            <p>© 2025 Page Academy × Crebit. All rights reserved.</p>
                            <p>본 서비스의 결제는 <span className="text-slate-400">나이스페이먼츠(주)</span>를 통해 안전하게 처리됩니다.</p>
                        </div>
                    </div>
                </footer>

                {/* Sticky Bottom Bar */}
                <div id="apply" className="fixed bottom-0 left-0 right-0 z-30 p-6 border-t border-white/10 bg-[#0a0a0c]/90 backdrop-blur-xl">
                    <div className="max-w-7xl mx-auto flex items-center justify-between">
                        <div className="hidden md:block">
                            <div className="text-xs text-[#FF0045] font-bold mb-1 tracking-widest uppercase">얼리버드 마감까지</div>
                            <div className="font-mono text-xl text-white font-bold tracking-widest">
                                {String(timeLeft.days).padStart(2, '0')}d {String(timeLeft.hours).padStart(2, '0')}h {String(timeLeft.minutes).padStart(2, '0')}m {String(timeLeft.seconds).padStart(2, '0')}s
                            </div>
                        </div>

                        <div className="flex items-center gap-8 w-full md:w-auto justify-between md:justify-start">
                            <div className="text-right hidden sm:block">
                                <div className="text-[#64748b] text-sm line-through">정가 45만원</div>
                                <div className="text-white font-bold text-2xl">34만원 <span className="text-sm font-normal text-[#FF0045] ml-1">1기 특가</span></div>
                            </div>
                            <button
                                onClick={() => { trackEvent(EVENTS.CTA_CLICK, { location: 'sticky_bar' }); setIsModalOpen(true); }}
                                className="flex-1 md:flex-none bg-[#4200FF] text-white px-10 py-4 rounded-xl font-bold text-lg hover:bg-[#5500FF] transition-colors shadow-lg shadow-[#4200FF]/30 active:scale-95 transform transition-transform"
                            >
                                지금 지원하기
                            </button>
                        </div>
                    </div>
                </div>

                <div className="h-24" />

                {/* Application Modal */}
                <ApplicationModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />

                {/* Portfolio Lightbox */}
                <PortfolioLightbox
                    isOpen={!!selectedPortfolio}
                    onClose={() => setSelectedPortfolio(null)}
                    item={selectedPortfolio}
                />
            </div>
        </AppShell>
    );
}

// --- Sub Components ---

function SectionHeader({ title, subtitle, desc, color = 'text-[#4200FF]' }: { title: string, subtitle: string, desc?: string, color?: string }) {
    return (
        <div className="text-center space-y-4">
            <motion.span
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className={`font-bold tracking-[0.2em] uppercase text-sm ${color}`}
            >
                {title}
            </motion.span>
            <motion.h2
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 }}
                className="text-4xl md:text-5xl font-bold text-white leading-tight"
            >
                {subtitle}
            </motion.h2>
            {desc && (
                <motion.p
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.2 }}
                    className="text-[#9CA3AF] text-lg max-w-2xl mx-auto"
                >
                    {desc}
                </motion.p>
            )}
        </div>
    );
}

function StatItem({ label, value, highlight, badge, urgent }: { label: string, value: string, highlight?: boolean, badge?: string, urgent?: boolean }) {
    return (
        <div className="flex flex-col items-center">
            <div className="text-[#9CA3AF] text-xs font-bold tracking-widest uppercase mb-2">{label}</div>
            <div className="flex items-center gap-2">
                <span className={`text-xl md:text-2xl font-bold ${highlight ? 'text-[#FF0045]' : 'text-white'}`}>
                    {value}
                </span>
                {badge && (
                    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${urgent ? 'border-[#FF0045]/30 bg-[#FF0045]/10 text-[#FF0045]' : 'border-white/20 bg-white/5 text-slate-300'}`}>
                        {urgent && (
                            <span className="relative flex h-1.5 w-1.5">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FF0045] opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-[#FF0045]"></span>
                            </span>
                        )}
                        <span className="text-[11px] font-bold tracking-tight leading-none">{badge}</span>
                    </div>
                )}
            </div>
        </div>
    );
}

function PortfolioItem({ img, tag, title, desc, delay, color, height = "h-[400px]", onClick }: { img: string, tag: string, title: string, desc: string, delay: number, color: string, height?: string, onClick?: () => void }) {
    const colors = {
        purple: 'bg-[#4200FF]',
        pink: 'bg-pink-500',
        sky: 'bg-sky-500',
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay, duration: 0.6 }}
            onClick={onClick}
            className={`group relative w-full ${height} overflow-hidden cursor-pointer bg-[#050505] transition-all duration-500`}
        >
            {/* Full Bleed Image */}
            <Image
                src={img}
                alt={title}
                fill
                className="object-cover transition-transform duration-700 group-hover:scale-105 opacity-70 group-hover:opacity-100 grayscale group-hover:grayscale-0"
            />

            {/* Cinematic Letterbox / Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent opacity-60 group-hover:opacity-80 transition-opacity" />

            {/* Hover Content - Minimalist & Bold */}
            <div className="absolute inset-x-0 bottom-0 p-8 transform translate-y-2 group-hover:translate-y-0 transition-transform duration-500 ease-out z-10">
                <div className="flex items-center gap-3 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 transform -translate-y-2 group-hover:translate-y-0 delay-75">
                    <span className={`w-1.5 h-1.5 rounded-full ${colors[color as keyof typeof colors]}`} />
                    <span className="text-[10px] font-bold text-slate-300 tracking-[0.2em] uppercase font-mono">
                        {tag}
                    </span>
                </div>

                <h3 className="text-3xl md:text-4xl font-black text-white mb-2 tracking-tighter uppercase italic leading-none">
                    {title}
                </h3>

                <div className="h-0 group-hover:h-auto overflow-hidden transition-all duration-500">
                    <p className="text-slate-400 text-sm font-mono pt-2 border-t border-white/20 mt-2">
                        {desc}
                    </p>
                </div>
            </div>

            {/* Center Play Button - Subtle */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-20 rounded-full border border-white/30 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-500 scale-90 group-hover:scale-100 backdrop-blur-sm bg-white/5">
                <PlayCircle className="w-8 h-8 text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.5)]" />
            </div>
        </motion.div>
    );
}

function PipelineNode({ step, type, label, desc, tags, active }: { step: string, type: string, label: string, desc: string, tags: string[], active?: boolean }) {
    return (
        <div className={`relative z-10 bg-[#0A0A0A] border rounded-lg p-5 flex flex-col items-start gap-4 transition-all duration-300 group hover:-translate-y-1 ${active ? 'border-[#4200FF] shadow-[0_0_20px_rgba(66,0,255,0.2)]' : 'border-white/10 hover:border-white/30'}`}>
            {/* Input/Output Ports */}
            <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-[#1a1a1c] border border-white/20" />
            <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-[#1a1a1c] border border-white/20 group-hover:bg-[#4200FF] transition-colors" />

            <div className="flex justify-between items-center w-full border-b border-white/5 pb-3">
                <span className="text-[10px] font-mono text-slate-500 bg-white/5 px-2 py-0.5 rounded">{type}</span>
                <span className="text-[10px] font-mono text-[#4200FF] font-bold">NODE_{step}</span>
            </div>

            <div>
                <h4 className={`text-lg font-bold mb-2 ${active ? 'text-white' : 'text-slate-300 group-hover:text-white'}`}>{label}</h4>
                <p className="text-xs text-slate-500 leading-relaxed font-mono">{desc}</p>
            </div>

            <div className="flex flex-wrap gap-2 mt-2">
                {tags.map((tag, i) => (
                    <span key={i} className="text-[9px] text-slate-400 bg-white/5 px-1.5 py-0.5 border border-white/5 rounded-sm">{tag}</span>
                ))}
            </div>
        </div>
    );
}



// CurriculumBox - Minimalist & Technical (Dark Mode)
function CurriculumBox({ section, title, items }: { section: string, title: string, items: string[] }) {
    const [isOpen, setIsOpen] = React.useState(section === "01");

    return (
        <div className="bg-[#0A0A0A] border border-white/5 overflow-hidden group hover:border-[#4200FF]/50 transition-colors duration-300">
            {/* Header */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between h-24 px-8 text-left"
            >
                <div className="flex items-center gap-8">
                    <span className="text-[#4200FF] text-xs font-mono font-bold tracking-widest border border-[#4200FF]/30 px-3 py-1.5 rounded bg-[#4200FF]/5">SECTION {section}</span>
                    <h3 className={`text-xl md:text-2xl font-bold transition-colors ${isOpen ? 'text-white' : 'text-slate-400 group-hover:text-white'}`}>{title}</h3>
                </div>
                <div className={`text-slate-500 transition-transform duration-300 ${isOpen ? 'rotate-180 text-white' : ''}`}>
                    <ChevronDown className="w-6 h-6" />
                </div>
            </button>

            {/* Content */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden bg-[#050505] border-t border-white/5"
                    >
                        <ul className="space-y-4 px-8 py-10">
                            {items.map((item, idx) => (
                                <li key={idx} className="flex items-start gap-4 text-[15px] text-slate-300 font-light leading-relaxed">
                                    <div className="w-1 h-1 rounded-full bg-[#4200FF] mt-2.5 shrink-0" />
                                    <span>{item}</span>
                                </li>
                            ))}
                        </ul>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

// TrackCard - Dark Glass + Neon
function TrackCard({ type, title, badge, schedule, desc, color }: { type: string, title: string, badge: string, schedule: string, desc: string, color: string }) {
    return (
        <div className="group relative p-10 bg-[#0A0A0A] border border-white/5 hover:border-white/20 transition-all duration-300 hover:-translate-y-2 overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
                <Film className="w-32 h-32 text-white" />
            </div>

            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded border border-white/10 bg-white/5 text-[11px] font-bold text-slate-300 mb-8 tracking-widest uppercase font-mono">
                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
                {badge}
            </div>

            {/* Background Letter */}
            <div className="text-[12rem] font-black absolute -top-10 -right-4 font-mono select-none pointer-events-none text-[#ffffff] opacity-[0.02]">
                {type}
            </div>

            <div className="relative z-10">
                <h3 className="text-3xl font-black text-white mb-3 tracking-tight">{title}</h3>
                <p className="text-slate-400 mb-8 font-light leading-relaxed">{desc}</p>

                <div className="space-y-4 border-t border-white/5 pt-8">
                    <div className="flex items-center gap-4">
                        <div className="w-8 h-8 rounded bg-white/5 flex items-center justify-center text-slate-400 border border-white/5">
                            <Calendar className="w-4 h-4" />
                        </div>
                        <span className="text-slate-300 font-mono text-sm">{schedule}</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="w-8 h-8 rounded bg-white/5 flex items-center justify-center text-slate-400 border border-white/5">
                            <Users className="w-4 h-4" />
                        </div>
                        <span className="text-slate-300 text-sm font-mono tracking-tight">정원 20명 소수정예</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

// MentorProfile - Minimal Pro
function MentroProfile({ img, name, role, tags }: { img: string, name: string, role: string, tags: string[] }) {
    return (
        <div className="bg-[#151515] p-6 border border-white/5 hover:border-white/20 transition-all hover:bg-[#1a1a1c] flex items-center gap-6 group">
            <div className="w-20 h-20 bg-slate-800 shrink-0 overflow-hidden relative grayscale group-hover:grayscale-0 transition-all duration-500">
                <Image src={img} alt={name} fill className="object-cover" />
            </div>
            <div>
                <h4 className="text-lg font-bold text-white mb-1 group-hover:text-[#4200FF] transition-colors">{name}</h4>
                <p className="text-sm text-slate-500 mb-3">{role}</p>
                <div className="flex flex-wrap gap-2">
                    {tags.map((tag, i) => (
                        <span key={i} className="text-[10px] text-slate-400 bg-white/5 px-2 py-0.5 border border-white/5">{tag}</span>
                    ))}
                </div>
            </div>
        </div>
    );
}
