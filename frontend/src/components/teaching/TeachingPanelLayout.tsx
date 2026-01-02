"use client";

import { ReactNode, useState } from "react";
import Link from "next/link";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useBYOK } from "@/hooks/useBYOK";

interface TeachingPanelLayoutProps {
    title: string;
    sidebarContent: ReactNode;
    children: ReactNode;
    onBack?: () => void;
    isLoading?: boolean;
    /** Credit cost for this tool (shown in sidebar) */
    creditCost?: number;
}

export default function TeachingPanelLayout({
    title,
    sidebarContent,
    children,
    onBack,
    isLoading = false,
    creditCost,
}: TeachingPanelLayoutProps) {
    const creditCtx = useCreditContextOptional();
    const { byokKey, setBYOKKey, isBYOKEnabled } = useBYOK();
    const [showBYOKInput, setShowBYOKInput] = useState(false);
    const [byokInputValue, setBYOKInputValue] = useState(byokKey || "");

    const handleSaveBYOK = () => {
        setBYOKKey(byokInputValue);
        setShowBYOKInput(false);
    };

    const handleClearBYOK = () => {
        setBYOKKey(null);
        setBYOKInputValue("");
    };

    return (
        <div className="flex h-full w-full bg-[#09090b] text-white overflow-hidden font-sans">
            {/* Sidebar (Input Panel) */}
            <div className="w-[360px] flex-shrink-0 flex flex-col border-r border-white/10 bg-[#121212]">
                {/* Sidebar Header */}
                <div className="h-14 flex items-center justify-between px-5 border-b border-white/10 flex-shrink-0">
                    <div className="flex items-center">
                        <Link
                            href="/studio"
                            className="mr-3 p-1.5 rounded-md text-white/50 hover:text-white hover:bg-white/5 transition-colors"
                            title="Back to Studio"
                        >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                        </Link>
                        <h1 className="text-lg font-semibold tracking-tight text-white">{title}</h1>
                    </div>

                    {/* Credit Display */}
                    {creditCtx && !isBYOKEnabled && (
                        <Link
                            href="/credits"
                            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/10 transition-all group"
                            title="크레딧 충전하기"
                        >
                            <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1" />
                            </svg>
                            <span className="text-xs font-medium text-white/80 group-hover:text-white">
                                {creditCtx.isLoading ? "..." : creditCtx.balance.toLocaleString()}
                            </span>
                        </Link>
                    )}

                    {/* BYOK Active Badge */}
                    {isBYOKEnabled && (
                        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-green-500/10 border border-green-500/20">
                            <svg className="w-3.5 h-3.5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            <span className="text-xs font-medium text-green-400">BYOK</span>
                        </div>
                    )}
                </div>

                {/* Sidebar Content (Scrollable) */}
                <div className="flex-1 overflow-y-auto px-5 py-6">
                    <div className="space-y-6">
                        {sidebarContent}
                    </div>
                </div>

                {/* Sidebar Footer - BYOK Section */}
                <div className="border-t border-white/5 p-4">
                    {!showBYOKInput ? (
                        <button
                            onClick={() => setShowBYOKInput(true)}
                            className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-white/5 transition-colors group"
                        >
                            <div className="flex items-center gap-2">
                                <svg className="w-4 h-4 text-zinc-500 group-hover:text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                                </svg>
                                <span className="text-xs text-zinc-500 group-hover:text-zinc-400">
                                    {isBYOKEnabled ? "API Key 설정됨" : "내 API Key 사용하기"}
                                </span>
                            </div>
                            <svg className="w-4 h-4 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5l7 7-7 7" />
                            </svg>
                        </button>
                    ) : (
                        <div className="space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-200">
                            <div className="flex items-center justify-between">
                                <label className="text-xs font-medium text-zinc-400">Gemini API Key</label>
                                <button
                                    onClick={() => setShowBYOKInput(false)}
                                    className="text-xs text-zinc-500 hover:text-white"
                                >
                                    닫기
                                </button>
                            </div>
                            <input
                                type="password"
                                value={byokInputValue}
                                onChange={(e) => setBYOKInputValue(e.target.value)}
                                placeholder="AIzaSy... (Google AI Studio에서 발급)"
                                className="w-full px-3 py-2 bg-black/30 border border-white/10 rounded-lg text-white text-xs font-mono placeholder-white/20 focus:outline-none focus:border-amber-400/50 focus:ring-1 focus:ring-amber-400/20 transition-all"
                            />
                            <div className="flex gap-2">
                                <button
                                    onClick={handleSaveBYOK}
                                    disabled={!byokInputValue.trim()}
                                    className="flex-1 py-2 text-xs font-medium bg-amber-400/10 text-amber-400 hover:bg-amber-400/20 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-all"
                                >
                                    저장
                                </button>
                                {isBYOKEnabled && (
                                    <button
                                        onClick={handleClearBYOK}
                                        className="px-4 py-2 text-xs font-medium text-red-400 hover:bg-red-500/10 rounded-lg transition-all"
                                    >
                                        삭제
                                    </button>
                                )}
                            </div>
                            <p className="text-[10px] text-zinc-600 leading-relaxed">
                                🔒 API Key는 브라우저에만 저장되며 서버로 전송되지 않습니다.
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {/* Main Content (Result Panel) */}
            <div className="flex-1 flex flex-col min-w-0 bg-[#09090b]">
                <div className="flex-1 overflow-y-auto p-8 relative">
                    {children}

                    {/* Loading Overlay */}
                    {isLoading && (
                        <div className="absolute inset-0 bg-[#09090b]/60 backdrop-blur-sm flex items-center justify-center z-50">
                            <div className="flex flex-col items-center gap-4 p-6 rounded-2xl bg-[#18181b] border border-white/10 shadow-2xl">
                                <div className="relative w-12 h-12">
                                    <div className="absolute inset-0 border-4 border-white/10 rounded-full"></div>
                                    <div className="absolute inset-0 border-4 border-t-amber-400 border-r-transparent border-b-transparent border-l-transparent rounded-full animate-spin"></div>
                                </div>
                                <span className="text-sm font-medium text-white/80 animate-pulse">
                                    Generating...
                                </span>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

/**
 * Export BYOK-related utilities for use in panel components
 */
export { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
