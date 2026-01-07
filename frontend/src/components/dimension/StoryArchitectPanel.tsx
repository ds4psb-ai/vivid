"use client";

import { useState, useEffect } from "react";
import TeachingPanelLayout, { type ThemeColor } from "./DimensionPanelLayout";
import { useBYOK } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionChainOptional, type ChainData } from "@/contexts/DimensionChainContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import ChainDataInput from "./ChainDataInput";
import NextDimensionNav from "./NextDimensionNav";
import { api } from "@/lib/api";
import { Layers, ArrowRight, CheckCircle, AlertCircle } from "lucide-react";

const CREDIT_COST = 10;
const THEME_COLOR: ThemeColor = "emerald";
const DIMENSION_KEY = "story-architect";

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

const GENRES = [
    { value: "drama", label: "드라마" },
    { value: "ad", label: "광고" },
    { value: "mv", label: "뮤직비디오" },
    { value: "documentary", label: "다큐멘터리" },
    { value: "short", label: "숏폼" },
];

const DURATIONS = [
    { value: "15s", label: "15초" },
    { value: "30s", label: "30초" },
    { value: "60s", label: "1분" },
    { value: "3m", label: "3분" },
    { value: "5m", label: "5분" },
];

const STRUCTURES = [
    { value: "3act", label: "3막 구조" },
    { value: "hero", label: "영웅의 여정" },
    { value: "circular", label: "순환 구조" },
    { value: "montage", label: "몽타주" },
];

export default function StoryArchitectPanel() {
    const [concept, setConcept] = useState("");
    const [genre, setGenre] = useState("drama");
    const [duration, setDuration] = useState("60s");
    const [structure, setStructure] = useState("3act");

    // Chain data from previous dimensions
    const [personaData, setPersonaData] = useState<Record<string, unknown>>({});
    const [referenceAnalysis, setReferenceAnalysis] = useState<Record<string, unknown>>({});

    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<StoryResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showCreditModal, setShowCreditModal] = useState(false);

    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();
    const chainCtx = useDimensionChainOptional();

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

    const handleGenerate = async () => {
        if (!concept.trim() || concept.length < 10) {
            setError("컨셉을 10자 이상 입력해주세요.");
            return;
        }

        // Credit check
        if (!byokKey && creditCtx) {
            if (creditCtx.balance < CREDIT_COST) {
                setShowCreditModal(true);
                return;
            }
        }

        setIsLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await api.executeStoryArchitect({
                concept,
                genre,
                duration,
                structure,
                language: "ko",
                model: "gemini-2.5-pro",
                persona_data: personaData,
                reference_analysis: referenceAnalysis,
            });

            if (response.success && response.output) {
                const storyResult = response.output as StoryResult;
                setResult(storyResult);

                // Store in chain context for next dimensions
                if (chainCtx) {
                    chainCtx.setChainData(
                        DIMENSION_KEY,
                        response.output as Record<string, unknown>,
                        storyResult.title || storyResult.logline || concept.slice(0, 50)
                    );
                }

                // Refresh credits
                if (creditCtx) {
                    creditCtx.refresh();
                }
            } else {
                setError(response.error || "시나리오 생성에 실패했습니다.");
            }
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.";
            // Error classification for better UX
            if (errorMessage.includes("402") || errorMessage.includes("insufficient") || errorMessage.includes("INSUFFICIENT_CREDITS")) {
                setShowCreditModal(true);
            } else if (errorMessage.includes("timeout") || errorMessage.includes("504") || errorMessage.includes("TIMEOUT")) {
                setError("요청 시간이 초과되었습니다. 다시 시도해주세요.");
            } else if (errorMessage.includes("network") || errorMessage.includes("fetch") || errorMessage.includes("Failed to fetch")) {
                setError("네트워크 연결을 확인해주세요.");
            } else if (errorMessage.includes("401") || errorMessage.includes("unauthorized")) {
                setError("로그인이 필요합니다.");
            } else {
                setError(errorMessage);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const sidebarContent = (
        <div className="space-y-6">
            {/* Chain Data Input */}
            <ChainDataInput
                currentDimension={DIMENSION_KEY}
                onApplyData={handleApplyChainData}
                themeColor={THEME_COLOR}
            />

            {/* Concept Input */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-white/80">
                    영상 컨셉
                </label>
                <textarea
                    value={concept}
                    onChange={(e) => setConcept(e.target.value)}
                    placeholder="어떤 영상을 만들고 싶으신가요? 아이디어, 분위기, 메시지 등을 자유롭게 적어주세요..."
                    className="w-full h-32 px-4 py-3 bg-white/5 border border-white/10 rounded-xl
                              text-white placeholder:text-white/30 resize-none
                              focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                    disabled={isLoading}
                />
                <div className="text-xs text-white/40 text-right">{concept.length}/3000</div>
            </div>

            {/* Genre */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-white/80">장르</label>
                <select
                    value={genre}
                    onChange={(e) => setGenre(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl
                              text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                    disabled={isLoading}
                >
                    {GENRES.map((g) => (
                        <option key={g.value} value={g.value} className="bg-black">
                            {g.label}
                        </option>
                    ))}
                </select>
            </div>

            {/* Duration */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-white/80">길이</label>
                <select
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl
                              text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                    disabled={isLoading}
                >
                    {DURATIONS.map((d) => (
                        <option key={d.value} value={d.value} className="bg-black">
                            {d.label}
                        </option>
                    ))}
                </select>
            </div>

            {/* Structure */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-white/80">스토리 구조</label>
                <select
                    value={structure}
                    onChange={(e) => setStructure(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl
                              text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                    disabled={isLoading}
                >
                    {STRUCTURES.map((s) => (
                        <option key={s.value} value={s.value} className="bg-black">
                            {s.label}
                        </option>
                    ))}
                </select>
            </div>

            {/* Generate Button */}
            <button
                onClick={handleGenerate}
                disabled={isLoading || concept.length < 10}
                className={`w-full py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all
                          ${isLoading || concept.length < 10
                              ? "bg-emerald-500/20 text-emerald-400/50 cursor-not-allowed"
                              : "bg-gradient-to-r from-emerald-500 to-teal-500 text-black hover:from-emerald-400 hover:to-teal-400"
                          }`}
            >
                {isLoading ? (
                    <>
                        <div className="w-5 h-5 border-2 border-emerald-400/30 border-t-emerald-400 rounded-full animate-spin" />
                        생성 중...
                    </>
                ) : (
                    <>
                        시나리오 생성하기
                        <ArrowRight className="w-4 h-4" />
                    </>
                )}
            </button>

            {/* Credit Cost */}
            {!byokKey && (
                <div className="text-xs text-white/40 text-center">
                    예상 비용: {CREDIT_COST} 크레딧
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
                creditCost={CREDIT_COST}
                isLoading={isLoading}
            >
                {/* Main Content */}
                <div className="space-y-6">
                    {/* Error Display */}
                    {error && (
                        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                            <div>
                                <p className="text-red-400 font-medium">오류</p>
                                <p className="text-white/60 text-sm">{error}</p>
                            </div>
                        </div>
                    )}

                    {/* Result Display */}
                    {result && (
                        <div className="space-y-6 animate-in fade-in duration-500">
                            {/* Title & Logline */}
                            <div className="p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
                                <div className="flex items-center gap-2 mb-3">
                                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                                    <span className="text-emerald-400 font-bold text-sm">생성 완료</span>
                                </div>
                                <h2 className="text-2xl font-bold text-white mb-2">{result.title}</h2>
                                <p className="text-white/70 italic">&ldquo;{result.logline}&rdquo;</p>
                            </div>

                            {/* Synopsis */}
                            {result.synopsis && (
                                <div className="space-y-2">
                                    <h3 className="text-lg font-bold text-white">개요</h3>
                                    <p className="text-white/70 leading-relaxed">{result.synopsis}</p>
                                </div>
                            )}

                            {/* Structure */}
                            {result.structure && result.structure.length > 0 && (
                                <div className="space-y-3">
                                    <h3 className="text-lg font-bold text-white">구조</h3>
                                    <div className="space-y-2">
                                        {result.structure.map((act, i) => (
                                            <div key={i} className="p-4 rounded-xl bg-white/5 border border-white/10">
                                                <div className="flex items-center justify-between mb-2">
                                                    <span className="text-emerald-400 font-bold">Act {act.act}</span>
                                                    <span className="text-xs text-white/40">{act.duration}</span>
                                                </div>
                                                <p className="text-white/70 text-sm">{act.description}</p>
                                                <span className="inline-block mt-2 px-2 py-1 text-xs rounded-full bg-emerald-500/20 text-emerald-400">
                                                    {act.emotion}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Characters */}
                            {result.characters && result.characters.length > 0 && (
                                <div className="space-y-3">
                                    <h3 className="text-lg font-bold text-white">등장인물</h3>
                                    <div className="grid gap-3">
                                        {result.characters.map((char, i) => (
                                            <div key={i} className="p-4 rounded-xl bg-white/5 border border-white/10">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className="text-white font-bold">{char.name}</span>
                                                    <span className="text-xs px-2 py-0.5 rounded-full bg-white/10 text-white/60">
                                                        {char.role}
                                                    </span>
                                                </div>
                                                <p className="text-white/60 text-sm mb-2">{char.arc}</p>
                                                <div className="flex flex-wrap gap-1">
                                                    {char.traits?.map((trait, j) => (
                                                        <span key={j} className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400">
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
                                {result.themes && result.themes.length > 0 && (
                                    <div className="space-y-2">
                                        <h3 className="text-sm font-bold text-white/80">주제</h3>
                                        <div className="flex flex-wrap gap-1">
                                            {result.themes.map((theme, i) => (
                                                <span key={i} className="text-xs px-2 py-1 rounded-full bg-white/10 text-white/70">
                                                    {theme}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                {result.visual_motifs && result.visual_motifs.length > 0 && (
                                    <div className="space-y-2">
                                        <h3 className="text-sm font-bold text-white/80">시각적 모티프</h3>
                                        <div className="flex flex-wrap gap-1">
                                            {result.visual_motifs.map((motif, i) => (
                                                <span key={i} className="text-xs px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400">
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
                    {!result && !error && (
                        <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center">
                            <Layers className="w-16 h-16 text-emerald-400/30 mb-4" />
                            <h3 className="text-xl font-bold text-white/60 mb-2">시나리오 생성기</h3>
                            <p className="text-white/40 text-sm max-w-md">
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
