"use client";

/**
 * InsufficientCreditsModal - Credit shortage notification
 * 
 * Shows when user tries to use AI feature without enough credits.
 * Offers credit recharge or BYOK options.
 */

import { useState } from "react";
import Link from "next/link";

interface InsufficientCreditsModalProps {
    isOpen: boolean;
    onClose: () => void;
    requiredCredits: number;
    currentBalance: number;
    onEnterBYOK?: () => void;
}

export default function InsufficientCreditsModal({
    isOpen,
    onClose,
    requiredCredits,
    currentBalance,
    onEnterBYOK,
}: InsufficientCreditsModalProps) {
    if (!isOpen) return null;

    const shortage = requiredCredits - currentBalance;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/70 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative bg-[#18181b] border border-white/10 rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                {/* Header */}
                <div className="p-6 pb-4 text-center border-b border-white/5">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-amber-500/10 flex items-center justify-center">
                        <svg className="w-8 h-8 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h2 className="text-xl font-bold text-white mb-2">크레딧이 부족합니다</h2>
                    <p className="text-sm text-zinc-400">
                        이 기능을 사용하려면 크레딧이 필요합니다.
                    </p>
                </div>

                {/* Credit Info */}
                <div className="p-6 space-y-4">
                    <div className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                        <div>
                            <span className="text-xs text-zinc-500 uppercase tracking-wider">필요</span>
                            <p className="text-lg font-bold text-white">{requiredCredits.toLocaleString()} 크레딧</p>
                        </div>
                        <div className="w-px h-10 bg-white/10" />
                        <div className="text-right">
                            <span className="text-xs text-zinc-500 uppercase tracking-wider">보유</span>
                            <p className="text-lg font-bold text-red-400">{currentBalance.toLocaleString()} 크레딧</p>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="space-y-3">
                        <Link
                            href="/credits"
                            className="w-full py-3.5 bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-300 hover:to-amber-400 text-[#121212] font-bold rounded-xl shadow-lg shadow-amber-500/20 transition-all flex items-center justify-center gap-2"
                        >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                            </svg>
                            크레딧 충전하기
                        </Link>

                        <div className="relative flex items-center gap-3">
                            <div className="flex-1 h-px bg-white/10" />
                            <span className="text-xs text-zinc-500">또는</span>
                            <div className="flex-1 h-px bg-white/10" />
                        </div>

                        <button
                            onClick={() => {
                                onClose();
                                onEnterBYOK?.();
                            }}
                            className="w-full py-3 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 text-white font-medium rounded-xl transition-all flex items-center justify-center gap-2"
                        >
                            <svg className="w-5 h-5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                            </svg>
                            내 API Key 직접 사용하기
                        </button>
                    </div>

                    <p className="text-xs text-zinc-500 text-center leading-relaxed">
                        본인의 Gemini API Key를 사용하면<br />
                        크레딧 소진 없이 무제한 사용 가능합니다.
                    </p>
                </div>

                {/* Close button */}
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-2 text-zinc-500 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        </div>
    );
}
