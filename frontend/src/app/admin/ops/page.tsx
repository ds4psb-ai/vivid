"use client";

/**
 * 관리자 운영 대시보드
 * 
 * 정산 및 실패한 작업을 관리하는 중앙 대시보드:
 * - 정산 (대기/실패 처리)
 * - Dead Letter Queue (실패한 환불)
 * - 시스템 상태 개요
 */

import { useState, useEffect, useCallback } from "react";
import {
    DollarSign,
    AlertTriangle,
    RefreshCw,
    CheckCircle,
    XCircle,
    Clock,
    Play,
    ArrowRight,
    Inbox,
    Activity,
    Shield,
    RotateCcw,
    FileX,
} from "lucide-react";

import { fetchWithAuth } from "@/lib/api-client";
import { StatusBadge, StatCard } from "@/components/shared";
import AppShell from "@/components/AppShell";

// =============================================================================
// Types
// =============================================================================

interface SettlementItem {
    id: string;
    tool_key: string;
    status: string;
    total_credits: number;
    platform_fee: number;
    creator_pool: number;
    payer_user_id: string | null;
    created_at: string;
    processed_at: string | null;
    error_message: string | null;
}

interface SettlementListResponse {
    settlements: SettlementItem[];
    total: number;
    pending_count: number;
    failed_count: number;
}

interface DLQItem {
    id: string;
    event_type: string;
    status: string;
    user_id: string;
    operation_type: string;
    amount: number;
    error_message: string;
    retry_count: number;
    created_at: string;
    resolved_by: string | null;
    resolved_at: string | null;
}

interface DLQListResponse {
    items: DLQItem[];
    total: number;
}

interface DLQStats {
    by_status: Record<string, number>;
    pending_by_type: Record<string, number>;
    pending_refund_credits: number;
    total_pending: number;
}

interface BatchProcessResult {
    processed: number;
    succeeded: number;
    failed: number;
}

// =============================================================================
// 통계 개요
// =============================================================================

function StatsOverview({
    settlementData,
    dlqStats,
    loading
}: {
    settlementData: SettlementListResponse | null;
    dlqStats: DLQStats | null;
    loading: boolean;
}) {
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

    return (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard
                title="대기 중인 정산"
                value={settlementData?.pending_count ?? 0}
                icon={Clock}
                color="yellow"
                subtitle="건"
            />
            <StatCard
                title="실패한 정산"
                value={settlementData?.failed_count ?? 0}
                icon={XCircle}
                color="red"
                subtitle="건"
            />
            <StatCard
                title="DLQ 대기 중"
                value={dlqStats?.total_pending ?? 0}
                icon={Inbox}
                color="orange"
                subtitle="건"
            />
            <StatCard
                title="환불 필요"
                value={dlqStats?.pending_refund_credits ?? 0}
                icon={AlertTriangle}
                color="red"
                subtitle="크레딧"
            />
        </div>
    );
}

// =============================================================================
// 정산 섹션
// =============================================================================

function SettlementSection({
    data,
    loading,
    onProcessBatch,
    onRetry,
    processingBatch,
}: {
    data: SettlementListResponse | null;
    loading: boolean;
    onProcessBatch: () => Promise<void>;
    onRetry: (id: string) => Promise<void>;
    processingBatch: boolean;
}) {
    const [retryingId, setRetryingId] = useState<string | null>(null);

    const handleRetry = async (id: string) => {
        setRetryingId(id);
        await onRetry(id);
        setRetryingId(null);
    };

    return (
        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <DollarSign className="w-5 h-5 text-emerald-400" />
                    <h3 className="text-lg font-semibold">정산</h3>
                    <span className="text-sm text-gray-500 ml-2">
                        {data?.pending_count ?? 0}개 대기 중
                    </span>
                </div>
                <button
                    onClick={onProcessBatch}
                    disabled={processingBatch || (data?.pending_count ?? 0) === 0}
                    className="flex items-center gap-2 px-4 py-2 bg-emerald-500/20 hover:bg-emerald-500/30 
                             text-emerald-400 rounded-lg text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {processingBatch ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                        <Play className="w-4 h-4" />
                    )}
                    전체 처리
                </button>
            </div>

            {loading ? (
                <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="bg-gray-900/50 rounded-lg p-4 animate-pulse">
                            <div className="h-4 w-32 bg-gray-700 rounded mb-2" />
                            <div className="h-3 w-24 bg-gray-700/50 rounded" />
                        </div>
                    ))}
                </div>
            ) : data?.settlements.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                    <CheckCircle className="w-12 h-12 mb-3 text-emerald-500/50" />
                    <p>모든 정산이 완료되었습니다</p>
                </div>
            ) : (
                <div className="space-y-3 max-h-80 overflow-y-auto">
                    {data?.settlements.map((settlement) => (
                        <div
                            key={settlement.id}
                            className="bg-gray-900/50 rounded-lg p-4 hover:bg-gray-900/70 transition-colors"
                        >
                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-white font-medium">
                                            {settlement.total_credits} 크레딧
                                        </span>
                                        <StatusBadge status={settlement.status} />
                                    </div>
                                    <div className="flex items-center gap-3 text-sm text-gray-500">
                                        <span>{settlement.tool_key}</span>
                                        <span>•</span>
                                        <span>{new Date(settlement.created_at).toLocaleString("ko-KR")}</span>
                                    </div>
                                    {settlement.error_message && (
                                        <p className="text-xs text-red-400 mt-1 truncate max-w-md">
                                            {settlement.error_message}
                                        </p>
                                    )}
                                </div>
                                {settlement.status === "failed" && (
                                    <button
                                        onClick={() => handleRetry(settlement.id)}
                                        disabled={retryingId === settlement.id}
                                        className="p-2 hover:bg-white/5 rounded-lg transition-colors"
                                        title="재시도"
                                    >
                                        <RotateCcw className={`w-4 h-4 text-gray-400 ${retryingId === settlement.id ? 'animate-spin' : ''}`} />
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// =============================================================================
// DLQ 섹션
// =============================================================================

function DLQSection({
    data,
    loading,
    onRetry,
    onResolve,
}: {
    data: DLQListResponse | null;
    loading: boolean;
    onRetry: (id: string) => Promise<void>;
    onResolve: (id: string, skip: boolean) => Promise<void>;
}) {
    const [processingId, setProcessingId] = useState<string | null>(null);

    const handleRetry = async (id: string) => {
        setProcessingId(id);
        await onRetry(id);
        setProcessingId(null);
    };

    const handleResolve = async (id: string, skip: boolean) => {
        setProcessingId(id);
        await onResolve(id, skip);
        setProcessingId(null);
    };

    return (
        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Inbox className="w-5 h-5 text-orange-400" />
                    <h3 className="text-lg font-semibold">실패 항목 대기열</h3>
                    <span className="text-sm text-gray-500 ml-2">
                        {data?.total ?? 0}개 항목
                    </span>
                </div>
            </div>

            {loading ? (
                <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="bg-gray-900/50 rounded-lg p-4 animate-pulse">
                            <div className="h-4 w-32 bg-gray-700 rounded mb-2" />
                            <div className="h-3 w-24 bg-gray-700/50 rounded" />
                        </div>
                    ))}
                </div>
            ) : data?.items.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                    <CheckCircle className="w-12 h-12 mb-3 text-emerald-500/50" />
                    <p>실패한 작업이 없습니다</p>
                </div>
            ) : (
                <div className="space-y-3 max-h-80 overflow-y-auto">
                    {data?.items.map((item) => (
                        <div
                            key={item.id}
                            className="bg-gray-900/50 rounded-lg p-4 hover:bg-gray-900/70 transition-colors"
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-white font-medium">
                                            {item.amount} 크레딧
                                        </span>
                                        <StatusBadge status={item.status} />
                                        <span className="text-xs px-2 py-0.5 bg-orange-500/20 text-orange-400 rounded">
                                            {item.event_type === 'refund_failed' ? '환불 실패' : item.event_type.replace('_', ' ')}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-3 text-sm text-gray-500">
                                        <span>사용자: {item.user_id}</span>
                                        <span>•</span>
                                        <span>{item.operation_type}</span>
                                        <span>•</span>
                                        <span>재시도: {item.retry_count}회</span>
                                    </div>
                                    <p className="text-xs text-red-400 mt-1 truncate max-w-lg">
                                        {item.error_message}
                                    </p>
                                </div>
                                {item.status === "pending" && (
                                    <div className="flex items-center gap-2 ml-4">
                                        <button
                                            onClick={() => handleRetry(item.id)}
                                            disabled={processingId === item.id}
                                            className="p-2 hover:bg-emerald-500/10 text-emerald-400 rounded-lg transition-colors"
                                            title="재시도"
                                        >
                                            <RotateCcw className={`w-4 h-4 ${processingId === item.id ? 'animate-spin' : ''}`} />
                                        </button>
                                        <button
                                            onClick={() => handleResolve(item.id, false)}
                                            disabled={processingId === item.id}
                                            className="p-2 hover:bg-blue-500/10 text-blue-400 rounded-lg transition-colors"
                                            title="해결 완료"
                                        >
                                            <CheckCircle className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => handleResolve(item.id, true)}
                                            disabled={processingId === item.id}
                                            className="p-2 hover:bg-gray-500/10 text-gray-400 rounded-lg transition-colors"
                                            title="건너뛰기"
                                        >
                                            <FileX className="w-4 h-4" />
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// =============================================================================
// 메인 페이지
// =============================================================================

export default function AdminOpsPage() {
    const [settlementData, setSettlementData] = useState<SettlementListResponse | null>(null);
    const [dlqData, setDlqData] = useState<DLQListResponse | null>(null);
    const [dlqStats, setDlqStats] = useState<DLQStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [processingBatch, setProcessingBatch] = useState(false);
    const [batchResult, setBatchResult] = useState<BatchProcessResult | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [settlements, dlq, stats] = await Promise.all([
                fetchWithAuth<SettlementListResponse>("/api/v1/admin/settlements/pending"),
                fetchWithAuth<DLQListResponse>("/api/v1/admin/dlq?status=pending"),
                fetchWithAuth<DLQStats>("/api/v1/admin/dlq/stats"),
            ]);
            setSettlementData(settlements);
            setDlqData(dlq);
            setDlqStats(stats);
        } catch (err) {
            setError(err instanceof Error ? err.message : "데이터를 불러오지 못했습니다");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleProcessBatch = async () => {
        setProcessingBatch(true);
        setBatchResult(null);
        try {
            const result = await fetchWithAuth<BatchProcessResult>(
                "/api/v1/admin/settlements/process-batch",
                { method: "POST", body: JSON.stringify({ limit: 100 }) }
            );
            setBatchResult(result);
            await fetchData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "일괄 처리에 실패했습니다");
        } finally {
            setProcessingBatch(false);
        }
    };

    const handleSettlementRetry = async (id: string) => {
        try {
            await fetchWithAuth(`/api/v1/admin/settlements/${id}/retry`, { method: "POST" });
            await fetchData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "재시도에 실패했습니다");
        }
    };

    const handleDLQRetry = async (id: string) => {
        try {
            await fetchWithAuth(`/api/v1/admin/dlq/${id}/retry`, { method: "POST" });
            await fetchData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "DLQ 재시도에 실패했습니다");
        }
    };

    const handleDLQResolve = async (id: string, skip: boolean) => {
        try {
            await fetchWithAuth(`/api/v1/admin/dlq/${id}/resolve`, {
                method: "POST",
                body: JSON.stringify({
                    resolution_notes: skip ? "관리자가 수동으로 건너뜀" : "관리자가 수동으로 해결함",
                    skip,
                }),
            });
            await fetchData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "해결에 실패했습니다");
        }
    };

    return (
        <AppShell>
            <div className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
                <div className="mx-auto max-w-6xl">
                    {/* 헤더 */}
                    <div className="mb-6 sm:mb-8">
                        <div className="flex items-center justify-between">
                            <div>
                                <h1 className="text-xl font-bold text-[var(--fg-0)] sm:text-2xl flex items-center gap-2">
                                    <Shield className="w-6 h-6 text-purple-400" />
                                    운영 대시보드
                                </h1>
                                <p className="mt-1 text-sm text-[var(--fg-muted)] sm:text-base">
                                    정산 및 실패한 작업 관리
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

                    {/* 에러 */}
                    {error && (
                        <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center gap-3">
                            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
                            <p className="text-red-300">{error}</p>
                            <button
                                onClick={fetchData}
                                className="ml-auto px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg text-sm"
                            >
                                재시도
                            </button>
                        </div>
                    )}

                    {/* 일괄 처리 결과 */}
                    {batchResult && (
                        <div className="mb-6 bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 flex items-center gap-3">
                            <Activity className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                            <p className="text-emerald-300">
                                {batchResult.processed}개 처리: {batchResult.succeeded}개 성공, {batchResult.failed}개 실패
                            </p>
                            <button
                                onClick={() => setBatchResult(null)}
                                className="ml-auto px-3 py-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 rounded-lg text-sm"
                            >
                                닫기
                            </button>
                        </div>
                    )}

                    <StatsOverview
                        settlementData={settlementData}
                        dlqStats={dlqStats}
                        loading={loading}
                    />

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <SettlementSection
                            data={settlementData}
                            loading={loading}
                            onProcessBatch={handleProcessBatch}
                            onRetry={handleSettlementRetry}
                            processingBatch={processingBatch}
                        />
                        <DLQSection
                            data={dlqData}
                            loading={loading}
                            onRetry={handleDLQRetry}
                            onResolve={handleDLQResolve}
                        />
                    </div>
                </div>
            </div>
        </AppShell>
    );
}
