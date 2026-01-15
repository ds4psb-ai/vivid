"use client";

import { useState, useCallback } from "react";
import TeachingPanelLayout, {
    type ThemeColor,
    useAsyncOperation,
    useResultExport,
} from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import NextDimensionNav from "./NextDimensionNav";
import EvidenceDisplay, { type EvidenceRef } from "./EvidenceDisplay";  // P5: Shared component

// SSoT: Use context instead of hardcode
// const CREDIT_COST = 5; // REMOVED
const THEME_COLOR: ThemeColor = "emerald";
const DIMENSION_KEY = "visual-realizer";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

interface ImagePromptResult {
    prompt: string;
    negative_prompt?: string;
    parameters?: {
        style?: string;
        aspect_ratio?: string;
        quality?: string;
    };
    evidence_refs?: EvidenceRef[];  // P5: Added
    confidence?: number;
}

const STYLES = [
    { value: "photorealistic", label: "포토리얼리스틱" },
    { value: "cinematic", label: "시네마틱" },
    { value: "anime", label: "애니메이션" },
    { value: "illustration", label: "일러스트" },
    { value: "3d-render", label: "3D 렌더" },
    { value: "oil-painting", label: "유화" },
    { value: "watercolor", label: "수채화" },
    { value: "digital-art", label: "디지털 아트" },
];

const ASPECT_RATIOS = [
    { value: "16:9", label: "16:9 (와이드)" },
    { value: "9:16", label: "9:16 (세로)" },
    { value: "1:1", label: "1:1 (정사각형)" },
    { value: "4:3", label: "4:3 (스탠다드)" },
    { value: "3:2", label: "3:2 (사진)" },
    { value: "21:9", label: "21:9 (울트라와이드)" },
];

const MODELS = [
    { value: "gemini-3-flash-preview", label: "Flash (빠름)" },
    { value: "gemini-3-pro-preview", label: "Pro (고품질)" },
];

export default function VisualRealizerPanel() {
    // Form state
    const [description, setDescription] = useState("");
    const [style, setStyle] = useState("photorealistic");
    const [aspectRatio, setAspectRatio] = useState("16:9");
    const [model, setModel] = useState("gemini-3-flash-preview");
    const [showCreditModal, setShowCreditModal] = useState(false);
    const [validationError, setValidationError] = useState<string | null>(null);

    // BYOK and credits
    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();
    const { getToolByDimension } = useDimensionConfig();
    const toolConfig = getToolByDimension("3D");
    const CREDIT_COST = toolConfig?.creditCost ?? 5;

    // Export utilities
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
    } = useAsyncOperation<{ success: boolean; output: ImagePromptResult; error?: string }>({
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
    const MAX_DESCRIPTION_LENGTH = 2000;

    const handleGenerate = useCallback(async () => {
        const trimmedDescription = description.trim();
        if (!trimmedDescription) {
            setValidationError("이미지 설명을 입력해주세요");
            return;
        }
        if (trimmedDescription.length > MAX_DESCRIPTION_LENGTH) {
            setValidationError(`이미지 설명은 ${MAX_DESCRIPTION_LENGTH}자 이하로 입력해주세요`);
            return;
        }
        setValidationError(null);

        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
            setShowCreditModal(true);
            return;
        }

        await execute(
            `${API_BASE}/api/dimension/3d/generate`,
            { description, style, aspect_ratio: aspectRatio, model },
            getBYOKHeaders(byokKey)
        );
    }, [description, style, aspectRatio, model, byokKey, creditCtx, execute]);

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
            exportJSON(result.output, `image-prompt-${Date.now()}.json`);
        }
    }, [result?.output, exportJSON]);

    // Extracted result data for display
    const displayResult = result?.success ? result.output : null;
    const displayError = validationError || (result && !result.success ? result.error : error);

    const SidebarContent = (
        <>
            {/* Description Input */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:text-emerald-600 dark:group-focus-within:text-emerald-400/80 transition-colors">이미지 설명 (Prompt)</label>
                <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="생성하고 싶은 이미지를 상세히 설명하세요..."
                    className="w-full h-32 px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-white/20 focus:outline-none focus:border-emerald-500 dark:focus:border-emerald-400/50 focus:bg-white dark:focus:bg-white/[0.07] focus:ring-4 focus:ring-emerald-500/10 dark:focus:ring-emerald-400/5 transition-all resize-none text-sm font-light leading-relaxed"
                />
            </div>

            {/* Style */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:text-emerald-600 dark:group-focus-within:text-emerald-400/80 transition-colors">스타일 (Style)</label>
                <div className="relative">
                    <select
                        value={style}
                        onChange={(e) => setStyle(e.target.value)}
                        className="w-full px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white text-sm focus:outline-none focus:border-emerald-500 dark:focus:border-emerald-400/50 focus:bg-white dark:focus:bg-white/[0.07] focus:ring-4 focus:ring-emerald-500/10 dark:focus:ring-emerald-400/5 transition-all appearance-none cursor-pointer hover:bg-slate-50 dark:hover:bg-white/[0.07]"
                    >
                        {STYLES.map((s) => (
                            <option key={s.value} value={s.value} className="bg-white dark:bg-[#0F0F1A] text-slate-900 dark:text-white py-2">{s.label}</option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400 dark:text-white/30 group-focus-within:text-emerald-500 dark:group-focus-within:text-emerald-400/50">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            {/* Aspect Ratio */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:text-emerald-600 dark:group-focus-within:text-emerald-400/80 transition-colors">비율 (Aspect Ratio)</label>
                <div className="grid grid-cols-2 gap-2">
                    {ASPECT_RATIOS.map((ratio) => (
                        <button
                            key={ratio.value}
                            onClick={() => setAspectRatio(ratio.value)}
                            className={`py-2 text-xs font-medium rounded-xl border transition-all ${aspectRatio === ratio.value
                                ? "bg-emerald-100 dark:bg-emerald-500/10 border-emerald-500 dark:border-emerald-500/50 text-emerald-700 dark:text-emerald-400 shadow-sm"
                                : "bg-white dark:bg-white/5 border-slate-200 dark:border-white/5 text-slate-500 dark:text-zinc-400 hover:bg-slate-50 dark:hover:bg-white/10 hover:text-slate-900 dark:hover:text-white"
                                }`}
                        >
                            {ratio.value}
                        </button>
                    ))}
                </div>
            </div>

            {/* Model Select */}
            <div className="space-y-2 pt-4 border-t border-slate-200 dark:border-white/5 mt-4 group">
                <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:text-emerald-600 dark:group-focus-within:text-emerald-400/80 transition-colors">AI 모델 Engine</label>
                <div className="relative">
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="w-full px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white text-sm focus:outline-none focus:border-emerald-500 dark:focus:border-emerald-400/50 focus:bg-white dark:focus:bg-white/[0.07] focus:ring-4 focus:ring-emerald-500/10 dark:focus:ring-emerald-400/5 transition-all appearance-none cursor-pointer font-mono"
                    >
                        {MODELS.map((m) => (
                            <option key={m.value} value={m.value} className="bg-white dark:bg-[#0F0F1A] text-slate-900 dark:text-white">{m.label}</option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400 dark:text-white/30">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            {/* Generate Button */}
            <button
                onClick={handleGenerate}
                disabled={isLoading || !description.trim()}
                className="w-full py-4 mt-6 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 disabled:from-slate-200 disabled:to-slate-300 disabled:text-slate-500 dark:disabled:from-zinc-800 dark:disabled:to-zinc-800 dark:disabled:text-zinc-600 text-white dark:text-black font-bold text-base rounded-xl shadow-[0_0_30px_rgba(16,185,129,0.3)] hover:shadow-[0_0_50px_rgba(16,185,129,0.5)] transition-all active:scale-[0.98] flex items-center justify-center gap-3 group relative overflow-hidden"
            >
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                <span className="relative flex items-center gap-2">
                    {isLoading ? (
                        <>
                            <div className="w-5 h-5 border-2 border-white/30 dark:border-black/30 border-t-white dark:border-t-black rounded-full animate-spin" />
                            <span>GENERATING...</span>
                        </>
                    ) : (
                        <>
                            <span className="tracking-widest uppercase text-white">Generate Prompt</span>
                            <div className="w-5 h-5 rounded-full bg-white/20 dark:bg-black/10 flex items-center justify-center">
                                <svg className="w-3 h-3 text-white dark:text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
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
                title="비주얼 리얼라이저"
                sidebarContent={SidebarContent}
                isLoading={isLoading}
                themeColor={THEME_COLOR}
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
                            <div className="p-8 bg-white dark:bg-black/40 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-2xl shadow-sm dark:shadow-[0_8px_32px_rgba(0,0,0,0.3)] font-mono text-base leading-relaxed text-slate-800 dark:text-zinc-100 whitespace-pre-wrap group-hover:border-emerald-300 dark:group-hover:border-emerald-500/30 group-hover:bg-slate-50 dark:group-hover:bg-black/50 transition-all relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-emerald-500 to-teal-500 shadow-[0_0_20px_#10b981]"></div>
                                <div className="flex items-center justify-between mb-4 border-b border-slate-200 dark:border-white/5 pb-3">
                                    <h3 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                                        Generated Prompt
                                    </h3>
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={handleExportJSON}
                                            className="px-3 py-1.5 text-[10px] font-bold tracking-wider uppercase rounded-lg transition-all flex items-center gap-1.5 bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-zinc-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-200 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/10"
                                            title="JSON으로 내보내기"
                                        >
                                            EXPORT
                                        </button>
                                        <button
                                            onClick={() => handleCopy(displayResult.prompt)}
                                            className={`px-3 py-1.5 text-[10px] font-bold tracking-wider uppercase rounded-lg transition-all flex items-center gap-1.5 ${isCopied
                                                ? "bg-green-100 dark:bg-green-500/10 text-green-600 dark:text-green-400 border border-green-200 dark:border-green-500/20"
                                                : "bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-zinc-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-200 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/10"
                                                }`}
                                        >
                                            {isCopied ? "COPIED" : "COPY"}
                                        </button>
                                    </div>
                                </div>
                                {displayResult.prompt}
                            </div>
                        </div>

                        {/* Negative Prompt */}
                        <div className="group relative">
                            <div className="flex items-center justify-between mb-3 px-1">
                                <h3 className="text-sm font-semibold text-slate-500 dark:text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-red-400/50"></span>
                                    Negative Prompt
                                </h3>
                                <button
                                    onClick={() => handleCopy(displayResult.negative_prompt || "text, watermark")}
                                    className="px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-200 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/10"
                                >
                                    Copy
                                </button>
                            </div>
                            <div className="p-5 bg-slate-50 dark:bg-[#18181b]/50 border border-slate-200 dark:border-white/10 rounded-xl shadow-inner font-mono text-sm leading-relaxed text-slate-600 dark:text-zinc-400 whitespace-pre-wrap group-hover:border-slate-300 dark:group-hover:border-white/20 transition-colors">
                                {displayResult.negative_prompt || "text, watermark, low quality, blurred, distorted"}
                            </div>
                        </div>

                        {/* Parameters Grid */}
                        {displayResult.parameters && (
                            <div className="p-6 bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/5 rounded-xl space-y-4 hover:border-emerald-300 dark:hover:border-white/10 transition-colors">
                                <h3 className="text-xs font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest border-b border-slate-200 dark:border-white/5 pb-3 mb-1">Parameters</h3>
                                <div className="grid grid-cols-3 gap-6">
                                    {Object.entries(displayResult.parameters).map(([key, value]) => (
                                        <div key={key} className="flex flex-col gap-1">
                                            <span className="text-xs text-slate-500 dark:text-zinc-500 capitalize">{key.replace(/_/g, " ")}</span>
                                            <span className="text-sm font-mono text-emerald-600 dark:text-emerald-400/90">{value}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* P5: Evidence Sources */}
                        <EvidenceDisplay
                            refs={displayResult.evidence_refs}
                            confidence={displayResult.confidence}
                            themeColor="emerald"
                        />

                        {/* Next Dimension Navigation */}
                        <NextDimensionNav
                            currentDimension={DIMENSION_KEY}
                            show={true}
                            themeColor={THEME_COLOR}
                        />
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-slate-500 dark:text-zinc-500 space-y-8 animate-in fade-in zoom-in-95 duration-700">
                        <div className="relative group">
                            <div className="absolute inset-0 bg-emerald-500/20 blur-[80px] rounded-full group-hover:bg-emerald-500/30 transition-colors duration-1000" />
                            <div className="w-32 h-32 rounded-[2rem] bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex items-center justify-center shadow-lg dark:shadow-[0_0_60px_rgba(0,0,0,0.3)] backdrop-blur-md relative transform group-hover:scale-105 transition-all duration-500 group-hover:border-emerald-300 dark:group-hover:border-emerald-500/20">
                                <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/5 to-transparent rounded-[2rem]" />
                                <svg className="w-12 h-12 text-slate-400 dark:text-white/20 group-hover:text-emerald-500 dark:group-hover:text-emerald-400 transition-colors duration-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                            </div>
                        </div>
                        <div className="text-center space-y-3">
                            <h3 className="text-2xl font-bold text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-b dark:from-white dark:to-white/40 tracking-tight">Ready to Generate</h3>
                            <p className="text-sm text-slate-500 dark:text-zinc-500 max-w-xs mx-auto font-light leading-relaxed">
                                이미지를 설명하고 생성형 AI를 위한<br />
                                <span className="text-emerald-600 dark:text-emerald-500/80 font-medium">최적화된 프롬프트</span>를 받아보세요.
                            </p>
                        </div>
                    </div >
                )
                }
            </TeachingPanelLayout >

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
