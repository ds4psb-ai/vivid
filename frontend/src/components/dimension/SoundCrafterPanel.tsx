"use client";

import { useState, useEffect, useCallback } from "react";
import TeachingPanelLayout, {
    type ThemeColor,
    useAsyncOperation,
    useResultExport,
} from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionChainOptional, type ChainData } from "@/contexts/DimensionChainContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import ChainDataInput from "./ChainDataInput";
import NextDimensionNav from "./NextDimensionNav";
import {
    Music,
    ArrowRight,
    Copy,
    Check,
    Download,
    Layers,
    Activity,
    Disc,
    Sliders,
    Zap
} from "lucide-react";

// --- Constants ---
const CREDIT_COST_MOOD = 5; // Cheaper for brainstorming
const CREDIT_COST_CRAFT = 8; // Final generation
const THEME_COLOR: ThemeColor = "rose";
const DIMENSION_KEY = "sound-crafter";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

const MAX_CONCEPT_LENGTH = 2000;

// --- Interfaces ---

interface AudioDirection {
    id: string;
    title: string;
    description: string;
    visual_style: {
        color: string;
        icon: string;
    };
    bpm_range: string;
    key_elements: string[];
}

interface MoodboardResult {
    directions: AudioDirection[];
}

interface SoundResult {
    music_prompt?: string;
    udio_prompt?: string;
    style_tags?: string[];
    bpm_range?: string;
    key_signature?: string;
    layers?: {
        melody: string;
        rhythm: string;
        texture: string;
    };
    mixing_guide?: string;
    visualization?: {
        energy_levels: number[];
        color_palette: string[];
    };
    next_dimension?: string;
}

interface MixRecipe {
    melody_focus: number; // 0-10
    rhythm_intensity: number; // 0-10
    texture_density: number; // 0-10
}

// --- Main Component ---

export default function SoundCrafterPanel() {
    // Stage Management: 'intro' | 'mood' | 'layers' | 'mastering'
    const [currentStage, setCurrentStage] = useState<"intro" | "mood" | "layers" | "mastering">("intro");

    // Inputs
    const [concept, setConcept] = useState("");
    const [selectedDirection, setSelectedDirection] = useState<AudioDirection | null>(null);
    const [mixRecipe, setMixRecipe] = useState<MixRecipe>({
        melody_focus: 5,
        rhythm_intensity: 5,
        texture_density: 5
    });

    // Outputs
    const [moodResult, setMoodResult] = useState<MoodboardResult | null>(null);
    const [finalResult, setFinalResult] = useState<SoundResult | null>(null);

    // Platform State (for output display)
    const [activePlatform, setActivePlatform] = useState<"suno" | "udio">("suno");

    const [showCreditModal, setShowCreditModal] = useState(false);
    const [requiredCredits, setRequiredCredits] = useState(CREDIT_COST_MOOD);
    const [validationError, setValidationError] = useState<string | null>(null);
    const [copiedField, setCopiedField] = useState<string | null>(null);

    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();
    const chainCtx = useDimensionChainOptional();

    // Export utilities
    const { exportJSON, copyToClipboard } = useResultExport();

    // Set current dimension on mount
    useEffect(() => {
        if (chainCtx) {
            chainCtx.setCurrentDimension(DIMENSION_KEY);
        }
    }, [chainCtx]);

    // ASYNC OP 1: Moodboard Generator
    const moodOp = useAsyncOperation<{ success: boolean; output: MoodboardResult; error?: string }>({
        onSuccess: (data) => {
            if (data.success && data.output) {
                setMoodResult(data.output);
                setCurrentStage("mood");
                if (!byokKey && creditCtx) void creditCtx.refresh();
            }
        },
        onError: (err) => {
            if (err.message.includes("크레딧") || err.message.includes("402")) {
                setRequiredCredits(CREDIT_COST_MOOD);
                setShowCreditModal(true);
            }
        },
    });

    // ASYNC OP 2: Sound Crafter (Final)
    const craftOp = useAsyncOperation<{ success: boolean; output: SoundResult; error?: string }>({
        onSuccess: (data) => {
            if (data.success && data.output) {
                setFinalResult(data.output);
                setCurrentStage("mastering");

                // Chain Data Update
                if (chainCtx) {
                    chainCtx.setChainData(
                        DIMENSION_KEY,
                        data.output as unknown as Record<string, unknown>,
                        data.output.music_prompt?.slice(0, 50) || concept.slice(0, 50)
                    );
                }
                if (!byokKey && creditCtx) void creditCtx.refresh();
            }
        },
        onError: (err) => {
            if (err.message.includes("크레딧") || err.message.includes("402")) {
                setRequiredCredits(CREDIT_COST_CRAFT);
                setShowCreditModal(true);
            }
        },
    });

    // --- Handlers ---

    const handleApplyChainData = (data: Record<string, ChainData>) => {
        // Auto-fill concept from story or aesthetic
        if (data["story-architect"]?.output?.logline && !concept) {
            setConcept(data["story-architect"].output.logline as string);
        } else if (data["aesthetic-director"]?.output?.mood && !concept) {
            setConcept(`Mood: ${data["aesthetic-director"].output.mood}`);
        }
    };

    const handleGenerateMood = useCallback(async () => {
        const trimmed = concept.trim();
        if (trimmed.length < 5) {
            setValidationError("컨셉을 5자 이상 입력해주세요.");
            return;
        }
        setValidationError(null);

        // Credit check
        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST_MOOD)) {
            setRequiredCredits(CREDIT_COST_MOOD);
            setShowCreditModal(true);
            return;
        }

        await moodOp.execute(
            `${API_BASE}/api/dimension/sound/moodboard`,
            { concept: trimmed, model: "gemini-3-pro-preview" },
            getBYOKHeaders(byokKey)
        );
    }, [concept, byokKey, creditCtx, moodOp]);

    const handleSelectDirection = (direction: AudioDirection) => {
        setSelectedDirection(direction);
        setCurrentStage("layers");
    };

    const handleGenerateFinal = useCallback(async () => {
        if (!selectedDirection) return;

        // Credit check
        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST_CRAFT)) {
            setRequiredCredits(CREDIT_COST_CRAFT);
            setShowCreditModal(true);
            return;
        }

        await craftOp.execute(
            `${API_BASE}/api/dimension/sound/craft`,
            {
                concept: `${concept} (Style: ${selectedDirection.title})`,
                sound_type: "full", // Defaulting to full for this advanced mode
                mood: selectedDirection.description,
                mix_recipe: mixRecipe, // Sending the user's mix
                target_platform: "suno", // Default (backend handles both)
                model: "gemini-3-flash-preview",
            },
            getBYOKHeaders(byokKey)
        );
    }, [concept, selectedDirection, mixRecipe, byokKey, creditCtx, craftOp]);

    const handleCopy = useCallback(async (text: string, field: string) => {
        const success = await copyToClipboard(text);
        if (success) {
            setCopiedField(field);
            setTimeout(() => setCopiedField(null), 2000);
        }
    }, [copyToClipboard]);

    // --- Renderers ---

    const renderMoodStage = () => (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Activity className="w-5 h-5 text-rose-400" />
                1단계: 오디오 디렉션 선택
            </h3>

            <div className="grid grid-cols-1 gap-4">
                {moodResult?.directions.map((dir) => (
                    <button
                        key={dir.id}
                        onClick={() => handleSelectDirection(dir)}
                        className="group relative p-5 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 
                                 text-left transition-all hover:border-rose-500/50 hover:shadow-lg hover:shadow-rose-500/10"
                    >
                        <div className="flex justify-between items-start mb-2">
                            <h4 className="text-lg font-bold text-rose-400 group-hover:text-rose-300 transition-colors">
                                {dir.title}
                            </h4>
                            <span className="text-xs px-2 py-1 rounded-full bg-black/50 text-white/50 border border-white/10">
                                {dir.bpm_range} BPM
                            </span>
                        </div>
                        <p className="text-white/70 text-sm mb-4 leading-relaxed">
                            {dir.description}
                        </p>
                        <div className="flex flex-wrap gap-2">
                            {dir.key_elements.map((el, i) => (
                                <span key={i} className="text-xs px-2 py-1 rounded bg-rose-500/10 text-rose-300/70">
                                    {el}
                                </span>
                            ))}
                        </div>
                    </button>
                ))}
            </div>

            <button
                onClick={() => {
                    setMoodResult(null);
                    setCurrentStage("intro");
                }}
                className="text-sm text-white/40 hover:text-white underline"
            >
                다시 컨셉 입력하기
            </button>
        </div>
    );

    const renderLayersStage = () => (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Sliders className="w-5 h-5 text-rose-400" />
                2단계: 사운드 레이어 믹싱
            </h3>

            <div className="bg-white/5 border border-white/10 rounded-xl p-6 space-y-6">
                <div className="flex items-center gap-4 pb-4 border-b border-white/10">
                    <div className="w-12 h-12 rounded-lg bg-rose-500/20 flex items-center justify-center">
                        <Music className="w-6 h-6 text-rose-400" />
                    </div>
                    <div>
                        <h4 className="font-bold text-white">{selectedDirection?.title}</h4>
                        <p className="text-sm text-white/50">{selectedDirection?.description}</p>
                    </div>
                </div>

                {/* Mixing Sliders */}
                <div className="space-y-6">
                    <div className="space-y-3">
                        <div className="flex justify-between text-sm">
                            <label className="text-white/80 font-medium">멜로디 포커스</label>
                            <span className="text-rose-400">{mixRecipe.melody_focus * 10}%</span>
                        </div>
                        <input
                            type="range" min="0" max="10"
                            value={mixRecipe.melody_focus}
                            onChange={(e) => setMixRecipe({ ...mixRecipe, melody_focus: parseInt(e.target.value) })}
                            className="w-full accent-rose-500 bg-white/10 h-2 rounded-lg appearance-none cursor-pointer"
                        />
                        <p className="text-xs text-white/40">높을수록 멜로디라인이 강조됩니다.</p>
                    </div>

                    <div className="space-y-3">
                        <div className="flex justify-between text-sm">
                            <label className="text-white/80 font-medium">리듬 인텐시티</label>
                            <span className="text-rose-400">{mixRecipe.rhythm_intensity * 10}%</span>
                        </div>
                        <input
                            type="range" min="0" max="10"
                            value={mixRecipe.rhythm_intensity}
                            onChange={(e) => setMixRecipe({ ...mixRecipe, rhythm_intensity: parseInt(e.target.value) })}
                            className="w-full accent-rose-500 bg-white/10 h-2 rounded-lg appearance-none cursor-pointer"
                        />
                        <p className="text-xs text-white/40">비트와 퍼커션의 강도를 조절합니다.</p>
                    </div>

                    <div className="space-y-3">
                        <div className="flex justify-between text-sm">
                            <label className="text-white/80 font-medium">텍스처 밀도</label>
                            <span className="text-rose-400">{mixRecipe.texture_density * 10}%</span>
                        </div>
                        <input
                            type="range" min="0" max="10"
                            value={mixRecipe.texture_density}
                            onChange={(e) => setMixRecipe({ ...mixRecipe, texture_density: parseInt(e.target.value) })}
                            className="w-full accent-rose-500 bg-white/10 h-2 rounded-lg appearance-none cursor-pointer"
                        />
                        <p className="text-xs text-white/40">배경음과 앰비언스의 풍부함을 조절합니다.</p>
                    </div>
                </div>
            </div>

            <div className="flex gap-3">
                <button
                    onClick={() => setCurrentStage("mood")}
                    className="flex-1 py-4 rounded-xl border border-white/10 text-white/60 hover:bg-white/5 transition-all font-medium"
                >
                    이전
                </button>
                <button
                    onClick={handleGenerateFinal}
                    disabled={craftOp.isLoading}
                    className="flex-[2] py-4 rounded-xl bg-gradient-to-r from-rose-500 to-pink-500 text-black font-bold 
                             hover:from-rose-400 hover:to-pink-400 transition-all flex items-center justify-center gap-2"
                >
                    {craftOp.isLoading ? (
                        <>
                            <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                            최종 프롬프트 생성 중...
                        </>
                    ) : (
                        <>
                            마스터링 시작
                            <Zap className="w-4 h-4 fill-current" />
                        </>
                    )}
                </button>
            </div>

            {!byokKey && (
                <div className="text-xs text-center text-white/30">
                    최종 생성 비용: {CREDIT_COST_CRAFT} 크레딧
                </div>
            )}
        </div>
    );

    const renderMasteringStage = () => (
        <div className="space-y-6 animate-in fade-in zoom-in-95 duration-500">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Disc className="w-5 h-5 text-rose-400 animate-spin-slow" />
                    사운드 테크 팩
                </h3>
                <div className="flex bg-white/5 rounded-lg p-1">
                    <button
                        onClick={() => setActivePlatform("suno")}
                        className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activePlatform === "suno" ? "bg-rose-500 text-black shadow-lg" : "text-white/50 hover:text-white"}`}
                    >
                        Suno v3
                    </button>
                    <button
                        onClick={() => setActivePlatform("udio")}
                        className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activePlatform === "udio" ? "bg-rose-500 text-black shadow-lg" : "text-white/50 hover:text-white"}`}
                    >
                        Udio
                    </button>
                </div>
            </div>

            {/* Prompt Display */}
            <div className="p-6 rounded-2xl bg-gradient-to-br from-rose-500/10 to-black border border-rose-500/20 relative group">
                <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                        onClick={() => handleCopy(
                            activePlatform === "suno" ? finalResult?.music_prompt || "" : finalResult?.udio_prompt || "",
                            "prompt"
                        )}
                        className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors"
                    >
                        {copiedField === "prompt" ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                    </button>
                </div>
                <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider mb-3">
                    {activePlatform === "suno" ? "Suno v3.5 최적화" : "Udio Beta 최적화"}
                </h4>
                <p className="text-white/90 font-mono text-sm leading-relaxed whitespace-pre-wrap">
                    {activePlatform === "suno" ? finalResult?.music_prompt : finalResult?.udio_prompt || "Udio 프롬프트가 생성되지 않았습니다."}
                </p>
            </div>

            {/* Layers Breakdown */}
            {finalResult?.layers && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                        <span className="text-xs text-rose-400/70 block mb-2">멜로디</span>
                        <p className="text-sm text-white/80">{finalResult.layers.melody}</p>
                    </div>
                    <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                        <span className="text-xs text-rose-400/70 block mb-2">리듬</span>
                        <p className="text-sm text-white/80">{finalResult.layers.rhythm}</p>
                    </div>
                    <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                        <span className="text-xs text-rose-400/70 block mb-2">텍스처</span>
                        <p className="text-sm text-white/80">{finalResult.layers.texture}</p>
                    </div>
                </div>
            )}

            {/* Mixing Guide */}
            {finalResult?.mixing_guide && (
                <div className="p-5 rounded-xl bg-black/40 border dashed border-white/10">
                    <h4 className="text-sm font-bold text-white/60 mb-2 flex items-center gap-2">
                        <Sliders className="w-4 h-4" />
                        믹싱 가이드
                    </h4>
                    <p className="text-sm text-white/50">{finalResult.mixing_guide}</p>
                </div>
            )}

            <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
                <button
                    onClick={() => {
                        if (finalResult) {
                            exportJSON(finalResult, `sound-pack-${Date.now()}.json`);
                        }
                    }}
                    disabled={!finalResult}
                    className="px-4 py-2 hover:bg-white/5 rounded-lg text-sm text-white/60 hover:text-white flex items-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <Download className="w-4 h-4" />
                    JSON 내보내기
                </button>
                <button
                    onClick={() => {
                        setFinalResult(null);
                        setCurrentStage("layers");
                    }}
                    className="px-6 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-medium text-white transition-colors"
                >
                    다시 믹싱하기
                </button>
            </div>
        </div>
    );

    const sidebarContent = (
        <div className="space-y-8">
            <ChainDataInput
                currentDimension={DIMENSION_KEY}
                onApplyData={handleApplyChainData}
                themeColor={THEME_COLOR}
            />

            {/* Stage Indicator */}
            <div className="space-y-4">
                <h4 className="text-xs font-bold text-white/40 uppercase tracking-wider">제작 플로우</h4>
                <div className="space-y-0 relative">
                    {/* Connection Line */}
                    <div className="absolute left-[15px] top-2 bottom-2 w-0.5 bg-white/10" />

                    {[
                        { id: "intro", label: "컨셉", icon: Music },
                        { id: "mood", label: "소닉 무드", icon: Activity },
                        { id: "layers", label: "레이어 믹싱", icon: Layers },
                        { id: "mastering", label: "마스터링", icon: Disc },
                    ].map((step, idx) => {
                        const isActive = currentStage === step.id;
                        const isPast = ["intro", "mood", "layers", "mastering"].indexOf(currentStage) > idx;

                        return (
                            <div key={step.id} className={`relative flex items-center gap-3 p-2 rounded-lg transition-all ${isActive ? "bg-white/5" : ""}`}>
                                <div className={`relative z-10 w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all
                                    ${isActive || isPast ? "bg-black border-rose-500 text-rose-500" : "bg-black border-white/10 text-white/30"}`}>
                                    <step.icon className="w-4 h-4" />
                                </div>
                                <span className={`text-sm font-medium ${isActive ? "text-white" : isPast ? "text-white/60" : "text-white/30"}`}>
                                    {step.label}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Concept Input - Only editable in early stages */}
            {currentStage === "intro" && (
                <div className="space-y-2 animate-in fade-in">
                    <label className="text-sm font-medium text-white/80">
                        사운드 컨셉
                    </label>
                    <textarea
                        value={concept}
                        onChange={(e) => setConcept(e.target.value)}
                        placeholder="어떤 분위기의 사운드가 필요한가요? (예: 비 오는 네오 도쿄의 사이버펑크 재즈)"
                        className="w-full h-40 px-4 py-3 bg-white/5 border border-white/10 rounded-xl
                                  text-white placeholder:text-white/30 resize-none
                                  focus:outline-none focus:ring-2 focus:ring-rose-500/50"
                        disabled={moodOp.isLoading}
                    />
                    <div className="text-xs text-white/40 text-right">{concept.length}/2000</div>

                    <button
                        onClick={handleGenerateMood}
                        disabled={moodOp.isLoading || concept.length < 5}
                        className={`w-full py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all mt-4
                                  ${moodOp.isLoading || concept.length < 5
                                ? "bg-rose-500/20 text-rose-400/50 cursor-not-allowed"
                                : "bg-gradient-to-r from-rose-500 to-pink-500 text-black hover:from-rose-400 hover:to-pink-400"
                            }`}
                    >
                        {moodOp.isLoading ? (
                            <>
                                <div className="w-5 h-5 border-2 border-rose-400/30 border-t-rose-400 rounded-full animate-spin" />
                                분석 중...
                            </>
                        ) : (
                            <>
                                사운드 디렉션 생성
                                <ArrowRight className="w-4 h-4" />
                            </>
                        )}
                    </button>
                    {!byokKey && (
                        <div className="text-xs text-center text-white/30 mt-2">
                            예상 비용: {CREDIT_COST_MOOD} 크레딧
                        </div>
                    )}
                </div>
            )}
        </div>
    );

    return (
        <>
            <TeachingPanelLayout
                title="사운드 디자인 스튜디오"
                sidebarContent={sidebarContent}
                themeColor={THEME_COLOR}
                creditCost={0} // Managed individually
                isLoading={moodOp.isLoading || craftOp.isLoading}
                progress={moodOp.isLoading ? moodOp.progress : craftOp.progress}
                onCancel={() => {
                    if (moodOp.isLoading) moodOp.cancel();
                    if (craftOp.isLoading) craftOp.cancel();
                }}
                onRetry={() => {
                    if (moodOp.canRetry) void moodOp.retry();
                    else if (craftOp.canRetry) void craftOp.retry();
                }}
                canRetry={moodOp.canRetry || craftOp.canRetry}
                error={validationError || moodOp.error || craftOp.error}
                retryCount={moodOp.currentRetryCount || craftOp.currentRetryCount}
                maxRetries={3}
            >
                <div className="h-full flex flex-col justify-center">
                    {currentStage === "intro" ? (
                        <div className="flex flex-col items-center justify-center text-center opacity-50">
                            <Music className="w-16 h-16 text-rose-400 mb-6" />
                            <h2 className="text-2xl font-bold text-white mb-2">사운드 디자인 스튜디오</h2>
                            <p className="text-white/50 max-w-md">
                                추상적인 아이디어를 구체적인 사운드 텍스처로 변환하세요.<br />
                                Suno 및 Udio 용 전문 프롬프트가 생성됩니다.
                            </p>
                        </div>
                    ) : currentStage === "mood" ? (
                        renderMoodStage()
                    ) : currentStage === "layers" ? (
                        renderLayersStage()
                    ) : (
                        renderMasteringStage()
                    )}
                </div>
            </TeachingPanelLayout>

            <InsufficientCreditsModal
                isOpen={showCreditModal}
                onClose={() => setShowCreditModal(false)}
                requiredCredits={requiredCredits}
                currentBalance={creditCtx?.balance || 0}
            />
        </>
    );
}
