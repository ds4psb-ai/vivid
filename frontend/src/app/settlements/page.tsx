"use client";

/**
 * User Settlement Dashboard
 * 
 * Shows user's revenue earnings from tool ownership:
 * - Summary stats (total earned, pending, avg)
 * - Payout history with status
 * - Tool breakdown
 * - Dispute option
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
    DollarSign,
    TrendingUp,
    Clock,
    CheckCircle,
    AlertTriangle,
    XCircle,
    ChevronRight,
    RefreshCw,
    Loader2,
    Wallet,
    PieChart,
    History,
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// =============================================================================
// Types
// =============================================================================

interface PayoutSummary {
    period_days: number;
    total_payouts: number;
    total_earned: number;
    avg_per_payout: number;
    pending_amount: number;
}

interface Payout {
    id: string;
    settlement_id: string;
    recipient_id: string;
    recipient_tool_key: string | null;
    amount: number;
    share_type: string;
    share_rate: number;
    lineage_position: number;
    status: string;
    credited_at: string | null;
    created_at: string;
}

// =============================================================================
// API Functions
// =============================================================================

async function fetchWithAuth(url: string, options: RequestInit = {}) {
    const token = localStorage.getItem("token");
    const res = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
}

async function getSettlementSummary(days: number = 30): Promise<PayoutSummary> {
    return fetchWithAuth(`${API_BASE_URL}/api/v1/settlements/my/summary?days=${days}`);
}

async function getMyPayouts(days: number = 30): Promise<Payout[]> {
    return fetchWithAuth(`${API_BASE_URL}/api/v1/settlements/my?days=${days}`);
}

// =============================================================================
// Status Badge Component
// =============================================================================

function StatusBadge({ status }: { status: string }) {
    const config: Record<string, { icon: typeof CheckCircle; className: string; label: string }> = {
        credited: {
            icon: CheckCircle,
            className: "bg-green-500/10 text-green-400 border-green-500/30",
            label: "Credited",
        },
        pending: {
            icon: Clock,
            className: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
            label: "Pending",
        },
        failed: {
            icon: XCircle,
            className: "bg-red-500/10 text-red-400 border-red-500/30",
            label: "Failed",
        },
        reversed: {
            icon: AlertTriangle,
            className: "bg-gray-500/10 text-gray-400 border-gray-500/30",
            label: "Reversed",
        },
    };

    const { icon: Icon, className, label } = config[status] || config.pending;

    return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full border ${className}`}>
            <Icon className="w-3.5 h-3.5" />
            {label}
        </span>
    );
}

// =============================================================================
// Summary Cards
// =============================================================================

function SummaryCards({ summary, loading }: { summary: PayoutSummary | null; loading: boolean }) {
    if (loading) {
        return (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4 animate-pulse">
                        <div className="h-4 w-20 bg-gray-700 rounded mb-2"></div>
                        <div className="h-8 w-16 bg-gray-700 rounded"></div>
                    </div>
                ))}
            </div>
        );
    }

    if (!summary) return null;

    const stats = [
        {
            label: "Total Earned",
            value: summary.total_earned.toLocaleString(),
            subValue: `${summary.period_days}일`,
            icon: DollarSign,
            color: "text-emerald-400",
            bgColor: "bg-emerald-500/10",
        },
        {
            label: "Pending",
            value: summary.pending_amount.toLocaleString(),
            icon: Clock,
            color: "text-yellow-400",
            bgColor: "bg-yellow-500/10",
        },
        {
            label: "Payouts",
            value: summary.total_payouts.toString(),
            icon: TrendingUp,
            color: "text-blue-400",
            bgColor: "bg-blue-500/10",
        },
        {
            label: "Average",
            value: summary.avg_per_payout.toFixed(1),
            subValue: "credits/payout",
            icon: PieChart,
            color: "text-purple-400",
            bgColor: "bg-purple-500/10",
        },
    ];

    return (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {stats.map((stat) => (
                <div
                    key={stat.label}
                    className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4"
                >
                    <div className="flex items-center gap-2 mb-2">
                        <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                            <stat.icon className={`w-4 h-4 ${stat.color}`} />
                        </div>
                        <span className="text-sm text-gray-400">{stat.label}</span>
                    </div>
                    <div className="text-2xl font-bold text-white">{stat.value}</div>
                    {stat.subValue && (
                        <div className="text-xs text-gray-500 mt-1">{stat.subValue}</div>
                    )}
                </div>
            ))}
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
                    {[1, 2, 3, 4, 5].map((i) => (
                        <div key={i} className="bg-gray-900/50 rounded-lg p-4 animate-pulse">
                            <div className="h-4 w-32 bg-gray-700 rounded mb-2"></div>
                            <div className="h-3 w-24 bg-gray-700/50 rounded"></div>
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
                <div className="text-center py-12">
                    <Wallet className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                    <h4 className="text-gray-400 text-lg mb-2">No Payouts Yet</h4>
                    <p className="text-gray-500 text-sm">
                        Create and share tools to start earning revenue
                    </p>
                </div>
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
                                    <StatusBadge status={payout.status} />
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

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [summaryData, payoutsData] = await Promise.all([
                getSettlementSummary(periodDays),
                getMyPayouts(periodDays),
            ]);
            setSummary(summaryData);
            setPayouts(payoutsData);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load data");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [periodDays]);

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
                            <p className="text-gray-400 text-sm">
                                Revenue from your tool contributions
                            </p>
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
