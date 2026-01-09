"use client";

import { useState, useRef, useCallback } from "react";
import TeachingPanelLayout, {
    type ThemeColor,
    useAsyncOperation,
    useResultExport,
} from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";

// SSoT: Use context instead of hardcode
// const CREDIT_COST = 50; // REMOVED
const THEME_COLOR: ThemeColor = "sky";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

interface VideoResult {
    video_url?: string;
    status: "pending" | "processing" | "completed" | "failed";
    operation_id?: string;
    error?: string;
    metadata?: {
        duration?: string;
        resolution?: string;
        fps?: string;
        model?: string;
    };
}

const ASPECT_RATIOS = [
    { value: "16:9", label: "16:9 (Landscape)" },
    { value: "9:16", label: "9:16 (Portrait)" },
    { value: "1:1", label: "1:1 (Square)" },
    { value: "4:3", label: "4:3 (Classic)" },
];

const DURATIONS = [
    { value: "4", label: "4초" },
    { value: "6", label: "6초" },
    { value: "8", label: "8초" },
];

const STYLES = [
    { value: "cinematic", label: "Cinematic" },
    { value: "realistic", label: "Realistic" },
    { value: "artistic", label: "Artistic" },
    { value: "anime", label: "Anime" },
];

export default function VeoVideoPanel() {
    // Form state
    const [prompt, setPrompt] = useState("");
    const [negativePrompt, setNegativePrompt] = useState("");
    const [aspectRatio, setAspectRatio] = useState("16:9");
    const [duration, setDuration] = useState("8");
    const [style, setStyle] = useState("cinematic");
    const [seed, setSeed] = useState<number | undefined>(undefined);
    const [useRandomSeed, setUseRandomSeed] = useState(true);
    const [showCreditModal, setShowCreditModal] = useState(false);
    const [validationError, setValidationError] = useState<string | null>(null);

    const videoRef = useRef<HTMLVideoElement>(null);

    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();
    const { getToolByDimension } = useDimensionConfig();
    const toolConfig = getToolByDimension("VEO");
    const creditCost = toolConfig?.creditCost ?? 200; // SSoT with fallback

    // Export utilities (copy, download)
    const { downloadFile, copyToClipboard, isCopied } = useResultExport();

    // Async operation hook for SSE streaming with progress
    const {
        isLoading,
        progress,
        error,
        data: result,
        executeStream,
        cancel,
        retry,
        canRetry,
        currentRetryCount,
    } = useAsyncOperation<VideoResult>({
        onSuccess: (data) => {
            // Refresh credits on successful generation
            if (data.status === "completed" && !byokKey && creditCtx) {
                void creditCtx.refresh();
            }
        },
        onError: (err) => {
            // Show credit modal for insufficient credits
            if (err.message.includes("크레딧") || err.message.includes("402")) {
                setShowCreditModal(true);
            }
        },
        retryCount: 3,
        retryDelay: 1000,
        nonRetryableErrors: ["400", "401", "402", "403", "404", "크레딧", "부족"],
    });

    // Generate video using SSE streaming
    const MAX_PROMPT_LENGTH = 2000;

    const handleGenerate = useCallback(async () => {
        // Validation
        const trimmedPrompt = prompt.trim();
        if (!trimmedPrompt) {
            setValidationError("프롬프트를 입력해주세요");
            return;
        }
        if (trimmedPrompt.length < 10) {
            setValidationError("프롬프트는 최소 10자 이상 입력해주세요");
            return;
        }
        if (trimmedPrompt.length > MAX_PROMPT_LENGTH) {
            setValidationError(`프롬프트는 ${MAX_PROMPT_LENGTH}자 이하로 입력해주세요`);
            return;
        }
        setValidationError(null);

        // Credit check
        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(creditCost)) {
            setShowCreditModal(true);
            return;
        }

        // Execute SSE streaming request
        await executeStream(
            `${API_BASE}/api/dimension/veo/generate/stream`,
            {
                prompt: prompt.trim(),
                negative_prompt: negativePrompt.trim() || undefined,
                aspect_ratio: aspectRatio,
                duration: parseInt(duration),
                style,
                seed: useRandomSeed ? undefined : seed,
            },
            getBYOKHeaders(byokKey)
        );
    }, [
        prompt,
        negativePrompt,
        aspectRatio,
        duration,
        style,
        seed,
        useRandomSeed,
        byokKey,
        creditCtx,
        executeStream,
    ]);

    // Download video
    const handleDownload = useCallback(async () => {
        if (!result?.video_url) return;

        try {
            const response = await fetch(result.video_url);
            const blob = await response.blob();
            const content = await blob.text();
            downloadFile(content, `veo-video-${Date.now()}.mp4`, "video/mp4");
        } catch {
            // Fallback: Direct link download
            const a = document.createElement("a");
            a.href = result.video_url;
            a.download = `veo-video-${Date.now()}.mp4`;
            a.target = "_blank";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }
    }, [result?.video_url, downloadFile]);

    // Copy prompt to clipboard
    const handleCopyPrompt = useCallback(() => {
        copyToClipboard(prompt);
    }, [prompt, copyToClipboard]);

    // Combined error (validation + operation error)
    const displayError = validationError || error;

    const SidebarContent = (
        <>
            {/* Prompt Input */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1 group-focus-within:text-sky-400/80 transition-colors">
                    프롬프트
                </label>
                <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="생성할 비디오를 상세히 설명하세요...&#10;예: A cinematic shot of a sunrise over mountains, golden light casting long shadows..."
                    className="w-full h-36 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/20 focus:outline-none focus:border-sky-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-sky-400/5 transition-all resize-none text-sm font-light leading-relaxed"
                />
                <div className="text-[10px] text-zinc-500 text-right">{prompt.length} / 1000</div>
            </div>

            {/* Negative Prompt */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:text-sky-400/80 transition-colors">
                    네거티브 프롬프트 (선택)
                </label>
                <textarea
                    value={negativePrompt}
                    onChange={(e) => setNegativePrompt(e.target.value)}
                    placeholder="제외할 요소를 입력하세요..."
                    className="w-full h-20 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/20 focus:outline-none focus:border-sky-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-sky-400/5 transition-all resize-none text-sm font-light"
                />
            </div>

            {/* Aspect Ratio & Duration */}
            <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2 group">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1">비율</label>
                    <div className="relative">
                        <select
                            value={aspectRatio}
                            onChange={(e) => setAspectRatio(e.target.value)}
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-sky-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-sky-400/5 transition-all appearance-none cursor-pointer"
                        >
                            {ASPECT_RATIOS.map((r) => (
                                <option key={r.value} value={r.value} className="bg-[#0F0F1A] text-white">{r.label}</option>
                            ))}
                        </select>
                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-white/30">
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                        </div>
                    </div>
                </div>
                <div className="space-y-2 group">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1">길이</label>
                    <div className="relative">
                        <select
                            value={duration}
                            onChange={(e) => setDuration(e.target.value)}
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-sky-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-sky-400/5 transition-all appearance-none cursor-pointer"
                        >
                            {DURATIONS.map((d) => (
                                <option key={d.value} value={d.value} className="bg-[#0F0F1A] text-white">{d.label}</option>
                            ))}
                        </select>
                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-white/30">
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                        </div>
                    </div>
                </div>
            </div>

            {/* Style */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1">스타일</label>
                <div className="grid grid-cols-2 gap-2">
                    {STYLES.map((s) => (
                        <button
                            key={s.value}
                            onClick={() => setStyle(s.value)}
                            className={`px-4 py-3 rounded-xl text-sm font-medium transition-all border ${style === s.value
                                ? "bg-sky-500/20 border-sky-500/40 text-sky-400 shadow-[0_0_15px_rgba(14,165,233,0.2)]"
                                : "bg-white/5 border-white/10 text-zinc-400 hover:bg-white/10 hover:text-white"
                                }`}
                        >
                            {s.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Seed Control */}
            <div className="space-y-3 pt-4 border-t border-white/5 mt-2">
                <div className="flex items-center justify-between">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">시드 설정</label>
                    <button
                        onClick={() => setUseRandomSeed(!useRandomSeed)}
                        className={`relative w-10 h-5 rounded-full transition-all ${useRandomSeed ? "bg-sky-500" : "bg-white/10"
                            }`}
                    >
                        <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow-sm transition-all ${useRandomSeed ? "left-5" : "left-0.5"
                            }`} />
                    </button>
                </div>
                {!useRandomSeed && (
                    <input
                        type="number"
                        value={seed ?? ""}
                        onChange={(e) => setSeed(e.target.value ? parseInt(e.target.value) : undefined)}
                        placeholder="시드 값 입력..."
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/20 focus:outline-none focus:border-sky-400/50 text-sm font-mono"
                    />
                )}
                <p className="text-[10px] text-zinc-600">
                    {useRandomSeed ? "매번 새로운 결과 생성" : "동일한 시드로 재현 가능한 결과"}
                </p>
            </div>

            {/* Credit Cost Info */}
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-sky-500/5 border border-sky-500/10">
                <svg className="w-4 h-4 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span className="text-xs text-sky-400 font-medium">{creditCost} 크레딧 소모</span>
            </div>

            {/* Generate Button */}
            <button
                onClick={handleGenerate}
                disabled={isLoading || !prompt.trim()}
                className="w-full py-4 mt-4 bg-gradient-to-r from-sky-500 to-blue-500 hover:from-sky-400 hover:to-blue-400 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-600 text-white font-bold text-base rounded-xl shadow-[0_0_30px_rgba(14,165,233,0.3)] hover:shadow-[0_0_50px_rgba(14,165,233,0.5)] transition-all active:scale-[0.98] flex items-center justify-center gap-3 group relative overflow-hidden"
            >
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                <span className="relative flex items-center gap-2">
                    {isLoading ? (
                        <>
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            <span>생성 중...</span>
                        </>
                    ) : (
                        <>
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                            <span className="tracking-widest uppercase">비디오 생성</span>
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
                title="Veo 3.1 비디오"
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
                {result ? (
                    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
                        {/* Status Badge */}
                        {result.status === "processing" && (
                            <div className="flex items-center justify-center gap-3 p-6 bg-sky-500/10 border border-sky-500/20 rounded-2xl">
                                <div className="w-6 h-6 border-2 border-sky-400/30 border-t-sky-400 rounded-full animate-spin" />
                                <div className="text-center">
                                    <p className="text-sky-400 font-medium">비디오 생성 중...</p>
                                    <p className="text-xs text-zinc-500 mt-1">Veo 3.1이 영상을 렌더링하고 있습니다</p>
                                </div>
                            </div>
                        )}

                        {/* Video Player */}
                        {result.status === "completed" && result.video_url && (
                            <div className="relative group">
                                <div className="absolute -inset-1 bg-gradient-to-r from-sky-500/20 to-blue-500/20 rounded-2xl blur opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                <div className="relative bg-black rounded-2xl overflow-hidden border border-white/10 shadow-2xl">
                                    <video
                                        ref={videoRef}
                                        src={result.video_url}
                                        controls
                                        autoPlay
                                        loop
                                        className="w-full aspect-video"
                                    />
                                </div>

                                {/* Download Button */}
                                <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                        onClick={handleDownload}
                                        className="flex items-center gap-2 px-4 py-2 bg-black/60 backdrop-blur-xl border border-white/10 rounded-lg text-white text-sm font-medium hover:bg-black/80 transition-colors"
                                    >
                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                        </svg>
                                        다운로드
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Failed State */}
                        {result.status === "failed" && (
                            <div className="flex flex-col items-center justify-center p-12 bg-red-500/5 border border-red-500/20 rounded-2xl">
                                <svg className="w-16 h-16 text-red-400/50 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                                <p className="text-red-400 font-medium mb-2">비디오 생성 실패</p>
                                <p className="text-xs text-zinc-500">{result.error || "알 수 없는 오류가 발생했습니다"}</p>
                                <button
                                    onClick={canRetry ? retry : handleGenerate}
                                    className="mt-4 px-4 py-2 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm hover:bg-red-500/20 transition-colors flex items-center gap-2"
                                >
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                    </svg>
                                    다시 시도
                                    {canRetry && currentRetryCount > 0 && (
                                        <span className="text-red-400/60">({currentRetryCount}/3)</span>
                                    )}
                                </button>
                            </div>
                        )}

                        {/* Metadata */}
                        {result.metadata && result.status === "completed" && (
                            <div className="grid grid-cols-4 gap-4">
                                {result.metadata.duration && (
                                    <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl text-center">
                                        <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Duration</p>
                                        <p className="text-lg font-mono text-sky-400">{result.metadata.duration}</p>
                                    </div>
                                )}
                                {result.metadata.resolution && (
                                    <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl text-center">
                                        <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Resolution</p>
                                        <p className="text-lg font-mono text-sky-400">{result.metadata.resolution}</p>
                                    </div>
                                )}
                                {result.metadata.fps && (
                                    <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl text-center">
                                        <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">FPS</p>
                                        <p className="text-lg font-mono text-sky-400">{result.metadata.fps}</p>
                                    </div>
                                )}
                                {result.metadata.model && (
                                    <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl text-center">
                                        <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Model</p>
                                        <p className="text-lg font-mono text-sky-400">{result.metadata.model}</p>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Used Prompt */}
                        {result.status === "completed" && (
                            <div className="p-6 bg-white/[0.02] border border-white/5 rounded-xl">
                                <div className="flex items-center justify-between mb-3">
                                    <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest">사용된 프롬프트</h3>
                                    <button
                                        onClick={handleCopyPrompt}
                                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-zinc-400 hover:text-white bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 hover:border-white/20 transition-all"
                                    >
                                        {isCopied ? (
                                            <>
                                                <svg className="w-3.5 h-3.5 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                </svg>
                                                <span className="text-sky-400">복사됨!</span>
                                            </>
                                        ) : (
                                            <>
                                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                                </svg>
                                                복사
                                            </>
                                        )}
                                    </button>
                                </div>
                                <p className="text-sm text-zinc-300 leading-relaxed">{prompt}</p>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-8 animate-in fade-in zoom-in-95 duration-700">
                        <div className="relative group">
                            <div className="absolute inset-0 bg-sky-500/20 blur-[80px] rounded-full group-hover:bg-sky-500/30 transition-colors duration-1000" />
                            <div className="w-32 h-32 rounded-[2rem] bg-white/[0.02] border border-white/10 flex items-center justify-center shadow-[0_0_60px_rgba(0,0,0,0.3)] backdrop-blur-md relative transform group-hover:scale-105 transition-all duration-500 group-hover:border-sky-500/20">
                                <div className="absolute inset-0 bg-gradient-to-tr from-white/5 to-transparent rounded-[2rem]" />
                                <svg className="w-12 h-12 text-white/20 group-hover:text-sky-400 transition-colors duration-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                            </div>
                        </div>
                        <div className="text-center space-y-3">
                            <h3 className="text-2xl font-bold text-white tracking-tight">Veo 3.1 Video Generation</h3>
                            <p className="text-sm text-[var(--fg-muted)] max-w-xs mx-auto font-light leading-relaxed">
                                프롬프트를 입력하고<br />
                                <span className="text-sky-400 font-medium">AI 비디오</span>를 생성하세요.
                            </p>
                            <div className="flex items-center justify-center gap-2 pt-2">
                                <span className="px-2 py-1 bg-sky-500/10 border border-sky-500/20 rounded text-[10px] text-sky-400 font-medium">Veo 3.1</span>
                                <span className="px-2 py-1 bg-white/5 border border-white/10 rounded text-[10px] text-zinc-500">HD Quality</span>
                                <span className="px-2 py-1 bg-white/5 border border-white/10 rounded text-[10px] text-zinc-500">4-8초</span>
                            </div>
                        </div>
                    </div>
                )}
            </TeachingPanelLayout>

            <InsufficientCreditsModal
                isOpen={showCreditModal}
                onClose={() => setShowCreditModal(false)}
                requiredCredits={creditCost}
                currentBalance={creditCtx?.balance ?? 0}
                onRetry={handleGenerate}
            />
        </>
    );
}
