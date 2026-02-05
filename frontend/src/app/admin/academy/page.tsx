"use client";

/**
 * Academy Access Request Admin Page
 * 
 * 수강생 접근 요청을 관리하는 관리자 페이지
 * - 요청 목록 조회
 * - 승인/거절 버튼
 */

import { useState, useEffect, useCallback } from "react";
import {
    CheckCircle,
    XCircle,
    Clock,
    RefreshCw,
    UserCheck,
    Mail,
} from "lucide-react";

import { api } from "@/lib/api";
import { StatusBadge, StatCard, EmptyState } from "@/components/shared";
import AppShell from "@/components/AppShell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// =============================================================================
// Types
// =============================================================================

interface AccessRequestItem {
    id: string;
    user_id: string;
    email: string;
    name: string | null;
    status: string;
    created_at: string;
    updated_at: string;
}

interface AccessRequestListResponse {
    requests: AccessRequestItem[];
    total: number;
    pending_count: number;
}

// =============================================================================
// Components
// =============================================================================

function RequestCard({
    item,
    onApprove,
    onReject,
    processing,
}: {
    item: AccessRequestItem;
    onApprove: () => void;
    onReject: () => void;
    processing: boolean;
}) {
    const statusColors: Record<string, string> = {
        pending: "bg-amber-500/20 text-amber-300 border-amber-500/30",
        approved: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
        rejected: "bg-red-500/20 text-red-300 border-red-500/30",
    };

    const statusLabels: Record<string, string> = {
        pending: "대기 중",
        approved: "승인됨",
        rejected: "거절됨",
    };

    return (
        <div className="rounded-xl border border-white/5 bg-[var(--surface-2)]/60 p-4 transition-colors hover:border-purple-500/30">
            <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                        <Mail className="w-4 h-4 text-purple-400 flex-shrink-0" />
                        <span className="text-[var(--fg-0)] font-medium truncate">
                            {item.email}
                        </span>
                        <Badge className={`text-xs border ${statusColors[item.status] || statusColors.pending}`}>
                            {statusLabels[item.status] || item.status}
                        </Badge>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-[var(--fg-subtle)]">
                        {item.name && <span>{item.name}</span>}
                        <span>•</span>
                        <span>{new Date(item.created_at).toLocaleString("ko-KR")}</span>
                    </div>
                </div>

                {item.status === "pending" && (
                    <div className="flex items-center gap-2">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={onApprove}
                            disabled={processing}
                            className="gap-2 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                        >
                            <CheckCircle className="w-4 h-4" />
                            승인
                        </Button>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={onReject}
                            disabled={processing}
                            className="gap-2 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                        >
                            <XCircle className="w-4 h-4" />
                            거절
                        </Button>
                    </div>
                )}
            </div>
        </div>
    );
}

// =============================================================================
// Main Page
// =============================================================================

export default function AdminAcademyPage() {
    const [data, setData] = useState<AccessRequestListResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [processingId, setProcessingId] = useState<string | null>(null);
    const [filter, setFilter] = useState<string>("pending");

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const statusParam = filter === "all" ? "" : `?status=${filter}`;
            const response = await api.get<AccessRequestListResponse>(
                `/api/v1/access-request/admin/list${statusParam}`
            );
            setData(response);
        } catch (err) {
            setError(err instanceof Error ? err.message : "데이터를 불러오지 못했습니다");
        } finally {
            setLoading(false);
        }
    }, [filter]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleApprove = async (id: string) => {
        setProcessingId(id);
        try {
            await api.patch(`/api/v1/access-request/admin/${id}/approve`, {});
            await fetchData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "승인 처리 실패");
        } finally {
            setProcessingId(null);
        }
    };

    const handleReject = async (id: string) => {
        setProcessingId(id);
        try {
            await api.patch(`/api/v1/access-request/admin/${id}/reject`, {});
            await fetchData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "거절 처리 실패");
        } finally {
            setProcessingId(null);
        }
    };

    return (
        <AppShell>
            <div className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
                <div className="mx-auto max-w-4xl">
                    {/* Header */}
                    <div className="mb-6 sm:mb-8">
                        <div className="flex items-center justify-between">
                            <div>
                                <h1 className="text-xl font-bold text-[var(--fg-0)] sm:text-2xl flex items-center gap-2">
                                    <UserCheck className="w-6 h-6 text-purple-400" />
                                    Academy 접근 요청
                                </h1>
                                <p className="mt-1 text-sm text-[var(--fg-muted)] sm:text-base">
                                    수강생 접근 요청 관리
                                </p>
                            </div>
                            <button
                                onClick={fetchData}
                                disabled={loading}
                                className="p-2 text-[var(--fg-muted)] hover:text-[var(--fg-0)] hover:bg-white/5 rounded-lg transition-colors"
                                title="새로고침"
                            >
                                <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
                            </button>
                        </div>
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-3 gap-4 mb-6">
                        <StatCard
                            title="대기 중"
                            value={data?.pending_count ?? 0}
                            icon={Clock}
                            color="yellow"
                            subtitle="건"
                        />
                        <StatCard
                            title="전체"
                            value={data?.total ?? 0}
                            icon={Mail}
                            color="purple"
                            subtitle="건"
                        />
                        <StatCard
                            title="승인됨"
                            value={(data?.total ?? 0) - (data?.pending_count ?? 0)}
                            icon={CheckCircle}
                            color="green"
                            subtitle="건"
                        />
                    </div>

                    {/* Filter Tabs */}
                    <div className="flex gap-2 mb-6">
                        {[
                            { key: "pending", label: "대기 중" },
                            { key: "approved", label: "승인됨" },
                            { key: "rejected", label: "거절됨" },
                            { key: "all", label: "전체" },
                        ].map((tab) => (
                            <button
                                key={tab.key}
                                onClick={() => setFilter(tab.key)}
                                className={`px-4 py-2 text-sm rounded-lg transition-colors ${filter === tab.key
                                        ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                                        : "text-[var(--fg-muted)] hover:bg-white/5"
                                    }`}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center gap-3">
                            <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                            <p className="text-red-300">{error}</p>
                            <button
                                onClick={fetchData}
                                className="ml-auto px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg text-sm"
                            >
                                재시도
                            </button>
                        </div>
                    )}

                    {/* Request List */}
                    <Card className="border border-white/5 bg-[var(--surface-1)]/70">
                        <CardHeader className="pb-4">
                            <div className="flex items-center gap-2">
                                <Mail className="w-5 h-5 text-purple-400" />
                                <CardTitle className="text-base">접근 요청 목록</CardTitle>
                                <Badge variant="secondary" className="text-xs">
                                    {data?.requests.length ?? 0}개
                                </Badge>
                            </div>
                        </CardHeader>

                        <CardContent>
                            {loading ? (
                                <div className="space-y-3">
                                    {[1, 2, 3].map((i) => (
                                        <div
                                            key={i}
                                            className="rounded-xl border border-white/5 bg-[var(--surface-2)]/60 p-4 animate-pulse"
                                        >
                                            <div className="h-4 w-48 bg-white/10 rounded mb-2" />
                                            <div className="h-3 w-32 bg-white/10 rounded" />
                                        </div>
                                    ))}
                                </div>
                            ) : data?.requests.length === 0 ? (
                                <EmptyState
                                    icon={CheckCircle}
                                    title="요청이 없습니다"
                                    description={
                                        filter === "pending"
                                            ? "대기 중인 접근 요청이 없습니다."
                                            : "해당 상태의 요청이 없습니다."
                                    }
                                />
                            ) : (
                                <div className="space-y-3">
                                    {data?.requests.map((item) => (
                                        <RequestCard
                                            key={item.id}
                                            item={item}
                                            onApprove={() => handleApprove(item.id)}
                                            onReject={() => handleReject(item.id)}
                                            processing={processingId === item.id}
                                        />
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
