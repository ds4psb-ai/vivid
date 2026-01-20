"use client";

/**
 * Admin Review Dashboard
 * 
 * Complete review workflow management using shared component library.
 */

import { useState, useEffect, useCallback } from "react";
import {
    Shield,
    CheckCircle,
    XCircle,
    Clock,
    Loader2,
    Eye,
    TrendingUp,
    User,
    GitFork,
    Zap,
    Filter,
    RefreshCw,
} from "lucide-react";

// Shared imports
import { fetchWithAuth } from "@/lib/api-client";
import { StatCard, StatusBadge, PageHeader, EmptyState } from "@/components/shared";
import type { Review, ReviewStats, CheckResult } from "@/types/api.types";
import AppShell from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

type ReviewDetail = Review & {
    tool?: {
        display_name: string;
        tool_key: string;
        tier: string;
    };
    checks?: CheckResult[];
};

// =============================================================================
// Review Card Component
// =============================================================================

function ReviewCard({
    review,
    onView,
    onApprove,
    onReject
}: {
    review: Review;
    onView: () => void;
    onApprove: () => void;
    onReject: () => void;
}) {
    const typeIcons: Record<string, typeof GitFork> = {
        fork_submission: GitFork,
        tier_promotion: TrendingUp,
    };
    const TypeIcon = typeIcons[review.review_type] || Zap;

    return (
        <div className="bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-xl p-5 hover:border-purple-500/50 transition-colors">
            <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-500/20 rounded-lg">
                        <TypeIcon className="w-4 h-4 text-purple-400" />
                    </div>
                    <div>
                        <div className="font-medium text-[var(--fg-0)]">
                            {review.review_type.replace(/_/g, " ")}
                        </div>
                        <div className="text-sm text-[var(--fg-muted)]">
                            by {review.submitted_by.slice(0, 8)}...
                        </div>
                    </div>
                </div>
                <StatusBadge status={review.status} />
            </div>

            {/* Auto-check score */}
            <div className="mb-4">
                <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-[var(--fg-muted)]">Auto-check Score</span>
                    <span className={review.auto_checks_passed ? "text-green-400" : "text-red-400"}>
                        {review.auto_checks_score.toFixed(1)}
                    </span>
                </div>
                <div className="h-2 bg-[var(--surface-2)] rounded-full overflow-hidden">
                    <div
                        className={`h-full ${review.auto_checks_passed ? "bg-green-500" : "bg-red-500"}`}
                        style={{ width: `${Math.min(100, review.auto_checks_score)}%` }}
                    />
                </div>
            </div>

            {review.submission_notes && (
                <p className="text-sm text-[var(--fg-muted)] mb-4 line-clamp-2">
                    {review.submission_notes}
                </p>
            )}

            {/* Actions */}
            <div className="flex items-center gap-2">
                <button
                    onClick={onView}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-[var(--surface-2)] hover:bg-[var(--surface-1)] text-[var(--fg-0)] rounded-lg text-sm"
                >
                    <Eye className="w-4 h-4" />
                    View
                </button>
                {review.status === "pending" && (
                    <>
                        <button
                            onClick={onApprove}
                            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-lg text-sm"
                        >
                            <CheckCircle className="w-4 h-4" />
                            Approve
                        </button>
                        <button
                            onClick={onReject}
                            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg text-sm"
                        >
                            <XCircle className="w-4 h-4" />
                            Reject
                        </button>
                    </>
                )}
            </div>

            <div className="mt-3 text-xs text-[var(--fg-subtle)]">
                {new Date(review.created_at).toLocaleDateString("ko-KR", {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                })}
            </div>
        </div>
    );
}

// =============================================================================
// Review Detail Modal
// =============================================================================

function ReviewDetailModal({
    reviewId,
    onClose,
    onApprove,
    onReject,
}: {
    reviewId: string;
    onClose: () => void;
    onApprove: () => void;
    onReject: () => void;
}) {
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState<ReviewDetail | null>(null);
    const [rejecting, setRejecting] = useState(false);
    const [rejectReason, setRejectReason] = useState("");

    useEffect(() => {
        fetchWithAuth<ReviewDetail>(`/api/v1/reviews/${reviewId}`)
            .then(setData)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [reviewId]);

    if (loading) {
        return (
            <div className="fixed inset-0 dialog-overlay flex items-center justify-center z-50">
                <div className="bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-xl p-8">
                    <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 dialog-overlay flex items-center justify-center z-50 p-6">
            <div className="dialog-panel rounded-xl w-full max-w-3xl max-h-[var(--layout-max-height-lg)] overflow-y-auto">
                <div className="sticky top-0 bg-[var(--surface-1)] border-b border-[var(--border-subtle)] p-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold text-[var(--fg-0)] flex items-center gap-2">
                            <Shield className="w-5 h-5 text-purple-400" />
                            Review Details
                        </h2>
                        <button onClick={onClose} className="text-[var(--fg-muted)] hover:text-[var(--fg-0)] text-2xl">
                            ×
                        </button>
                    </div>
                </div>

                <div className="p-6 space-y-6">
                    {data?.tool && (
                        <div className="bg-[var(--surface-2)] rounded-lg p-4">
                            <h3 className="font-medium text-[var(--fg-0)] mb-2">{data.tool.display_name}</h3>
                            <div className="flex items-center gap-4 text-sm text-[var(--fg-muted)]">
                                <span>Key: {data.tool.tool_key}</span>
                                <span>Tier: {data.tool.tier}</span>
                            </div>
                        </div>
                    )}

                    <div>
                        <h3 className="font-medium text-[var(--fg-0)] mb-3">Automated Checks</h3>
                        <div className="space-y-3">
                            {data?.checks?.map((check: CheckResult) => (
                                <div
                                    key={check.id}
                                    className={`p-4 rounded-lg border ${check.passed ? "bg-green-500/5 border-green-500/30" : "bg-red-500/5 border-red-500/30"}`}
                                >
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center gap-2">
                                            {check.passed ? (
                                                <CheckCircle className="w-4 h-4 text-green-400" />
                                            ) : (
                                                <XCircle className="w-4 h-4 text-red-400" />
                                            )}
                                            <span className="font-medium text-[var(--fg-0)]">{check.check_name}</span>
                                            <span className="text-xs text-[var(--fg-subtle)] bg-[var(--surface-2)] px-2 py-0.5 rounded">
                                                {check.category}
                                            </span>
                                        </div>
                                        <span className={check.passed ? "text-green-400" : "text-red-400"}>
                                            {check.score.toFixed(0)}
                                        </span>
                                    </div>
                                    {check.description && <p className="text-sm text-[var(--fg-muted)]">{check.description}</p>}
                                    {check.error_message && <p className="text-sm text-red-400 mt-2">{check.error_message}</p>}
                                </div>
                            ))}
                        </div>
                    </div>

                    {rejecting && (
                        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                            <h4 className="font-medium text-red-400 mb-2">Rejection Reason</h4>
                            <textarea
                                value={rejectReason}
                                onChange={(e) => setRejectReason(e.target.value)}
                                rows={3}
                                className="w-full px-3 py-2 bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-lg text-[var(--fg-0)] resize-none"
                                placeholder="Explain why this review is rejected..."
                            />
                        </div>
                    )}

                    {data?.status === "pending" && (
                        <div className="flex items-center gap-3">
                            <button
                                onClick={onApprove}
                                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-green-500 hover:bg-green-600 text-[var(--fg-on-emphasis)] font-medium rounded-lg"
                            >
                                <CheckCircle className="w-5 h-5" />
                                Approve
                            </button>
                            {rejecting ? (
                                <button
                                    onClick={() => rejectReason.length >= 10 && onReject()}
                                    disabled={rejectReason.length < 10}
                                    className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-red-500 hover:bg-red-600 text-[var(--fg-on-emphasis)] font-medium rounded-lg disabled:opacity-50"
                                >
                                    <XCircle className="w-5 h-5" />
                                    Confirm Reject
                                </button>
                            ) : (
                                <button
                                    onClick={() => setRejecting(true)}
                                    className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-red-500/20 hover:bg-red-500/30 text-red-400 font-medium rounded-lg"
                                >
                                    <XCircle className="w-5 h-5" />
                                    Reject
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// =============================================================================
// Main Component
// =============================================================================

export default function AdminReviewsPage() {
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState<ReviewStats | null>(null);
    const [reviews, setReviews] = useState<Review[]>([]);
    const [filter, setFilter] = useState<string | null>(null);
    const [selectedReview, setSelectedReview] = useState<string | null>(null);

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const [statsData, queueData] = await Promise.all([
                fetchWithAuth<ReviewStats>("/api/v1/reviews/stats"),
                fetchWithAuth<Review[]>(`/api/v1/reviews/queue${filter ? `?review_type=${filter}` : ""}`),
            ]);
            setStats(statsData);
            setReviews(queueData);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [filter]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleApprove = async (reviewId: string) => {
        try {
            await fetchWithAuth(`/api/v1/reviews/${reviewId}/approve`, {
                method: "POST",
                body: JSON.stringify({ notes: "Approved via admin dashboard" }),
            });
            await loadData();
            setSelectedReview(null);
        } catch (err) {
            alert(err instanceof Error ? err.message : "Failed to approve");
        }
    };

    const handleReject = async (reviewId: string, reason = "Does not meet quality standards") => {
        try {
            await fetchWithAuth(`/api/v1/reviews/${reviewId}/reject`, {
                method: "POST",
                body: JSON.stringify({ reason }),
            });
            await loadData();
            setSelectedReview(null);
        } catch (err) {
            alert(err instanceof Error ? err.message : "Failed to reject");
        }
    };

    if (loading && !stats) {
        return (
            <div className="min-h-screen bg-[var(--bg-0)] flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
            </div>
        );
    }

    return (
        <AppShell showTopBar={false}>
            <div className="min-h-screen bg-[var(--bg-0)] text-[var(--fg-0)]">
                <PageHeader
                    title="Review Queue"
                    subtitle="Manage tool submissions and promotions"
                    icon={Shield}
                    backHref="/admin"
                    backLabel="Admin Dashboard"
                    actions={
                        <Button
                            size="sm"
                            variant="secondary"
                            onClick={loadData}
                            className="gap-2"
                        >
                            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                            Refresh
                        </Button>
                    }
                />

                <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
                    {/* Stats */}
                    {stats && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <StatCard title="Pending" value={stats.pending_count} icon={Clock} color="yellow" />
                            <StatCard title="In Progress" value={stats.in_progress_count} icon={User} color="blue" />
                            <StatCard title="Decided Today" value={stats.decided_today} icon={CheckCircle} color="green" />
                            <StatCard title="Avg Auto Score" value={stats.avg_auto_score.toFixed(1)} icon={Zap} color="purple" />
                        </div>
                    )}

                    {/* Filters */}
                    <div className="flex items-center gap-2">
                        <Filter className="w-4 h-4 text-[var(--fg-muted)]" />
                        <Tabs value={filter ?? "all"} onValueChange={(value) => setFilter(value === "all" ? null : value)}>
                            <TabsList className="flex flex-wrap gap-2">
                                {["all", "fork_submission", "tier_promotion", "code_update"].map((type) => (
                                    <TabsTrigger key={type} value={type}>
                                        {type === "all" ? "All" : type.replace(/_/g, " ")}
                                    </TabsTrigger>
                                ))}
                            </TabsList>
                        </Tabs>
                    </div>

                    {/* Review Grid */}
                    {reviews.length === 0 ? (
                        <EmptyState
                            icon={CheckCircle}
                            title="No pending reviews"
                            description="All caught up! 🎉"
                        />
                    ) : (
                        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {reviews.map((review) => (
                                <ReviewCard
                                    key={review.id}
                                    review={review}
                                    onView={() => setSelectedReview(review.id)}
                                    onApprove={() => handleApprove(review.id)}
                                    onReject={() => handleReject(review.id)}
                                />
                            ))}
                        </div>
                    )}
                </div>

                {selectedReview && (
                    <ReviewDetailModal
                        reviewId={selectedReview}
                        onClose={() => setSelectedReview(null)}
                        onApprove={() => handleApprove(selectedReview)}
                        onReject={() => handleReject(selectedReview)}
                    />
                )}
            </div>
        </AppShell>
    );
}
