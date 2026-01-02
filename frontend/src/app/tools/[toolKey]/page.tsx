"use client";

/**
 * Tool Detail Page
 * 
 * UX Hardening Features:
 * - Attribution Score visualization with radar chart
 * - Fork history with diff preview
 * - Run history with status timeline
 * - Feedback submission with star rating
 * - Fork button with confirmation
 * - Sybil warning display
 * - Revenue breakdown
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
    ArrowLeft,
    GitFork,
    Star,
    Zap,
    TrendingUp,
    Clock,
    CheckCircle,
    XCircle,
    AlertTriangle,
    Copy,
    ExternalLink,
    Play,
    MessageSquare,
    ChevronDown,
    ChevronUp,
    Loader2,
    Shield,
    DollarSign,
} from "lucide-react";
import * as telemetryApi from "@/lib/telemetry-api";
import type {
    ToolManifest,
    ToolRunEvent,
    ForkEvent,
    AttributionScore,
} from "@/lib/telemetry-api";

// =============================================================================
// Attribution Score Visualization
// =============================================================================

function AttributionScoreCard({ score }: { score: AttributionScore | null }) {
    if (!score) {
        return (
            <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Shield className="w-5 h-5 text-purple-400" />
                    Attribution Score
                </h3>
                <p className="text-gray-400 text-sm">
                    Attribution score will be calculated after the first fork.
                </p>
            </div>
        );
    }

    const components = [
        { label: "Diff", value: score.diff_score, weight: score.weights.diff, color: "bg-blue-500" },
        { label: "Tests", value: score.test_score, weight: score.weights.test, color: "bg-green-500" },
        { label: "Usage", value: score.usage_score, weight: score.weights.usage, color: "bg-purple-500" },
        { label: "Revenue", value: score.revenue_score, weight: score.weights.revenue, color: "bg-yellow-500" },
        { label: "Quality", value: score.quality_score, weight: score.weights.quality, color: "bg-pink-500" },
    ];

    return (
        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <Shield className="w-5 h-5 text-purple-400" />
                    Attribution Score
                </h3>
                <div className="text-3xl font-bold text-purple-400">
                    {score.total_score.toFixed(1)}
                </div>
            </div>

            <div className="space-y-3">
                {components.map(({ label, value, weight, color }) => (
                    <div key={label}>
                        <div className="flex items-center justify-between text-sm mb-1">
                            <span className="text-gray-400">
                                {label} <span className="text-gray-600">({(weight * 100).toFixed(0)}%)</span>
                            </span>
                            <span className="text-white font-medium">{value.toFixed(1)}</span>
                        </div>
                        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                            <div
                                className={`h-full ${color} rounded-full transition-all duration-500`}
                                style={{ width: `${value}%` }}
                            />
                        </div>
                    </div>
                ))}
            </div>

            <p className="text-xs text-gray-500 mt-4">
                Last calculated: {new Date(score.calculated_at).toLocaleString()}
            </p>
        </div>
    );
}

// =============================================================================
// Run History
// =============================================================================

function RunHistoryCard({
    runs,
    onFeedback,
}: {
    runs: ToolRunEvent[];
    onFeedback: (runId: string, rating: number, feedback?: string) => void;
}) {
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [feedbackRunId, setFeedbackRunId] = useState<string | null>(null);
    const [rating, setRating] = useState(0);
    const [feedback, setFeedback] = useState("");

    const getStatusIcon = (status: string) => {
        switch (status) {
            case "success":
                return <CheckCircle className="w-4 h-4 text-green-400" />;
            case "failed":
                return <XCircle className="w-4 h-4 text-red-400" />;
            case "timeout":
                return <Clock className="w-4 h-4 text-yellow-400" />;
            default:
                return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
        }
    };

    const handleSubmitFeedback = (runId: string) => {
        if (rating > 0) {
            onFeedback(runId, rating, feedback || undefined);
            setFeedbackRunId(null);
            setRating(0);
            setFeedback("");
        }
    };

    return (
        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Play className="w-5 h-5 text-blue-400" />
                Recent Runs
            </h3>

            {runs.length === 0 ? (
                <p className="text-gray-400 text-sm">No runs yet</p>
            ) : (
                <div className="space-y-3">
                    {runs.slice(0, 10).map((run) => (
                        <div
                            key={run.id}
                            className="bg-gray-900/50 rounded-lg border border-gray-700/30"
                        >
                            <div
                                className="flex items-center justify-between p-3 cursor-pointer"
                                onClick={() => setExpandedId(expandedId === run.id ? null : run.id)}
                            >
                                <div className="flex items-center gap-3">
                                    {getStatusIcon(run.status)}
                                    <div>
                                        <div className="text-sm text-white">
                                            {new Date(run.created_at).toLocaleString()}
                                        </div>
                                        <div className="text-xs text-gray-500">
                                            {run.latency_ms ? `${run.latency_ms}ms` : "In progress"} • {run.credits_charged} credits
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    {run.user_rating && (
                                        <div className="flex items-center gap-1 text-yellow-400">
                                            <Star className="w-3 h-3 fill-current" />
                                            <span className="text-xs">{run.user_rating}</span>
                                        </div>
                                    )}
                                    {expandedId === run.id ? (
                                        <ChevronUp className="w-4 h-4 text-gray-400" />
                                    ) : (
                                        <ChevronDown className="w-4 h-4 text-gray-400" />
                                    )}
                                </div>
                            </div>

                            {expandedId === run.id && (
                                <div className="px-3 pb-3 border-t border-gray-700/30">
                                    <div className="grid grid-cols-2 gap-4 py-3">
                                        <div>
                                            <div className="text-xs text-gray-500 mb-1">Inputs</div>
                                            <pre className="text-xs text-gray-300 bg-gray-800 p-2 rounded overflow-x-auto">
                                                {JSON.stringify(run.inputs_summary, null, 2)}
                                            </pre>
                                        </div>
                                        <div>
                                            <div className="text-xs text-gray-500 mb-1">Outputs</div>
                                            <pre className="text-xs text-gray-300 bg-gray-800 p-2 rounded overflow-x-auto">
                                                {JSON.stringify(run.outputs_summary, null, 2)}
                                            </pre>
                                        </div>
                                    </div>

                                    {run.error_message && (
                                        <div className="bg-red-500/10 border border-red-500/30 rounded p-2 mb-3">
                                            <p className="text-xs text-red-300">{run.error_message}</p>
                                        </div>
                                    )}

                                    {!run.user_rating && (
                                        <div className="pt-3 border-t border-gray-700/30">
                                            {feedbackRunId === run.id ? (
                                                <div className="space-y-2">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-xs text-gray-400">Rate this run:</span>
                                                        <div className="flex gap-1">
                                                            {[1, 2, 3, 4, 5].map((star) => (
                                                                <button
                                                                    key={star}
                                                                    onClick={() => setRating(star)}
                                                                    className="p-0.5"
                                                                >
                                                                    <Star
                                                                        className={`w-5 h-5 ${star <= rating
                                                                                ? "text-yellow-400 fill-yellow-400"
                                                                                : "text-gray-600"
                                                                            }`}
                                                                    />
                                                                </button>
                                                            ))}
                                                        </div>
                                                    </div>
                                                    <input
                                                        type="text"
                                                        placeholder="Add feedback (optional)"
                                                        value={feedback}
                                                        onChange={(e) => setFeedback(e.target.value)}
                                                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-white"
                                                    />
                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={() => handleSubmitFeedback(run.id)}
                                                            disabled={rating === 0}
                                                            className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 
                                       text-white text-xs rounded transition-colors"
                                                        >
                                                            Submit
                                                        </button>
                                                        <button
                                                            onClick={() => setFeedbackRunId(null)}
                                                            className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded"
                                                        >
                                                            Cancel
                                                        </button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <button
                                                    onClick={() => setFeedbackRunId(run.id)}
                                                    className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-purple-400"
                                                >
                                                    <MessageSquare className="w-3.5 h-3.5" />
                                                    Add Feedback
                                                </button>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// =============================================================================
// Fork History with Sybil Warning
// =============================================================================

function ForkHistoryCard({ forks }: { forks: ForkEvent[] }) {
    return (
        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <GitFork className="w-5 h-5 text-emerald-400" />
                Fork History
            </h3>

            {forks.length === 0 ? (
                <p className="text-gray-400 text-sm">No forks yet. Be the first to fork this tool!</p>
            ) : (
                <div className="space-y-3">
                    {forks.map((fork) => (
                        <div
                            key={fork.id}
                            className={`p-3 rounded-lg border ${fork.is_suspicious
                                    ? "bg-yellow-500/10 border-yellow-500/30"
                                    : "bg-gray-900/50 border-gray-700/30"
                                }`}
                        >
                            <div className="flex items-start justify-between">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm text-white font-medium">{fork.forker_id}</span>
                                        {fork.is_suspicious && (
                                            <span className="flex items-center gap-1 px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-xs rounded-full">
                                                <AlertTriangle className="w-3 h-3" />
                                                Flagged
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-xs text-gray-500">
                                        {new Date(fork.created_at).toLocaleString()}
                                    </p>
                                </div>
                                <div className="text-right">
                                    <div className="text-sm font-medium text-purple-400">
                                        Score: {fork.attribution_score.toFixed(1)}
                                    </div>
                                    <div className="text-xs text-gray-500">
                                        +{fork.diff_lines_added} -{fork.diff_lines_removed} ~{fork.diff_lines_modified}
                                    </div>
                                </div>
                            </div>

                            {fork.is_suspicious && fork.suspicion_reason && (
                                <div className="mt-2 p-2 bg-yellow-500/10 rounded text-xs text-yellow-300">
                                    <strong>Warning:</strong> {fork.suspicion_reason}
                                </div>
                            )}

                            {fork.fork_reason && (
                                <p className="mt-2 text-xs text-gray-400 italic">
                                    &ldquo;{fork.fork_reason}&rdquo;
                                </p>
                            )}

                            <div className="flex items-center gap-4 mt-3 text-xs">
                                <span className={fork.test_passed ? "text-green-400" : "text-gray-500"}>
                                    {fork.test_passed ? "✓ Tests Passed" : "○ Tests Pending"}
                                </span>
                                <span className="text-gray-500">
                                    Revenue: {fork.revenue_generated} credits
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function ToolDetailPage() {
    const params = useParams();
    const router = useRouter();
    const toolKey = params.toolKey as string;

    const [tool, setTool] = useState<ToolManifest | null>(null);
    const [runs, setRuns] = useState<ToolRunEvent[]>([]);
    const [forks, setForks] = useState<ForkEvent[]>([]);
    const [attribution, setAttribution] = useState<AttributionScore | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showForkModal, setShowForkModal] = useState(false);

    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const toolData = await telemetryApi.getTool(toolKey);
            setTool(toolData);

            const [runsData, forksData] = await Promise.all([
                telemetryApi.listRuns({ tool_key: toolKey, limit: 20 }),
                telemetryApi.listForks({ parent_tool_id: toolData.id }),
            ]);

            setRuns(runsData);
            setForks(forksData);

            // Get attribution for first fork if exists
            if (forksData.length > 0) {
                try {
                    const attr = await telemetryApi.calculateAttribution(forksData[0].id);
                    setAttribution(attr);
                } catch {
                    // Attribution may not exist yet
                }
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load tool");
        } finally {
            setLoading(false);
        }
    }, [toolKey]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleFeedback = async (runId: string, rating: number, feedback?: string) => {
        try {
            await telemetryApi.submitRunFeedback(runId, rating, feedback);
            // Refresh runs
            const updatedRuns = await telemetryApi.listRuns({ tool_key: toolKey, limit: 20 });
            setRuns(updatedRuns);
        } catch (err) {
            console.error("Failed to submit feedback:", err);
        }
    };

    const handleFork = () => {
        router.push(`/tools/${toolKey}/fork`);
    };

    const copyToolKey = () => {
        navigator.clipboard.writeText(toolKey);
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
            </div>
        );
    }

    if (error || !tool) {
        return (
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
                <div className="text-center">
                    <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                    <h2 className="text-xl text-white mb-2">Tool Not Found</h2>
                    <p className="text-gray-400 mb-4">{error}</p>
                    <button
                        onClick={() => router.push("/tools")}
                        className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg"
                    >
                        Back to Dashboard
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-900 text-white">
            {/* Header */}
            <div className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <button
                        onClick={() => router.push("/tools")}
                        className="flex items-center gap-2 text-gray-400 hover:text-white mb-4 transition-colors"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back to Dashboard
                    </button>

                    <div className="flex items-start justify-between">
                        <div>
                            <div className="flex items-center gap-3 mb-2">
                                <h1 className="text-2xl font-bold">{tool.display_name}</h1>
                                <span
                                    className={`px-2.5 py-1 text-xs font-medium rounded-full ${tool.tier === "certified"
                                            ? "bg-emerald-500/10 text-emerald-400"
                                            : tool.tier === "verified"
                                                ? "bg-blue-500/10 text-blue-400"
                                                : "bg-yellow-500/10 text-yellow-400"
                                        }`}
                                >
                                    {tool.tier}
                                </span>
                            </div>
                            <div className="flex items-center gap-2 text-gray-400">
                                <code className="text-sm bg-gray-800 px-2 py-0.5 rounded">{tool.tool_key}</code>
                                <button onClick={copyToolKey} className="p-1 hover:text-white">
                                    <Copy className="w-4 h-4" />
                                </button>
                            </div>
                        </div>

                        <div className="flex items-center gap-3">
                            <button
                                onClick={handleFork}
                                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 
                         text-white font-medium rounded-lg transition-colors"
                            >
                                <GitFork className="w-5 h-5" />
                                Fork Tool
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* Stats Row */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
                        <div className="flex items-center gap-2 text-gray-400 mb-2">
                            <Zap className="w-4 h-4" />
                            <span className="text-sm">Total Runs</span>
                        </div>
                        <div className="text-2xl font-bold">{tool.usage_count}</div>
                    </div>
                    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
                        <div className="flex items-center gap-2 text-gray-400 mb-2">
                            <GitFork className="w-4 h-4" />
                            <span className="text-sm">Forks</span>
                        </div>
                        <div className="text-2xl font-bold">{tool.fork_count}</div>
                    </div>
                    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
                        <div className="flex items-center gap-2 text-gray-400 mb-2">
                            <DollarSign className="w-4 h-4" />
                            <span className="text-sm">Revenue</span>
                        </div>
                        <div className="text-2xl font-bold text-emerald-400">{tool.total_revenue}</div>
                    </div>
                    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
                        <div className="flex items-center gap-2 text-gray-400 mb-2">
                            <Star className="w-4 h-4" />
                            <span className="text-sm">Rating</span>
                        </div>
                        <div className="text-2xl font-bold">
                            {tool.quality_rating ? tool.quality_rating.toFixed(1) : "—"}
                        </div>
                    </div>
                </div>

                {/* Description */}
                <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 mb-8">
                    <h3 className="text-lg font-semibold mb-3">Description</h3>
                    <p className="text-gray-300">{tool.description}</p>
                    <div className="flex items-center gap-4 mt-4 text-sm text-gray-500">
                        <span>Category: {tool.category}</span>
                        <span>•</span>
                        <span>Cost: {tool.credit_cost} credits</span>
                        <span>•</span>
                        <span>Created by: {tool.created_by}</span>
                    </div>
                </div>

                {/* Two Column Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <AttributionScoreCard score={attribution} />
                    <ForkHistoryCard forks={forks} />
                </div>

                <div className="mt-6">
                    <RunHistoryCard runs={runs} onFeedback={handleFeedback} />
                </div>
            </div>
        </div>
    );
}
