"use client";

/**
 * User Settlement Dashboard
 * 
 * Shows user's revenue earnings using shared component library.
 */

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
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
import type { Payout, PayoutSummary } from "@/types/api.types";

// =============================================================================
// Summary Cards
// =============================================================================

function SummaryCards({ summary, loading }: { summary: PayoutSummary | null; loading: boolean }) {
    if (loading) {
        return (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-5 animate-pulse">
                        <div className="h-4 w-20 bg-gray-700 rounded mb-3" />
                        <div className="h-8 w-16 bg-gray-700 rounded" />
                    </div>
                ))}
            </div>
        );
    }

    if (!summary) return null;

    return (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard
                title="Total Earned"
                value={summary.total_earned.toLocaleString()}
                icon={DollarSign}
                color="green"
                subtitle={`${summary.period_days} days`}
            />
            <StatCard
                title="Pending"
                value={summary.pending_amount.toLocaleString()}
                icon={Clock}
                color="yellow"
            />
            <StatCard
                title="Payouts"
                value={summary.total_payouts}
                icon={TrendingUp}
                color="blue"
            />
            <StatCard
                title="Average"
                value={summary.avg_per_payout.toFixed(1)}
                icon={PieChart}
                color="purple"
                subtitle="credits/payout"
            />
        </div>
    );
}

// =============================================================================
// Payout History
// =============================================================================

function PayoutHistory({ payouts, loading }: { payouts: Payout[]; loading: boolean }) {
    const router = useRouter();

    if (loading) {
        return (
            <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
                <div className="flex items-center gap-2 mb-4">
                    <History className="w-5 h-5 text-gray-400" />
                    <h3 className="text-lg font-semibold">Payout History</h3>
                </div>
                <div className="space-y-3">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="bg-gray-900/50 rounded-lg p-4 animate-pulse">
                            <div className="h-4 w-32 bg-gray-700 rounded mb-2" />
                            <div className="h-3 w-24 bg-gray-700/50 rounded" />
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    if (payouts.length === 0) {
        return (
            <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
                <div className="flex items-center gap-2 mb-4">
                    <History className="w-5 h-5 text-gray-400" />
                    <h3 className="text-lg font-semibold">Payout History</h3>
                </div>
                <EmptyState
                    icon={Wallet}
                    title="No Payouts Yet"
                    description="Create and share tools to start earning revenue"
                />
            </div>
        );
    }

    return (
        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <History className="w-5 h-5 text-gray-400" />
                    <h3 className="text-lg font-semibold">Payout History</h3>
                </div>
                <span className="text-sm text-gray-500">{payouts.length} payouts</span>
            </div>

            <div className="space-y-3">
                {payouts.map((payout) => (
                    <div
                        key={payout.id}
                        onClick={() => router.push(`/settlements/${payout.settlement_id}`)}
                        className="bg-gray-900/50 rounded-lg p-4 hover:bg-gray-900/70 cursor-pointer transition-colors group"
                    >
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-white font-medium">
                                        +{payout.amount.toLocaleString()} credits
                                    </span>
                                    <StatusBadge status={payout.status === "credited" ? "completed" : payout.status} />
                                </div>
                                <div className="flex items-center gap-3 text-sm text-gray-500">
                                    <span>{payout.recipient_tool_key || "Unknown tool"}</span>
                                    <span>•</span>
                                    <span className="capitalize">{payout.share_type}</span>
                                    <span>•</span>
                                    <span>{new Date(payout.created_at).toLocaleDateString()}</span>
                                </div>
                            </div>
                            <ChevronRight className="w-5 h-5 text-gray-600 group-hover:text-purple-400 transition-colors" />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function SettlementsPage() {
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
            setError(err instanceof Error ? err.message : "Failed to load data");
        } finally {
            setLoading(false);
        }
    }, [periodDays]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return (
        <div className="min-h-screen bg-gray-900 text-white">
            {/* Header */}
            <div className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-10">
                <div className="max-w-6xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold flex items-center gap-2">
                                <DollarSign className="w-6 h-6 text-emerald-400" />
                                My Earnings
                            </h1>
                            <p className="text-gray-400 text-sm">Revenue from your tool contributions</p>
                        </div>
                        <div className="flex items-center gap-3">
                            <select
                                value={periodDays}
                                onChange={(e) => setPeriodDays(Number(e.target.value))}
                                className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm"
                            >
                                <option value={7}>Last 7 days</option>
                                <option value={30}>Last 30 days</option>
                                <option value={90}>Last 90 days</option>
                                <option value={365}>Last year</option>
                            </select>
                            <button
                                onClick={fetchData}
                                disabled={loading}
                                className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg"
                            >
                                <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-6xl mx-auto px-6 py-8">
                {error && (
                    <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center gap-3">
                        <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
                        <p className="text-red-300">{error}</p>
                        <button
                            onClick={fetchData}
                            className="ml-auto px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg text-sm"
                        >
                            Retry
                        </button>
                    </div>
                )}

                <SummaryCards summary={summary} loading={loading} />
                <PayoutHistory payouts={payouts} loading={loading} />
            </div>
        </div>
    );
}
