"use client";

import { ReactNode, useState } from "react";
import Link from "next/link";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useBYOK } from "@/hooks/useBYOK";
import BYOKSettingsModal from "./BYOKSettingsModal";
import OperationProgress from "@/components/shared/OperationProgress";
import type { ProgressEvent } from "@/hooks/useAsyncOperation";

export type ThemeColor = "violet" | "cyan" | "emerald" | "amber" | "rose" | "fuchsia" | "indigo" | "sky";

const THEME_COLORS = {
    violet: {
        accent: "text-violet-600 dark:text-violet-400",
        border: "border-violet-200 dark:border-violet-500/30",
        bg: "bg-violet-500/5 dark:bg-violet-500/10",
        glow: "shadow-[0_0_30px_rgba(139,92,246,0.15)]",
        gradient: "from-violet-500 to-purple-500",
        focus: "focus:border-violet-400/50 focus:ring-violet-400/20",
        button: "from-violet-500 to-purple-500 hover:from-violet-400 hover:to-purple-400 shadow-violet-500/10 hover:shadow-violet-500/20",
        spinner: "border-t-violet-500 border-b-purple-500",
    },
    cyan: {
        accent: "text-cyan-600 dark:text-cyan-400",
        border: "border-cyan-200 dark:border-cyan-500/30",
        bg: "bg-cyan-500/5 dark:bg-cyan-500/10",
        glow: "shadow-[0_0_30px_rgba(6,182,212,0.15)]",
        gradient: "from-cyan-500 to-blue-500",
        focus: "focus:border-cyan-400/50 focus:ring-cyan-400/20",
        button: "from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 shadow-cyan-500/10 hover:shadow-cyan-500/20",
        spinner: "border-t-cyan-500 border-b-blue-500",
    },
    emerald: {
        accent: "text-emerald-600 dark:text-emerald-400",
        border: "border-emerald-200 dark:border-emerald-500/30",
        bg: "bg-emerald-500/5 dark:bg-emerald-500/10",
        glow: "shadow-[0_0_30px_rgba(16,185,129,0.15)]",
        gradient: "from-emerald-500 to-teal-500",
        focus: "focus:border-emerald-400/50 focus:ring-emerald-400/20",
        button: "from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 shadow-emerald-500/10 hover:shadow-emerald-500/20",
        spinner: "border-t-emerald-500 border-b-teal-500",
    },
    amber: {
        accent: "text-amber-600 dark:text-amber-400",
        border: "border-amber-200 dark:border-amber-500/30",
        bg: "bg-amber-500/5 dark:bg-amber-500/10",
        glow: "shadow-[0_0_30px_rgba(245,158,11,0.15)]",
        gradient: "from-amber-400 to-amber-500",
        focus: "focus:border-amber-400/50 focus:ring-amber-400/20",
        button: "from-amber-400 to-amber-500 hover:from-amber-300 hover:to-amber-400 shadow-amber-500/10 hover:shadow-amber-500/20",
        spinner: "border-t-amber-500 border-b-orange-500",
    },
    rose: {
        accent: "text-rose-600 dark:text-rose-400",
        border: "border-rose-200 dark:border-rose-500/30",
        bg: "bg-rose-500/5 dark:bg-rose-500/10",
        glow: "shadow-[0_0_30px_rgba(244,63,94,0.15)]",
        gradient: "from-rose-500 to-pink-500",
        focus: "focus:border-rose-400/50 focus:ring-rose-400/20",
        button: "from-rose-500 to-pink-500 hover:from-rose-400 hover:to-pink-400 shadow-rose-500/10 hover:shadow-rose-500/20",
        spinner: "border-t-rose-500 border-b-pink-500",
    },
    fuchsia: {
        accent: "text-fuchsia-600 dark:text-fuchsia-400",
        border: "border-fuchsia-200 dark:border-fuchsia-500/30",
        bg: "bg-fuchsia-500/5 dark:bg-fuchsia-500/10",
        glow: "shadow-[0_0_30px_rgba(217,70,239,0.15)]",
        gradient: "from-fuchsia-500 to-purple-500",
        focus: "focus:border-fuchsia-400/50 focus:ring-fuchsia-400/20",
        button: "from-fuchsia-500 to-purple-500 hover:from-fuchsia-400 hover:to-purple-400 shadow-fuchsia-500/10 hover:shadow-fuchsia-500/20",
        spinner: "border-t-fuchsia-500 border-b-purple-500",
    },
    indigo: {
        accent: "text-indigo-600 dark:text-indigo-400",
        border: "border-indigo-200 dark:border-indigo-500/30",
        bg: "bg-indigo-500/5 dark:bg-indigo-500/10",
        glow: "shadow-[0_0_30px_rgba(99,102,241,0.15)]",
        gradient: "from-indigo-500 to-violet-500",
        focus: "focus:border-indigo-400/50 focus:ring-indigo-400/20",
        button: "from-indigo-500 to-violet-500 hover:from-indigo-400 hover:to-violet-400 shadow-indigo-500/10 hover:shadow-indigo-500/20",
        spinner: "border-t-indigo-500 border-b-violet-500",
    },
    sky: {
        accent: "text-sky-600 dark:text-sky-400",
        border: "border-sky-200 dark:border-sky-500/30",
        bg: "bg-sky-500/5 dark:bg-sky-500/10",
        glow: "shadow-[0_0_30px_rgba(14,165,233,0.15)]",
        gradient: "from-sky-500 to-blue-500",
        focus: "focus:border-sky-400/50 focus:ring-sky-400/20",
        button: "from-sky-500 to-blue-500 hover:from-sky-400 hover:to-blue-400 shadow-sky-500/10 hover:shadow-sky-500/20",
        spinner: "border-t-sky-500 border-b-blue-500",
    },
};

interface TeachingPanelLayoutProps {
    title: string;
    sidebarContent: ReactNode;
    children: ReactNode;
    onBack?: () => void;
    isLoading?: boolean;
    /** Credit cost for this tool (shown in sidebar) */
    creditCost?: number;
    /** Theme color for this dimension */
    themeColor?: ThemeColor;

    // New progress props (optional, backward compatible)
    /** Current progress state */
    progress?: ProgressEvent | null;
    /** Called when user clicks cancel */
    onCancel?: () => void;
    /** Called when user clicks retry */
    onRetry?: () => void;
    /** Whether retry is available */
    canRetry?: boolean;
    /** Error message if operation failed */
    error?: string | null;
    /** Current retry count */
    retryCount?: number;
    /** Max retry count */
    maxRetries?: number;
}

export default function TeachingPanelLayout({
    title,
    sidebarContent,
    children,
    onBack,
    isLoading = false,
    creditCost,
    themeColor = "amber",
    // New progress props
    progress,
    onCancel,
    onRetry,
    canRetry = false,
    error,
    retryCount = 0,
    maxRetries = 3,
}: TeachingPanelLayoutProps) {
    const theme = THEME_COLORS[themeColor];
    const creditCtx = useCreditContextOptional();
    const { isBYOKEnabled } = useBYOK();
    const [showBYOKModal, setShowBYOKModal] = useState(false);

    return (
        <div className="flex h-full w-full overflow-hidden relative">
            {/* Ambient Background handles by AppShell or Global Aurora */}

            {/* Sidebar (Input Panel) - Unified Glass Style */}
            <div className="w-[380px] flex-shrink-0 flex flex-col border-r border-slate-200 dark:border-white/10 bg-slate-50/80 dark:bg-slate-900/60 backdrop-blur-xl relative z-20">
                {/* Portal Glow Effect - Removed to clean up visual noise */}

                {/* Sidebar Header */}
                <div className={`h-16 flex items-center justify-between px-6 border-b ${theme.border} flex-shrink-0 bg-transparent relative`}>
                    <div className="flex items-center gap-3">
                        <Link
                            href="/dimension"
                            className="p-2 rounded-lg text-slate-500 dark:text-white/50 hover:text-black dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
                            title="Back to Dimension"
                        >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                        </Link>
                        <h1 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white/90">{title}</h1>
                    </div>

                    {/* Credit Display */}
                    {creditCtx && !isBYOKEnabled && (
                        <Link
                            href="/credits"
                            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/5 dark:bg-white/5 hover:bg-black/10 dark:hover:bg-white/10 border border-black/5 dark:border-white/5 hover:border-black/10 dark:hover:border-white/10 transition-all group"
                            title="크레딧 충전하기"
                        >
                            <svg className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                            <span className="text-xs font-bold text-slate-700 dark:text-white/80 group-hover:text-black dark:group-hover:text-white font-mono">
                                {creditCtx.isLoading ? "..." : creditCtx.balance.toLocaleString()}
                            </span>
                        </Link>
                    )}

                    {/* BYOK Active Badge */}
                    {isBYOKEnabled && (
                        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 shadow-[0_0_10px_rgba(139,92,246,0.2)]">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-violet-500"></span>
                            </span>
                            <span className="text-[10px] font-bold text-violet-400 tracking-wider">BYOK</span>
                        </div>
                    )}
                </div>

                {/* Sidebar Content (Scrollable) */}
                <div className="flex-1 overflow-y-auto px-6 py-6 custom-scrollbar">
                    <div className="space-y-6">
                        {sidebarContent}
                    </div>
                </div>

                {/* Sidebar Footer - BYOK Status */}
                <div className="border-t border-slate-200 dark:border-white/5 p-4 bg-transparent">
                    <button
                        onClick={() => setShowBYOKModal(true)}
                        className="w-full flex items-center justify-between px-4 py-3 rounded-xl hover:bg-white/5 transition-all group border border-transparent hover:border-white/5"
                    >
                        <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${isBYOKEnabled ? 'bg-violet-500/20 text-violet-400' : 'bg-white/5 text-zinc-400'}`}>
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                                </svg>
                            </div>
                            <div className="flex flex-col text-left">
                                <span className="text-xs font-semibold text-slate-500 dark:text-zinc-400 group-hover:text-slate-800 dark:group-hover:text-white transition-colors">
                                    API Key
                                </span>
                                <span className={`text-[10px] ${isBYOKEnabled ? 'text-violet-600 dark:text-violet-400' : 'text-slate-400 dark:text-zinc-600'} group-hover:text-slate-500 dark:group-hover:text-zinc-400`}>
                                    {isBYOKEnabled ? "✓ 내 키 사용 중" : "클릭하여 등록하기"}
                                </span>
                            </div>
                        </div>
                        <svg className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-transform group-hover:translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5l7 7-7 7" />
                        </svg>
                    </button>
                </div>

                {/* BYOK Settings Modal */}
                <BYOKSettingsModal
                    isOpen={showBYOKModal}
                    onClose={() => setShowBYOKModal(false)}
                />
            </div>

            {/* Main Content (Result Panel) */}
            <div className="flex-1 flex flex-col min-w-0 bg-transparent relative z-10">
                <div className="flex-1 overflow-y-auto p-8 relative scroll-smooth">
                    {children}

                    {/* Loading/Error Overlay - Enhanced with OperationProgress */}
                    {(isLoading || error) && (
                        <div className="absolute inset-0 bg-[#0F0F1A]/40 backdrop-blur-md flex items-center justify-center z-50 animate-in fade-in duration-300">
                            {/* Use OperationProgress if progress props are provided */}
                            {(progress || error) && onCancel ? (
                                <div className="w-full max-w-md px-4">
                                    <OperationProgress
                                        progress={progress ?? null}
                                        isLoading={isLoading}
                                        error={error ?? null}
                                        onCancel={onCancel}
                                        onRetry={onRetry ?? (() => { })}
                                        canRetry={canRetry}
                                        themeColor={themeColor}
                                        retryCount={retryCount}
                                        maxRetries={maxRetries}
                                    />
                                </div>
                            ) : (
                                /* Fallback to legacy spinner for backward compatibility */
                                <div className={`flex flex-col items-center gap-6 p-8 rounded-3xl bg-[#0F0F1A]/80 border ${theme.border} ${theme.glow} backdrop-blur-xl`}>
                                    <div className="relative w-16 h-16">
                                        <div className="absolute inset-0 border-4 border-white/5 rounded-full"></div>
                                        <div className={`absolute inset-0 border-4 ${theme.spinner.split(' ')[0]} border-r-transparent border-b-transparent border-l-transparent rounded-full animate-spin`}></div>
                                        <div className={`absolute inset-0 border-4 ${theme.spinner.split(' ')[1]} border-t-transparent border-l-transparent border-r-transparent rounded-full animate-spin-reverse opacity-70`}></div>
                                    </div>
                                    <div className="flex flex-col items-center gap-1">
                                        <span className={`text-sm font-medium ${theme.accent} tracking-wide`}>
                                            처리 중
                                        </span>
                                        <span className="text-[10px] text-white/30">잠시만 기다려주세요</span>
                                    </div>
                                </div>
                            )}
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

/**
 * Re-export progress types for convenience
 */
export type { ProgressEvent } from "@/hooks/useAsyncOperation";
export { useAsyncOperation } from "@/hooks/useAsyncOperation";
export { useResultExport } from "@/hooks/useResultExport";
