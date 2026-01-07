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

const CREDIT_COST = 5;
const THEME_COLOR: ThemeColor = "violet";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

interface PromptResult {
    prompt: string;
    negative_prompt?: string;
    style?: {
        cinematography?: string;
        lighting?: string;
        color_grade?: string;
    };
    technical?: {
        aspect_ratio?: string;
        duration?: string;
        fps?: string;
    };
}

const STYLES = [
    { value: "cinematic", label: "시네마틱" },
    { value: "documentary", label: "다큐멘터리" },
    { value: "commercial", label: "광고/커머셜" },
    { value: "artistic", label: "아트/실험" },
    { value: "vlog", label: "브이로그" },
];

const MOODS = [
    { value: "neutral", label: "중립" },
    { value: "dramatic", label: "드라마틱" },
    { value: "calm", label: "차분함" },
    { value: "energetic", label: "에너지틱" },
    { value: "melancholic", label: "멜랑콜릭" },
];

const DURATIONS = [
    { value: "5 seconds", label: "5초" },
    { value: "10 seconds", label: "10초" },
    { value: "15 seconds", label: "15초" },
    { value: "30 seconds", label: "30초" },
    { value: "60 seconds", label: "60초" },
];

const MODELS = [
    { value: "gemini-3.0-flash-preview", label: "Flash (빠름)" },
    { value: "gemini-3.0-pro-preview", label: "Pro (고품질)" },
];

export default function PromptGeneratorPanel() {
    // Form state
    const [topic, setTopic] = useState("");
    const [style, setStyle] = useState("cinematic");
    const [mood, setMood] = useState("neutral");
    const [duration, setDuration] = useState("15 seconds");
    const [language, setLanguage] = useState<"ko" | "en">("ko");
    const [model, setModel] = useState("gemini-3.0-flash-preview");
    const [showCreditModal, setShowCreditModal] = useState(false);
    const [validationError, setValidationError] = useState<string | null>(null);

    // BYOK and credits
    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();

    // Export utilities (copy, download)
    const { copyToClipboard, isCopied, exportJSON } = useResultExport();

    // Async operation hook with progress
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
    } = useAsyncOperation<{ success: boolean; output: PromptResult; error?: string }>({
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

    // Generate prompt
    const MAX_TOPIC_LENGTH = 500;

    const handleGenerate = useCallback(async () => {
        const trimmedTopic = topic.trim();
        if (!trimmedTopic) {
            setValidationError("주제를 입력해주세요");
            return;
        }
        if (trimmedTopic.length > MAX_TOPIC_LENGTH) {
            setValidationError(`주제는 ${MAX_TOPIC_LENGTH}자 이하로 입력해주세요`);
            return;
        }
        setValidationError(null);

        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
            setShowCreditModal(true);
            return;
        }

        await execute(
            `${API_BASE}/api/dimension/1d/generate`,
            { topic, style, mood, duration, language, model },
            getBYOKHeaders(byokKey)
        );
    }, [topic, style, mood, duration, language, model, byokKey, creditCtx, execute]);

    // Copy handler using useResultExport
    const handleCopy = useCallback(
        (text: string) => {
            copyToClipboard(text);
        },
        [copyToClipboard]
    );

    // Export result as JSON
    const handleExportJSON = useCallback(() => {
        if (result?.output) {
            exportJSON(result.output, `veo-prompt-${Date.now()}.json`);
        }
    }, [result?.output, exportJSON]);

    // Extracted result data for display
    const displayResult = result?.success ? result.output : null;
    const displayError = validationError || (result && !result.success ? result.error : error);

    const SidebarContent = (
        <>
            {/* Topic Input */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1 group-focus-within:text-violet-400/80 transition-colors">주제 (Topic)</label>
                <textarea
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="영상의 핵심 주제를 입력하세요..."
                    className="w-full h-32 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/20 focus:outline-none focus:border-violet-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-violet-400/5 transition-all resize-none text-sm font-light leading-relaxed"
                />
            </div>

            {/* Style & Mood */}
            <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2 group">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:text-violet-400/80 transition-colors">스타일</label>
                    <div className="relative">
                        <select
                            value={style}
                            onChange={(e) => setStyle(e.target.value)}
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-violet-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-violet-400/5 transition-all appearance-none cursor-pointer hover:bg-white/[0.07]"
                        >
                            {STYLES.map((s) => (
                                <option key={s.value} value={s.value} className="bg-[#0F0F1A] text-white py-2">{s.label}</option>
                            ))}
                        </select>
                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-white/30 group-focus-within:text-violet-400/50">
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                        </div>
                    </div>
                </div>
                <div className="space-y-2">
                    <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">무드</label>
                    <div className="relative">
                        <select
                            value={mood}
                            onChange={(e) => setMood(e.target.value)}
                            className="w-full px-2 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-violet-400/50 focus:ring-1 focus:ring-violet-400/20 transition-all appearance-none"
                        >
                            {MOODS.map((m) => (
                                <option key={m.value} value={m.value}>{m.label}</option>
                            ))}
                        </select>
                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-white/50">
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                        </div>
                    </div>
                </div>
            </div>

            {/* Duration & Language */}
            <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                    <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">길이</label>
                    <div className="relative">
                        <select
                            value={duration}
                            onChange={(e) => setDuration(e.target.value)}
                            className="w-full px-2 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-violet-400/50 focus:ring-1 focus:ring-violet-400/20 transition-all appearance-none"
                        >
                            {DURATIONS.map((d) => (
                                <option key={d.value} value={d.value}>{d.label}</option>
                            ))}
                        </select>
                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-white/50">
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                        </div>
                    </div>
                </div>
                <div className="space-y-2">
                    <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">언어</label>
                    <div className="flex gap-1 p-1 bg-white/5 rounded-lg border border-white/10">
                        <button
                            onClick={() => setLanguage("ko")}
                            className={`flex-1 py-1 rounded-md text-xs font-medium transition-all ${language === "ko"
                                ? "bg-violet-500 text-white shadow-sm"
                                : "text-zinc-400 hover:text-white hover:bg-white/5"
                                }`}
                        >
                            KO
                        </button>
                        <button
                            onClick={() => setLanguage("en")}
                            className={`flex-1 py-1 rounded-md text-xs font-medium transition-all ${language === "en"
                                ? "bg-violet-500 text-white shadow-sm"
                                : "text-zinc-400 hover:text-white hover:bg-white/5"
                                }`}
                        >
                            EN
                        </button>
                    </div>
                </div>
            </div>

            {/* Model Select */}
            <div className="space-y-4 pt-4 border-t border-white/5 mt-4">
                <div className="space-y-2 group">
                    <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1 group-focus-within:text-violet-400/80 transition-colors">AI 모델 Engine</label>
                    <div className="relative">
                        <select
                            value={model}
                            onChange={(e) => setModel(e.target.value)}
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-violet-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-violet-400/5 transition-all appearance-none cursor-pointer font-mono"
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
            </div>

            {/* Generate Button */}
            <button
                onClick={handleGenerate}
                disabled={isLoading || !topic.trim()}
                className="w-full py-4 mt-6 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-600 text-white font-bold text-base rounded-xl shadow-[0_0_30px_rgba(139,92,246,0.3)] hover:shadow-[0_0_50px_rgba(139,92,246,0.5)] transition-all active:scale-[0.98] flex items-center justify-center gap-3 group relative overflow-hidden"
            >
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                <span className="relative flex items-center gap-2">
                    {isLoading ? (
                        <>
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            <span>PROCESSING...</span>
                        </>
                    ) : (
                        <>
                            <span className="tracking-widest uppercase">Generate Prompt</span>
                            <div className="w-5 h-5 rounded-full bg-white/10 flex items-center justify-center">
                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                            </div>
                        </>
                    )}
                </span>
            </button>

            {/* Validation error only - API errors shown in OperationProgress overlay */}
            {validationError && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs break-keep leading-relaxed animate-in fade-in slide-in-from-top-1">
                    {validationError}
                </div>
            )}
        </>
    );

    return (
        <>
            <TeachingPanelLayout
                title="Veo 프롬프트 생성"
                sidebarContent={SidebarContent}
                isLoading={isLoading}
                themeColor={THEME_COLOR}
                // New progress props for enhanced UX
                progress={progress}
                onCancel={cancel}
                onRetry={retry}
                canRetry={canRetry}
                error={error}
                retryCount={currentRetryCount}
                maxRetries={3}
            >
                {displayResult ? (
                    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
                        {/* Main Prompt */}
                        <div className="group relative">
                            <div className="flex items-center justify-between mb-3 px-1">
                                <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-violet-400"></span>
                                    Generated Prompt
                                </h3>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={handleExportJSON}
                                        className="px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 border border-white/5 hover:border-white/10"
                                        title="JSON으로 내보내기"
                                    >
                                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                        </svg>
                                        Export
                                    </button>
                                    <button
                                        onClick={() => handleCopy(displayResult.prompt)}
                                        className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 ${isCopied
                                            ? "bg-green-500/10 text-green-400 border border-green-500/20"
                                            : "bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 border border-white/5 hover:border-white/10"
                                            }`}
                                    >
                                        {isCopied ? (
                                            <>
                                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                </svg>
                                                Copied
                                            </>
                                        ) : (
                                            <>
                                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                                </svg>
                                                Copy
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>
                            <div className="p-8 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.3)] font-mono text-base leading-relaxed text-zinc-100 whitespace-pre-wrap group-hover:border-violet-500/30 group-hover:bg-black/50 transition-all relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-violet-500 to-purple-500 shadow-[0_0_20px_#8B5CF6]"></div>
                                {displayResult.prompt}
                            </div>
                        </div>

                        {/* Negative Prompt */}
                        {displayResult.negative_prompt && (
                            <div className="group relative">
                                <div className="flex items-center justify-between mb-3 px-1">
                                    <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                                        <span className="w-1.5 h-1.5 rounded-full bg-red-400/50"></span>
                                        Negative Prompt
                                    </h3>
                                    <button
                                        onClick={() => handleCopy(displayResult.negative_prompt || "")}
                                        className="px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 border border-white/5 hover:border-white/10"
                                    >
                                        Copy
                                    </button>
                                </div>
                                <div className="p-5 bg-black/30 backdrop-blur-md border border-white/10 rounded-xl shadow-inner font-mono text-sm leading-relaxed text-zinc-400 whitespace-pre-wrap group-hover:border-white/20 transition-colors">
                                    {displayResult.negative_prompt}
                                </div>
                            </div>
                        )}

                        {/* Technical Details Grid */}
                        {(displayResult.style || displayResult.technical) && (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {displayResult.style && (
                                    <div className="p-6 bg-white/[0.03] backdrop-blur-sm border border-white/5 rounded-xl space-y-4 hover:border-white/10 transition-colors hover:bg-white/[0.05]">
                                        <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest border-b border-white/5 pb-3 mb-1">Style Parameters</h3>
                                        <div className="space-y-4">
                                            {Object.entries(displayResult.style).map(([key, value]) => (
                                                <div key={key} className="flex flex-col gap-1">
                                                    <span className="text-xs text-zinc-500 capitalize">{key.replace(/_/g, " ")}</span>
                                                    <span className="text-sm text-zinc-200 font-medium">{value}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                {displayResult.technical && (
                                    <div className="p-6 bg-white/[0.03] backdrop-blur-sm border border-white/5 rounded-xl space-y-4 hover:border-white/10 transition-colors hover:bg-white/[0.05]">
                                        <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest border-b border-white/5 pb-3 mb-1">Technical Specs</h3>
                                        <div className="grid grid-cols-2 gap-6">
                                            {Object.entries(displayResult.technical).map(([key, value]) => (
                                                <div key={key} className="flex flex-col gap-1">
                                                    <span className="text-xs text-zinc-500 capitalize">{key.replace(/_/g, " ")}</span>
                                                    <span className="text-sm font-mono text-violet-400/90">{value}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-8 animate-in fade-in zoom-in-95 duration-700">
                        <div className="relative group">
                            <div className="absolute inset-0 bg-violet-500/20 blur-[80px] rounded-full group-hover:bg-violet-500/30 transition-colors duration-1000" />
                            <div className="w-32 h-32 rounded-[2rem] bg-white/[0.02] border border-white/10 flex items-center justify-center shadow-[0_0_60px_rgba(0,0,0,0.3)] backdrop-blur-md relative transform group-hover:scale-105 transition-all duration-500 group-hover:border-violet-500/20">
                                <div className="absolute inset-0 bg-gradient-to-tr from-white/5 to-transparent rounded-[2rem]" />
                                <svg className="w-12 h-12 text-white/20 group-hover:text-violet-400 transition-colors duration-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                </svg>
                            </div>
                        </div>
                        <div className="text-center space-y-3">
                            <h3 className="text-2xl font-bold text-white tracking-tight">Ready to Generate</h3>
                            <p className="text-sm text-[var(--fg-muted)] max-w-xs mx-auto font-light leading-relaxed">
                                좌측 패널에서 설정을 완료하고<br />
                                <span className="text-violet-400 font-medium">Veo 시네마틱 프롬프트</span>를 생성하세요.
                            </p>
                        </div>
                    </div>
                )}
            </TeachingPanelLayout>

            {/* Credit Modal */}
            <InsufficientCreditsModal
                isOpen={showCreditModal}
                onClose={() => setShowCreditModal(false)}
                requiredCredits={CREDIT_COST}
                currentBalance={creditCtx?.balance ?? 0}
                onRetry={handleGenerate}
            />
        </>
    );
}
