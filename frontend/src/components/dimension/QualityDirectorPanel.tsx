"use client";

import { useState, useCallback } from "react";
import TeachingPanelLayout, {
    type ThemeColor,
    useAsyncOperation,
    useResultExport,
} from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import { CheckCircle, XCircle, AlertTriangle, Download } from "lucide-react";

const CREDIT_COST = 8;
const THEME_COLOR: ThemeColor = "rose";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

interface CriterionResult {
    score: number;
    passed: boolean;
    details: string;
}

interface QualityResult {
    passed: boolean;
    score: number;
    criteria_results: Record<string, CriterionResult>;
    issues: string[];
    suggestions: string[];
}

const CONTENT_TYPES = [
    { value: "prompt", label: "프롬프트" },
    { value: "storyboard", label: "스토리보드" },
    { value: "script", label: "스크립트" },
    { value: "image_prompt", label: "이미지 프롬프트" },
];

const CRITERIA_OPTIONS = [
    { value: "aesthetic", label: "미적 품질", desc: "시각적 아름다움과 예술성" },
    { value: "ad_suitability", label: "광고 적합성", desc: "브랜드 및 광고 목적 부합" },
    { value: "consistency", label: "일관성", desc: "스타일 및 톤 일관성" },
    { value: "safety", label: "안전성", desc: "유해 콘텐츠 검출" },
    { value: "technical", label: "기술적 품질", desc: "해상도, 프레임 등" },
    { value: "narrative", label: "내러티브", desc: "스토리텔링 완성도" },
];

const MODELS = [
    { value: "gemini-2.0-flash-exp", label: "Flash (빠름)" },
    { value: "gemini-1.5-pro", label: "Pro (정확)" },
];

export default function QualityDirectorPanel() {
    const [content, setContent] = useState("");
    const [contentType, setContentType] = useState("prompt");
    const [selectedCriteria, setSelectedCriteria] = useState<string[]>(["aesthetic", "consistency", "safety"]);
    const [model, setModel] = useState("gemini-1.5-pro");
    const [threshold, setThreshold] = useState(70);

    const [showCreditModal, setShowCreditModal] = useState(false);
    const [validationError, setValidationError] = useState<string | null>(null);

    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();

    // Export utilities
    const { exportJSON } = useResultExport();

    // Async operation hook
    const {
        isLoading,
        progress,
        error,
        data: result,
        execute,
        cancel,
        retry,
        canRetry,
        currentRetryCount,
    } = useAsyncOperation<{ success: boolean; output: QualityResult; error?: string }>({
        onSuccess: (data) => {
            if (data.success && !byokKey && creditCtx) {
                void creditCtx.refresh();
            }
        },
        onError: (err) => {
            if (err.message.includes("크레딧") || err.message.includes("402")) {
                setShowCreditModal(true);
            }
        },
        retryCount: 3,
        retryDelay: 1000,
        nonRetryableErrors: ["400", "401", "402", "403", "404", "크레딧", "부족"],
    });

    const toggleCriterion = (criterion: string) => {
        setSelectedCriteria(prev =>
            prev.includes(criterion)
                ? prev.filter(c => c !== criterion)
                : [...prev, criterion]
        );
    };

    const MAX_CONTENT_LENGTH = 5000;

    const handleCheck = useCallback(async () => {
        const trimmedContent = content.trim();
        if (!trimmedContent) {
            setValidationError("검수할 콘텐츠를 입력해주세요");
            return;
        }
        if (trimmedContent.length > MAX_CONTENT_LENGTH) {
            setValidationError(`콘텐츠는 ${MAX_CONTENT_LENGTH}자 이하로 입력해주세요`);
            return;
        }
        if (selectedCriteria.length === 0) {
            setValidationError("최소 하나의 검수 기준을 선택해주세요");
            return;
        }
        setValidationError(null);

        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
            setShowCreditModal(true);
            return;
        }

        await execute(
            `${API_BASE}/api/dimension/quality/check`,
            {
                content,
                content_type: contentType,
                criteria: selectedCriteria,
                model,
                threshold,
            },
            getBYOKHeaders(byokKey)
        );
    }, [content, contentType, selectedCriteria, model, threshold, byokKey, creditCtx, execute]);

    // Export result as JSON
    const handleExportJson = useCallback(() => {
        if (!result?.output) return;
        exportJSON(result.output, `quality-check-${Date.now()}.json`);
    }, [result?.output, exportJSON]);

    // Extracted result data for display
    const displayResult = result?.success ? result.output : null;
    const displayError = validationError || (result && !result.success ? result.error : error);

    const getScoreColor = (score: number) => {
        if (score >= 80) return "text-emerald-400";
        if (score >= 60) return "text-amber-400";
        return "text-rose-400";
    };

    const SidebarContent = (
        <>
            {/* Content Input */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1">검수 콘텐츠</label>
                <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="검수할 프롬프트, 스크립트, 또는 스토리보드를 입력하세요..."
                    className="w-full h-40 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/20 focus:outline-none focus:border-rose-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-rose-400/5 transition-all resize-none text-sm font-light leading-relaxed"
                />
            </div>

            {/* Content Type */}
            <div className="space-y-2">
                <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1">콘텐츠 유형</label>
                <div className="grid grid-cols-2 gap-2">
                    {CONTENT_TYPES.map((type) => (
                        <button
                            key={type.value}
                            onClick={() => setContentType(type.value)}
                            className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${contentType === type.value
                                ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                                : "bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 border border-transparent"
                                }`}
                        >
                            {type.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Criteria Selection */}
            <div className="space-y-2">
                <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1">검수 기준</label>
                <div className="space-y-2">
                    {CRITERIA_OPTIONS.map((criterion) => (
                        <button
                            key={criterion.value}
                            onClick={() => toggleCriterion(criterion.value)}
                            className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-left transition-all ${selectedCriteria.includes(criterion.value)
                                ? "bg-rose-500/10 border border-rose-500/30"
                                : "bg-white/5 border border-white/10 hover:border-white/20"
                                }`}
                        >
                            <div>
                                <div className={`text-sm font-medium ${selectedCriteria.includes(criterion.value) ? "text-rose-400" : "text-zinc-300"}`}>
                                    {criterion.label}
                                </div>
                                <div className="text-[10px] text-zinc-500">{criterion.desc}</div>
                            </div>
                            <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${selectedCriteria.includes(criterion.value)
                                ? "border-rose-500 bg-rose-500"
                                : "border-white/20"
                                }`}>
                                {selectedCriteria.includes(criterion.value) && (
                                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                    </svg>
                                )}
                            </div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Threshold Slider */}
            <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1">통과 기준</label>
                    <span className="text-sm font-mono text-rose-400">{threshold}점</span>
                </div>
                <input
                    type="range"
                    min="50"
                    max="95"
                    value={threshold}
                    onChange={(e) => setThreshold(Number(e.target.value))}
                    className="w-full accent-rose-500"
                />
            </div>

            {/* Model Select */}
            <div className="space-y-2 pt-4 border-t border-white/5">
                <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1">AI 모델</label>
                <div className="relative">
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-rose-400/50 transition-all appearance-none cursor-pointer font-mono"
                    >
                        {MODELS.map((m) => (
                            <option key={m.value} value={m.value} className="bg-[#0F0F1A] text-white">{m.label}</option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-white/30">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            {/* Check Button */}
            <button
                onClick={handleCheck}
                disabled={isLoading || !content.trim() || selectedCriteria.length === 0}
                className="w-full py-4 mt-6 bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-600 text-white font-bold text-base rounded-xl shadow-[0_0_30px_rgba(244,63,94,0.3)] hover:shadow-[0_0_50px_rgba(244,63,94,0.5)] transition-all active:scale-[0.98] flex items-center justify-center gap-3"
            >
                {isLoading ? (
                    <>
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        <span>검수 중...</span>
                    </>
                ) : (
                    <span className="tracking-widest uppercase">품질 검수 시작</span>
                )}
            </button>

            {/* Validation error only - API errors shown in OperationProgress overlay */}
            {validationError && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs">
                    {validationError}
                </div>
            )}
        </>
    );

    return (
        <>
            <TeachingPanelLayout
                title="퀄리티 디렉터"
                sidebarContent={SidebarContent}
                isLoading={isLoading}
                themeColor={THEME_COLOR}
                progress={progress}
                onCancel={cancel}
                onRetry={retry}
                canRetry={canRetry}
                error={displayError}
                retryCount={currentRetryCount}
                maxRetries={3}
            >
                {displayResult ? (
                    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
                        {/* Export Button */}
                        <div className="flex justify-end">
                            <button
                                onClick={handleExportJson}
                                className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg flex items-center gap-2 text-sm text-white/70 hover:text-white transition-all"
                            >
                                <Download className="w-4 h-4" />
                                JSON 내보내기
                            </button>
                        </div>

                        {/* Overall Score */}
                        <div className="relative overflow-hidden rounded-3xl bg-black/40 backdrop-blur-xl border border-white/10 p-8">
                            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-rose-500 to-pink-500" />
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    {displayResult.passed ? (
                                        <CheckCircle className="w-16 h-16 text-emerald-400" />
                                    ) : (
                                        <XCircle className="w-16 h-16 text-rose-400" />
                                    )}
                                    <div>
                                        <h2 className="text-2xl font-bold text-white">
                                            {displayResult.passed ? "검수 통과" : "검수 미통과"}
                                        </h2>
                                        <p className="text-sm text-zinc-400">
                                            {selectedCriteria.length}개 기준 검사 완료
                                        </p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className={`text-5xl font-bold ${getScoreColor(displayResult.score)}`}>
                                        {displayResult.score}
                                    </div>
                                    <div className="text-xs text-zinc-500 uppercase tracking-wider">/ 100</div>
                                </div>
                            </div>
                        </div>

                        {/* Criteria Results */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {Object.entries(displayResult.criteria_results).map(([key, criterion]) => (
                                <div
                                    key={key}
                                    className={`p-5 rounded-2xl border backdrop-blur-sm transition-all ${criterion.passed
                                        ? "bg-emerald-500/5 border-emerald-500/20"
                                        : "bg-rose-500/5 border-rose-500/20"
                                        }`}
                                >
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-2">
                                            {criterion.passed ? (
                                                <CheckCircle className="w-4 h-4 text-emerald-400" />
                                            ) : (
                                                <AlertTriangle className="w-4 h-4 text-rose-400" />
                                            )}
                                            <span className="text-sm font-semibold text-white capitalize">
                                                {CRITERIA_OPTIONS.find(c => c.value === key)?.label || key}
                                            </span>
                                        </div>
                                        <span className={`text-lg font-bold ${getScoreColor(criterion.score)}`}>
                                            {criterion.score}
                                        </span>
                                    </div>
                                    <p className="text-xs text-zinc-400 leading-relaxed">{criterion.details}</p>
                                </div>
                            ))}
                        </div>

                        {/* Issues */}
                        {displayResult.issues.length > 0 && (
                            <div className="p-6 bg-rose-500/5 border border-rose-500/20 rounded-2xl">
                                <h3 className="text-sm font-bold text-rose-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                    <XCircle className="w-4 h-4" />
                                    발견된 문제점
                                </h3>
                                <ul className="space-y-2">
                                    {displayResult.issues.map((issue, i) => (
                                        <li key={i} className="text-sm text-zinc-300 flex items-start gap-2">
                                            <span className="text-rose-400 mt-1">•</span>
                                            {issue}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Suggestions */}
                        {displayResult.suggestions.length > 0 && (
                            <div className="p-6 bg-sky-500/5 border border-sky-500/20 rounded-2xl">
                                <h3 className="text-sm font-bold text-sky-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                    <AlertTriangle className="w-4 h-4" />
                                    개선 제안
                                </h3>
                                <ul className="space-y-2">
                                    {displayResult.suggestions.map((suggestion, i) => (
                                        <li key={i} className="text-sm text-zinc-300 flex items-start gap-2">
                                            <span className="text-sky-400 mt-1">→</span>
                                            {suggestion}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-8">
                        <div className="relative group">
                            <div className="absolute inset-0 bg-rose-500/20 blur-[80px] rounded-full" />
                            <div className="w-32 h-32 rounded-[2rem] bg-white/[0.02] border border-white/10 flex items-center justify-center backdrop-blur-md relative">
                                <CheckCircle className="w-12 h-12 text-white/20 group-hover:text-rose-400 transition-colors" />
                            </div>
                        </div>
                        <div className="text-center space-y-3">
                            <h3 className="text-2xl font-bold text-white tracking-tight">품질 검수 대기</h3>
                            <p className="text-sm text-[var(--fg-muted)] max-w-xs mx-auto font-light leading-relaxed">
                                좌측 패널에서 콘텐츠와 검수 기준을 설정하고<br />
                                <span className="text-rose-400 font-medium">6가지 기준</span>으로 품질을 검증하세요.
                            </p>
                        </div>
                    </div>
                )}
            </TeachingPanelLayout>

            <InsufficientCreditsModal
                isOpen={showCreditModal}
                onClose={() => setShowCreditModal(false)}
                requiredCredits={CREDIT_COST}
                currentBalance={creditCtx?.balance ?? 0}
                onRetry={handleCheck}
            />
        </>
    );
}
