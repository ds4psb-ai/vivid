"use client";

/**
 * User Settlement Dashboard
 * 
 * Shows user's revenue earnings using shared component library.
 */

import { useState, useEffect, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import {
    DollarSign,
    TrendingUp,
    Clock,
    ChevronRight,
    RefreshCw,
    Wallet,
    PieChart,
    History,
    AlertTriangle,
} from "lucide-react";

// Shared imports
import { fetchWithAuth } from "@/lib/api-client";
import { StatusBadge, StatCard, EmptyState } from "@/components/shared";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Payout, PayoutSummary } from "@/types/api.types";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";

// =============================================================================
// Labels
// =============================================================================

const getLabels = (language: "ko" | "en") => ({
    title: language === "ko" ? "내 수익" : "My Earnings",
    subtitle: language === "ko" ? "도구 기여로 얻은 수익" : "Revenue from your tool contributions",
    totalEarned: language === "ko" ? "총 수익" : "Total Earned",
    pending: language === "ko" ? "대기 중" : "Pending",
    payouts: language === "ko" ? "정산" : "Payouts",
    average: language === "ko" ? "평균" : "Average",
    creditsPerPayout: language === "ko" ? "크레딧/정산" : "credits/payout",
    days: language === "ko" ? "일" : "days",
    payoutHistory: language === "ko" ? "정산 내역" : "Payout History",
    noPayoutsTitle: language === "ko" ? "정산 내역 없음" : "No Payouts Yet",
    noPayoutsDesc: language === "ko" ? "도구를 만들고 공유하여 수익을 올리세요" : "Create and share tools to start earning revenue",
    credits: language === "ko" ? "크레딧" : "credits",
    unknownTool: language === "ko" ? "알 수 없는 도구" : "Unknown tool",
    last7Days: language === "ko" ? "최근 7일" : "Last 7 days",
    last30Days: language === "ko" ? "최근 30일" : "Last 30 days",
    last90Days: language === "ko" ? "최근 90일" : "Last 90 days",
    lastYear: language === "ko" ? "최근 1년" : "Last year",
    retry: language === "ko" ? "다시 시도" : "Retry",
    failedToLoad: language === "ko" ? "데이터를 불러오지 못했습니다" : "Failed to load data",
});

// =============================================================================
// Summary Cards
// =============================================================================

function SummaryCards({ summary, loading, labels }: { summary: PayoutSummary | null; loading: boolean; labels: ReturnType<typeof getLabels> }) {
    if (loading) {
        return (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                {[1, 2, 3, 4].map((i) => (
                    <Card key={i} className="border border-white/5 bg-[var(--surface-1)]/70 animate-pulse">
                        <CardContent className="p-5">
                            <div className="h-4 w-20 bg-white/10 rounded mb-3" />
                            <div className="h-8 w-16 bg-white/10 rounded" />
                        </CardContent>
                    </Card>
                ))}
            </div>
        );
    }

    if (!summary) return null;

    return (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard
                title={labels.totalEarned}
                value={summary.total_earned.toLocaleString()}
                icon={DollarSign}
                color="green"
                subtitle={`${summary.period_days} ${labels.days}`}
            />
            <StatCard
                title={labels.pending}
                value={summary.pending_amount.toLocaleString()}
                icon={Clock}
                color="yellow"
            />
            <StatCard
                title={labels.payouts}
                value={summary.total_payouts}
                icon={TrendingUp}
                color="blue"
            />
            <StatCard
                title={labels.average}
                value={summary.avg_per_payout.toFixed(1)}
                icon={PieChart}
                color="purple"
                subtitle={labels.creditsPerPayout}
            />
        </div>
    );
}

// =============================================================================
// Payout History
// =============================================================================

function PayoutHistory({ payouts, loading, labels }: { payouts: Payout[]; loading: boolean; labels: ReturnType<typeof getLabels> }) {
    const router = useRouter();

    if (loading) {
        return (
            <Card className="border border-white/5 bg-[var(--surface-1)]/70">
                <CardHeader className="pb-4">
                    <div className="flex items-center gap-2">
                        <History className="w-5 h-5 text-violet-400" />
                        <CardTitle className="text-base">{labels.payoutHistory}</CardTitle>
                    </div>
                </CardHeader>
                <CardContent className="space-y-3">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="rounded-lg border border-white/5 bg-[var(--surface-2)]/60 p-4 animate-pulse">
                            <div className="h-4 w-32 bg-white/10 rounded mb-2" />
                            <div className="h-3 w-24 bg-white/10 rounded" />
                        </div>
                    ))}
                </CardContent>
            </Card>
        );
    }

    if (payouts.length === 0) {
        return (
            <Card className="border border-white/5 bg-[var(--surface-1)]/70">
                <CardHeader className="pb-4">
                    <div className="flex items-center gap-2">
                        <History className="w-5 h-5 text-violet-400" />
                        <CardTitle className="text-base">{labels.payoutHistory}</CardTitle>
                    </div>
                </CardHeader>
                <CardContent>
                    <EmptyState
                        icon={Wallet}
                        title={labels.noPayoutsTitle}
                        description={labels.noPayoutsDesc}
                    />
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="border border-white/5 bg-[var(--surface-1)]/70">
            <CardHeader className="pb-4">
                <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                        <History className="w-5 h-5 text-violet-400" />
                        <CardTitle className="text-base">{labels.payoutHistory}</CardTitle>
                    </div>
                    <span className="text-sm text-[var(--fg-subtle)]">{payouts.length} {labels.payouts.toLowerCase()}</span>
                </div>
            </CardHeader>
            <CardContent className="space-y-3">
                {payouts.map((payout) => (
                    <div
                        key={payout.id}
                        onClick={() => router.push(`/settlements/${payout.settlement_id}`)}
                        className="rounded-lg border border-white/5 bg-[var(--surface-2)]/60 p-4 hover:border-violet-500/30 cursor-pointer transition-colors group"
                    >
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-[var(--fg-0)] font-medium">
                                        +{payout.amount.toLocaleString()} {labels.credits}
                                    </span>
                                    <StatusBadge status={payout.status === "credited" ? "completed" : payout.status} />
                                </div>
                                <div className="flex items-center gap-3 text-sm text-[var(--fg-subtle)]">
                                    <span>{payout.recipient_tool_key || labels.unknownTool}</span>
                                    <span>•</span>
                                    <span className="capitalize">{payout.share_type}</span>
                                    <span>•</span>
                                    <span>{new Date(payout.created_at).toLocaleDateString()}</span>
                                </div>
                            </div>
                            <ChevronRight className="w-5 h-5 text-[var(--fg-subtle)] group-hover:text-violet-400 transition-colors" />
                        </div>
                    </div>
                ))}
            </CardContent>
        </Card>
    );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function SettlementsPage() {
    const { language } = useLanguage();
    const labels = getLabels(language);
    const pathname = usePathname();
    const [summary, setSummary] = useState<PayoutSummary | null>(null);
    const [payouts, setPayouts] = useState<Payout[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [periodDays, setPeriodDays] = useState(30);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [summaryData, payoutsData] = await Promise.all([
                fetchWithAuth<PayoutSummary>(`/api/v1/settlements/my/summary?days=${periodDays}`),
                fetchWithAuth<Payout[]>(`/api/v1/settlements/my?days=${periodDays}`),
            ]);
            setSummary(summaryData);
            setPayouts(payoutsData);
        } catch (err) {
            setError(err instanceof Error ? err.message : labels.failedToLoad);
        } finally {
            setLoading(false);
        }
    }, [periodDays, labels.failedToLoad]);

    useEffect(() => {
        fetchData();
    }, [fetchData, pathname]);

    return (
        <AppShell showTopBar={false}>
            <div className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
                <div className="mx-auto max-w-4xl">
                    {/* Header */}
                    <div className="mb-6 sm:mb-8">
                        <h1 className="text-xl font-bold text-[var(--fg-0)] sm:text-2xl flex items-center gap-2">
                            <DollarSign className="w-6 h-6 text-emerald-400" />
                            {labels.title}
                        </h1>
                        <p className="mt-1 text-sm text-[var(--fg-muted)] sm:text-base">{labels.subtitle}</p>
                    </div>

                    {/* Period Selector */}
                    <div className="flex items-center justify-end gap-3 mb-6">
                        <select
                            value={periodDays}
                            onChange={(e) => setPeriodDays(Number(e.target.value))}
                            className="px-3 py-2 bg-[var(--bg-1)] border border-white/10 rounded-lg text-sm text-[var(--fg-0)]"
                        >
                            <option value={7}>{labels.last7Days}</option>
                            <option value={30}>{labels.last30Days}</option>
                            <option value={90}>{labels.last90Days}</option>
                            <option value={365}>{labels.lastYear}</option>
                        </select>
                        <button
                            onClick={fetchData}
                            disabled={loading}
                            className="p-2 text-[var(--fg-muted)] hover:text-[var(--fg-0)] hover:bg-white/5 rounded-lg transition-colors"
                        >
                            <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
                        </button>
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center gap-3">
                            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
                            <p className="text-red-300">{error}</p>
                            <button
                                onClick={fetchData}
                                className="ml-auto px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg text-sm"
                            >
                                {labels.retry}
                            </button>
                        </div>
                    )}

                    <SummaryCards summary={summary} loading={loading} labels={labels} />
                    <PayoutHistory payouts={payouts} loading={loading} labels={labels} />
                </div>
            </div>
        </AppShell>
    );
}
