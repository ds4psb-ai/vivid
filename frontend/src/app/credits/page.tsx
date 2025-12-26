"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
    Wallet,
    History,
    TrendingUp,
    Gift,
    Sparkles,
    ArrowUpRight,
    ArrowDownLeft,
    Plus,
    Download,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";
import { api, type CreditTransaction } from "@/lib/api";
import { normalizeApiError } from "@/lib/errors";

interface CreditPack {
    id: string;
    name: string;
    credits: number;
    price: number;
    badge: string;
}

const TRANSACTION_CONFIG: Record<string, { bgClass: string; icon: React.ElementType; iconClass: string }> = {
    usage: { bgClass: "bg-rose-500/10", icon: ArrowUpRight, iconClass: "text-rose-400" },
    topup: { bgClass: "bg-sky-500/10", icon: ArrowDownLeft, iconClass: "text-sky-400" },
    reward: { bgClass: "bg-emerald-500/10", icon: Gift, iconClass: "text-emerald-400" },
    promo: { bgClass: "bg-amber-500/10", icon: Sparkles, iconClass: "text-amber-400" },
    refund: { bgClass: "bg-slate-500/10", icon: ArrowDownLeft, iconClass: "text-slate-300" },
};

export default function CreditsPage() {
    const { language } = useLanguage();
    const [balance, setBalance] = useState(0);
    const [transactions, setTransactions] = useState<CreditTransaction[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isToppingUp, setIsToppingUp] = useState<string | null>(null);
    const [loadError, setLoadError] = useState<string | null>(null);
    const userId = process.env.NEXT_PUBLIC_USER_ID || "demo-user";

    const creditPacks = useMemo<CreditPack[]>(() => [
        {
            id: "pack-1",
            name: language === "ko" ? "스타터" : "Starter",
            credits: 500,
            price: 9,
            badge: "",
        },
        {
            id: "pack-2",
            name: language === "ko" ? "프로" : "Pro",
            credits: 2000,
            price: 29,
            badge: language === "ko" ? "인기" : "Popular",
        },
        {
            id: "pack-3",
            name: language === "ko" ? "스튜디오" : "Studio",
            credits: 5000,
            price: 59,
            badge: language === "ko" ? "최고 효율" : "Best Value",
        },
    ], [language]);

    const loadErrorFallback =
        language === "ko" ? "크레딧 데이터를 불러오지 못했습니다." : "Unable to load credits.";
    const topupErrorFallback =
        language === "ko" ? "크레딧 충전에 실패했습니다." : "Unable to top up credits.";

    const loadCredits = useCallback(async () => {
        setIsLoading(true);
        setLoadError(null);
        try {
            const [balanceData, ledger] = await Promise.all([
                api.getCreditsBalance(userId),
                api.getCreditsTransactions(userId, 20, 0),
            ]);
            setBalance(balanceData.balance);
            setTransactions(ledger.transactions);
        } catch (err) {
            setLoadError(normalizeApiError(err, loadErrorFallback));
        } finally {
            setIsLoading(false);
        }
    }, [userId, loadErrorFallback]);

    useEffect(() => {
        void loadCredits();
    }, [loadCredits]);

    const handleTopUpScroll = useCallback(() => {
        if (typeof document === "undefined") return;
        document.getElementById("credit-packs-heading")?.scrollIntoView({
            behavior: "smooth",
            block: "start",
        });
    }, []);

    const handleTopUp = useCallback(
        async (pack: CreditPack) => {
            setIsToppingUp(pack.id);
            try {
                await api.topupCredits(pack.credits, pack.id, userId);
                await loadCredits();
            } catch (err) {
                setLoadError(normalizeApiError(err, topupErrorFallback));
            } finally {
                setIsToppingUp(null);
            }
        },
        [loadCredits, topupErrorFallback, userId]
    );

    // Calculate stats
    const usedThisMonth = useMemo(() => {
        const now = new Date();
        return transactions
            .filter((tx) => {
                if (tx.event_type !== "usage") return false;
                const ts = new Date(tx.created_at);
                return ts.getFullYear() === now.getFullYear() && ts.getMonth() === now.getMonth();
            })
            .reduce((sum, tx) => sum + Math.abs(tx.amount), 0);
    }, [transactions]);

    const earnedAffiliate = useMemo(
        () =>
            transactions
                .filter((tx) => tx.event_type === "reward")
                .reduce((sum, tx) => sum + tx.amount, 0),
        [transactions]
    );

    const totalRuns = useMemo(
        () => transactions.filter((tx) => tx.event_type === "usage").length,
        [transactions]
    );

    const labels = {
        title: language === "ko" ? "크레딧" : "Credits",
        subtitle: language === "ko" ? "크레딧 잔액 및 구매 내역 관리" : "Manage your credit balance and purchase history",
        availableBalance: language === "ko" ? "사용 가능 잔액" : "Available Balance",
        credits: language === "ko" ? "크레딧" : "credits",
        topUp: language === "ko" ? "충전하기" : "Top Up",
        loadError: language === "ko" ? "크레딧 데이터를 불러오지 못했습니다." : "Unable to load credits.",
        topupError: language === "ko" ? "크레딧 충전에 실패했습니다." : "Unable to top up credits.",
        usedThisMonth: language === "ko" ? "이번 달 사용" : "Used This Month",
        earnedAffiliate: language === "ko" ? "획득 (제휴)" : "Earned (Affiliate)",
        totalRuns: language === "ko" ? "총 실행 횟수" : "Total Runs",
        creditPacks: language === "ko" ? "크레딧 팩" : "Credit Packs",
        recentTransactions: language === "ko" ? "최근 거래 내역" : "Recent Transactions",
        exportCsv: language === "ko" ? "CSV 내보내기" : "Export CSV",
        runType: language === "ko" ? "실행 유형" : "Run type",
        resourceId: language === "ko" ? "대상" : "Resource",
        inviteTitle: language === "ko" ? "친구 초대 + 무료 크레딧" : "Invite + Earn Credits",
        inviteDesc:
            language === "ko"
                ? "초대 링크로 크레딧을 받고, 팀원도 보너스를 받습니다."
                : "Share your invite link to earn bonus credits for both sides.",
        inviteCta: language === "ko" ? "제휴 페이지로 이동" : "Go to Affiliate",
        loadingTransactions: language === "ko" ? "거래 내역 불러오는 중..." : "Loading transactions...",
        noTransactions: language === "ko" ? "거래 내역이 없습니다." : "No transactions yet.",
    };

    const handleExportCsv = useCallback(() => {
        if (transactions.length === 0) return;
        const headers = [
            "created_at",
            "event_type",
            "amount",
            "balance_snapshot",
            "description",
            "capsule_run_id",
            "run_type",
            "meta_json",
        ];
        const escapeValue = (value: string) => `"${value.replace(/"/g, '""')}"`;
        const rows = transactions.map((tx) => [
            tx.created_at,
            tx.event_type,
            String(tx.amount),
            String(tx.balance_snapshot),
            tx.description || "",
            tx.capsule_run_id || "",
            typeof tx.meta?.run_type === "string" ? tx.meta.run_type : "",
            JSON.stringify(tx.meta || {}),
        ]);
        const csv = [
            headers.join(","),
            ...rows.map((row) => row.map(escapeValue).join(",")),
        ].join("\n");
        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        const today = new Date().toISOString().slice(0, 10);
        link.href = url;
        link.download = `vivid_credits_${today}.csv`;
        link.click();
        URL.revokeObjectURL(url);
    }, [transactions]);

    return (
        <AppShell showTopBar={false} creditBalance={balance}>
            <div className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
                <div className="mx-auto max-w-4xl">
                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-6 sm:mb-8"
                    >
                        <h1 className="text-xl font-bold text-[var(--fg-0)] sm:text-2xl">{labels.title}</h1>
                        <p className="mt-1 text-sm text-[var(--fg-muted)] sm:text-base">{labels.subtitle}</p>
                    </motion.div>
                    {loadError && (
                        <div className="mb-4 rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                            {loadError}
                        </div>
                    )}

                    {/* Balance Card */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="mb-6 rounded-xl border border-white/10 bg-gradient-to-br from-sky-500/10 via-transparent to-amber-500/10 p-4 sm:mb-8 sm:rounded-2xl sm:p-6"
                    >
                        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                            <div>
                                <div className="flex items-center gap-2 text-xs text-[var(--fg-muted)] sm:text-sm">
                                    <Wallet className="h-4 w-4" aria-hidden="true" />
                                    {labels.availableBalance}
                                </div>
                                <div className="mt-2 text-3xl font-bold text-[var(--fg-0)] sm:text-4xl">
                                    {isLoading ? "..." : balance.toLocaleString()}
                                    <span className="ml-2 text-base font-normal text-[var(--fg-muted)] sm:text-lg">
                                        {labels.credits}
                                    </span>
                                </div>
                            </div>
                            <button
                                onClick={handleTopUpScroll}
                                disabled={isLoading}
                                className="flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-sky-500 to-sky-600 px-5 py-3 font-semibold text-white shadow-lg shadow-sky-500/25 transition-all hover:from-sky-400 hover:to-sky-500 disabled:opacity-60 disabled:cursor-not-allowed"
                                aria-label={labels.topUp}
                            >
                                <Plus className="h-4 w-4" aria-hidden="true" />
                                {labels.topUp}
                            </button>
                        </div>

                        {/* Stats Row */}
                        <div className="mt-4 grid grid-cols-3 gap-3 border-t border-white/10 pt-4 sm:mt-6 sm:gap-4 sm:pt-6">
                            <div>
                                <div className="text-[10px] text-[var(--fg-muted)] sm:text-xs">{labels.usedThisMonth}</div>
                                <div className="mt-1 flex items-center gap-1">
                                    <TrendingUp className="h-3 w-3 text-amber-400 sm:h-4 sm:w-4" aria-hidden="true" />
                                    <span className="text-base font-semibold text-[var(--fg-0)] sm:text-lg">{usedThisMonth}</span>
                                </div>
                            </div>
                            <div>
                                <div className="text-[10px] text-[var(--fg-muted)] sm:text-xs">{labels.earnedAffiliate}</div>
                                <div className="mt-1 flex items-center gap-1">
                                    <Gift className="h-3 w-3 text-emerald-400 sm:h-4 sm:w-4" aria-hidden="true" />
                                    <span className="text-base font-semibold text-[var(--fg-0)] sm:text-lg">{earnedAffiliate}</span>
                                </div>
                            </div>
                            <div>
                                <div className="text-[10px] text-[var(--fg-muted)] sm:text-xs">{labels.totalRuns}</div>
                                <div className="mt-1 flex items-center gap-1">
                                    <Sparkles className="h-3 w-3 text-sky-400 sm:h-4 sm:w-4" aria-hidden="true" />
                                    <span className="text-base font-semibold text-[var(--fg-0)] sm:text-lg">{totalRuns}</span>
                                </div>
                            </div>
                        </div>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                        className="mb-6 rounded-2xl border border-white/10 bg-gradient-to-br from-emerald-500/10 via-transparent to-sky-500/10 p-5 sm:mb-8 sm:p-6"
                    >
                        <div className="flex flex-wrap items-center justify-between gap-4">
                            <div>
                                <div className="flex items-center gap-2 text-xs text-[var(--fg-muted)] sm:text-sm">
                                    <Gift className="h-4 w-4" aria-hidden="true" />
                                    {labels.inviteTitle}
                                </div>
                                <div className="mt-2 text-sm text-[var(--fg-muted)] sm:text-base">
                                    {labels.inviteDesc}
                                </div>
                            </div>
                            <a
                                href="/affiliate"
                                className="inline-flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-xs font-semibold text-emerald-200 transition-colors hover:bg-emerald-500/20"
                            >
                                {labels.inviteCta}
                                <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
                            </a>
                        </div>
                    </motion.div>

                    {/* Credit Packs */}
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="mb-6 sm:mb-8"
                        aria-labelledby="credit-packs-heading"
                    >
                        <h2 id="credit-packs-heading" className="mb-3 text-base font-semibold text-[var(--fg-0)] sm:mb-4 sm:text-lg">
                            {labels.creditPacks}
                        </h2>
                        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 sm:gap-4">
                            {creditPacks.map((pack) => (
                                <div
                                    key={pack.id}
                                    className="group relative flex flex-col rounded-xl border border-white/10 bg-slate-900/60 p-5 transition-all duration-300 hover:-translate-y-1 hover:border-sky-500/30 hover:bg-slate-800/80 hover:shadow-xl hover:shadow-sky-500/10"
                                >
                                    {pack.badge && (
                                        <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-sky-500 to-amber-500 px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-white shadow-lg shadow-sky-900/50">
                                            {pack.badge}
                                        </div>
                                    )}
                                    <div className="mb-2 text-sm font-medium text-slate-400 group-hover:text-sky-300 transition-colors">{pack.name}</div>
                                    <div className="flex items-baseline gap-1">
                                        <span className="text-3xl font-bold text-white tracking-tight">{pack.credits.toLocaleString()}</span>
                                        <span className="text-xs text-slate-500 font-medium uppercase tracking-wider">{labels.credits}</span>
                                    </div>

                                    <div className="mt-6 pt-6 border-t border-white/5">
                                        <button
                                            onClick={() => handleTopUp(pack)}
                                            disabled={isLoading || isToppingUp === pack.id}
                                            className="w-full rounded-lg bg-sky-500/10 py-2.5 text-sm font-semibold text-sky-400 transition-all group-hover:bg-sky-500 group-hover:text-white group-hover:shadow-lg group-hover:shadow-sky-500/25 disabled:opacity-60 disabled:cursor-not-allowed"
                                            aria-label={`${pack.name} pack for $${pack.price}`}
                                        >
                                            {isToppingUp === pack.id ? "Processing..." : `$${pack.price}`}
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </motion.section>

                    {/* Transaction History */}
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        aria-labelledby="transactions-heading"
                    >
                        <div className="mb-3 flex flex-wrap items-center justify-between gap-3 sm:mb-4">
                            <div className="flex items-center gap-2">
                                <History className="h-4 w-4 text-[var(--fg-muted)]" aria-hidden="true" />
                                <h2 id="transactions-heading" className="text-base font-semibold text-[var(--fg-0)] sm:text-lg">
                                    {labels.recentTransactions}
                                </h2>
                            </div>
                            <button
                                type="button"
                                onClick={handleExportCsv}
                                disabled={transactions.length === 0}
                                className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-slate-200 transition-colors hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
                                aria-label={labels.exportCsv}
                            >
                                <Download className="h-4 w-4" aria-hidden="true" />
                                {labels.exportCsv}
                            </button>
                        </div>
                        <div className="overflow-hidden rounded-xl border border-white/10 bg-slate-900/40 backdrop-blur-sm">
                            <div className="divide-y divide-white/5">
                                {isLoading ? (
                                    <div className="px-5 py-6 text-sm text-slate-500">{labels.loadingTransactions}</div>
                                ) : transactions.length === 0 ? (
                                    <div className="px-5 py-6 text-sm text-slate-500">{labels.noTransactions}</div>
                                ) : (
                                    transactions.map((tx) => {
                                        const config = TRANSACTION_CONFIG[tx.event_type] || TRANSACTION_CONFIG.usage;
                                        const TxIcon = config.icon;
                                        const createdAt = new Date(tx.created_at);
                                        const runType = typeof tx.meta?.run_type === "string" ? tx.meta.run_type : "";
                                        const resourceId =
                                            (typeof tx.meta?.capsule_id === "string" && tx.meta.capsule_id) ||
                                            (typeof tx.meta?.canvas_id === "string" && tx.meta.canvas_id) ||
                                            "";
                                        const typeBadge =
                                            tx.event_type === "topup"
                                                ? "border-sky-500/20 bg-sky-500/10 text-sky-400"
                                                : tx.event_type === "reward"
                                                    ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
                                                    : tx.event_type === "promo"
                                                        ? "border-amber-500/20 bg-amber-500/10 text-amber-400"
                                                        : "border-slate-700 bg-slate-800 text-slate-400";
                                        return (
                                            <div
                                                key={tx.id}
                                                className="group flex items-center justify-between px-5 py-4 transition-colors hover:bg-white/5"
                                            >
                                                <div className="flex items-center gap-4">
                                                    <div className={`flex h-10 w-10 items-center justify-center rounded-full ${config.bgClass} transition-transform group-hover:scale-110`}>
                                                        <TxIcon className={`h-5 w-5 ${config.iconClass}`} aria-hidden="true" />
                                                    </div>
                                                    <div>
                                                        <div className="font-medium text-slate-200 group-hover:text-white transition-colors">
                                                            {tx.description || "Credit transaction"}
                                                        </div>
                                                        <div className="flex items-center gap-2 mt-0.5">
                                                            <span className="text-xs font-mono text-slate-500">
                                                                {Number.isNaN(createdAt.getTime())
                                                                    ? "--"
                                                                    : createdAt.toLocaleDateString(
                                                                        language === "ko" ? "ko-KR" : "en-US",
                                                                        { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }
                                                                    )}
                                                            </span>
                                                            <span className={`inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide border ${typeBadge}`}>
                                                                {tx.event_type}
                                                            </span>
                                                        </div>
                                                        {(runType || resourceId) && (
                                                            <div className="mt-1 text-[10px] text-slate-500">
                                                                {runType && (
                                                                    <span className="mr-2">{labels.runType}: {runType}</span>
                                                                )}
                                                                {resourceId && (
                                                                    <span>{labels.resourceId}: {resourceId}</span>
                                                                )}
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className={`text-sm font-bold font-mono tracking-tight ${tx.amount > 0 ? "text-emerald-400" : "text-rose-400"
                                                    }`}>
                                                    {tx.amount > 0 ? "+" : ""}{tx.amount}
                                                </div>
                                            </div>
                                        );
                                    })
                                )}
                            </div>
                        </div>
                    </motion.section>
                </div>
            </div>
        </AppShell>
    );
}
