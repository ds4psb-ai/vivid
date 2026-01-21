"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, Clock, ChevronRight, BookOpen, Loader2 } from "lucide-react";

interface WorkflowStep {
    tool_id: string;
    name: string;
    dimension: string;
}

interface WorkflowRecommendation {
    template: string;
    steps: WorkflowStep[];
    confidence: number;
    reasoning: string;
}

interface WorkflowRecommendationPanelProps {
    ipSlug: string;
    ipGenre?: string;
    language?: "ko" | "en";
}

export default function WorkflowRecommendationPanel({
    ipSlug,
    ipGenre,
    language = "ko",
}: WorkflowRecommendationPanelProps) {
    const router = useRouter();
    const [userPrompt, setUserPrompt] = useState("");
    const [recommendation, setRecommendation] = useState<WorkflowRecommendation | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleRecommend = async () => {
        if (!userPrompt.trim()) return;

        setLoading(true);
        setError(null);

        try {
            const response = await fetch("/api/v1/tools/recommend-workflow", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_prompt: userPrompt,
                    ip_slug: ipSlug,
                    content_type: ipGenre?.includes("shortform") ? "shortform" : "anime-mv",
                }),
            });

            if (!response.ok) {
                throw new Error("Recommendation failed");
            }

            const data = await response.json();
            setRecommendation(data);

            // Auto-scroll to results
            setTimeout(() => {
                document.getElementById("workflow-results")?.scrollIntoView({
                    behavior: "smooth",
                    block: "center",
                });
            }, 100);
        } catch (err) {
            console.error("Workflow recommendation error:", err);
            setError(language === "ko" ? "추천 생성에 실패했습니다." : "Failed to generate recommendation.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="mt-8 mb-8 p-6 bg-slate-100/50 dark:bg-slate-800/50 rounded-2xl border border-slate-200 dark:border-slate-700">
            {/* Header */}
            <div className="flex items-center gap-2 mb-4">
                <Sparkles className="w-5 h-5 text-violet-500 animate-pulse" />
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                    {language === "ko" ? "AI 워크플로우 추천" : "AI Workflow Recommendation"}
                </h3>
            </div>

            {/* Prompt Input */}
            <div className="flex gap-3 mb-6">
                <input
                    value={userPrompt}
                    onChange={(e) => setUserPrompt(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && !loading && handleRecommend()}
                    placeholder={
                        language === "ko"
                            ? "원하는 변주 방향을 입력하세요 (예: 캐릭터를 사이버펑크 스타일로 변주해줘)"
                            : "Enter variation prompt (e.g., Remix this character in cyberpunk style)"
                    }
                    className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all"
                    disabled={loading}
                />
                <button
                    onClick={handleRecommend}
                    disabled={loading || !userPrompt.trim()}
                    className="px-6 py-3 bg-violet-600 hover:bg-violet-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium rounded-xl shadow-lg transition-all active:scale-95 flex items-center gap-2 shrink-0"
                >
                    {loading ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                        <Sparkles className="w-5 h-5" />
                    )}
                    {language === "ko" ? "추천받기" : "Recommend"}
                </button>
            </div>

            {/* Error State */}
            {error && (
                <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-500/20 rounded-lg text-red-600 dark:text-red-400 text-sm">
                    {error}
                </div>
            )}

            {/* Results */}
            {recommendation && (
                <div id="workflow-results" className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                    {/* Template & Confidence Badge */}
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-violet-600 dark:text-violet-300 bg-violet-100 dark:bg-violet-500/10 px-3 py-1 rounded-full">
                                {recommendation.template}
                            </span>
                            <span className="text-sm text-slate-500 dark:text-slate-400">
                                Confidence: {Math.round(recommendation.confidence * 100)}%
                            </span>
                        </div>
                    </div>

                    {/* Step Cards Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {recommendation.steps.map((step, idx) => (
                            <div
                                key={idx}
                                onClick={() => router.push(`/dimension/${step.tool_id}?ip=${ipSlug}&ref=recommendation`)}
                                className="cursor-pointer group relative bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 hover:border-violet-500/30 rounded-xl p-4 transition-all hover:shadow-lg hover:shadow-violet-500/10"
                            >
                                <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <ChevronRight className="w-4 h-4 text-violet-500" />
                                </div>

                                <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-300">
                                    <span className="text-xs font-bold text-slate-600 dark:text-slate-300">
                                        {step.dimension}
                                    </span>
                                </div>

                                <h4 className="text-sm font-medium text-slate-900 dark:text-white mb-1">
                                    {step.name}
                                </h4>
                                <p className="text-xs text-slate-500 dark:text-slate-400 group-hover:text-violet-500 transition-colors">
                                    Step {idx + 1}
                                </p>
                            </div>
                        ))}
                    </div>

                    {/* Reasoning */}
                    {recommendation.reasoning && (
                        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-500/10 rounded-lg">
                            <p className="text-xs text-blue-600 dark:text-blue-300 leading-relaxed flex items-start gap-2">
                                <BookOpen className="w-3 h-3 mt-0.5 shrink-0" />
                                {recommendation.reasoning}
                            </p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
