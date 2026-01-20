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

import AppShell from "@/components/AppShell";
import { PageHeader, StatusBadge, EmptyState } from "@/components/shared";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

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
                    <Card key={i} className="border border-white/5 bg-[var(--surface-1)]/70 animate-pulse">
                        <CardContent className="p-4">
                            <div className="h-4 w-16 bg-white/10 rounded mb-2"></div>
                            <div className="h-8 w-12 bg-white/10 rounded"></div>
                        </CardContent>
                    </Card>
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
                <Card
                    key={card.label}
                    className="border border-white/5 bg-[var(--surface-1)]/70"
                >
                    <CardContent className="p-4">
                        <div className="flex items-center gap-2 mb-2">
                            <div className={`p-1.5 rounded-lg ${card.bgColor}`}>
                                <card.icon className={`w-4 h-4 ${card.color}`} />
                            </div>
                            <span className="text-xs text-[var(--fg-muted)]">{card.label}</span>
                        </div>
                        <div className="text-2xl font-bold text-[var(--fg-0)]">{card.value}</div>
                    </CardContent>
                </Card>
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
        <AppShell showTopBar={false}>
            <div className="min-h-screen">
                <PageHeader
                    title="Settlement Admin"
                    subtitle="Manage revenue distributions"
                    icon={DollarSign}
                    backLabel=""
                    actions={
                        <div className="flex items-center gap-3">
                            <Button
                                size="sm"
                                onClick={handleBatchProcess}
                                disabled={batchLoading || (stats?.pending_count ?? 0) === 0}
                                className="gap-2"
                            >
                                {batchLoading ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Zap className="w-4 h-4" />
                                )}
                                Process Batch
                            </Button>
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={fetchData}
                            >
                                <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
                            </Button>
                        </div>
                    }
                />

                <div className="max-w-7xl mx-auto px-6 py-6">
                    <StatsCards stats={stats} loading={loading} />

                    <div className="flex items-center justify-between mb-6">
                        <Tabs value={statusFilter} onValueChange={setStatusFilter}>
                            <TabsList className="flex gap-2">
                                {["pending", "processing", "completed", "failed"].map((status) => (
                                    <TabsTrigger key={status} value={status}>
                                        {status.charAt(0).toUpperCase() + status.slice(1)}
                                    </TabsTrigger>
                                ))}
                            </TabsList>
                        </Tabs>
                        <Badge variant="secondary" className="text-xs">
                            {settlements.length} items
                        </Badge>
                    </div>

                    <Card className="border border-white/5 bg-[var(--surface-1)]/70 overflow-hidden mb-8">
                        <CardHeader className="pb-4">
                            <CardTitle className="text-base">Settlement Queue</CardTitle>
                        </CardHeader>
                        <CardContent className="p-0">
                            <table className="w-full">
                                <thead className="bg-[var(--surface-2)]/60">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-[var(--fg-muted)]">Settlement</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-[var(--fg-muted)]">Amount</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-[var(--fg-muted)]">Payer</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-[var(--fg-muted)]">Created</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-[var(--fg-muted)]">Status</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-[var(--fg-muted)]">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {settlements.map((s) => (
                                        <tr key={s.id} className="hover:bg-[var(--surface-2)]/60">
                                            <td className="px-4 py-3">
                                                <div className="text-sm font-medium text-[var(--fg-0)]">{s.tool_key}</div>
                                                <div className="text-xs text-[var(--fg-subtle)]">{s.id.slice(0, 8)}...</div>
                                            </td>
                                            <td className="px-4 py-3">
                                                <div className="text-sm text-[var(--fg-0)]">{s.total_credits} credits</div>
                                                <div className="text-xs text-[var(--fg-subtle)]">Pool: {s.creator_pool}</div>
                                            </td>
                                            <td className="px-4 py-3 text-sm text-[var(--fg-muted)]">
                                                {s.payer_user_id.slice(0, 8)}...
                                            </td>
                                            <td className="px-4 py-3 text-sm text-[var(--fg-muted)]">
                                                {new Date(s.created_at).toLocaleString()}
                                            </td>
                                            <td className="px-4 py-3">
                                                <StatusBadge status={s.status} />
                                            </td>
                                            <td className="px-4 py-3 text-right">
                                                <div className="flex items-center justify-end gap-2">
                                                    {s.status === "pending" && (
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            onClick={() => handleProcessSingle(s.id)}
                                                            title="Process"
                                                        >
                                                            <PlayCircle className="w-4 h-4 text-violet-400" />
                                                        </Button>
                                                    )}
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => router.push(`/settlements/${s.id}`)}
                                                    >
                                                        <ChevronRight className="w-4 h-4" />
                                                    </Button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {settlements.length === 0 && (
                                <div className="p-8 text-center text-[var(--fg-subtle)]">
                                    No {statusFilter} settlements
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    <Card className="border border-white/5 bg-[var(--surface-1)]/70">
                        <CardHeader className="pb-4">
                            <div className="flex items-center gap-2">
                                <MessageSquare className="w-5 h-5 text-orange-400" />
                                <CardTitle className="text-base">Open Disputes</CardTitle>
                                <Badge variant="secondary" className="text-xs">
                                    {disputes.length}
                                </Badge>
                            </div>
                        </CardHeader>
                        <CardContent>
                            {disputes.length === 0 ? (
                                <EmptyState
                                    icon={CheckCircle}
                                    title="No disputes"
                                    description="All disputes have been resolved."
                                />
                            ) : (
                                <div className="space-y-3">
                                    {disputes.map((d) => (
                                        <div
                                            key={d.id}
                                            onClick={() => router.push(`/settlements/${d.settlement_id}`)}
                                            className="rounded-lg border border-white/5 bg-[var(--surface-2)]/60 p-4 cursor-pointer hover:border-violet-500/30"
                                        >
                                            <p className="text-[var(--fg-0)] line-clamp-2 mb-2">{d.reason}</p>
                                            <div className="flex items-center gap-3 text-xs text-[var(--fg-subtle)]">
                                                <span>By {d.complainant_id.slice(0, 8)}...</span>
                                                <span>{new Date(d.created_at).toLocaleDateString()}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </AppShell>
    );
}
