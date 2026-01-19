"use client";

/**
 * Admin Settlement Management
 * 
 * Admin dashboard for managing settlements:
 * - Stats overview
 * - Pending queue with batch processing
 * - Dispute management
 */

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
    DollarSign,
    Clock,
    CheckCircle,
    AlertTriangle,
    PlayCircle,
    MessageSquare,
    RefreshCw,
    Loader2,
    ChevronRight,
    Zap,
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// =============================================================================
// Types
// =============================================================================

interface AdminStats {
    pending_count: number;
    processing_count: number;
    completed_today: number;
    total_settled_today: number;
    open_disputes: number;
}

interface Settlement {
    id: string;
    tool_key: string;
    status: string;
    total_credits: number;
    platform_fee: number;
    creator_pool: number;
    payer_user_id: string;
    created_at: string;
    retry_count: number;
}

interface Dispute {
    id: string;
    settlement_id: string;
    complainant_id: string;
    reason: string;
    status: string;
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

async function getAdminStats(): Promise<AdminStats> {
    return fetchWithAuth(`${API_BASE_URL}/api/v1/settlements/admin/stats`);
}

async function listSettlements(status?: string): Promise<{ settlements: Settlement[] }> {
    const params = status ? `?status=${status}` : "";
    return fetchWithAuth(`${API_BASE_URL}/api/v1/settlements/admin/list${params}`);
}

async function listDisputes(): Promise<{ disputes: Dispute[] }> {
    return fetchWithAuth(`${API_BASE_URL}/api/v1/settlements/admin/disputes`);
}

async function batchProcess(limit: number): Promise<{ processed: number; succeeded: number }> {
    return fetchWithAuth(`${API_BASE_URL}/api/v1/settlements/admin/batch`, {
        method: "POST",
        body: JSON.stringify({ limit }),
    });
}

async function processSingle(id: string): Promise<void> {
    return fetchWithAuth(`${API_BASE_URL}/api/v1/settlements/admin/${id}/process`, {
        method: "POST",
    });
}

// =============================================================================
// Stats Cards
// =============================================================================

function StatsCards({ stats, loading }: { stats: AdminStats | null; loading: boolean }) {
    if (loading || !stats) {
        return (
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
                {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4 animate-pulse">
                        <div className="h-4 w-16 bg-gray-700 rounded mb-2"></div>
                        <div className="h-8 w-12 bg-gray-700 rounded"></div>
                    </div>
                ))}
            </div>
        );
    }

    const cards = [
        {
            label: "Pending",
            value: stats.pending_count,
            icon: Clock,
            color: "text-yellow-400",
            bgColor: "bg-yellow-500/10",
        },
        {
            label: "Processing",
            value: stats.processing_count,
            icon: Loader2,
            color: "text-blue-400",
            bgColor: "bg-blue-500/10",
        },
        {
            label: "Completed Today",
            value: stats.completed_today,
            icon: CheckCircle,
            color: "text-green-400",
            bgColor: "bg-green-500/10",
        },
        {
            label: "Settled Today",
            value: stats.total_settled_today.toLocaleString(),
            icon: DollarSign,
            color: "text-emerald-400",
            bgColor: "bg-emerald-500/10",
        },
        {
            label: "Open Disputes",
            value: stats.open_disputes,
            icon: AlertTriangle,
            color: "text-orange-400",
            bgColor: "bg-orange-500/10",
        },
    ];

    return (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
            {cards.map((card) => (
                <div
                    key={card.label}
                    className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4"
                >
                    <div className="flex items-center gap-2 mb-2">
                        <div className={`p-1.5 rounded-lg ${card.bgColor}`}>
                            <card.icon className={`w-4 h-4 ${card.color}`} />
                        </div>
                        <span className="text-xs text-gray-400">{card.label}</span>
                    </div>
                    <div className="text-2xl font-bold text-white">{card.value}</div>
                </div>
            ))}
        </div>
    );
}

// =============================================================================
// Main Component
// =============================================================================

export default function AdminSettlementsPage() {
    const router = useRouter();
    const [stats, setStats] = useState<AdminStats | null>(null);
    const [settlements, setSettlements] = useState<Settlement[]>([]);
    const [disputes, setDisputes] = useState<Dispute[]>([]);
    const [loading, setLoading] = useState(true);
    const [batchLoading, setBatchLoading] = useState(false);
    const [statusFilter, setStatusFilter] = useState<string>("pending");

    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const [statsData, settlementsData, disputesData] = await Promise.all([
                getAdminStats(),
                listSettlements(statusFilter),
                listDisputes(),
            ]);
            setStats(statsData);
            setSettlements(settlementsData.settlements);
            setDisputes(disputesData.disputes);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [statusFilter]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleBatchProcess = async () => {
        setBatchLoading(true);
        try {
            const result = await batchProcess(100);
            alert(`Processed ${result.processed} settlements, ${result.succeeded} succeeded`);
            fetchData();
        } catch (err) {
            console.error(err);
            alert("Batch processing failed");
        } finally {
            setBatchLoading(false);
        }
    };

    const handleProcessSingle = async (id: string) => {
        try {
            await processSingle(id);
            fetchData();
        } catch (err) {
            console.error(err);
            alert("Processing failed");
        }
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white">
            {/* Header */}
            <div className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold flex items-center gap-2">
                                <DollarSign className="w-6 h-6 text-emerald-400" />
                                Settlement Admin
                            </h1>
                            <p className="text-gray-400 text-sm">Manage revenue distributions</p>
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={handleBatchProcess}
                                disabled={batchLoading || (stats?.pending_count ?? 0) === 0}
                                className="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white font-medium rounded-lg disabled:opacity-50"
                            >
                                {batchLoading ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Zap className="w-4 h-4" />
                                )}
                                Process Batch
                            </button>
                            <button
                                onClick={fetchData}
                                className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg"
                            >
                                <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-6 py-8">
                <StatsCards stats={stats} loading={loading} />

                {/* Tabs */}
                <div className="flex gap-2 mb-6">
                    {["pending", "processing", "completed", "failed"].map((status) => (
                        <button
                            key={status}
                            onClick={() => setStatusFilter(status)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${statusFilter === status
                                    ? "bg-purple-500 text-white"
                                    : "bg-gray-800 text-gray-400 hover:text-white"
                                }`}
                        >
                            {status.charAt(0).toUpperCase() + status.slice(1)}
                        </button>
                    ))}
                </div>

                {/* Settlements Table */}
                <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl overflow-hidden mb-8">
                    <table className="w-full">
                        <thead className="bg-gray-800">
                            <tr>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400">Settlement</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400">Amount</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400">Payer</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400">Created</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400">Status</th>
                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-400">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-700/50">
                            {settlements.map((s) => (
                                <tr key={s.id} className="hover:bg-gray-800/50">
                                    <td className="px-4 py-3">
                                        <div className="text-sm font-medium text-white">{s.tool_key}</div>
                                        <div className="text-xs text-gray-500">{s.id.slice(0, 8)}...</div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="text-sm text-white">{s.total_credits} credits</div>
                                        <div className="text-xs text-gray-500">Pool: {s.creator_pool}</div>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-400">
                                        {s.payer_user_id.slice(0, 8)}...
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-400">
                                        {new Date(s.created_at).toLocaleString()}
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className={`px-2 py-1 text-xs rounded-full ${s.status === "pending" ? "bg-yellow-500/20 text-yellow-400" :
                                                s.status === "completed" ? "bg-green-500/20 text-green-400" :
                                                    s.status === "failed" ? "bg-red-500/20 text-red-400" :
                                                        "bg-gray-500/20 text-gray-400"
                                            }`}>
                                            {s.status}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            {s.status === "pending" && (
                                                <button
                                                    onClick={() => handleProcessSingle(s.id)}
                                                    className="p-1.5 text-purple-400 hover:bg-purple-500/20 rounded"
                                                    title="Process"
                                                >
                                                    <PlayCircle className="w-4 h-4" />
                                                </button>
                                            )}
                                            <button
                                                onClick={() => router.push(`/settlements/${s.id}`)}
                                                className="p-1.5 text-gray-400 hover:bg-gray-700 rounded"
                                            >
                                                <ChevronRight className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {settlements.length === 0 && (
                        <div className="p-8 text-center text-gray-500">
                            No {statusFilter} settlements
                        </div>
                    )}
                </div>

                {/* Disputes Section */}
                {disputes.length > 0 && (
                    <div className="bg-orange-500/10 border border-orange-500/30 rounded-xl p-6">
                        <div className="flex items-center gap-2 mb-4">
                            <MessageSquare className="w-5 h-5 text-orange-400" />
                            <h3 className="text-lg font-semibold text-orange-400">
                                Open Disputes ({disputes.length})
                            </h3>
                        </div>
                        <div className="space-y-3">
                            {disputes.map((d) => (
                                <div
                                    key={d.id}
                                    onClick={() => router.push(`/settlements/${d.settlement_id}`)}
                                    className="bg-gray-900/50 rounded-lg p-4 cursor-pointer hover:bg-gray-900/70"
                                >
                                    <p className="text-gray-300 line-clamp-2 mb-2">{d.reason}</p>
                                    <div className="flex items-center gap-3 text-xs text-gray-500">
                                        <span>By {d.complainant_id.slice(0, 8)}...</span>
                                        <span>{new Date(d.created_at).toLocaleDateString()}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
