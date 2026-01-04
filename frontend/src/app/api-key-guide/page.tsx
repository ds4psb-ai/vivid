"use client";

/**
 * API Key 가이드 페이지
 * 
 * Google Gemini API Key 발급 및 무료 크레딧 활성화 방법 안내
 * Design: Vivid Premium Dark Theme (Glassmorphism + Neon Accents)
 */

import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import AppShell from "@/components/AppShell";

const FREE_TRIAL_URL = "https://console.cloud.google.com/freetrial/signup/tos?facet_url=https:%2F%2Fcloud.google.com%2Ffree&facet_utm_source=google&facet_utm_campaign=17100102-GCP-DR-APAC-KR-ko-Google-BKWS-MIX-GenericCloud&facet_utm_medium=cpc";

export default function APIKeyGuidePage() {
    return (
        <AppShell showTopBar={false}>
            <div className="min-h-screen px-4 py-8 sm:px-6 lg:px-8 bg-[#0F0F1A]">
                <div className="mx-auto max-w-3xl">
                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-10 text-center"
                    >
                        <Link
                            href="/dimension"
                            className="inline-flex items-center gap-2 text-xs font-medium text-zinc-500 hover:text-white mb-6 transition-colors px-3 py-1.5 rounded-full hover:bg-white/5"
                        >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                            </svg>
                            스튜디오로 돌아가기
                        </Link>
                        <h1 className="text-3xl sm:text-4xl font-bold text-white mb-4 tracking-tight">
                            <span className="bg-clip-text text-transparent bg-gradient-to-r from-violet-400 to-purple-400">
                                $300 무료 크레딧
                            </span>으로 시작하기
                        </h1>
                        <p className="text-zinc-400 text-lg max-w-xl mx-auto leading-relaxed">
                            Google Cloud의 파격적인 혜택을 놓치지 마세요.<br />
                            단 3분이면 40만원 상당의 크레딧을 받을 수 있습니다.
                        </p>
                    </motion.div>

                    {/* Step 1: 무료 크레딧 신청 */}
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="mb-8 relative group"
                    >
                        <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 to-teal-500/5 rounded-3xl blur-xl group-hover:blur-2xl transition-all opacity-50" />
                        <div className="relative rounded-3xl border border-white/10 bg-[#13131F]/80 backdrop-blur-xl overflow-hidden shadow-2xl">
                            <div className="px-6 py-5 border-b border-white/5 bg-white/[0.02] flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 text-sm font-bold shadow-[0_0_10px_rgba(16,185,129,0.2)]">1</span>
                                    <h3 className="text-lg font-bold text-white">무료 크레딧 신청하기</h3>
                                </div>
                                <span className="px-3 py-1 text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full uppercase tracking-wider">
                                    Recommended
                                </span>
                            </div>

                            <div className="p-6 sm:p-8 space-y-8">
                                <div className="flex items-start gap-4 p-5 rounded-2xl bg-emerald-500/5 border border-emerald-500/10">
                                    <div className="p-2 bg-emerald-500/10 rounded-lg shrink-0">
                                        <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                        </svg>
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-emerald-200 font-semibold text-sm">왜 필요한가요?</p>
                                        <p className="text-sm text-emerald-100/70 leading-relaxed">
                                            '무료 체험판(Free Trial)' 계정은 사용량 제한이 없어 <strong>가장 빠르고 쾌적한 속도</strong>로 AI를 생성할 수 있습니다.
                                        </p>
                                    </div>
                                </div>

                                <div className="space-y-6">
                                    <div className="flex flex-col gap-4">
                                        <span className="text-sm font-semibold text-zinc-300 flex items-center gap-2">
                                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                                            신청 페이지 접속
                                        </span>
                                        <div className="rounded-xl overflow-hidden border border-white/10 shadow-2xl shadow-black/50 group/image">
                                            <Image
                                                src="/guide/google-cloud-free.jpg"
                                                alt="Google Cloud 무료 크레딧 안내"
                                                width={800}
                                                height={400}
                                                className="w-full transition-transform duration-700 group-hover/image:scale-105"
                                            />
                                        </div>
                                    </div>

                                    <div className="relative pl-4 border-l-2 border-white/5 space-y-6 ml-1">
                                        <div className="space-y-2">
                                            <h4 className="text-sm font-medium text-zinc-300">1. 계정 정보 입력</h4>
                                            <p className="text-xs text-zinc-500">Google 계정으로 로그인하고 약관에 동의합니다.</p>
                                        </div>
                                        <div className="space-y-4">
                                            <h4 className="text-sm font-medium text-zinc-300">2. 결제 정보 등록 (안심하세요!)</h4>
                                            <div className="rounded-xl overflow-hidden border border-white/10 shadow-2xl shadow-black/50 group/image">
                                                <Image
                                                    src="/guide/google-cloud-signup.jpg"
                                                    alt="Google Cloud 무료 크레딧 가입 화면"
                                                    width={800}
                                                    height={400}
                                                    className="w-full transition-transform duration-700 group-hover/image:scale-105"
                                                />
                                            </div>
                                            <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                                                <ul className="space-y-2 text-xs text-zinc-400">
                                                    <li className="flex items-center gap-2">
                                                        <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                                        즉시 결제되지 않으며 <strong>$300 무료 크레딧이 먼저 사용</strong>됩니다.
                                                    </li>
                                                    <li className="flex items-center gap-2">
                                                        <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                                        유료 전환 버튼을 누르기 전까진 <strong>자동 결제되지 않습니다.</strong>
                                                    </li>
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="pt-2">
                                    <a
                                        href={FREE_TRIAL_URL}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="relative block w-full group overflow-hidden rounded-xl"
                                    >
                                        <div className="absolute inset-0 bg-gradient-to-r from-emerald-600 to-teal-600 transition-all duration-300 group-hover:scale-105" />
                                        <div className="absolute inset-0 bg-black/10 group-hover:bg-transparent transition-colors" />
                                        <div className="relative py-4 px-6 flex items-center justify-center gap-3 text-white font-bold shadow-lg">
                                            <span>$300 무료 크레딧 받으러 가기</span>
                                            <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                                            </svg>
                                        </div>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </motion.section>

                    {/* Step 2: API Key 발급 */}
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                        className="mb-8 relative"
                    >
                        <div className="relative rounded-3xl border border-white/10 bg-[#13131F]/80 backdrop-blur-xl overflow-hidden">
                            <div className="px-6 py-5 border-b border-white/5 bg-white/[0.02] flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-violet-500/20 text-violet-400 text-sm font-bold shadow-[0_0_10px_rgba(139,92,246,0.2)]">2</span>
                                    <h3 className="text-lg font-bold text-white">API Key 발급하기</h3>
                                </div>
                            </div>

                            <div className="p-6 sm:p-8 space-y-6">
                                <ol className="space-y-6">
                                    {[
                                        { text: "Google AI Studio 접속", detail: "아래 버튼을 통해 이동하세요." },
                                        { text: "Create API Key 클릭", detail: "좌측 상단 파란색 버튼을 찾으세요." },
                                        { text: "키 복사", detail: "생성된 문자열(sk-...)을 복사합니다." }
                                    ].map((step, idx) => (
                                        <li key={idx} className="flex gap-4">
                                            <div className="flex flex-col items-center">
                                                <span className="w-6 h-6 rounded-full bg-white/5 flex items-center justify-center text-xs font-medium text-zinc-500 border border-white/5">{idx + 1}</span>
                                                {idx < 2 && <div className="w-px h-full bg-white/5 my-2"></div>}
                                            </div>
                                            <div className="pb-4">
                                                <p className="text-white font-medium mb-0.5">{step.text}</p>
                                                <p className="text-zinc-500 text-xs">{step.detail}</p>
                                            </div>
                                        </li>
                                    ))}
                                </ol>

                                <a
                                    href="https://aistudio.google.com/app/apikey"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="block w-full py-3.5 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-violet-500/30 text-zinc-300 hover:text-white font-medium text-center rounded-xl transition-all group"
                                >
                                    <span className="flex items-center justify-center gap-2">
                                        Google AI Studio로 이동
                                        <svg className="w-4 h-4 opacity-50 group-hover:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                        </svg>
                                    </span>
                                </a>
                            </div>
                        </div>
                    </motion.section>

                    {/* Step 3: 앱 설정 */}
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="mb-8 relative"
                    >
                        <div className="relative rounded-3xl border border-white/10 bg-[#13131F]/80 backdrop-blur-xl overflow-hidden">
                            <div className="px-6 py-5 border-b border-white/5 bg-white/[0.02] flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 text-sm font-bold shadow-[0_0_10px_rgba(6,182,212,0.2)]">3</span>
                                    <h3 className="text-lg font-bold text-white">마지막 단계! 키 입력하기</h3>
                                </div>
                            </div>

                            <div className="p-6 sm:p-8">
                                <div className="flex flex-col sm:flex-row items-center gap-6 p-6 rounded-2xl bg-gradient-to-br from-cyan-500/10 to-blue-500/5 border border-cyan-500/20">
                                    <div className="p-4 bg-cyan-500/20 rounded-full shrink-0 animate-pulse">
                                        <svg className="w-8 h-8 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                                        </svg>
                                    </div>
                                    <div className="text-center sm:text-left space-y-2">
                                        <p className="text-cyan-100 font-medium">
                                            앱 사이드바 하단의 <span className="text-white font-bold bg-white/10 px-2 py-0.5 rounded">API Key</span> 버튼을 눌러<br />
                                            방금 복사한 키를 붙여넣기만 하면 끝입니다.
                                        </p>
                                        <p className="text-xs text-cyan-500/70">
                                            이제 모든 기능이 무제한으로 열립니다!
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.section>

                    {/* Footer */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.3 }}
                        className="text-center pb-12"
                    >
                        <Link
                            href="/dimension"
                            className="inline-flex items-center gap-2 text-sm font-medium text-zinc-400 hover:text-white transition-colors px-6 py-3 rounded-xl border border-white/5 hover:border-white/10 hover:bg-white/5"
                        >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                            스튜디오로 돌아가서 시작하기
                        </Link>
                        <p className="text-[10px] text-zinc-600 mt-8">
                            🔒 입력하신 API Key는 클라이언트(브라우저)에만 안전하게 저장되며 서버로 전송되지 않습니다.
                        </p>
                    </motion.div>
                </div>
            </div>
        </AppShell>
    );
}
