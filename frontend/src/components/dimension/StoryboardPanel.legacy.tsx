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

// SSoT: Use context instead of hardcode
// const CREDIT_COST = 10; // REMOVED
const THEME_COLOR: ThemeColor = "cyan";
const DIMENSION_CODE = "storyboard" as const;
const DIMENSION_KEY = "storyboard";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

interface StoryboardScene {
    scene_number: number;
    description: string;
    camera: string;
    duration: string;
    notes?: string;
    visual_prompt?: string;
    shot_type?: string;
    camera_movement?: string;
    audio_cues?: string;
    camera_angle?: string;
    midjourney_prompt?: string;
}

interface StoryboardResult {
    scenes: StoryboardScene[];
}

const SCENE_COUNTS = [3, 5, 7, 10, 15, 20];

const MODELS = [
    { value: "gemini-3-pro-preview", label: "Pro (고품질)" },
];

const VISUAL_STYLES = [
    "Cinematic", "Anime", "3D Render", "Watercolor", "Cyberpunk", "Noir", "Realistic", "Fantasy"
];

export default function StoryboardPanel() {
    // Form state
    const [script, setScript] = useState("");
    const [style, setStyle] = useState("Cinematic");
    const [sceneCount, setSceneCount] = useState(5);
    const [language, setLanguage] = useState<"ko" | "en">("ko");
    const [model, setModel] = useState("gemini-3-flash-preview");
    const [showCreditModal, setShowCreditModal] = useState(false);
    const [validationError, setValidationError] = useState<string | null>(null);

    // BYOK and credits
    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();
    const { getToolByDimension } = useDimensionConfig();
    const toolConfig = getToolByDimension("2D");
    const CREDIT_COST = toolConfig?.creditCost ?? 10;

    // Export utilities
    const { copyToClipboard, isCopied, exportJSON } = useResultExport();

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
    } = useAsyncOperation<{ success: boolean; output: StoryboardResult; error?: string }>({
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

    // Generate storyboard
    const MAX_SCRIPT_LENGTH = 3000;

    const handleGenerate = async () => {
        const trimmedScript = script.trim();
        if (!trimmedScript) {
            setValidationError("스토리 컨셉을 입력해주세요");
            return;
        }
        if (trimmedScript.length > MAX_SCRIPT_LENGTH) {
            setValidationError(`스토리 컨셉은 ${MAX_SCRIPT_LENGTH}자 이하로 입력해주세요`);
            return;
        }
        setValidationError(null);

        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
            setShowCreditModal(true);
            return;
        }

        await execute(
            `${API_BASE}/api/dimension/2d/create`,
            { concept: script, scene_count: sceneCount, language, model },
            getBYOKHeaders(byokKey)
        );
    };

    // Copy handler
    const handleCopy = useCallback(
        (text: string) => {
            copyToClipboard(text);
        },
        [copyToClipboard]
    );

    // Export result as JSON
    const handleExportJson = () => {
        if (result?.output) {
            exportJSON(result.output, `storyboard-${Date.now()}.json`);
        }
    };

    // Helper to format duration
    const formatTime = (duration: string | undefined) => {
        if (!duration) return "N/A";
        const match = duration.match(/(\d+)([smh])/);
        if (match) {
            const value = parseInt(match[1]);
            const unit = match[2];
            if (unit === 's') return `${value}s`;
            if (unit === 'm') return `${value}m`;
            if (unit === 'h') return `${value}h`;
        }
        return duration;
    };

    // Extracted result data for display
    const displayResult = result?.success ? result.output : null;
    const displayError = validationError || (result && !result.success ? result.error : error);

    const SidebarContent = (
        <>
            {/* Script Input */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700 dark:text-white/80">
                    스크립트 입력
                </label>
                <textarea
                    value={script}
                    onChange={(e) => setScript(e.target.value)}
                    placeholder="시각화할 스크립트나 시나리오를 입력하세요..."
                    className="w-full h-48 px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl
                              text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-white/30 resize-none
                              focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                    disabled={isLoading}
                />
                <div className="text-xs text-slate-400 dark:text-white/40 text-right">{script.length}/3000</div>
            </div>

            {/* Scene Count */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700 dark:text-white/80">장면 수</label>
                <div className="relative">
                    <select
                        value={sceneCount}
                        onChange={(e) => setSceneCount(Number(e.target.value))}
                        className="w-full px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl
                              text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                        disabled={isLoading}
                    >
                        <option value={4} className="bg-white dark:bg-black text-slate-900 dark:text-white">4 장면 (Short)</option>
                        <option value={6} className="bg-white dark:bg-black text-slate-900 dark:text-white">6 장면 (Standard)</option>
                        <option value={8} className="bg-white dark:bg-black text-slate-900 dark:text-white">8 장면 (Extended)</option>
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400 dark:text-white/30">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            {/* Visual Style */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700 dark:text-white/80">비주얼 스타일</label>
                <div className="relative">
                    <select
                        value={style}
                        onChange={(e) => setStyle(e.target.value)}
                        className="w-full px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl
                              text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                        disabled={isLoading}
                    >
                        {VISUAL_STYLES.map((s) => (
                            <option key={s} value={s} className="bg-white dark:bg-black text-slate-900 dark:text-white">{s}</option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400 dark:text-white/30">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            {/* Language */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:text-cyan-400/80 transition-colors">언어</label>
                <div className="flex gap-1 p-1 bg-white/5 rounded-xl border border-white/10">
                    <button
                        onClick={() => setLanguage("ko")}
                        className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${language === "ko"
                            ? "bg-cyan-500 text-black shadow-sm"
                            : "text-zinc-400 hover:text-white hover:bg-white/5"
                            }`}
                    >
                        KO
                    </button>
                    <button
                        onClick={() => setLanguage("en")}
                        className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${language === "en"
                            ? "bg-cyan-500 text-black shadow-sm"
                            : "text-zinc-400 hover:text-white hover:bg-white/5"
                            }`}
                    >
                        EN
                    </button>
                </div>
            </div>

            {/* Model Select */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:text-cyan-400/80 transition-colors">AI 모델</label>
                <div className="relative">
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-cyan-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-cyan-400/5 transition-all appearance-none cursor-pointer hover:bg-white/[0.07]"
                    >
                        {MODELS.map((m) => (
                            <option key={m.value} value={m.value} className="bg-[#0F0F1A] text-white py-2">{m.label}</option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-white/30 group-focus-within:text-cyan-400/50">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            {/* Generate Button */}
            <button
                onClick={handleGenerate} // Changed handleCreate to handleGenerate
                disabled={isLoading || !script.trim()} // Changed concept to script
                className="w-full py-4 mt-6 bg-gradient-to-r from-cyan-500 to-sky-500 hover:from-cyan-400 hover:to-sky-400 disabled:from-zinc-800 disabled:to-zinc-800 disabled:text-zinc-600 text-black font-bold text-base rounded-xl shadow-[0_0_30px_rgba(6,182,212,0.3)] hover:shadow-[0_0_50px_rgba(6,182,212,0.5)] transition-all active:scale-[0.98] flex items-center justify-center gap-3 group relative overflow-hidden"
            >
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                <span className="relative flex items-center gap-2">
                    {isLoading ? (
                        <>
                            <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                            <span>CREATING...</span>
                        </>
                    ) : (
                        <>
                            <span className="tracking-widest uppercase">Create Storyboard</span>
                            <div className="w-5 h-5 rounded-full bg-black/10 flex items-center justify-center">
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
                title="스토리보드 생성기"
                sidebarContent={SidebarContent}
                isLoading={isLoading}
                themeColor={THEME_COLOR}
                dimensionCode={DIMENSION_CODE}
                progress={progress}
                onCancel={cancel}
                onRetry={retry}
                canRetry={canRetry}
                error={error}
                retryCount={3}
                maxRetries={3}
            >
                {displayResult ? (
                    <div className="max-w-5xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
                        <div className="flex items-center justify-between px-1">
                            <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                                Generated Scenes ({displayResult.scenes.length})
                            </h3>
                            <div className="flex gap-2">
                                <button
                                    onClick={handleExportJson}
                                    className="px-3 py-1.5 bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 text-white text-xs font-medium rounded-lg transition-all flex items-center gap-2"
                                >
                                    <svg className="w-4 h-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                    </svg>
                                    JSON Export
                                </button>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 gap-4">
                            {displayResult.scenes.map((scene, idx) => (
                                <div key={idx} className="group relative">
                                    <div className="absolute inset-0 bg-cyan-500/5 blur-xl rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                    <div className="p-4 bg-white/80 dark:bg-black/40 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-2xl shadow-sm dark:shadow-[0_8px_32px_rgba(0,0,0,0.3)] font-mono text-base leading-relaxed text-slate-800 dark:text-zinc-100 group-hover:border-cyan-400/50 dark:group-hover:border-cyan-500/30 group-hover:bg-white dark:group-hover:bg-black/50 transition-all relative overflow-hidden h-full">
                                        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-cyan-400 to-blue-500 dark:from-cyan-500 dark:to-blue-500 shadow-[0_0_20px_#06b6d4]"></div>

                                        {/* Scene Header */}
                                        <div className="flex justify-between items-center mb-4 border-b border-slate-100 dark:border-white/5 pb-2">
                                            <h4 className="text-[12px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest group-hover:text-cyan-600 dark:group-hover:text-cyan-400/80 transition-colors">
                                                Scene #{scene.scene_number}
                                            </h4>
                                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-500/30">
                                                {formatTime(scene.duration)}
                                            </span>
                                        </div>

                                        {/* Content Grid */}
                                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                            <div className="space-y-4">
                                                <div>
                                                    <span className="text-[10px] text-slate-400 dark:text-zinc-500 uppercase tracking-wider block mb-1">Visual</span>
                                                    <p className="text-sm text-slate-700 dark:text-white/90 leading-relaxed font-light">{scene.description}</p>
                                                </div>
                                                <div>
                                                    <span className="text-[10px] text-slate-400 dark:text-zinc-500 uppercase tracking-wider block mb-1">Audio</span>
                                                    <div className="flex gap-2 items-start">
                                                        <span className="text-xs bg-slate-100 dark:bg-white/5 px-2 py-1 rounded text-slate-600 dark:text-zinc-400 whitespace-nowrap">SFX</span>
                                                        <p className="text-xs text-slate-600 dark:text-zinc-400 italic leading-relaxed pt-0.5">{scene.audio_cues}</p>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="space-y-3 pt-3 lg:pt-0 lg:pl-4 lg:border-l lg:border-slate-100 dark:lg:border-white/5">
                                                <div className="grid grid-cols-2 gap-2">
                                                    <div className="bg-slate-50 dark:bg-white/5 rounded-lg p-2 text-center">
                                                        <span className="text-[10px] text-slate-400 dark:text-zinc-500 block mb-1">Camera</span>
                                                        <span className="text-xs text-cyan-700 dark:text-cyan-300 font-medium">{scene.camera_angle}</span>
                                                    </div>
                                                    <div className="bg-slate-50 dark:bg-white/5 rounded-lg p-2 text-center">
                                                        <span className="text-[10px] text-slate-400 dark:text-zinc-500 block mb-1">Movement</span>
                                                        <span className="text-xs text-cyan-700 dark:text-cyan-300 font-medium">{scene.camera_movement}</span>
                                                    </div>
                                                </div>

                                                <div className="bg-gradient-to-br from-slate-900/5 to-slate-900/10 dark:from-black/40 dark:to-black/60 rounded-lg p-3 border border-slate-200 dark:border-white/5">
                                                    <span className="text-[10px] text-slate-400 dark:text-zinc-600 block mb-1 text-center">Prompt Preview</span>
                                                    <p className="text-[10px] text-slate-500 dark:text-zinc-400 line-clamp-3 font-mono leading-tight opacity-70">
                                                        {scene.midjourney_prompt}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Next Dimension Navigation */}
                        <NextDimensionNav
                            currentDimension={DIMENSION_KEY}
                            show={true}
                            themeColor={THEME_COLOR}
                        />
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-8 animate-in fade-in zoom-in-95 duration-700">
                        <div className="relative group">
                            <div className="absolute inset-0 bg-cyan-500/20 blur-[80px] rounded-full group-hover:bg-cyan-500/30 transition-colors duration-1000" />
                            <div className="w-32 h-32 rounded-[2rem] bg-white/[0.02] border border-white/10 flex items-center justify-center shadow-[0_0_60px_rgba(0,0,0,0.3)] backdrop-blur-md relative transform group-hover:scale-105 transition-all duration-500 group-hover:border-cyan-500/20">
                                <div className="absolute inset-0 bg-gradient-to-tr from-white/5 to-transparent rounded-[2rem]" />
                                <svg className="w-12 h-12 text-white/20 group-hover:text-cyan-400 transition-colors duration-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                                </svg>
                            </div>
                        </div>
                        <div className="text-center space-y-3">
                            <h3 className="text-2xl font-bold text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-b dark:from-white dark:to-white/40 tracking-tight">Ready to Visualize</h3>
                            <p className="text-sm text-slate-500 dark:text-zinc-500 max-w-xs mx-auto font-light leading-relaxed">
                                스토리를 장면 단위로 시각화하고<br />
                                <span className="text-cyan-600 dark:text-cyan-500/80 font-medium">Midjourney & Runway 프롬프트</span>를 자동 생성합니다.
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
