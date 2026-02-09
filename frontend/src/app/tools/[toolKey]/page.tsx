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
    Clock,
    CheckCircle,
    XCircle,
    AlertTriangle,
    Copy,
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
import ForkToolModal from "@/components/tools/ForkToolModal";
import { useToast } from "@/components/Toast";
import { useLanguage } from "@/contexts/LanguageContext";

// =============================================================================
// Attribution Score Visualization
// =============================================================================

interface AttributionLabels {
    attributionScore: string;
    attributionWillBeCalculated: string;
    lastCalculated: string;
    diff: string;
    tests: string;
    usage: string;
    revenue: string;
    quality: string;
}

function AttributionScoreCard({ score, labels }: { score: AttributionScore | null; labels: AttributionLabels }) {
    if (!score) {
        return (
            <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Shield className="w-5 h-5 text-purple-400" />
                    {labels.attributionScore}
                </h3>
                <p className="text-gray-400 text-sm">
                    {labels.attributionWillBeCalculated}
                </p>
            </div>
        );
    }

    const components = [
        { label: labels.diff, value: score.diff_score, weight: score.weights.diff, color: "bg-blue-500" },
        { label: labels.tests, value: score.test_score, weight: score.weights.test, color: "bg-green-500" },
        { label: labels.usage, value: score.usage_score, weight: score.weights.usage, color: "bg-purple-500" },
        { label: labels.revenue, value: score.revenue_score, weight: score.weights.revenue, color: "bg-yellow-500" },
        { label: labels.quality, value: score.quality_score, weight: score.weights.quality, color: "bg-pink-500" },
    ];

    return (
        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <Shield className="w-5 h-5 text-purple-400" />
                    {labels.attributionScore}
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
                {labels.lastCalculated}: {new Date(score.calculated_at).toLocaleString()}
            </p>
        </div>
    );
}

// =============================================================================
// Run History
// =============================================================================

interface RunLabels {
    recentRuns: string;
    noRunsYet: string;
    inProgress: string;
    inputs: string;
    outputs: string;
    rateThisRun: string;
    addFeedbackOptional: string;
    submit: string;
    cancel: string;
    addFeedback: string;
}

function RunHistoryCard({
    runs,
    onFeedback,
    labels,
}: {
    runs: ToolRunEvent[];
    onFeedback: (runId: string, rating: number, feedback?: string) => void;
    labels: RunLabels;
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
                {labels.recentRuns}
            </h3>

            {runs.length === 0 ? (
                <p className="text-gray-400 text-sm">{labels.noRunsYet}</p>
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
                                            {run.latency_ms ? `${run.latency_ms}ms` : labels.inProgress} • {run.credits_charged} credits
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
                                            <div className="text-xs text-gray-500 mb-1">{labels.inputs}</div>
                                            <pre className="text-xs text-gray-300 bg-gray-800 p-2 rounded overflow-x-auto">
                                                {JSON.stringify(run.inputs_summary, null, 2)}
                                            </pre>
                                        </div>
                                        <div>
                                            <div className="text-xs text-gray-500 mb-1">{labels.outputs}</div>
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
                                                        <span className="text-xs text-gray-400">{labels.rateThisRun}</span>
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
                                                        placeholder={labels.addFeedbackOptional}
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
                                                            {labels.submit}
                                                        </button>
                                                        <button
                                                            onClick={() => setFeedbackRunId(null)}
                                                            className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded"
                                                        >
                                                            {labels.cancel}
                                                        </button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <button
                                                    onClick={() => setFeedbackRunId(run.id)}
                                                    className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-purple-400"
                                                >
                                                    <MessageSquare className="w-3.5 h-3.5" />
                                                    {labels.addFeedback}
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

interface ForkLabels {
    forkHistory: string;
    noForksYet: string;
    flagged: string;
    score: string;
    warning: string;
    testsPassed: string;
    testsPending: string;
    revenue: string;
}

function ForkHistoryCard({ forks, labels }: { forks: ForkEvent[]; labels: ForkLabels }) {
    return (
        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <GitFork className="w-5 h-5 text-emerald-400" />
                {labels.forkHistory}
            </h3>

            {forks.length === 0 ? (
                <p className="text-gray-400 text-sm">{labels.noForksYet}</p>
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
                                                {labels.flagged}
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-xs text-gray-500">
                                        {new Date(fork.created_at).toLocaleString()}
                                    </p>
                                </div>
                                <div className="text-right">
                                    <div className="text-sm font-medium text-purple-400">
                                        {labels.score}: {fork.attribution_score.toFixed(1)}
                                    </div>
                                    <div className="text-xs text-gray-500">
                                        +{fork.diff_lines_added} -{fork.diff_lines_removed} ~{fork.diff_lines_modified}
                                    </div>
                                </div>
                            </div>

                            {fork.is_suspicious && fork.suspicion_reason && (
                                <div className="mt-2 p-2 bg-yellow-500/10 rounded text-xs text-yellow-300">
                                    <strong>{labels.warning}:</strong> {fork.suspicion_reason}
                                </div>
                            )}

                            {fork.fork_reason && (
                                <p className="mt-2 text-xs text-gray-400 italic">
                                    &ldquo;{fork.fork_reason}&rdquo;
                                </p>
                            )}

                            <div className="flex items-center gap-4 mt-3 text-xs">
                                <span className={fork.test_passed ? "text-green-400" : "text-gray-500"}>
                                    {fork.test_passed ? `✓ ${labels.testsPassed}` : `○ ${labels.testsPending}`}
                                </span>
                                <span className="text-gray-500">
                                    {labels.revenue}: {fork.revenue_generated} credits
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
    const toast = useToast();
    const { language } = useLanguage();

    const [tool, setTool] = useState<ToolManifest | null>(null);
    const [runs, setRuns] = useState<ToolRunEvent[]>([]);
    const [forks, setForks] = useState<ForkEvent[]>([]);
    const [attribution, setAttribution] = useState<AttributionScore | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showForkModal, setShowForkModal] = useState(false);

    // i18n labels
    const labels = {
        toolNotFound: language === "ko" ? "도구를 찾을 수 없습니다" : "Tool Not Found",
        backToDashboard: language === "ko" ? "대시보드로 돌아가기" : "Back to Dashboard",
        forkTool: language === "ko" ? "도구 포크" : "Fork Tool",
        totalRuns: language === "ko" ? "총 실행" : "Total Runs",
        forks: language === "ko" ? "포크" : "Forks",
        revenue: language === "ko" ? "수익" : "Revenue",
        rating: language === "ko" ? "평점" : "Rating",
        description: language === "ko" ? "설명" : "Description",
        category: language === "ko" ? "카테고리" : "Category",
        cost: language === "ko" ? "비용" : "Cost",
        createdBy: language === "ko" ? "제작자" : "Created by",
        feedbackSubmitFailed: language === "ko" ? "피드백 제출에 실패했습니다" : "Failed to submit feedback",
        failedToLoadTool: language === "ko" ? "도구를 불러오지 못했습니다" : "Failed to load tool",
        // Attribution labels
        attributionScore: language === "ko" ? "기여도 점수" : "Attribution Score",
        attributionWillBeCalculated: language === "ko" ? "첫 번째 포크 이후 기여도 점수가 계산됩니다." : "Attribution score will be calculated after the first fork.",
        lastCalculated: language === "ko" ? "마지막 계산" : "Last calculated",
        diff: language === "ko" ? "차이" : "Diff",
        tests: language === "ko" ? "테스트" : "Tests",
        usage: language === "ko" ? "사용량" : "Usage",
        quality: language === "ko" ? "품질" : "Quality",
        copyToolKey: language === "ko" ? "툴 키 복사" : "Copy tool key",
        // Run labels
        recentRuns: language === "ko" ? "최근 실행" : "Recent Runs",
        noRunsYet: language === "ko" ? "아직 실행 기록이 없습니다" : "No runs yet",
        inProgress: language === "ko" ? "진행 중" : "In progress",
        inputs: language === "ko" ? "입력" : "Inputs",
        outputs: language === "ko" ? "출력" : "Outputs",
        rateThisRun: language === "ko" ? "이 실행 평가:" : "Rate this run:",
        addFeedbackOptional: language === "ko" ? "피드백 추가 (선택)" : "Add feedback (optional)",
        submit: language === "ko" ? "제출" : "Submit",
        cancel: language === "ko" ? "취소" : "Cancel",
        addFeedback: language === "ko" ? "피드백 추가" : "Add Feedback",
        // Fork labels
        forkHistory: language === "ko" ? "포크 기록" : "Fork History",
        noForksYet: language === "ko" ? "아직 포크가 없습니다. 첫 번째로 포크하세요!" : "No forks yet. Be the first to fork this tool!",
        flagged: language === "ko" ? "신고됨" : "Flagged",
        score: language === "ko" ? "점수" : "Score",
        warning: language === "ko" ? "경고" : "Warning",
        testsPassed: language === "ko" ? "테스트 통과" : "Tests Passed",
        testsPending: language === "ko" ? "테스트 대기 중" : "Tests Pending",
    };

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
            setError(err instanceof Error ? err.message : labels.failedToLoadTool);
        } finally {
            setLoading(false);
        }
    }, [toolKey, labels.failedToLoadTool]);

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
            toast.error(labels.feedbackSubmitFailed);
        }
    };

    const handleFork = () => {
        setShowForkModal(true);
    };

    const handleForkSuccess = (newToolKey: string) => {
        setShowForkModal(false);
        router.push(`/tools/${newToolKey}`);
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
                    <h2 className="text-xl text-white mb-2">{labels.toolNotFound}</h2>
                    <p className="text-gray-400 mb-4">{error}</p>
                    <button
                        onClick={() => router.push("/tools")}
                        className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg"
                    >
                        {labels.backToDashboard}
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
                        {labels.backToDashboard}
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
                                <button
                                    type="button"
                                    onClick={copyToolKey}
                                    className="p-1 hover:text-white"
                                    aria-label={labels.copyToolKey}
                                >
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
                                {labels.forkTool}
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
                            <span className="text-sm">{labels.totalRuns}</span>
                        </div>
                        <div className="text-2xl font-bold">{tool.usage_count}</div>
                    </div>
                    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
                        <div className="flex items-center gap-2 text-gray-400 mb-2">
                            <GitFork className="w-4 h-4" />
                            <span className="text-sm">{labels.forks}</span>
                        </div>
                        <div className="text-2xl font-bold">{tool.fork_count}</div>
                    </div>
                    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
                        <div className="flex items-center gap-2 text-gray-400 mb-2">
                            <DollarSign className="w-4 h-4" />
                            <span className="text-sm">{labels.revenue}</span>
                        </div>
                        <div className="text-2xl font-bold text-emerald-400">{tool.total_revenue}</div>
                    </div>
                    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
                        <div className="flex items-center gap-2 text-gray-400 mb-2">
                            <Star className="w-4 h-4" />
                            <span className="text-sm">{labels.rating}</span>
                        </div>
                        <div className="text-2xl font-bold">
                            {tool.quality_rating ? tool.quality_rating.toFixed(1) : "—"}
                        </div>
                    </div>
                </div>

                {/* Description */}
                <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 mb-8">
                    <h3 className="text-lg font-semibold mb-3">{labels.description}</h3>
                    <p className="text-gray-300">{tool.description}</p>
                    <div className="flex items-center gap-4 mt-4 text-sm text-gray-500">
                        <span>{labels.category}: {tool.category}</span>
                        <span>•</span>
                        <span>{labels.cost}: {tool.credit_cost} credits</span>
                        <span>•</span>
                        <span>{labels.createdBy}: {tool.created_by}</span>
                    </div>
                </div>

                {/* Two Column Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <AttributionScoreCard
                        score={attribution}
                        labels={{
                            attributionScore: labels.attributionScore,
                            attributionWillBeCalculated: labels.attributionWillBeCalculated,
                            lastCalculated: labels.lastCalculated,
                            diff: labels.diff,
                            tests: labels.tests,
                            usage: labels.usage,
                            revenue: labels.revenue,
                            quality: labels.quality,
                        }}
                    />
                    <ForkHistoryCard
                        forks={forks}
                        labels={{
                            forkHistory: labels.forkHistory,
                            noForksYet: labels.noForksYet,
                            flagged: labels.flagged,
                            score: labels.score,
                            warning: labels.warning,
                            testsPassed: labels.testsPassed,
                            testsPending: labels.testsPending,
                            revenue: labels.revenue,
                        }}
                    />
                </div>

                <div className="mt-6">
                    <RunHistoryCard
                        runs={runs}
                        onFeedback={handleFeedback}
                        labels={{
                            recentRuns: labels.recentRuns,
                            noRunsYet: labels.noRunsYet,
                            inProgress: labels.inProgress,
                            inputs: labels.inputs,
                            outputs: labels.outputs,
                            rateThisRun: labels.rateThisRun,
                            addFeedbackOptional: labels.addFeedbackOptional,
                            submit: labels.submit,
                            cancel: labels.cancel,
                            addFeedback: labels.addFeedback,
                        }}
                    />
                </div>
            </div>

            {/* Fork Modal */}
            {showForkModal && tool && (
                <ForkToolModal
                    toolId={tool.id}
                    toolName={tool.tool_key}
                    toolKey={toolKey}
                    onClose={() => setShowForkModal(false)}
                    onSuccess={handleForkSuccess}
                />
            )}
        </div>
    );
}
