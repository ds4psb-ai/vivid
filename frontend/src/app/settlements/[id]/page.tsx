"use client";

/**
 * Settlement Detail Page
 * 
 * Shows detailed breakdown of a single settlement:
 * - Distribution visualization
 * - Payout list with recipients
 * - Fork lineage
 * - Dispute option
 */

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
    ArrowLeft,
    DollarSign,
    Users,
    GitFork,
    Clock,
    CheckCircle,
    AlertTriangle,
    XCircle,
    ChevronRight,
    Loader2,
    PieChart,
    MessageSquare,
    History,
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// =============================================================================
// Types
// =============================================================================

interface Payout {
    id: string;
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

interface Dispute {
    id: string;
    complainant_id: string;
    reason: string;
    status: string;
    resolution: string | null;
    created_at: string;
}

interface Settlement {
    id: string;
    tool_run_id: string;
    tool_id: string | null;
    tool_key: string;
    status: string;
    total_credits: number;
    platform_fee: number;
    creator_pool: number;
    lineage_depth: number;
    attribution_score: number | null;
    payer_user_id: string;
    created_at: string;
    completed_at: string | null;
    payouts: Payout[];
    disputes: Dispute[];
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

async function getSettlement(id: string): Promise<Settlement> {
    return fetchWithAuth(`${API_BASE_URL}/api/v1/settlements/${id}`);
}

async function createDispute(
    settlementId: string,
    reason: string,
    expectedAmount?: number
): Promise<void> {
    return fetchWithAuth(`${API_BASE_URL}/api/v1/settlements/${settlementId}/dispute`, {
        method: "POST",
        body: JSON.stringify({ reason, expected_amount: expectedAmount }),
    });
}

// =============================================================================
// Status Badge
// =============================================================================

function SettlementStatusBadge({ status }: { status: string }) {
    const config: Record<string, { icon: typeof CheckCircle; className: string; label: string }> = {
        completed: {
            icon: CheckCircle,
            className: "bg-green-500/20 text-green-400 border-green-500/40",
            label: "Completed",
        },
        pending: {
            icon: Clock,
            className: "bg-yellow-500/20 text-yellow-400 border-yellow-500/40",
            label: "Pending",
        },
        processing: {
            icon: Loader2,
            className: "bg-blue-500/20 text-blue-400 border-blue-500/40",
            label: "Processing",
        },
        failed: {
            icon: XCircle,
            className: "bg-red-500/20 text-red-400 border-red-500/40",
            label: "Failed",
        },
        disputed: {
            icon: AlertTriangle,
            className: "bg-orange-500/20 text-orange-400 border-orange-500/40",
            label: "Disputed",
        },
        reversed: {
            icon: History,
            className: "bg-gray-500/20 text-gray-400 border-gray-500/40",
            label: "Reversed",
        },
    };

    const { icon: Icon, className, label } = config[status] || config.pending;

    return (
        <span className={`inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg border ${className}`}>
            <Icon className={`w-4 h-4 ${status === "processing" ? "animate-spin" : ""}`} />
            {label}
        </span>
    );
}

// =============================================================================
// Distribution Chart
// =============================================================================

function DistributionChart({ settlement }: { settlement: Settlement }) {
    const total = settlement.total_credits;
    const platformFee = settlement.platform_fee;
    const creatorPool = settlement.creator_pool;

    const platformPercent = Math.round((platformFee / total) * 100);
    const creatorPercent = 100 - platformPercent;

    return (
        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
                <PieChart className="w-5 h-5 text-purple-400" />
                <h3 className="text-lg font-semibold">Distribution</h3>
            </div>

            <div className="space-y-4">
                {/* Total */}
                <div className="flex justify-between items-center pb-3 border-b border-gray-700">
                    <span className="text-gray-400">Total Revenue</span>
                    <span className="text-2xl font-bold text-white">
                        {total.toLocaleString()} credits
                    </span>
                </div>

                {/* Platform Fee */}
                <div className="space-y-2">
                    <div className="flex justify-between items-center">
                        <span className="text-gray-400">Platform Fee (30%)</span>
                        <span className="text-red-400 font-medium">
                            -{platformFee.toLocaleString()}
                        </span>
                    </div>
                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-red-500/50"
                            style={{ width: `${platformPercent}%` }}
                        />
                    </div>
                </div>

                {/* Creator Pool */}
                <div className="space-y-2">
                    <div className="flex justify-between items-center">
                        <span className="text-gray-400">Creator Pool ({creatorPercent}%)</span>
                        <span className="text-emerald-400 font-medium">
                            {creatorPool.toLocaleString()}
                        </span>
                    </div>
                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-emerald-500"
                            style={{ width: `${creatorPercent}%` }}
                        />
                    </div>
                </div>

                {/* Attribution Score */}
                {settlement.attribution_score !== null && (
                    <div className="mt-4 pt-4 border-t border-gray-700">
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400">Attribution Score</span>
                            <span className="text-purple-400 font-medium">
                                {settlement.attribution_score.toFixed(1)}%
                            </span>
                        </div>
                        <div className="h-2 bg-gray-700 rounded-full overflow-hidden mt-2">
                            <div
                                className="h-full bg-gradient-to-r from-purple-500 to-purple-400"
                                style={{ width: `${settlement.attribution_score}%` }}
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

// =============================================================================
// Payouts List
// =============================================================================

function PayoutsList({ payouts }: { payouts: Payout[] }) {
    return (
        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
                <Users className="w-5 h-5 text-blue-400" />
                <h3 className="text-lg font-semibold">Recipients</h3>
            </div>

            <div className="space-y-3">
                {payouts.map((payout, index) => (
                    <div
                        key={payout.id}
                        className="bg-gray-900/50 rounded-lg p-4 border border-gray-700/30"
                    >
                        <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                                <span
                                    className={`px-2 py-0.5 text-xs font-medium rounded ${payout.share_type === "owner"
                                            ? "bg-emerald-500/20 text-emerald-400"
                                            : "bg-blue-500/20 text-blue-400"
                                        }`}
                                >
                                    {payout.share_type === "owner" ? "Owner" : "Ancestor"}
                                </span>
                                {payout.lineage_position > 0 && (
                                    <span className="text-xs text-gray-500">
                                        Level {payout.lineage_position}
                                    </span>
                                )}
                            </div>
                            <span className="text-emerald-400 font-bold">
                                +{payout.amount.toLocaleString()}
                            </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-400">
                                {payout.recipient_tool_key || payout.recipient_id.slice(0, 8)}
                            </span>
                            <span className="text-gray-500">
                                {(payout.share_rate * 100).toFixed(0)}% share
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

// =============================================================================
// Dispute Modal
// =============================================================================

function DisputeModal({
    isOpen,
    onClose,
    onSubmit,
    loading,
}: {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (reason: string, amount?: number) => void;
    loading: boolean;
}) {
    const [reason, setReason] = useState("");
    const [expectedAmount, setExpectedAmount] = useState("");

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-gray-800 border border-gray-700 rounded-xl w-full max-w-lg">
                <div className="p-6 border-b border-gray-700">
                    <h3 className="text-xl font-bold">File Dispute</h3>
                    <p className="text-gray-400 text-sm mt-1">
                        Explain why you believe this settlement is incorrect
                    </p>
                </div>

                <div className="p-6 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Reason *
                        </label>
                        <textarea
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                            rows={4}
                            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500"
                            placeholder="Describe why you believe the settlement amount is incorrect..."
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Expected Amount (optional)
                        </label>
                        <input
                            type="number"
                            value={expectedAmount}
                            onChange={(e) => setExpectedAmount(e.target.value)}
                            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white"
                            placeholder="What amount did you expect to receive?"
                        />
                    </div>
                </div>

                <div className="p-6 border-t border-gray-700 flex gap-3 justify-end">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-gray-400 hover:text-white"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={() => onSubmit(reason, expectedAmount ? Number(expectedAmount) : undefined)}
                        disabled={reason.length < 10 || loading}
                        className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white font-medium rounded-lg disabled:opacity-50"
                    >
                        {loading ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            "Submit Dispute"
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}

// =============================================================================
// Main Component
// =============================================================================

export default function SettlementDetailPage() {
    const params = useParams();
    const router = useRouter();
    const settlementId = params.id as string;

    const [settlement, setSettlement] = useState<Settlement | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [disputeModalOpen, setDisputeModalOpen] = useState(false);
    const [disputeLoading, setDisputeLoading] = useState(false);

    useEffect(() => {
        if (settlementId) {
            getSettlement(settlementId)
                .then(setSettlement)
                .catch((err) => setError(err.message))
                .finally(() => setLoading(false));
        }
    }, [settlementId]);

    const handleDispute = async (reason: string, expectedAmount?: number) => {
        setDisputeLoading(true);
        try {
            await createDispute(settlementId, reason, expectedAmount);
            setDisputeModalOpen(false);
            // Refresh
            const updated = await getSettlement(settlementId);
            setSettlement(updated);
        } catch (err) {
            alert(err instanceof Error ? err.message : "Failed to create dispute");
        } finally {
            setDisputeLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
            </div>
        );
    }

    if (error || !settlement) {
        return (
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
                <div className="text-center">
                    <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                    <p className="text-red-300">{error || "Settlement not found"}</p>
                    <button
                        onClick={() => router.back()}
                        className="mt-4 text-purple-400 hover:underline"
                    >
                        Go Back
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-900 text-white">
            {/* Header */}
            <div className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-10">
                <div className="max-w-4xl mx-auto px-6 py-4">
                    <button
                        onClick={() => router.back()}
                        className="flex items-center gap-2 text-gray-400 hover:text-white mb-4"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back
                    </button>
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-xl font-bold flex items-center gap-2">
                                <DollarSign className="w-5 h-5 text-emerald-400" />
                                Settlement #{settlement.id.slice(0, 8)}
                            </h1>
                            <p className="text-gray-400 text-sm">{settlement.tool_key}</p>
                        </div>
                        <SettlementStatusBadge status={settlement.status} />
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-4xl mx-auto px-6 py-8">
                <div className="grid md:grid-cols-2 gap-6">
                    <DistributionChart settlement={settlement} />
                    <PayoutsList payouts={settlement.payouts} />
                </div>

                {/* Actions */}
                {settlement.status === "completed" && settlement.disputes.length === 0 && (
                    <div className="mt-6 bg-gray-800/30 border border-gray-700/50 rounded-xl p-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <MessageSquare className="w-5 h-5 text-orange-400" />
                            <span className="text-gray-300">
                                Something wrong with this settlement?
                            </span>
                        </div>
                        <button
                            onClick={() => setDisputeModalOpen(true)}
                            className="px-4 py-2 bg-orange-500/20 hover:bg-orange-500/30 text-orange-400 rounded-lg text-sm font-medium"
                        >
                            File Dispute
                        </button>
                    </div>
                )}

                {/* Disputes */}
                {settlement.disputes.length > 0 && (
                    <div className="mt-6 bg-orange-500/10 border border-orange-500/30 rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-orange-400 mb-4">
                            Disputes ({settlement.disputes.length})
                        </h3>
                        {settlement.disputes.map((dispute) => (
                            <div key={dispute.id} className="bg-gray-900/50 rounded-lg p-4">
                                <p className="text-gray-300 mb-2">{dispute.reason}</p>
                                <div className="flex items-center gap-3 text-sm text-gray-500">
                                    <span className={`px-2 py-0.5 rounded ${dispute.status === "open" ? "bg-orange-500/20 text-orange-400" :
                                            dispute.status === "resolved" ? "bg-green-500/20 text-green-400" :
                                                "bg-gray-500/20 text-gray-400"
                                        }`}>
                                        {dispute.status}
                                    </span>
                                    <span>{new Date(dispute.created_at).toLocaleDateString()}</span>
                                </div>
                                {dispute.resolution && (
                                    <p className="mt-2 text-sm text-gray-400 border-t border-gray-700 pt-2">
                                        <strong>Resolution:</strong> {dispute.resolution}
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <DisputeModal
                isOpen={disputeModalOpen}
                onClose={() => setDisputeModalOpen(false)}
                onSubmit={handleDispute}
                loading={disputeLoading}
            />
        </div>
    );
}
