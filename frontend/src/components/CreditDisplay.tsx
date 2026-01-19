"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Coins, Plus, ChevronRight, Settings, Key, ChevronDown, X } from "lucide-react";
import { useCreditSystem } from "@/components/CreditGate";

interface CreditDisplayProps {
    isExpanded: boolean;
    onOpenSettings: () => void;
}

export function CreditDisplay({ isExpanded, onOpenSettings }: CreditDisplayProps) {
    const { credits, isLoading } = useCreditSystem();

    const isLowCredits = credits < 100;

    return (
        <div className="relative group/credit">
            <button
                onClick={onOpenSettings}
                className={`w-full flex items-center py-2.5 rounded-xl transition-all duration-200 ${isExpanded ? "gap-3 px-3 justify-start" : "px-0 justify-center"} ${isLowCredits
                    ? "bg-amber-500/10 border border-amber-500/20 hover:bg-amber-500/20"
                    : "hover:bg-white/5"
                    }`}
            >
                {/* Icon */}
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${isLowCredits
                    ? "bg-amber-500/20"
                    : "bg-lime-500/20"
                    }`}>
                    <Coins className={`w-4 h-4 ${isLowCredits ? "text-amber-400" : "text-lime-400"}`} />
                </div>

                {/* Content */}
                <AnimatePresence>
                    {isExpanded && (
                        <motion.div
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -10 }}
                            className="flex-1 flex items-center justify-between"
                        >
                            <div className="text-left">
                                <p className="text-[10px] text-zinc-500 uppercase tracking-wider font-medium">
                                    크레딧
                                </p>
                                <p className={`text-sm font-bold ${isLowCredits ? "text-amber-400" : "text-white"}`}>
                                    {isLoading ? "..." : credits.toLocaleString()}
                                </p>
                            </div>
                            <ChevronRight className="w-4 h-4 text-zinc-500" />
                        </motion.div>
                    )}
                </AnimatePresence>
            </button>

            {/* Collapsed Flyout */}
            {!isExpanded && (
                <div className="absolute left-[calc(100%+8px)] top-1/2 -translate-y-1/2 w-40
                               bg-[#1a1a1c] border border-white/10 rounded-xl shadow-xl 
                               opacity-0 invisible transform -translate-x-2 
                               group-hover/credit:opacity-100 group-hover/credit:visible group-hover/credit:translate-x-0 
                               transition-all duration-200 z-[60] p-3 
                               pointer-events-none group-hover/credit:pointer-events-auto
                               before:absolute before:inset-y-0 before:-left-4 before:w-4 before:content-['']">
                    <div className="text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">
                        크레딧
                    </div>
                    <p className={`text-lg font-bold ${isLowCredits ? "text-amber-400" : "text-lime-400"}`}>
                        {isLoading ? "..." : credits.toLocaleString()}
                    </p>
                    {isLowCredits && (
                        <p className="text-[10px] text-amber-400 mt-1">잔액이 부족합니다</p>
                    )}
                </div>
            )}
        </div>
    );
}

interface ProfileSettingsPanelProps {
    isOpen: boolean;
    onClose: () => void;
}

export function ProfileSettingsPanel({ isOpen, onClose }: ProfileSettingsPanelProps) {
    const { credits, breakdown, byokKey, setBYOKKey, showChargeModal } = useCreditSystem();
    const [showAdvanced, setShowAdvanced] = useState(false);
    const [geminiKey, setGeminiKey] = useState(byokKey || "");
    const [isSaving, setIsSaving] = useState(false);

    const handleSaveKey = async () => {
        setIsSaving(true);
        try {
            await setBYOKKey(geminiKey || null);
        } catch {
            // Silent fail - encryption might have failed
        } finally {
            setIsSaving(false);
        }
    };

    const handleClearKey = async () => {
        setGeminiKey("");
        await setBYOKKey(null);
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]"
                    />

                    {/* Panel */}
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="fixed left-16 top-0 h-screen w-80 bg-[#0a0a0b] border-r border-white/10 z-[101] flex flex-col shadow-2xl"
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
                            <h2 className="text-lg font-bold text-white">프로필 설정</h2>
                            <button
                                onClick={onClose}
                                className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-y-auto p-5 space-y-6">
                            {/* Credit Section */}
                            <div className="p-4 rounded-2xl bg-gradient-to-br from-lime-500/10 to-emerald-500/10 border border-lime-500/20">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="flex items-center gap-2">
                                        <Coins className="w-5 h-5 text-lime-400" />
                                        <span className="text-sm font-medium text-zinc-300">내 크레딧</span>
                                    </div>
                                    <span className="text-2xl font-bold text-lime-400">
                                        {credits.toLocaleString()}
                                    </span>
                                </div>

                                {/* Breakdown */}
                                {breakdown && (
                                    <div className="grid grid-cols-3 gap-2 mb-4 text-center">
                                        <div className="p-2 rounded-lg bg-black/30">
                                            <p className="text-[9px] text-zinc-500">구독</p>
                                            <p className="text-xs font-bold text-zinc-300">{breakdown.subscription}</p>
                                        </div>
                                        <div className="p-2 rounded-lg bg-black/30">
                                            <p className="text-[9px] text-zinc-500">충전</p>
                                            <p className="text-xs font-bold text-zinc-300">{breakdown.topup}</p>
                                        </div>
                                        <div className="p-2 rounded-lg bg-black/30">
                                            <p className="text-[9px] text-zinc-500">프로모</p>
                                            <p className="text-xs font-bold text-zinc-300">{breakdown.promo}</p>
                                        </div>
                                    </div>
                                )}

                                <button
                                    onClick={showChargeModal}
                                    className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-lime-500 hover:bg-lime-400 text-black font-bold text-sm transition-all shadow-[0_0_20px_rgba(132,204,22,0.3)] hover:shadow-[0_0_30px_rgba(132,204,22,0.5)]"
                                >
                                    <Plus className="w-4 h-4" />
                                    크레딧 충전하기
                                </button>
                                <p className="text-[10px] text-zinc-500 text-center mt-3">
                                    첫 충전 시 +20% 보너스 크레딧 증정!
                                </p>
                            </div>

                            {/* BYOK Status Indicator */}
                            {byokKey && (
                                <div className="p-3 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center gap-2">
                                    <Key className="w-4 h-4 text-violet-400" />
                                    <span className="text-xs text-violet-300 font-medium">내 API 키 사용 중</span>
                                    <span className="text-[10px] text-violet-400 ml-auto">크레딧 미차감</span>
                                </div>
                            )}

                            {/* Divider */}
                            <div className="border-t border-white/5" />

                            {/* Advanced Settings (Collapsed) */}
                            <div>
                                <button
                                    onClick={() => setShowAdvanced(!showAdvanced)}
                                    className="w-full flex items-center justify-between py-2 text-sm text-zinc-400 hover:text-white transition-colors"
                                >
                                    <span className="flex items-center gap-2">
                                        <Settings className="w-4 h-4" />
                                        고급 설정
                                    </span>
                                    <ChevronDown className={`w-4 h-4 transition-transform ${showAdvanced ? "rotate-180" : ""}`} />
                                </button>

                                <AnimatePresence>
                                    {showAdvanced && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: "auto", opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            className="overflow-hidden"
                                        >
                                            <div className="pt-4 space-y-4">
                                                {/* BYOK Section */}
                                                <div className="p-4 rounded-xl bg-zinc-900 border border-white/5">
                                                    <div className="flex items-center gap-2 mb-3">
                                                        <Key className="w-4 h-4 text-zinc-400" />
                                                        <span className="text-sm font-medium text-white">내 API 키 사용하기</span>
                                                    </div>
                                                    <p className="text-[11px] text-zinc-500 mb-3">
                                                        본인의 Gemini API 키를 입력하면 크레딧 차감 없이 사용할 수 있습니다.
                                                    </p>
                                                    <div className="space-y-2">
                                                        <label className="text-[10px] text-zinc-400 uppercase tracking-wider">
                                                            Gemini API Key
                                                        </label>
                                                        <input
                                                            type="password"
                                                            value={geminiKey}
                                                            onChange={(e) => setGeminiKey(e.target.value)}
                                                            placeholder="AIzaSy..."
                                                            className="w-full px-3 py-2.5 rounded-lg bg-black/50 border border-white/10 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-violet-500/50 transition-colors"
                                                        />
                                                        <div className="flex gap-2">
                                                            <button
                                                                onClick={handleSaveKey}
                                                                disabled={!geminiKey || isSaving}
                                                                className="flex-1 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
                                                            >
                                                                {isSaving ? "저장 중..." : "저장하기"}
                                                            </button>
                                                            {byokKey && (
                                                                <button
                                                                    onClick={handleClearKey}
                                                                    className="px-3 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm font-medium transition-colors"
                                                                >
                                                                    삭제
                                                                </button>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>

                                                <p className="text-[10px] text-zinc-600 text-center">
                                                    98%의 사용자가 크레딧을 사용합니다
                                                </p>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
