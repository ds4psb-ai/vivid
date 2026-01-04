"use client";

import { createContext, useContext, useState, useCallback, ReactNode, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Coins, Plus, AlertTriangle, X } from "lucide-react";
import { api } from "@/lib/api";
import { secureSet, secureGet, secureRemove, migratePlaintextToSecure } from "@/lib/secure-storage";

// ============================================
// Credit Context & Provider (실제 API 연동)
// ============================================

interface CreditContextType {
    credits: number;
    breakdown: {
        subscription: number;
        topup: number;
        promo: number;
    } | null;
    byokKey: string | null;
    isLoading: boolean;
    checkCredits: (amount: number) => Promise<boolean>;
    deductCredits: (amount: number, description: string) => Promise<boolean>;
    getApiKey: () => string | null;
    refreshCredits: () => Promise<void>;
    showChargeModal: () => void;
    setBYOKKey: (key: string | null) => Promise<void>;
}

const CreditContext = createContext<CreditContextType | null>(null);

export function useCreditSystem() {
    const context = useContext(CreditContext);
    if (!context) {
        throw new Error("useCreditSystem must be used within CreditProvider");
    }
    return context;
}

interface CreditProviderProps {
    children: ReactNode;
}

export function CreditProvider({ children }: CreditProviderProps) {
    const [credits, setCredits] = useState(0);
    const [breakdown, setBreakdown] = useState<CreditContextType["breakdown"]>(null);
    const [byokKey, setBYOKKey] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isChargeModalOpen, setIsChargeModalOpen] = useState(false);

    // Load BYOK key from secure storage (with migration from plaintext)
    useEffect(() => {
        const loadBYOKKey = async () => {
            // First, try to migrate any existing plaintext key
            await migratePlaintextToSecure("gemini_byok_key", "byok_gemini");

            // Then load from secure storage
            const savedKey = await secureGet("byok_gemini");
            if (savedKey) {
                setBYOKKey(savedKey);
            }
        };
        loadBYOKKey().catch(() => {
            // Silent fail - key not found or decryption failed
        });
    }, []);

    // Fetch credits from backend API
    const refreshCredits = useCallback(async () => {
        setIsLoading(true);
        try {
            const data = await api.getCreditsBalance();
            const total = data.balance ?? (
                (data.subscription_credits ?? 0) +
                (data.topup_credits ?? 0) +
                (data.promo_credits ?? 0)
            );
            setCredits(total);
            setBreakdown({
                subscription: data.subscription_credits ?? 0,
                topup: data.topup_credits ?? 0,
                promo: data.promo_credits ?? 0,
            });
        } catch {
            // API error - keep last known value
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Initial fetch
    useEffect(() => {
        void refreshCredits();
    }, [refreshCredits]);

    // Check if user has enough credits
    const checkCredits = useCallback(async (amount: number): Promise<boolean> => {
        // If BYOK key exists, always return true
        if (byokKey) return true;
        return credits >= amount;
    }, [credits, byokKey]);

    // Deduct credits (returns false if insufficient)
    const deductCredits = useCallback(async (amount: number, description: string): Promise<boolean> => {
        // If BYOK key exists, no deduction needed
        if (byokKey) return true;

        if (credits < amount) {
            setIsChargeModalOpen(true);
            return false;
        }

        try {
            // Call backend API to deduct
            await api.deductCredits({
                user_id: "", // Will be filled by backend from session
                amount,
                description,
            });

            // Refresh balance after deduction
            await refreshCredits();
            return true;
        } catch {
            // Deduction failed
            setIsChargeModalOpen(true);
            return false;
        }
    }, [credits, byokKey, refreshCredits]);

    // Get API key (BYOK or null for server-side key)
    const getApiKey = useCallback((): string | null => {
        return byokKey;
    }, [byokKey]);

    const showChargeModal = useCallback(() => {
        setIsChargeModalOpen(true);
    }, []);

    // Save BYOK key to secure storage (encrypted)
    const handleSetBYOKKey = useCallback(async (key: string | null) => {
        setBYOKKey(key);
        if (key) {
            await secureSet("byok_gemini", key);
        } else {
            secureRemove("byok_gemini");
        }
    }, []);

    return (
        <CreditContext.Provider
            value={{
                credits,
                breakdown,
                byokKey,
                isLoading,
                checkCredits,
                deductCredits,
                getApiKey,
                refreshCredits,
                showChargeModal,
                setBYOKKey: handleSetBYOKKey,
            }}
        >
            {children}

            {/* Credit Charge Modal */}
            <CreditChargeModal
                isOpen={isChargeModalOpen}
                onClose={() => setIsChargeModalOpen(false)}
                onTopup={refreshCredits}
            />
        </CreditContext.Provider>
    );
}

// ============================================
// Credit Gate Component
// ============================================

interface CreditGateProps {
    cost: number;
    children: (execute: () => Promise<void>) => ReactNode;
    onExecute: () => Promise<void>;
    featureName?: string;
}

/**
 * CreditGate wraps AI features that require credits.
 * It checks credits before execution and shows charge modal if insufficient.
 */
export function CreditGate({ cost, children, onExecute, featureName = "이 기능" }: CreditGateProps) {
    const { checkCredits, deductCredits, showChargeModal } = useCreditSystem();
    const [isExecuting, setIsExecuting] = useState(false);

    const execute = async () => {
        if (isExecuting) return;

        setIsExecuting(true);
        try {
            const hasCredits = await checkCredits(cost);
            if (!hasCredits) {
                showChargeModal();
                return;
            }

            // Deduct first, then execute
            const deducted = await deductCredits(cost, `${featureName} 사용`);
            if (!deducted) return;

            await onExecute();
        } finally {
            setIsExecuting(false);
        }
    };

    return <>{children(execute)}</>;
}

// ============================================
// Credit Charge Modal
// ============================================

interface CreditChargeModalProps {
    isOpen: boolean;
    onClose: () => void;
    onTopup?: () => void;
}

export function CreditChargeModal({ isOpen, onClose, onTopup }: CreditChargeModalProps) {
    const [selectedPackage, setSelectedPackage] = useState<number | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);

    const CREDIT_PACKAGES = [
        { credits: 500, price: 5000, label: "스타터", bonus: 0 },
        { credits: 1500, price: 12000, label: "베이직", bonus: 10, popular: true },
        { credits: 5000, price: 35000, label: "프로", bonus: 20 },
    ];

    const handlePurchase = async () => {
        if (selectedPackage === null) return;

        setIsProcessing(true);
        try {
            const pkg = CREDIT_PACKAGES[selectedPackage];
            const totalCredits = pkg.credits + Math.floor(pkg.credits * pkg.bonus / 100);

            // TODO: 결제 시스템 연동 (아캐인 법인 별도 서비스)
            // 현재는 Mock topup
            await api.topupCredits({
                amount: totalCredits,
                pack_id: pkg.label,
            });

            onTopup?.();
            onClose();
        } catch {
            // Payment processing failed
        } finally {
            setIsProcessing(false);
        }
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
                        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[200]"
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-[#0a0a0b] border border-white/10 rounded-3xl shadow-2xl z-[201] overflow-hidden"
                    >
                        {/* Header */}
                        <div className="relative px-6 pt-6 pb-4 border-b border-white/5">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center">
                                    <AlertTriangle className="w-5 h-5 text-amber-400" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-bold text-white">크레딧이 부족해요</h2>
                                    <p className="text-sm text-zinc-400">충전하고 계속 사용하세요!</p>
                                </div>
                            </div>
                            <button
                                onClick={onClose}
                                className="absolute top-4 right-4 p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Packages */}
                        <div className="p-6 space-y-3">
                            {CREDIT_PACKAGES.map((pkg, index) => (
                                <button
                                    key={pkg.credits}
                                    onClick={() => setSelectedPackage(index)}
                                    className={`w-full p-4 rounded-2xl border transition-all text-left relative ${selectedPackage === index
                                        ? "bg-lime-500/20 border-lime-500/50 ring-2 ring-lime-500/30"
                                        : pkg.popular
                                            ? "bg-lime-500/10 border-lime-500/30 hover:border-lime-500/50"
                                            : "bg-white/5 border-white/10 hover:border-white/20"
                                        }`}
                                >
                                    {pkg.popular && (
                                        <span className="absolute -top-2 right-4 px-2 py-0.5 rounded-full bg-lime-500 text-black text-[10px] font-bold">
                                            인기
                                        </span>
                                    )}
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="text-sm font-medium text-zinc-400">{pkg.label}</p>
                                            <p className="text-xl font-bold text-white flex items-center gap-2">
                                                <Coins className="w-5 h-5 text-lime-400" />
                                                {pkg.credits.toLocaleString()}
                                                {pkg.bonus > 0 && (
                                                    <span className="text-xs font-medium text-lime-400">
                                                        +{pkg.bonus}% 보너스
                                                    </span>
                                                )}
                                            </p>
                                        </div>
                                        <p className="text-lg font-bold text-white">
                                            ₩{pkg.price.toLocaleString()}
                                        </p>
                                    </div>
                                </button>
                            ))}
                        </div>

                        {/* Footer */}
                        <div className="px-6 pb-6">
                            <button
                                onClick={handlePurchase}
                                disabled={selectedPackage === null || isProcessing}
                                className="w-full py-3.5 rounded-xl bg-lime-500 hover:bg-lime-400 disabled:opacity-50 disabled:cursor-not-allowed text-black font-bold transition-all shadow-[0_0_20px_rgba(132,204,22,0.3)] hover:shadow-[0_0_30px_rgba(132,204,22,0.5)] flex items-center justify-center gap-2"
                            >
                                <Plus className="w-5 h-5" />
                                {isProcessing ? "처리 중..." : "선택한 패키지 결제하기"}
                            </button>
                            <p className="text-[10px] text-zinc-600 text-center mt-3">
                                결제 시스템 연동 예정 (아캐인 법인)
                            </p>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
