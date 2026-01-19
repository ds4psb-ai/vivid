"use client";

import { useState, useEffect, useCallback } from "react";
import TeachingPanelLayout, {
    type ThemeColor,
    useAsyncOperation,
    useResultExport,
} from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import { useDimensionChainOptional, type ChainData } from "@/contexts/DimensionChainContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import ChainDataInput from "./ChainDataInput";
import NextDimensionNav from "./NextDimensionNav";
import { Layers, ArrowRight, CheckCircle, Download, Sparkles, BookOpen } from "lucide-react";

// const CREDIT_COST = 10; // REMOVED
const THEME_COLOR: ThemeColor = "emerald";
const DIMENSION_CODE = "story" as const;
const DIMENSION_KEY = "story-architect";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

interface StoryResult {
    title?: string;
    logline?: string;
    synopsis?: string;
    structure?: Array<{
        act: string;
        description: string;
        duration: string;
        emotion: string;
    }>;
    characters?: Array<{
        name: string;
        role: string;
        arc: string;
        traits: string[];
    }>;
    themes?: string[];
    visual_motifs?: string[];
    next_dimension?: string;
}

interface NarrativeAngle {
    id: string;
    title: string;
    logline: string;
    tone: string;
    theme: string;
}

interface StoryRefineResult {
    angles: NarrativeAngle[];
}

type Stage = "pitch" | "blueprint" | "script";

const GENRES = [
    { value: "drama", label: "드라마" },
    { value: "thriller", label: "스릴러" },
    { value: "comedy", label: "코미디" },
    { value: "documentary", label: "다큐멘터리" },
    { value: "horror", label: "호러" },
    { value: "scifi", label: "SF" },
    { value: "ad", label: "광고" },
    { value: "mv", label: "뮤직비디오" },
    { value: "short", label: "숏폼" },
];

const DURATIONS = [
    { value: "15", label: "15초 (숏폼)" },
    { value: "30", label: "30초" },
    { value: "60", label: "1분" },
    { value: "180", label: "3분" },
    { value: "300", label: "5분" },
];

const STRUCTURES = [
    { value: "3-act", label: "3막 구조" },
    { value: "5-act", label: "5막 구조" },
    { value: "hero-journey", label: "영웅의 여정" },
    { value: "hook-body-cta", label: "훅-본론-CTA" },
    { value: "problem-solution", label: "문제-해결" },
    { value: "story-arc", label: "스토리 아크" },
    { value: "nonlinear", label: "비선형" },
    { value: "slice-of-life", label: "일상물" },
    { value: "montage", label: "몽타주" },
];

export default function StoryArchitectPanel() {
    const [concept, setConcept] = useState("");
    const [genre, setGenre] = useState("drama");
    const [duration, setDuration] = useState("60");
    const [structure, setStructure] = useState("3-act");

    // Writer's Room Workflow State
    const [stage, setStage] = useState<Stage>("pitch");
    const [angles, setAngles] = useState<NarrativeAngle[]>([]);
    const [selectedAngle, setSelectedAngle] = useState<NarrativeAngle | null>(null);

    // Chain data from previous dimensions
    const [personaData, setPersonaData] = useState<Record<string, unknown>>({});
    const [referenceAnalysis, setReferenceAnalysis] = useState<Record<string, unknown>>({});

    const [showCreditModal, setShowCreditModal] = useState(false);
    const [validationError, setValidationError] = useState<string | null>(null);

    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();
    const chainCtx = useDimensionChainOptional();

    const { getToolByDimension } = useDimensionConfig();
    const toolConfig = getToolByDimension("STORY") ?? getToolByDimension("SA");
    const CREDIT_COST = toolConfig?.creditCost ?? 10;

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
    } = useAsyncOperation<{ success: boolean; output: StoryResult; error?: string }>({
        onSuccess: (data) => {
            if (data.success && data.output) {
                // Store in chain context for next dimensions
                if (chainCtx) {
                    chainCtx.setChainData(
                        DIMENSION_KEY,
                        data.output as unknown as Record<string, unknown>,
                        data.output.title || data.output.logline || concept.slice(0, 50)
                    );
                }
                // Refresh credits
                if (!byokKey && creditCtx) {
                    void creditCtx.refresh();
                }
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

    // Set current dimension on mount
    useEffect(() => {
        if (chainCtx) {
            chainCtx.setCurrentDimension(DIMENSION_KEY);
        }
    }, [chainCtx]);

    // Handler to apply chain data from previous dimensions
    const handleApplyChainData = (data: Record<string, ChainData>) => {
        if (data["abyss-mirror"]) {
            setPersonaData(data["abyss-mirror"].output);
        }
        if (data["reference-decoder"]) {
            setReferenceAnalysis(data["reference-decoder"].output);
        }
    };

    const MAX_CONCEPT_LENGTH = 3000;

    // Async operation hook for refine (returns angles)
    const {
        isLoading: _isRefineLoading,
        execute: executeRefine,
    } = useAsyncOperation<{ success: boolean; output: StoryRefineResult; error?: string }>({
        onSuccess: (data) => {
            if (data.success && data.output?.angles) {
                setAngles(data.output.angles);
                setStage("blueprint");
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

    const handleRefine = useCallback(async () => {
        const trimmedConcept = concept.trim();
        if (!trimmedConcept || trimmedConcept.length < 5) {
            setValidationError("컨셉을 입력해주세요.");
            return;
        }
        setValidationError(null);

        // Call refine endpoint
        await executeRefine(
            `${API_BASE}/api/dimension/story/refine`,
            {
                concept,
                genre,
                model: "gemini-3-pro-preview",
            },
            getBYOKHeaders(byokKey)
        );
    }, [concept, genre, byokKey, executeRefine]);

    const handleGenerate = async () => {
        if (!selectedAngle && stage !== "pitch") {
            // Fallback if no angle selected in blueprint mode
        }

        const trimmedConcept = concept.trim();
        if (!trimmedConcept || trimmedConcept.length < 10) {
            setValidationError("컨셉을 10자 이상 입력해주세요.");
            return;
        }
        if (trimmedConcept.length > MAX_CONCEPT_LENGTH) {
            setValidationError(`컨셉은 ${MAX_CONCEPT_LENGTH}자 이하로 입력해주세요.`);
            return;
        }
        setValidationError(null);

        // Credit check
        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
            setShowCreditModal(true);
            return;
        }

        // Combine original concept with selected angle
        const finalConcept = selectedAngle
            ? `Original Concept: ${trimmedConcept}\nSelected Angle: ${selectedAngle.title} - ${selectedAngle.logline}\nTone: ${selectedAngle.tone}\nTheme: ${selectedAngle.theme}`
            : trimmedConcept;

        await execute(
            `${API_BASE}/api/dimension/story/architect`,
            {
                concept: finalConcept,
                genre,
                duration,
                structure,
                language: "ko",
                model: "gemini-3-pro-preview",
                persona_data: personaData,
                reference_analysis: referenceAnalysis,
            },
            getBYOKHeaders(byokKey)
        ).then((res) => {
            if (res && res.success) {
                setStage("script");
            }
        });
    };

    // Export result as JSON
    const handleExportJson = () => {
        if (!result?.output) return;
        exportJSON(result.output, `story-architect-${Date.now()}.json`);
    };

    // Extracted result data for display
    const displayResult = result?.success ? result.output : null;
    const displayError = validationError || (result && !result.success ? result.error : error);

    const sidebarContent = (
        <div className="space-y-6">
            {/* Chain Data Input */}
            <ChainDataInput
                currentDimension={DIMENSION_KEY}
                onApplyData={handleApplyChainData}
                themeColor={THEME_COLOR}
            />

            {/* Stage Indicator */}
            <div className="flex items-center justify-between text-xs text-slate-400 dark:text-white/50 mb-2">
                <span className={stage === "pitch" ? "text-emerald-600 dark:text-emerald-400 font-bold" : ""}>1. 발상</span>
                <span>→</span>
                <span className={stage === "blueprint" ? "text-emerald-600 dark:text-emerald-400 font-bold" : ""}>2. 설계</span>
                <span>→</span>
                <span className={stage === "script" ? "text-emerald-600 dark:text-emerald-400 font-bold" : ""}>3. 집필</span>
            </div>

            {/* Concept Input (Always visible but disabled in later stages) */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700 dark:text-white/80">
                    영상 컨셉
                </label>
                <textarea
                    value={concept}
                    onChange={(e) => setConcept(e.target.value)}
                    placeholder="어떤 영상을 만들고 싶으신가요? 아이디어, 분위기, 메시지 등을 자유롭게 적어주세요..."
                    className="w-full h-32 px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl
                              text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-white/30 resize-none
                              focus:outline-none focus:ring-2 focus:ring-emerald-500/50 disabled:opacity-50 disabled:bg-slate-100 dark:disabled:bg-white/5"
                    disabled={isLoading || stage !== "pitch"}
                />
                <div className="text-xs text-slate-400 dark:text-white/40 text-right">{concept.length}/3000</div>
            </div>

            {/* Stage Actions */}
            {stage === "pitch" && (
                <>
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-700 dark:text-white/80">선호 장르</label>
                        <select
                            value={genre}
                            onChange={(e) => setGenre(e.target.value)}
                            className="w-full px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl
                                  text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                            disabled={isLoading}
                        >
                            {GENRES.map((g) => (
                                <option key={g.value} value={g.value} className="bg-white dark:bg-black text-slate-900 dark:text-white">
                                    {g.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <button
                        onClick={handleRefine}
                        disabled={isLoading || concept.length < 5}
                        className={`w-full py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all
                              ${isLoading || concept.length < 5
                                ? "bg-emerald-500/20 text-emerald-400/50 cursor-not-allowed"
                                : "bg-emerald-500 text-black hover:bg-emerald-400"
                            }`}
                    >
                        {isLoading ? (
                            <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                        ) : (
                            <>
                                <Sparkles className="w-4 h-4" />
                                아이디어 다듬기 (Pitch)
                            </>
                        )}
                    </button>
                </>
            )}

            {stage === "blueprint" && (
                <>
                    <div className="p-4 bg-emerald-100 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 rounded-xl">
                        <h4 className="text-emerald-600 dark:text-emerald-400 text-sm font-bold mb-1">선택된 앵글</h4>
                        <p className="text-slate-800 dark:text-white font-medium text-sm">{selectedAngle?.title}</p>
                    </div>

                    {/* Duration */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-700 dark:text-white/80">길이</label>
                        <select
                            value={duration}
                            onChange={(e) => setDuration(e.target.value)}
                            className="w-full px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl
                                  text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                            disabled={isLoading}
                        >
                            {DURATIONS.map((d) => (
                                <option key={d.value} value={d.value} className="bg-white dark:bg-black text-slate-900 dark:text-white">
                                    {d.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Structure */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-700 dark:text-white/80">스토리 구조</label>
                        <select
                            value={structure}
                            onChange={(e) => setStructure(e.target.value)}
                            className="w-full px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl
                                  text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                            disabled={isLoading}
                        >
                            {STRUCTURES.map((s) => (
                                <option key={s.value} value={s.value} className="bg-white dark:bg-black text-slate-900 dark:text-white">
                                    {s.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <button
                        onClick={handleGenerate}
                        disabled={isLoading || !selectedAngle}
                        className={`w-full py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all
                            ${isLoading || !selectedAngle
                                ? "bg-emerald-500/20 text-emerald-400/50 cursor-not-allowed"
                                : "bg-emerald-500 text-black hover:bg-emerald-400"
                            }`}
                    >
                        {isLoading ? (
                            <>
                                <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                                시나리오 쓰는 중...
                            </>
                        ) : (
                            <>
                                시나리오 완성하기
                                <ArrowRight className="w-4 h-4" />
                            </>
                        )}
                    </button>
                </>
            )}

            {/* Refine / Reset (Stage 3) */}
            {stage === "script" && (
                <button
                    onClick={() => {
                        setStage("blueprint");
                        // We keep the selected angle
                    }}
                    className="w-full py-3 rounded-xl bg-white/5 hover:bg-white/10 text-white border border-white/10 transition-all font-medium"
                >
                    ◀ 다시 설계하기
                </button>
            )}

            {/* Credit Cost */}
            {!byokKey && (
                <div className="text-xs text-slate-500 dark:text-white/40 text-center mt-4">
                    예상 비용: {stage === "pitch" ? "무료 (BYOK)" : CREDIT_COST} 크레딧
                </div>
            )}
        </div>
    );

    return (
        <>
            <TeachingPanelLayout
                title="시나리오 생성기"
                sidebarContent={sidebarContent}
                themeColor={THEME_COLOR}
                dimensionCode={DIMENSION_CODE}
                creditCost={CREDIT_COST}
                isLoading={isLoading}
                progress={progress}
                onCancel={cancel}
                onRetry={retry}
                canRetry={canRetry}
                error={displayError}
                retryCount={currentRetryCount}
                maxRetries={3}
            >
                {/* Main Content */}
                <div className="space-y-6">
                    {/* Note: Error display moved to OperationProgress in DimensionPanelLayout */}

                    {/* Stage 1: Pitch (Initial State) */}
                    {stage === "pitch" && !isLoading && (
                        <div className="flex flex-col items-center justify-center h-full min-h-[var(--layout-panel-min-height)] text-center p-8">
                            <div className="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center mb-6">
                                <Sparkles className="w-10 h-10 text-emerald-600 dark:text-emerald-400" />
                            </div>
                            <h3 className="text-2xl font-bold text-slate-800 dark:text-white mb-2">Writer&apos;s Room에 오신 것을 환영합니다</h3>
                            <p className="text-slate-600 dark:text-white/60 max-w-md leading-relaxed">
                                단순한 문장이 위대한 스토리로 발전하는 공간입니다.<br />
                                먼저 떠오르는 영감을 좌측에 적어주세요.<br />
                                AI가 3가지 다른 이야기 방향을 제안해드립니다.
                            </p>
                        </div>
                    )}

                    {/* Stage 2: Blueprint (Select Angle) */}
                    {stage === "blueprint" && (
                        <div className="space-y-6 animate-in fade-in duration-500">
                            <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                <BookOpen className="w-5 h-5 text-emerald-400" />
                                이야기의 방향을 선택하세요
                            </h3>
                            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                {angles.map((angle) => (
                                    <button
                                        key={angle.id}
                                        onClick={() => setSelectedAngle(angle)}
                                        className={`text-left p-6 rounded-2xl border transition-all relative overflow-hidden group
                                            ${selectedAngle?.id === angle.id
                                                ? "bg-emerald-100 dark:bg-emerald-500/20 border-emerald-500 ring-2 ring-emerald-500/30"
                                                : "bg-white dark:bg-white/5 border-slate-200 dark:border-white/10 hover:border-emerald-300 dark:hover:border-white/20 hover:bg-slate-50 dark:hover:bg-white/10"
                                            }`}
                                    >
                                        <div className="relative z-10">
                                            <div className="mb-4">
                                                <span className={`text-xs font-bold px-2 py-1 rounded-full ${selectedAngle?.id === angle.id ? "bg-emerald-200 text-emerald-800 dark:bg-white/10 dark:text-white/70" : "bg-slate-200 text-slate-700 dark:bg-white/10 dark:text-white/70"}`}>
                                                    {angle.tone}
                                                </span>
                                            </div>
                                            <h4 className={`text-lg font-bold mb-2 ${selectedAngle?.id === angle.id ? "text-emerald-700 dark:text-emerald-300" : "text-slate-900 dark:text-white"}`}>
                                                {angle.title}
                                            </h4>
                                            <p className={`text-sm leading-relaxed mb-4 ${selectedAngle?.id === angle.id ? "text-emerald-800 dark:text-white/70" : "text-slate-600 dark:text-white/70"}`}>
                                                {angle.logline}
                                            </p>
                                            <div className="pt-4 border-t border-black/5 dark:border-white/5">
                                                <p className="text-xs text-slate-400 dark:text-white/40 italic">
                                                    핵심 테마: {angle.theme}
                                                </p>
                                            </div>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Stage 3: Script (Result Display) */}
                    {stage === "script" && displayResult && (
                        <div className="space-y-6 animate-in fade-in duration-500">
                            {/* Title & Logline */}
                            <div className="p-6 rounded-2xl bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-100 dark:border-emerald-500/20">
                                <div className="flex items-center gap-2 mb-3">
                                    <CheckCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                                    <span className="text-emerald-700 dark:text-emerald-400 font-bold text-sm">생성 완료</span>
                                </div>
                                <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">{displayResult.title}</h2>
                                <p className="text-slate-600 dark:text-white/70 italic">&ldquo;{displayResult.logline}&rdquo;</p>
                            </div>

                            {/* Export Button */}
                            <div className="flex justify-end">
                                <button
                                    onClick={handleExportJson}
                                    className="px-4 py-2 bg-white dark:bg-white/5 hover:bg-slate-100 dark:hover:bg-white/10 border border-slate-200 dark:border-white/10 rounded-lg flex items-center gap-2 text-sm text-slate-600 dark:text-white/70 hover:text-slate-900 dark:hover:text-white transition-all"
                                >
                                    <Download className="w-4 h-4" />
                                    JSON 내보내기
                                </button>
                            </div>

                            {/* Synopsis */}
                            {displayResult.synopsis && (
                                <div className="space-y-2">
                                    <h3 className="text-lg font-bold text-slate-800 dark:text-white">개요</h3>
                                    <p className="text-slate-600 dark:text-white/70 leading-relaxed">{displayResult.synopsis}</p>
                                </div>
                            )}

                            {/* Structure */}
                            {displayResult.structure && displayResult.structure.length > 0 && (
                                <div className="space-y-3">
                                    <h3 className="text-lg font-bold text-slate-800 dark:text-white">구조</h3>
                                    <div className="space-y-2">
                                        {displayResult.structure.map((act, i) => (
                                            <div key={i} className="p-4 rounded-xl bg-white/50 dark:bg-white/5 border border-slate-200 dark:border-white/10">
                                                <div className="flex items-center justify-between mb-2">
                                                    <span className="text-emerald-600 dark:text-emerald-400 font-bold">Act {act.act}</span>
                                                    <span className="text-xs text-slate-400 dark:text-white/40">{act.duration}</span>
                                                </div>
                                                <p className="text-slate-600 dark:text-white/70 text-sm">{act.description}</p>
                                                <span className="inline-block mt-2 px-2 py-1 text-xs rounded-full bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400">
                                                    {act.emotion}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Characters */}
                            {displayResult.characters && displayResult.characters.length > 0 && (
                                <div className="space-y-3">
                                    <h3 className="text-lg font-bold text-slate-800 dark:text-white">등장인물</h3>
                                    <div className="grid gap-3">
                                        {displayResult.characters.map((char, i) => (
                                            <div key={i} className="p-4 rounded-xl bg-white/50 dark:bg-white/5 border border-slate-200 dark:border-white/10">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className="text-slate-900 dark:text-white font-bold">{char.name}</span>
                                                    <span className="text-xs px-2 py-0.5 rounded-full bg-slate-200 dark:bg-white/10 text-slate-600 dark:text-white/60">
                                                        {char.role}
                                                    </span>
                                                </div>
                                                <p className="text-slate-600 dark:text-white/60 text-sm mb-2">{char.arc}</p>
                                                <div className="flex flex-wrap gap-1">
                                                    {char.traits?.map((trait, j) => (
                                                        <span key={j} className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400">
                                                            {trait}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Themes & Visual Motifs */}
                            <div className="grid grid-cols-2 gap-4">
                                {displayResult.themes && displayResult.themes.length > 0 && (
                                    <div className="space-y-2">
                                        <h3 className="text-sm font-bold text-slate-700 dark:text-white/80">주제</h3>
                                        <div className="flex flex-wrap gap-1">
                                            {displayResult.themes.map((theme, i) => (
                                                <span key={i} className="text-xs px-2 py-1 rounded-full bg-slate-100 dark:bg-white/10 text-slate-600 dark:text-white/70">
                                                    {theme}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                {displayResult.visual_motifs && displayResult.visual_motifs.length > 0 && (
                                    <div className="space-y-2">
                                        <h3 className="text-sm font-bold text-slate-700 dark:text-white/80">시각적 모티프</h3>
                                        <div className="flex flex-wrap gap-1">
                                            {displayResult.visual_motifs.map((motif, i) => (
                                                <span key={i} className="text-xs px-2 py-1 rounded-full bg-emerald-100 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400">
                                                    {motif}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Next Dimension Navigation */}
                            <NextDimensionNav
                                currentDimension={DIMENSION_KEY}
                                show={true}
                                themeColor={THEME_COLOR}
                            />
                        </div>
                    )}

                    {/* Empty State */}
                    {!stage && !displayResult && !displayError && (
                        <div className="flex flex-col items-center justify-center h-full min-h-[var(--layout-panel-min-height)] text-center">
                            <Layers className="w-16 h-16 text-emerald-500/30 dark:text-emerald-400/30 mb-4" />
                            <h3 className="text-xl font-bold text-slate-400 dark:text-white/60 mb-2">시나리오 생성기</h3>
                            <p className="text-slate-400 dark:text-white/40 text-sm max-w-md">
                                영상 컨셉을 입력하면 당신만의 스토리를 자동으로 작성합니다.
                                장르와 구조를 선택하여 맞춤형 시나리오를 만들어보세요.
                            </p>
                        </div>
                    )}
                </div>
            </TeachingPanelLayout>

            {/* Credit Modal */}
            <InsufficientCreditsModal
                isOpen={showCreditModal}
                onClose={() => setShowCreditModal(false)}
                requiredCredits={CREDIT_COST}
                currentBalance={creditCtx?.balance || 0}
            />
        </>
    );
}
