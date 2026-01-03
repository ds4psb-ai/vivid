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
        <div className="flex h-full w-full overflow-hidden font-sans">
            {/* Sidebar (Input Panel) - Glassmorphism */}
            <div className="w-[380px] flex-shrink-0 flex flex-col border-r border-white/5 bg-[#0F0F1A]/60 backdrop-blur-xl relative z-10">
                {/* Sidebar Header */}
                <div className="h-16 flex items-center justify-between px-6 border-b border-white/5 flex-shrink-0 bg-[#0F0F1A]/40">
                    <div className="flex items-center gap-3">
                        <Link
                            href="/studio"
                            className="p-2 rounded-lg text-white/50 hover:text-white hover:bg-white/5 transition-colors"
                            title="Back to Studio"
                        >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                        </Link>
                        <h1 className="text-lg font-bold tracking-tight text-white/90">{title}</h1>
                    </div>

                    {/* Credit Display */}
                    {creditCtx && !isBYOKEnabled && (
                        <Link
                            href="/credits"
                            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/10 transition-all group"
                            title="크레딧 충전하기"
                        >
                            <svg className="w-3.5 h-3.5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                            <span className="text-xs font-bold text-white/80 group-hover:text-white font-mono">
                                {creditCtx.isLoading ? "..." : creditCtx.balance.toLocaleString()}
                            </span>
                        </Link>
                    )}

                    {/* BYOK Active Badge */}
                    {isBYOKEnabled && (
                        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.2)]">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                            </span>
                            <span className="text-[10px] font-bold text-emerald-400 tracking-wider">BYOK</span>
                        </div>
                    )}
                </div>

                {/* Sidebar Content (Scrollable) */}
                <div className="flex-1 overflow-y-auto px-6 py-6 custom-scrollbar">
                    <div className="space-y-6">
                        {sidebarContent}
                    </div>
                </div>

                {/* Sidebar Footer - BYOK Section */}
                <div className="border-t border-white/5 p-4 bg-[#0F0F1A]/40 backdrop-blur-md">
                    {!showBYOKInput ? (
                        <button
                            onClick={() => setShowBYOKInput(true)}
                            className="w-full flex items-center justify-between px-4 py-3 rounded-xl hover:bg-white/5 transition-all group border border-transparent hover:border-white/5"
                        >
                            <div className="flex items-center gap-3">
                                <div className="p-1.5 rounded-lg bg-white/5 group-hover:bg-white/10 transition-colors">
                                    <svg className="w-4 h-4 text-zinc-400 group-hover:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                                    </svg>
                                </div>
                                <div className="flex flex-col items-start">
                                    <span className="text-xs font-semibold text-zinc-400 group-hover:text-white transition-colors">
                                        API configuration
                                    </span>
                                    <span className="text-[10px] text-zinc-600 group-hover:text-zinc-500">
                                        {isBYOKEnabled ? "Using your API Key" : "Use your own Gemini Key"}
                                    </span>
                                </div>
                            </div>
                            <svg className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-transform group-hover:translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5l7 7-7 7" />
                            </svg>
                        </button>
                    ) : (
                        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300 p-1">
                            <div className="flex items-center justify-between">
                                <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Gemini API Key</label>
                                <button
                                    onClick={() => setShowBYOKInput(false)}
                                    className="p-1 text-zinc-500 hover:text-white transition-colors"
                                >
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>
                            <input
                                type="password"
                                value={byokInputValue}
                                onChange={(e) => setBYOKInputValue(e.target.value)}
                                placeholder="AIzaSy... (Paste key here)"
                                className="w-full px-4 py-3 bg-[#050505]/50 border border-white/10 rounded-xl text-white text-sm font-mono placeholder-white/20 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/20 transition-all shadow-inner"
                            />
                            <div className="flex gap-2">
                                <button
                                    onClick={handleSaveBYOK}
                                    disabled={!byokInputValue.trim()}
                                    className="flex-1 py-2.5 text-xs font-bold bg-amber-500 text-black hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-all shadow-[0_0_15px_rgba(245,158,11,0.2)] hover:shadow-[0_0_20px_rgba(245,158,11,0.4)]"
                                >
                                    SAVE KEY
                                </button>
                                {isBYOKEnabled && (
                                    <button
                                        onClick={handleClearBYOK}
                                        className="px-4 py-2.5 text-xs font-bold text-red-400 hover:bg-red-500/10 border border-red-500/20 rounded-lg transition-all"
                                    >
                                        RESET
                                    </button>
                                )}
                            </div>
                            <p className="text-[10px] text-zinc-600 leading-relaxed text-center">
                                Key is stored locally in your browser only.
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {/* Main Content (Result Panel) */}
            <div className="flex-1 flex flex-col min-w-0 bg-transparent relative z-0">
                <div className="flex-1 overflow-y-auto p-8 relative scroll-smooth">
                    {children}

                    {/* Loading Overlay - Premium */}
                    {isLoading && (
                        <div className="absolute inset-0 bg-[#0F0F1A]/40 backdrop-blur-md flex items-center justify-center z-50 animate-in fade-in duration-300">
                            <div className="flex flex-col items-center gap-6 p-8 rounded-3xl bg-[#0F0F1A]/80 border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.5)] backdrop-blur-xl">
                                <div className="relative w-16 h-16">
                                    <div className="absolute inset-0 border-4 border-white/5 rounded-full"></div>
                                    <div className="absolute inset-0 border-4 border-t-amber-500 border-r-transparent border-b-transparent border-l-transparent rounded-full animate-spin"></div>
                                    <div className="absolute inset-0 border-4 border-b-violet-500 border-t-transparent border-l-transparent border-r-transparent rounded-full animate-spin-reverse opacity-70"></div>
                                </div>
                                <div className="flex flex-col items-center gap-1">
                                    <span className="text-sm font-bold text-white tracking-widest uppercase animate-pulse">
                                        Generating
                                    </span>
                                    <span className="text-xs text-white/40">Creating your masterpiece...</span>
                                </div>
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
