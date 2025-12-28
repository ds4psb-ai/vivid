"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
    Zap,
    MapPin,
    Calendar,
    Users,
    CheckCircle2,
    PlayCircle,
    Database,
    Globe,
    Clapperboard,
    ArrowRight,
    Shield,
    CreditCard,
    X,
    ChevronDown,
    Plus,
    Film
} from "lucide-react";
import AppShell from "@/components/AppShell";
import ApplicationModal from "@/components/ApplicationModal";
import PortfolioLightbox from "@/components/PortfolioLightbox";

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

                {/* 1. Hero Section (Cinema Verite) */}
                <section className="relative h-screen min-h-[900px] flex items-center justify-center overflow-hidden">
                    {/* Background Video/Image Placeholder */}
                    <div className="absolute inset-0 z-0">
                        <div className="absolute inset-0 bg-[#050505]/60 z-10" />
                        <div className="absolute inset-0 bg-gradient-to-t from-[#050505] via-transparent to-[#050505]/40 z-10" />
                        <Image
                            src="/images/hero_bg_main.png"
                            alt="Crebit Hero"
                            fill
                            className="object-cover opacity-100" // Increased opacity as the image is 4K premium
                            priority
                            quality={100}
                        />
                        {/* Cinematic Grain Overlay - Reduced for 4K clarity */}
                        <div className="absolute inset-0 bg-[url('/images/noise.png')] opacity-[0.02] mix-blend-overlay z-20 pointer-events-none" />
                    </div>

                    <div className="relative z-30 max-w-7xl mx-auto px-6 text-center flex flex-col items-center">
                        <motion.div
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                            className="space-y-8"
                        >
                            {/* Top Badge - Enhanced (Larger for Premium Feel) */}
                            <div className="inline-flex items-center gap-4 px-10 py-4 rounded-full border border-white/10 bg-black/50 backdrop-blur-xl mb-10 hover:bg-black/70 transition-colors cursor-default shadow-2xl ring-1 ring-white/5">
                                <span className="w-2.5 h-2.5 rounded-full bg-[#FF0045] animate-pulse shadow-[0_0_20px_#FF0045]" />
                                <span className="text-base font-bold tracking-[0.25em] text-white uppercase">Crebit × Page Academy</span>
                            </div>

                            {/* Main Heading - 2-Line Semantic Blocks */}
                            <div className="space-y-2">
                                <p className="text-2xl md:text-3xl font-light text-white/80 leading-tight tracking-wide">
                                    나만의 세계관을
                                </p>
                                <h1 className="text-5xl md:text-7xl font-black text-white leading-[1.1] tracking-tight">
                                    <span className="text-[#4200FF]">DATA</span>로 치환하다
                                </h1>
                            </div>

                            <p className="text-xl md:text-2xl text-slate-300 font-light tracking-wide max-w-3xl mx-auto leading-relaxed mt-12 drop-shadow-md">
                                Art & Viral, 감각을 성과로 증명하는 법.<br />
                                <strong className="text-white font-bold">성수동 크래빗 나이트 아티스트 1기</strong>
                            </p>

                            {/* Stats / Info */}
                            <div className="flex flex-wrap justify-center gap-8 md:gap-16 py-8 border-t border-b border-white/10 mt-12 bg-black/40 backdrop-blur-md w-full md:w-auto px-16 md:rounded-full shadow-2xl border-x border-white/5">
                                <StatItem label="모집 마감" value={`D-${timeLeft.days}`} highlight />
                                <StatItem label="정원" value="40명" badge="마감임박" urgent />
                                <StatItem label="장소" value="성수 페이지아카데미" />
                            </div>

                            {/* Primary CTA */}
                            <button
                                onClick={() => setIsModalOpen(true)}
                                className="inline-flex group relative px-14 py-7 bg-[#4200FF] text-white text-xl font-bold rounded-2xl mt-12 hover:bg-[#5500FF] transition-all transform hover:scale-[1.02] shadow-[0_0_40px_rgba(66,0,255,0.5)] hover:shadow-[0_0_80px_rgba(66,0,255,0.8)] ring-1 ring-white/20"
                            >
                                <span className="relative z-10 flex items-center gap-3">
                                    1기 얼리버드 신청하기 <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
                                </span>
                            </button>
                        </motion.div>
                    </div>

                    {/* Rabbit Logo Watermark */}
                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/3 w-[600px] h-[600px] bg-[radial-gradient(circle_chost,#4200FF_0%,transparent_70%)] opacity-20 blur-[100px] pointer-events-none" />
                </section>

                {/* 2. Portfolio Grid (Outcome) - NEW SECTION */}
                <section className="py-32 bg-[#0a0a0c]">
                    <div className="max-w-7xl mx-auto px-6">
                        <SectionHeader title="Outcomes" subtitle="압도적인 결과물" desc="이론이 아닙니다. 당신이 가져갈 포트폴리오입니다." />

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mt-20 h-[800px] md:h-[700px]">
                            {/* Item 1: Cinematic */}
                            <PortfolioItem
                                img="/images/portfolio_noir.png"
                                tag="시네마틱"
                                title="누아르 탐정"
                                desc="Midjourney v6 + Runway Gen-3"
                                delay={0.1}
                                color="purple"
                                onClick={() => setSelectedPortfolio({ img: "/images/portfolio_noir.png", tag: "시네마틱", title: "누아르 탐정", desc: "Midjourney v6 + Runway Gen-3" })}
                            />
                            {/* Item 2: Anime */}
                            <PortfolioItem
                                img="/images/portfolio_anime.png"
                                tag="애니메이션"
                                title="사이버펑크 소녀"
                                desc="Niji Journey + Live2D"
                                delay={0.2}
                                color="pink"
                                onClick={() => setSelectedPortfolio({ img: "/images/portfolio_anime.png", tag: "애니메이션", title: "사이버펑크 소녀", desc: "Niji Journey + Live2D" })}
                            />
                            {/* Item 3: Motion */}
                            <PortfolioItem
                                img="/images/portfolio_motion.png"
                                tag="모션그래픽"
                                title="추상 3D 루프"
                                desc="루프 애니메이션 + 업스케일링"
                                delay={0.3}
                                color="sky"
                                onClick={() => setSelectedPortfolio({ img: "/images/portfolio_motion.png", tag: "모션그래픽", title: "추상 3D 루프", desc: "루프 애니메이션 + 업스케일링" })}
                            />
                        </div>
                    </div>
                </section>

                {/* 3. System (Philosophy) */}
                <section className="py-32 bg-[#050505] relative overflow-hidden">
                    <div className="absolute top-1/2 left-0 w-full h-px bg-gradient-to-r from-transparent via-[#4200FF]/30 to-transparent" />

                    <div className="max-w-6xl mx-auto px-6 relative z-10">
                        <SectionHeader title="System" subtitle="감각의 시스템화" />

                        <div className="flex flex-col md:flex-row justify-between items-center gap-8 mt-20">
                            <SystemNode icon={Zap} label="아이디어" step="01" />
                            <Arrow />
                            <SystemNode icon={Database} label="세계관 데이터" step="02" highlight />
                            <Arrow />
                            <SystemNode icon={Clapperboard} label="스토리보드" step="03" />
                            <Arrow />
                            <SystemNode icon={PlayCircle} label="파이널 영상" step="04" />
                        </div>

                        <p className="text-center text-[#9CA3AF] mt-16 text-xl font-light">
                            "정리된 감각은, <span className="text-white font-bold border-b-2 border-[#4200FF]">대체 불가능한 브랜드</span>가 됩니다."
                        </p>
                    </div>
                </section>

                {/* 4. Curriculum - Coloso V2 (Light Background) */}
                <section id="curriculum" className="py-24 bg-[#F8F8F8] text-[#333333]">
                    <div className="max-w-5xl mx-auto px-6">
                        <div className="text-center mb-12 space-y-3">
                            <span className="text-[#ED2040] font-medium tracking-[0.15em] text-[14px] uppercase">Curriculum</span>
                            <h2 className="text-[28px] md:text-[32px] font-bold text-[#333333] tracking-[-0.3px]">12주 올인원 커리큘럼</h2>
                            <p className="text-[#666666] text-[16px]">기초부터 프로덕션 데뷔까지, 빈틈없는 로드맵</p>
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
                                <p className="text-white font-medium">주식회사 아캐인 (Arkain Inc.)</p>
                                <div className="space-y-1.5 text-slate-400">
                                    <p className="text-xs text-slate-500">콘텐츠 기획, 커리큘럼 설계, 강의 제작</p>
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
                                onClick={() => setIsModalOpen(true)}
                                className="flex-1 md:flex-none bg-[#4200FF] text-white px-10 py-4 rounded-xl font-bold text-lg hover:bg-[#5500FF] transition-colors shadow-lg shadow-[#4200FF]/30 active:scale-95 transform transition-transform"
                            >
                                지금 신청하기
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

function PortfolioItem({ img, tag, title, desc, delay, color, onClick }: { img: string, tag: string, title: string, desc: string, delay: number, color: string, onClick?: () => void }) {
    const colors = {
        purple: 'bg-[#4200FF]',
        pink: 'bg-pink-500',
        sky: 'bg-sky-500',
    };

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay, duration: 0.5 }}
            onClick={onClick}
            className="group relative w-full h-full overflow-hidden cursor-pointer bg-slate-900"
        >
            <Image src={img} alt={title} fill className="object-cover transition-transform duration-700 group-hover:scale-110 opacity-80 group-hover:opacity-100" />
            <div className="absolute inset-x-0 bottom-0 p-8 bg-gradient-to-t from-black via-black/50 to-transparent translate-y-4 group-hover:translate-y-0 transition-transform duration-300">
                <span className={`inline-block px-2 py-0.5 text-[10px] font-bold text-white mb-2 ${colors[color as keyof typeof colors]}`}>{tag}</span>
                <h3 className="text-2xl font-bold text-white mb-1">{title}</h3>
                <p className="text-slate-300 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-300 delay-100">{desc}</p>
            </div>
        </motion.div>
    );
}

function SystemNode({ icon: Icon, label, step, highlight }: { icon: any, label: string, step: string, highlight?: boolean }) {
    return (
        <div className="flex flex-col items-center relative z-10">
            <div className={`w-28 h-28 rounded-3xl flex items-center justify-center mb-6 border transition-all duration-300 ${highlight ? 'bg-[#4200FF]/10 border-[#4200FF]/50 shadow-[0_0_30px_rgba(66,0,255,0.3)]' : 'bg-[#1a1a1c] border-white/5'}`}>
                <Icon className={`w-10 h-10 ${highlight ? 'text-[#4200FF]' : 'text-slate-400'}`} />
                <div className="absolute -top-3 -right-3 w-8 h-8 rounded-full bg-[#121212] border border-white/10 flex items-center justify-center text-xs font-mono text-slate-500">
                    {step}
                </div>
            </div>
            <div className="text-lg font-bold text-white">{label}</div>
        </div>
    );
}

function Arrow() {
    return (
        <div className="hidden md:block">
            <ArrowRight className="w-6 h-6 text-white/20" />
        </div>
    );
}

// CurriculumBox - Coloso V2 (Light, Square, Red Labels) + Accordion
function CurriculumBox({ section, title, items }: { section: string, title: string, items: string[] }) {
    const [isOpen, setIsOpen] = React.useState(section === "01"); // First section open by default

    return (
        <div className="bg-white border-b border-slate-200 overflow-hidden group">
            {/* Header - Clickable (Compact 80px) */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between h-20 px-5 text-left hover:bg-slate-50 transition-all"
            >
                <div className="flex items-center gap-4 transition-transform group-hover:translate-x-1">
                    {/* Section Label: Montserrat ExtraBold Style */}
                    <span className="text-[#ED2040] text-[13px] font-extrabold tracking-[0.15em] uppercase">Section {section}</span>
                    {/* Divider */}
                    <span className="w-px h-4 bg-slate-300" />
                    {/* Title */}
                    <h3 className="text-[15px] font-medium text-[#333333]">{title}</h3>
                </div>
                {/* Chevron with Circle Background */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${isOpen ? 'bg-[#ED2040] text-white' : 'bg-slate-100 text-slate-600'}`}>
                    <ChevronDown className={`w-4 h-4 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} />
                </div>
            </button>

            {/* Collapsible Content */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden"
                    >
                        <ul className="space-y-2 pl-5 pr-5 pb-5">
                            {items.map((item, idx) => (
                                <li key={idx} className="flex items-start gap-3 text-[14px] text-[#666666]">
                                    <span className="text-[#ED2040]">•</span>
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

// TrackCard - Dark Glass Style
function TrackCard({ type, title, badge, schedule, desc, color }: { type: string, title: string, badge: string, schedule: string, desc: string, color: string }) {
    return (
        <div className="group relative p-10 rounded-3xl bg-[#1a1a1c] border border-white/5 hover:border-white/20 transition-all duration-300 hover:-translate-y-1 overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:opacity-20 transition-opacity">
                <Film className="w-24 h-24 text-white" />
            </div>

            <div className="inline-block px-3 py-1 rounded text-xs font-bold text-white mb-6" style={{ backgroundColor: color }}>{badge}</div>

            {/* Background Letter */}
            <div className="text-[12rem] font-black absolute -top-10 -right-4 font-mono select-none pointer-events-none mix-blend-overlay opacity-20 text-white leading-none">
                {type}
            </div>

            <div className="relative z-10">
                <h3 className="text-3xl font-bold text-white mb-2">{title}</h3>
                <p className="text-[#9CA3AF] mb-8">{desc}</p>

                <div className="space-y-4 border-t border-white/5 pt-8">
                    <div className="flex items-center gap-3">
                        <Calendar className="w-5 h-5 text-slate-500" />
                        <span className="text-slate-300 font-mono">{schedule}</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <Users className="w-5 h-5 text-slate-500" />
                        <span className="text-slate-300">정원 20명 소수 정예</span>
                    </div>
                </div>

                <div className="mt-8 pt-6 border-t border-white/5 flex gap-2 overflow-x-auto pb-2 scrollbar-none">
                    {[1, 2, 3, 4].map((week) => (
                        <div key={week} className="flex-shrink-0 w-[60px] h-[60px] rounded-lg bg-black/50 border border-white/5 flex flex-col items-center justify-center">
                            <span className="text-[10px] text-slate-500">W{week}</span>
                            <span className="text-xs font-bold" style={{ color: week % 2 !== 0 ? color : 'white' }}>{week % 2 !== 0 ? '수업' : '코칭'}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

// MentorProfile - Dark Glass Style
function MentroProfile({ img, name, role, tags }: { img: string, name: string, role: string, tags: string[] }) {
    return (
        <div className="bg-[#1a1a1c] p-6 rounded-2xl border border-white/5 hover:border-white/20 transition-all group hover:-translate-y-1 duration-300 flex items-center gap-6">
            <div className="w-24 h-24 rounded-full bg-slate-800 shrink-0 overflow-hidden relative border-2 border-white/5 group-hover:border-[#4200FF]/50 transition-colors">
                <Image src={img} alt={name} fill className="object-cover" />
            </div>
            <div>
                <h4 className="text-xl font-bold text-white mb-1">{name} <span className="text-sm font-normal text-slate-500 ml-1 block md:inline">{role}</span></h4>
                <div className="mt-2 flex flex-wrap gap-2">
                    {tags.map((tag, i) => (
                        <span key={i} className="text-[11px] text-slate-400 bg-black/30 px-2 py-1 rounded border border-white/5">{tag}</span>
                    ))}
                </div>
            </div>
        </div>
    );
}
