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
import { Palette, Copy, Check, Download, Sparkles, Eye, Wand2, Code, Type, Layers } from "lucide-react";

// const CREDIT_COST = 10; // REMOVED
const THEME_COLOR: ThemeColor = "fuchsia";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

interface AestheticResult {
    visual_guidelines: {
        composition?: string;
        lighting?: string;
        camera?: string;
        pacing?: string;
    };
    color_palette: string[];
    style_keywords: string[];
    avoid_elements: string[];
    auteur_influence?: {
        name: string;
        style_summary: string;
        signature_elements: string[];
    };
    textures?: string[];
    typography?: {
        primary: string;
        secondary: string;
        description: string;
    };
    generative_prompts?: {
        midjourney: string;
        veo: string;
    };
}

interface VisualDirection {
    id: string;
    title: string;
    description: string;
    keywords: string[];
    suggested_auteur: string;
    color_preview: string[];
}

interface MoodboardResult {
    directions: VisualDirection[];
}

type Stage = "moodboard" | "palette" | "guide";

const MOODS = [
    { value: "neutral", label: "중립" },
    { value: "dramatic", label: "드라마틱" },
    { value: "calm", label: "차분함" },
    { value: "energetic", label: "에너지틱" },
    { value: "melancholic", label: "멜랑콜릭" },
    { value: "mysterious", label: "미스터리" },
    { value: "romantic", label: "로맨틱" },
];

const TARGET_MEDIUMS = [
    { value: "video", label: "비디오" },
    { value: "image", label: "이미지" },
    { value: "animation", label: "애니메이션" },
];

export default function AestheticDirectorPanel() {
    const [concept, setConcept] = useState("");
    const [mood, setMood] = useState("neutral");
    const [targetMedium, setTargetMedium] = useState("video");
    const [useRag, setUseRag] = useState(true);

    // Visual Identity Workshop State
    const [stage, setStage] = useState<Stage>("moodboard");
    const [directions, setDirections] = useState<VisualDirection[]>([]);
    const [selectedDirection, setSelectedDirection] = useState<VisualDirection | null>(null);

    const [copiedField, setCopiedField] = useState<string | null>(null);
    const [showCreditModal, setShowCreditModal] = useState(false);
    const [validationError, setValidationError] = useState<string | null>(null);

    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();
    const { getToolByDimension } = useDimensionConfig();
    const toolConfig = getToolByDimension("AD");
    const CREDIT_COST = toolConfig?.creditCost ?? 10;

    // Export utilities
    const { exportJSON, copyToClipboard } = useResultExport();

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
    } = useAsyncOperation<{ success: boolean; output: AestheticResult; error?: string }>({
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

    const MAX_CONCEPT_LENGTH = 2000;

    // Async operation hook for moodboard (returns directions)
    const {
        isLoading: isMoodboardLoading,
        execute: executeMoodboard,
    } = useAsyncOperation<{ success: boolean; output: MoodboardResult; error?: string }>({
        onSuccess: (data) => {
            if (data.success && data.output?.directions) {
                setDirections(data.output.directions);
                setStage("palette");
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

    // Stage 1: Generate Moodboard (Visual Directions)
    const handleGenerateMoodboard = useCallback(async () => {
        const trimmedConcept = concept.trim();
        if (!trimmedConcept) {
            setValidationError("컨셉을 입력해주세요");
            return;
        }
        setValidationError(null);

        await executeMoodboard(
            `${API_BASE}/api/dimension/aesthetic/moodboard`,
            {
                concept,
                mood,
                model: "gemini-3-flash-preview",
            },
            getBYOKHeaders(byokKey)
        );
    }, [concept, mood, byokKey, executeMoodboard]);

    // Stage 2 -> 3: Generate Full Style Guide
    const handleGenerateGuide = useCallback(async () => {
        if (!selectedDirection) return;
        setValidationError(null);

        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
            setShowCreditModal(true);
            return;
        }

        // Use the selected direction to generate the full guide
        const enrichedConcept = `${concept}\n\nSelected Visual Direction: ${selectedDirection.title}\n${selectedDirection.description}\nKeywords: ${selectedDirection.keywords.join(", ")}\nSuggested Auteur: ${selectedDirection.suggested_auteur}`;

        await execute(
            `${API_BASE}/api/dimension/aesthetic/direct`,
            {
                concept: enrichedConcept,
                reference_style: selectedDirection.suggested_auteur.toLowerCase().split(" ")[0] || "",
                mood,
                target_medium: targetMedium,
                model: "gemini-3-pro-preview",
                use_rag: useRag,
            },
            getBYOKHeaders(byokKey)
        ).then((res) => {
            if (res && res.success) {
                setStage("guide");
            }
        });
    }, [concept, mood, targetMedium, useRag, byokKey, creditCtx, execute, selectedDirection]);

    const handleCopy = useCallback(async (text: string, field: string) => {
        const success = await copyToClipboard(text);
        if (success) {
            setCopiedField(field);
            setTimeout(() => setCopiedField(null), 2000);
        }
    }, [copyToClipboard]);

    // Export result as JSON
    const handleExportJson = useCallback(() => {
        if (!result?.output) return;
        exportJSON(result.output, `aesthetic-director-${Date.now()}.json`);
    }, [result?.output, exportJSON]);

    // Extracted result data for display
    const displayResult = result?.success ? result.output : null;
    const displayError = validationError || (result && !result.success ? result.error : error);

    const SidebarContent = (
        <>
            {/* Stage Indicator */}
            <div className="flex items-center justify-between text-xs text-white/50 mb-4">
                <span className={stage === "moodboard" ? "text-fuchsia-400 font-bold" : ""}>1. 영감</span>
                <span>→</span>
                <span className={stage === "palette" ? "text-fuchsia-400 font-bold" : ""}>2. 팔레트</span>
                <span>→</span>
                <span className={stage === "guide" ? "text-fuchsia-400 font-bold" : ""}>3. 가이드</span>
            </div>

            {/* Concept Input */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1">컨셉 / 주제</label>
                <textarea
                    value={concept}
                    onChange={(e) => setConcept(e.target.value)}
                    placeholder="시각적 스타일을 정의할 컨셉을 입력하세요..."
                    className="w-full h-32 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/20 focus:outline-none focus:border-fuchsia-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-fuchsia-400/5 transition-all resize-none text-sm font-light leading-relaxed disabled:opacity-50"
                    disabled={isLoading || stage !== "moodboard"}
                />
            </div>

            {/* Mood Selector (Stage 1 only) */}
            {stage === "moodboard" && (
                <div className="space-y-2">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1">분위기</label>
                    <div className="relative">
                        <select
                            value={mood}
                            onChange={(e) => setMood(e.target.value)}
                            className="w-full px-3 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-fuchsia-400/50 transition-all appearance-none"
                        >
                            {MOODS.map((m) => (
                                <option key={m.value} value={m.value} className="bg-[#0F0F1A]">{m.label}</option>
                            ))}
                        </select>
                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-white/30">
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                        </div>
                    </div>
                </div>
            )}

            {/* Selected Direction Display (Stage 2) */}
            {stage === "palette" && selectedDirection && (
                <div className="p-4 bg-fuchsia-500/10 border border-fuchsia-500/20 rounded-xl">
                    <h4 className="text-fuchsia-400 text-sm font-bold mb-1">선택된 방향</h4>
                    <p className="text-white font-medium text-sm">{selectedDirection.title}</p>
                    <div className="flex gap-1 mt-2">
                        {selectedDirection.color_preview.map((color, i) => (
                            <div key={i} className="w-6 h-6 rounded-full border border-white/10" style={{ backgroundColor: color }} />
                        ))}
                    </div>
                </div>
            )}

            {/* Medium Selector (Stage 2) */}
            {stage === "palette" && (
                <div className="space-y-2">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1">미디어</label>
                    <div className="relative">
                        <select
                            value={targetMedium}
                            onChange={(e) => setTargetMedium(e.target.value)}
                            className="w-full px-3 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-fuchsia-400/50 transition-all appearance-none"
                        >
                            {TARGET_MEDIUMS.map((t) => (
                                <option key={t.value} value={t.value} className="bg-[#0F0F1A]">{t.label}</option>
                            ))}
                        </select>
                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-white/30">
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                        </div>
                    </div>
                </div>
            )}

            {/* RAG Toggle (Stage 2) */}
            {stage === "palette" && (
                <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/10">
                    <div>
                        <div className="text-sm font-medium text-zinc-300">RAG 컨텍스트</div>
                        <div className="text-[10px] text-zinc-500">레퍼런스 검색 활성화</div>
                    </div>
                    <button
                        onClick={() => setUseRag(!useRag)}
                        className={`relative w-12 h-6 rounded-full transition-all ${useRag ? "bg-fuchsia-500" : "bg-white/10"}`}
                    >
                        <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${useRag ? "left-7" : "left-1"}`} />
                    </button>
                </div>
            )}

            {/* Action Buttons */}
            {stage === "moodboard" && (
                <button
                    onClick={handleGenerateMoodboard}
                    disabled={isLoading || !concept.trim()}
                    className="w-full py-4 mt-6 bg-fuchsia-500 hover:bg-fuchsia-400 disabled:bg-slate-800 disabled:text-slate-600 text-black font-bold text-base rounded-xl transition-all active:scale-[0.98]"
                >
                    {isLoading ? (
                        <span className="flex items-center justify-center gap-2">
                            <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                            영감 찾는 중...
                        </span>
                    ) : (
                        <span className="flex items-center justify-center gap-2">
                            <Sparkles className="w-4 h-4" />
                            비주얼 방향 탐색
                        </span>
                    )}
                </button>
            )}

            {stage === "palette" && (
                <button
                    onClick={handleGenerateGuide}
                    disabled={isLoading || !selectedDirection}
                    className="w-full py-4 mt-6 bg-fuchsia-500 hover:bg-fuchsia-400 disabled:bg-slate-800 disabled:text-slate-600 text-black font-bold text-base rounded-xl transition-all active:scale-[0.98]"
                >
                    {isLoading ? (
                        <span className="flex items-center justify-center gap-2">
                            <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                            스타일 가이드 생성 중...
                        </span>
                    ) : (
                        <span className="flex items-center justify-center gap-2">
                            <Wand2 className="w-4 h-4" />
                            스타일 가이드 완성
                        </span>
                    )}
                </button>
            )}

            {stage === "guide" && (
                <button
                    onClick={() => setStage("palette")}
                    className="w-full py-3 rounded-xl bg-white/5 hover:bg-white/10 text-white border border-white/10 transition-all font-medium"
                >
                    ◀ 다른 방향 선택하기
                </button>
            )}

            {/* Validation error only */}
            {validationError && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs">
                    {validationError}
                </div>
            )}

            {/* Credit Cost */}
            {!byokKey && (
                <div className="text-xs text-white/40 text-center mt-4">
                    예상 비용: {stage === "moodboard" ? "5" : CREDIT_COST} 크레딧
                </div>
            )}
        </>
    );

    return (
        <>
            <TeachingPanelLayout
                title="미학디렉터"
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
                {/* Stage 1: Moodboard (Initial State) */}
                {stage === "moodboard" && !isLoading && (
                    <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-8">
                        <div className="relative group">
                            <div className="absolute inset-0 bg-fuchsia-500/20 blur-[80px] rounded-full" />
                            <div className="w-32 h-32 rounded-[2rem] bg-white/[0.02] border border-white/10 flex items-center justify-center backdrop-blur-md relative">
                                <Eye className="w-12 h-12 text-white/20 group-hover:text-fuchsia-400 transition-colors" />
                            </div>
                        </div>
                        <div className="text-center space-y-3">
                            <h3 className="text-2xl font-bold text-white tracking-tight">Visual Identity Workshop</h3>
                            <p className="text-sm text-[var(--fg-muted)] max-w-xs mx-auto font-light leading-relaxed">
                                컨셉을 입력하면 AI가<br />
                                <span className="text-fuchsia-400 font-medium">3가지 시각적 방향</span>을 제안합니다.
                            </p>
                        </div>
                    </div>
                )}

                {/* Stage 2: Palette Lab (Select Direction) */}
                {stage === "palette" && (
                    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-500">
                        <h3 className="text-xl font-bold text-white flex items-center gap-2">
                            <Eye className="w-5 h-5 text-fuchsia-400" />
                            시각적 방향을 선택하세요
                        </h3>
                        <div className="grid gap-4 md:grid-cols-3">
                            {directions.map((dir) => (
                                <button
                                    key={dir.id}
                                    onClick={() => setSelectedDirection(dir)}
                                    className={`text-left p-6 rounded-2xl border transition-all relative overflow-hidden group
                                        ${selectedDirection?.id === dir.id
                                            ? "bg-fuchsia-500/20 border-fuchsia-500/50 ring-2 ring-fuchsia-500/30"
                                            : "bg-white/5 border-white/10 hover:border-white/20 hover:bg-white/10"
                                        }`}
                                >
                                    {/* Color Preview Bar */}
                                    <div className="flex gap-1 mb-4">
                                        {dir.color_preview.map((color, i) => (
                                            <div key={i} className="w-8 h-8 rounded-lg border border-white/10 shadow-lg" style={{ backgroundColor: color }} />
                                        ))}
                                    </div>

                                    <h4 className={`text-lg font-bold mb-2 ${selectedDirection?.id === dir.id ? "text-fuchsia-300" : "text-white"}`}>
                                        {dir.title}
                                    </h4>
                                    <p className="text-sm text-white/70 leading-relaxed mb-4">
                                        {dir.description}
                                    </p>
                                    <div className="flex flex-wrap gap-1 mb-3">
                                        {dir.keywords.slice(0, 3).map((kw, i) => (
                                            <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-white/10 text-white/60">
                                                {kw}
                                            </span>
                                        ))}
                                    </div>
                                    <div className="pt-3 border-t border-white/5">
                                        <p className="text-xs text-white/40 italic">
                                            추천 감독: {dir.suggested_auteur}
                                        </p>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Stage 3: Style Guide (Result) */}
                {stage === "guide" && displayResult && (
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

                        {/* Auteur Influence (if present) */}
                        {displayResult.auteur_influence && (
                            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-fuchsia-500/10 to-purple-500/10 border border-fuchsia-500/20 p-6">
                                <div className="absolute top-0 right-0 w-32 h-32 bg-fuchsia-500/20 blur-[60px] rounded-full" />
                                <h3 className="text-lg font-bold text-fuchsia-400 mb-2">{displayResult.auteur_influence.name}</h3>
                                <p className="text-sm text-zinc-300 mb-4">{displayResult.auteur_influence.style_summary}</p>
                                <div className="flex flex-wrap gap-2">
                                    {displayResult.auteur_influence.signature_elements.map((elem, i) => (
                                        <span key={i} className="px-3 py-1 rounded-full bg-fuchsia-500/20 text-fuchsia-300 text-xs">
                                            {elem}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Color Palette */}
                        <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                                    <Palette className="w-4 h-4 text-fuchsia-400" />
                                    Color Palette
                                </h3>
                                <button
                                    onClick={() => handleCopy(displayResult.color_palette.join(", "), "palette")}
                                    className="text-xs text-zinc-500 hover:text-white flex items-center gap-1"
                                >
                                    {copiedField === "palette" ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                                    {copiedField === "palette" ? "Copied" : "Copy"}
                                </button>
                            </div>
                            <div className="flex gap-3 flex-wrap">
                                {displayResult.color_palette.map((color, i) => (
                                    <div key={i} className="flex flex-col items-center gap-2">
                                        <div
                                            className="w-16 h-16 rounded-xl shadow-lg border border-white/10"
                                            style={{ backgroundColor: color }}
                                        />
                                        <span className="text-xs font-mono text-zinc-400">{color}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Visual Guidelines */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {Object.entries(displayResult.visual_guidelines).map(([key, value]) => (
                                <div key={key} className="p-5 bg-white/[0.03] border border-white/10 rounded-xl hover:border-fuchsia-500/30 transition-colors">
                                    <h4 className="text-xs font-bold text-fuchsia-400 uppercase tracking-wider mb-2 capitalize">
                                        {key.replace(/_/g, " ")}
                                    </h4>
                                    <p className="text-sm text-zinc-300 leading-relaxed">{value}</p>
                                </div>
                            ))}
                        </div>

                        {/* Style Keywords */}
                        <div className="p-6 bg-white/[0.03] border border-white/10 rounded-2xl">
                            <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">Style Keywords</h3>
                            <div className="flex flex-wrap gap-2">
                                {displayResult.style_keywords.map((keyword, i) => (
                                    <span key={i} className="px-4 py-2 rounded-full bg-fuchsia-500/10 border border-fuchsia-500/20 text-fuchsia-300 text-sm">
                                        {keyword}
                                    </span>
                                ))}
                            </div>
                        </div>

                        {/* Generative Tech Pack */}
                        {displayResult.generative_prompts && (
                            <div className="space-y-4">
                                <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                                    <Code className="w-4 h-4 text-fuchsia-400" />
                                    Generative Tech Pack
                                </h3>

                                {/* Midjourney */}
                                <div className="p-4 bg-white/[0.03] border border-white/10 rounded-xl">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-xs font-bold text-zinc-300">Midjourney v6</span>
                                        <button
                                            onClick={() => handleCopy(displayResult.generative_prompts!.midjourney, "mj")}
                                            className="text-xs text-fuchsia-400 hover:text-fuchsia-300 flex items-center gap-1"
                                        >
                                            {copiedField === "mj" ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                                            {copiedField === "mj" ? "Copied" : "Copy"}
                                        </button>
                                    </div>
                                    <code className="block p-3 bg-black/50 rounded-lg text-xs text-white/70 font-mono break-all leading-relaxed">
                                        {displayResult.generative_prompts.midjourney}
                                    </code>
                                </div>

                                {/* Veo */}
                                <div className="p-4 bg-white/[0.03] border border-white/10 rounded-xl">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-xs font-bold text-zinc-300">Google Veo</span>
                                        <button
                                            onClick={() => handleCopy(displayResult.generative_prompts!.veo, "veo")}
                                            className="text-xs text-fuchsia-400 hover:text-fuchsia-300 flex items-center gap-1"
                                        >
                                            {copiedField === "veo" ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                                            {copiedField === "veo" ? "Copied" : "Copy"}
                                        </button>
                                    </div>
                                    <code className="block p-3 bg-black/50 rounded-lg text-xs text-white/70 font-mono break-all leading-relaxed">
                                        {displayResult.generative_prompts.veo}
                                    </code>
                                </div>
                            </div>
                        )}

                        {/* Texture & Typography */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Textures */}
                            {displayResult.textures && displayResult.textures.length > 0 && (
                                <div className="space-y-4">
                                    <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                                        <Layers className="w-4 h-4 text-fuchsia-400" />
                                        Texture Elements
                                    </h3>
                                    <div className="space-y-2">
                                        {displayResult.textures.map((texture, i) => (
                                            <div key={i} className="group relative p-4 bg-white/[0.03] border border-white/10 rounded-xl hover:bg-white/[0.05] transition-colors">
                                                <div className="absolute inset-x-0 bottom-0 h-[2px] bg-gradient-to-r from-transparent via-fuchsia-500/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                                                <span className="text-sm text-zinc-200">{texture}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Typography */}
                            {displayResult.typography && (
                                <div className="space-y-4">
                                    <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                                        <Type className="w-4 h-4 text-fuchsia-400" />
                                        Typography
                                    </h3>
                                    <div className="p-5 bg-white/[0.03] border border-white/10 rounded-xl space-y-4">
                                        <div>
                                            <span className="text-[10px] text-zinc-500 uppercase tracking-widest">Primary Title</span>
                                            <p className="text-2xl font-bold text-white mt-1">{displayResult.typography.primary}</p>
                                        </div>
                                        <div className="h-px bg-white/5" />
                                        <div>
                                            <span className="text-[10px] text-zinc-500 uppercase tracking-widest">Secondary Body</span>
                                            <p className="text-base text-zinc-300 mt-1 font-serif">{displayResult.typography.secondary}</p>
                                        </div>
                                        <p className="text-xs text-white/40 italic pt-2">
                                            "{displayResult.typography.description}"
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Avoid Elements */}
                        {displayResult.avoid_elements.length > 0 && (
                            <div className="p-6 bg-rose-500/5 border border-rose-500/20 rounded-2xl">
                                <h3 className="text-sm font-bold text-rose-400 uppercase tracking-wider mb-4">피해야 할 요소</h3>
                                <ul className="space-y-2">
                                    {displayResult.avoid_elements.map((elem, i) => (
                                        <li key={i} className="text-sm text-zinc-300 flex items-start gap-2">
                                            <span className="text-rose-400">✕</span>
                                            {elem}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                )}
            </TeachingPanelLayout>

            <InsufficientCreditsModal
                isOpen={showCreditModal}
                onClose={() => setShowCreditModal(false)}
                requiredCredits={CREDIT_COST}
                currentBalance={creditCtx?.balance ?? 0}
                onRetry={handleGenerateGuide}
            />
        </>
    );
}
