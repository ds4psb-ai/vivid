"use client";

/**
 * Admin Review Dashboard
 * 
 * Complete review workflow management:
 * - Queue overview with stats
 * - Review list with filtering
 * - One-click approve/reject
 * - Check results visualization
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
    Shield,
    CheckCircle,
    XCircle,
    Clock,
    AlertTriangle,
    ArrowLeft,
    Loader2,
    Eye,
    ChevronRight,
    TrendingUp,
    User,
    GitFork,
    Zap,
    Filter,
    RefreshCw,
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// =============================================================================
// Types
// =============================================================================

interface ReviewStats {
    pending_count: number;
    in_progress_count: number;
    decided_today: number;
    avg_auto_score: number;
}

interface Review {
    id: string;
    tool_id: string;
    version_id: string | null;
    review_type: string;
    status: string;
    priority: number;
    submitted_by: string;
    submission_notes: string | null;
    assigned_to: string | null;
    auto_checks_passed: boolean;
    auto_checks_score: number;
    created_at: string;
}

interface CheckResult {
    id: string;
    category: string;
    check_name: string;
    description: string | null;
    passed: boolean;
    score: number;
    details: Record<string, any>;
    error_message: string | null;
    is_automated: boolean;
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
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || `Error: ${res.status}`);
    }
    return res.json();
}

// =============================================================================
// Components
// =============================================================================

function StatCard({ title, value, icon: Icon, color }: {
    title: string;
    value: number | string;
    icon: any;
    color: string;
}) {
    return (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
                <span className="text-gray-400 text-sm">{title}</span>
                <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <div className="text-3xl font-bold text-white">{value}</div>
        </div>
    );
}

function ReviewCard({ review, onView, onApprove, onReject }: {
    review: Review;
    onView: () => void;
    onApprove: () => void;
    onReject: () => void;
}) {
    const getStatusBadge = () => {
        switch (review.status) {
            case "pending":
                return <span className="px-2 py-1 text-xs bg-yellow-500/20 text-yellow-400 rounded">Pending</span>;
            case "in_progress":
                return <span className="px-2 py-1 text-xs bg-blue-500/20 text-blue-400 rounded">In Progress</span>;
            case "approved":
                return <span className="px-2 py-1 text-xs bg-green-500/20 text-green-400 rounded">Approved</span>;
            case "rejected":
                return <span className="px-2 py-1 text-xs bg-red-500/20 text-red-400 rounded">Rejected</span>;
            default:
                return null;
        }
    };

    const getTypeIcon = () => {
        switch (review.review_type) {
            case "fork_submission":
                return <GitFork className="w-4 h-4" />;
            case "tier_promotion":
                return <TrendingUp className="w-4 h-4" />;
            default:
                return <Zap className="w-4 h-4" />;
        }
    };

    return (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5 hover:border-purple-500/50 transition-colors">
            <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-500/20 rounded-lg">
                        {getTypeIcon()}
                    </div>
                    <div>
                        <div className="font-medium text-white">{review.review_type.replace("_", " ")}</div>
                        <div className="text-sm text-gray-400">
                            by {review.submitted_by.slice(0, 8)}...
                        </div>
                    </div>
                </div>
                {getStatusBadge()}
            </div>

            {/* Auto-check score */}
            <div className="mb-4">
                <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-400">Auto-check Score</span>
                    <span className={review.auto_checks_passed ? "text-green-400" : "text-red-400"}>
                        {review.auto_checks_score.toFixed(1)}
                    </span>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div
                        className={`h-full ${review.auto_checks_passed ? "bg-green-500" : "bg-red-500"}`}
                        style={{ width: `${Math.min(100, review.auto_checks_score)}%` }}
                    />
                </div>
            </div>

            {/* Submission notes */}
            {review.submission_notes && (
                <p className="text-sm text-gray-400 mb-4 line-clamp-2">
                    {review.submission_notes}
                </p>
            )}

            {/* Actions */}
            <div className="flex items-center gap-2">
                <button
                    onClick={onView}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm"
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

            <div className="mt-3 text-xs text-gray-500">
                {new Date(review.created_at).toLocaleDateString("ko-KR", {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                })}
            </div>
        </div>
    );
}

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
    const [data, setData] = useState<any>(null);
    const [rejecting, setRejecting] = useState(false);
    const [rejectReason, setRejectReason] = useState("");

    useEffect(() => {
        const load = async () => {
            try {
                const result = await fetchWithAuth(`${API_BASE_URL}/api/v1/reviews/${reviewId}`);
                setData(result);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [reviewId]);

    if (loading) {
        return (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                <div className="bg-gray-900 rounded-xl p-8">
                    <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-6">
            <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="sticky top-0 bg-gray-900 border-b border-gray-700 p-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                            <Shield className="w-5 h-5 text-purple-400" />
                            Review Details
                        </h2>
                        <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl">
                            ×
                        </button>
                    </div>
                </div>

                <div className="p-6 space-y-6">
                    {/* Tool Info */}
                    {data?.tool && (
                        <div className="bg-gray-800/50 rounded-lg p-4">
                            <h3 className="font-medium text-white mb-2">{data.tool.display_name}</h3>
                            <div className="flex items-center gap-4 text-sm text-gray-400">
                                <span>Key: {data.tool.tool_key}</span>
                                <span>Tier: {data.tool.tier}</span>
                            </div>
                        </div>
                    )}

                    {/* Check Results */}
                    <div>
                        <h3 className="font-medium text-white mb-3">Automated Checks</h3>
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
                                            <span className="font-medium text-white">{check.check_name}</span>
                                            <span className="text-xs text-gray-500 bg-gray-700 px-2 py-0.5 rounded">
                                                {check.category}
                                            </span>
                                        </div>
                                        <span className={check.passed ? "text-green-400" : "text-red-400"}>
                                            {check.score.toFixed(0)}
                                        </span>
                                    </div>
                                    {check.description && (
                                        <p className="text-sm text-gray-400">{check.description}</p>
                                    )}
                                    {check.error_message && (
                                        <p className="text-sm text-red-400 mt-2">{check.error_message}</p>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Rejection Form */}
                    {rejecting && (
                        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                            <h4 className="font-medium text-red-400 mb-2">Rejection Reason</h4>
                            <textarea
                                value={rejectReason}
                                onChange={(e) => setRejectReason(e.target.value)}
                                rows={3}
                                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white resize-none"
                                placeholder="Explain why this review is rejected..."
                            />
                        </div>
                    )}

                    {/* Actions */}
                    {data?.review?.status === "pending" && (
                        <div className="flex items-center gap-3">
                            <button
                                onClick={onApprove}
                                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-green-500 hover:bg-green-600 text-white font-medium rounded-lg"
                            >
                                <CheckCircle className="w-5 h-5" />
                                Approve
                            </button>
                            {rejecting ? (
                                <button
                                    onClick={() => {
                                        if (rejectReason.length >= 10) {
                                            onReject();
                                        }
                                    }}
                                    disabled={rejectReason.length < 10}
                                    className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-red-500 hover:bg-red-600 text-white font-medium rounded-lg disabled:opacity-50"
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
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState<ReviewStats | null>(null);
    const [reviews, setReviews] = useState<Review[]>([]);
    const [filter, setFilter] = useState<string | null>(null);
    const [selectedReview, setSelectedReview] = useState<string | null>(null);
    const [actionLoading, setActionLoading] = useState(false);

    const loadData = async () => {
        setLoading(true);
        try {
            const [statsData, queueData] = await Promise.all([
                fetchWithAuth(`${API_BASE_URL}/api/v1/reviews/stats`),
                fetchWithAuth(`${API_BASE_URL}/api/v1/reviews/queue${filter ? `?review_type=${filter}` : ""}`),
            ]);
            setStats(statsData);
            setReviews(queueData);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, [filter]);

    const handleApprove = async (reviewId: string) => {
        setActionLoading(true);
        try {
            await fetchWithAuth(`${API_BASE_URL}/api/v1/reviews/${reviewId}/approve`, {
                method: "POST",
                body: JSON.stringify({ notes: "Approved via admin dashboard" }),
            });
            await loadData();
            setSelectedReview(null);
        } catch (err) {
            alert(err instanceof Error ? err.message : "Failed to approve");
        } finally {
            setActionLoading(false);
        }
    };

    const handleReject = async (reviewId: string, reason: string = "Does not meet quality standards") => {
        setActionLoading(true);
        try {
            await fetchWithAuth(`${API_BASE_URL}/api/v1/reviews/${reviewId}/reject`, {
                method: "POST",
                body: JSON.stringify({ reason }),
            });
            await loadData();
            setSelectedReview(null);
        } catch (err) {
            alert(err instanceof Error ? err.message : "Failed to reject");
        } finally {
            setActionLoading(false);
        }
    };

    if (loading && !stats) {
        return (
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-900 text-white">
            {/* Header */}
            <div className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <button
                        onClick={() => router.push("/admin")}
                        className="flex items-center gap-2 text-gray-400 hover:text-white mb-3 text-sm"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Admin Dashboard
                    </button>

                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold flex items-center gap-2">
                                <Shield className="w-6 h-6 text-purple-400" />
                                Review Queue
                            </h1>
                            <p className="text-gray-400">Manage tool submissions and promotions</p>
                        </div>

                        <button
                            onClick={loadData}
                            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm"
                        >
                            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                            Refresh
                        </button>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
                {/* Stats */}
                {stats && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <StatCard title="Pending" value={stats.pending_count} icon={Clock} color="text-yellow-400" />
                        <StatCard title="In Progress" value={stats.in_progress_count} icon={User} color="text-blue-400" />
                        <StatCard title="Decided Today" value={stats.decided_today} icon={CheckCircle} color="text-green-400" />
                        <StatCard title="Avg Auto Score" value={stats.avg_auto_score} icon={Zap} color="text-purple-400" />
                    </div>
                )}

                {/* Filters */}
                <div className="flex items-center gap-2">
                    <Filter className="w-4 h-4 text-gray-400" />
                    {["all", "fork_submission", "tier_promotion", "code_update"].map((type) => (
                        <button
                            key={type}
                            onClick={() => setFilter(type === "all" ? null : type)}
                            className={`px-3 py-1.5 rounded-lg text-sm ${(type === "all" && !filter) || filter === type
                                    ? "bg-purple-500 text-white"
                                    : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                                }`}
                        >
                            {type === "all" ? "All" : type.replace("_", " ")}
                        </button>
                    ))}
                </div>

                {/* Review Grid */}
                {reviews.length === 0 ? (
                    <div className="text-center py-20">
                        <CheckCircle className="w-16 h-16 text-green-500/50 mx-auto mb-4" />
                        <h3 className="text-xl font-bold text-gray-400">No pending reviews</h3>
                        <p className="text-gray-500">All caught up! 🎉</p>
                    </div>
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

            {/* Detail Modal */}
            {selectedReview && (
                <ReviewDetailModal
                    reviewId={selectedReview}
                    onClose={() => setSelectedReview(null)}
                    onApprove={() => handleApprove(selectedReview)}
                    onReject={() => handleReject(selectedReview)}
                />
            )}
        </div>
    );
}
