"use client";

import { useState } from "react";
import TeachingPanelLayout, { type ThemeColor } from "./DimensionPanelLayout";
import { useBYOK } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import { api } from "@/lib/api";
import { Music, ArrowRight, CheckCircle, AlertCircle, Copy, Check } from "lucide-react";

const CREDIT_COST = 8;
const THEME_COLOR: ThemeColor = "rose";

interface SoundResult {
    music_prompt?: string;
    style_tags?: string[];
    bpm_range?: string;
    key_signature?: string;
    instrumentation?: string[];
    dynamics?: string;
    narration_script?: string | null;
    voice_direction?: {
        tone: string;
        pace: string;
        emotion: string;
    } | null;
    sfx_cues?: Array<{
        time: string;
        sound: string;
        description: string;
    }>;
    next_dimension?: string;
}

const SOUND_TYPES = [
    { value: "bgm", label: "BGM" },
    { value: "sfx", label: "효과음" },
    { value: "narration", label: "내레이션" },
    { value: "full", label: "풀 사운드" },
];

const GENRES = [
    { value: "cinematic", label: "시네마틱" },
    { value: "electronic", label: "일렉트로닉" },
    { value: "acoustic", label: "어쿠스틱" },
    { value: "ambient", label: "앰비언트" },
    { value: "pop", label: "팝" },
    { value: "classical", label: "클래식" },
];

const TEMPOS = [
    { value: "slow", label: "느림" },
    { value: "medium", label: "보통" },
    { value: "fast", label: "빠름" },
    { value: "dynamic", label: "다이나믹" },
];

const PLATFORMS = [
    { value: "suno", label: "Suno AI" },
    { value: "udio", label: "Udio" },
    { value: "elevenlabs", label: "ElevenLabs" },
];

export default function SoundCrafterPanel() {
    const [concept, setConcept] = useState("");
    const [soundType, setSoundType] = useState("bgm");
    const [genre, setGenre] = useState("cinematic");
    const [tempo, setTempo] = useState("medium");
    const [platform, setPlatform] = useState("suno");

    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<SoundResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showCreditModal, setShowCreditModal] = useState(false);
    const [copiedField, setCopiedField] = useState<string | null>(null);

    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();

    const handleCopy = async (text: string, field: string) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopiedField(field);
            setTimeout(() => setCopiedField(null), 2000);
        } catch (err) {
            console.error("Copy failed:", err);
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
            const response = await api.executeSoundCraft({
                concept,
                sound_type: soundType,
                genre,
                tempo,
                target_platform: platform,
                language: "ko",
                model: "gemini-3-flash-preview",
            });

            if (response.success && response.output) {
                setResult(response.output as SoundResult);
                // Refresh credits
                if (creditCtx) {
                    creditCtx.refresh();
                }
            } else {
                setError(response.error || "사운드 프롬프트 생성에 실패했습니다.");
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
            {/* Concept Input */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-white/80">
                    사운드 컨셉
                </label>
                <textarea
                    value={concept}
                    onChange={(e) => setConcept(e.target.value)}
                    placeholder="어떤 분위기의 사운드가 필요한가요? 감정, 템포, 악기 등을 자유롭게 적어주세요..."
                    className="w-full h-32 px-4 py-3 bg-white/5 border border-white/10 rounded-xl
                              text-white placeholder:text-white/30 resize-none
                              focus:outline-none focus:ring-2 focus:ring-rose-500/50"
                    disabled={isLoading}
                />
                <div className="text-xs text-white/40 text-right">{concept.length}/2000</div>
            </div>

            {/* Sound Type */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-white/80">사운드 유형</label>
                <select
                    value={soundType}
                    onChange={(e) => setSoundType(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl
                              text-white focus:outline-none focus:ring-2 focus:ring-rose-500/50"
                    disabled={isLoading}
                >
                    {SOUND_TYPES.map((t) => (
                        <option key={t.value} value={t.value} className="bg-black">
                            {t.label}
                        </option>
                    ))}
                </select>
            </div>

            {/* Genre & Tempo */}
            <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                    <label className="text-sm font-medium text-white/80">장르</label>
                    <select
                        value={genre}
                        onChange={(e) => setGenre(e.target.value)}
                        className="w-full px-3 py-2.5 bg-white/5 border border-white/10 rounded-xl
                                  text-white text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/50"
                        disabled={isLoading}
                    >
                        {GENRES.map((g) => (
                            <option key={g.value} value={g.value} className="bg-black">
                                {g.label}
                            </option>
                        ))}
                    </select>
                </div>
                <div className="space-y-2">
                    <label className="text-sm font-medium text-white/80">템포</label>
                    <select
                        value={tempo}
                        onChange={(e) => setTempo(e.target.value)}
                        className="w-full px-3 py-2.5 bg-white/5 border border-white/10 rounded-xl
                                  text-white text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/50"
                        disabled={isLoading}
                    >
                        {TEMPOS.map((t) => (
                            <option key={t.value} value={t.value} className="bg-black">
                                {t.label}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Target Platform */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-white/80">타겟 플랫폼</label>
                <div className="flex gap-2">
                    {PLATFORMS.map((p) => (
                        <button
                            key={p.value}
                            onClick={() => setPlatform(p.value)}
                            disabled={isLoading}
                            className={`flex-1 py-3 rounded-xl text-sm font-medium transition-all
                                      ${platform === p.value
                                          ? "bg-rose-500 text-black"
                                          : "bg-white/5 text-white/60 hover:bg-white/10"
                                      } ${isLoading ? "opacity-50 cursor-not-allowed" : ""}`}
                        >
                            {p.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Generate Button */}
            <button
                onClick={handleGenerate}
                disabled={isLoading || concept.length < 10}
                className={`w-full py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all
                          ${isLoading || concept.length < 10
                              ? "bg-rose-500/20 text-rose-400/50 cursor-not-allowed"
                              : "bg-gradient-to-r from-rose-500 to-pink-500 text-black hover:from-rose-400 hover:to-pink-400"
                          }`}
            >
                {isLoading ? (
                    <>
                        <div className="w-5 h-5 border-2 border-rose-400/30 border-t-rose-400 rounded-full animate-spin" />
                        생성 중...
                    </>
                ) : (
                    <>
                        사운드 프롬프트 생성
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
                title="사운드 크래프터"
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
                            {/* Music Prompt */}
                            {result.music_prompt && (
                                <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/20">
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-2">
                                            <CheckCircle className="w-5 h-5 text-rose-400" />
                                            <span className="text-rose-400 font-bold text-sm">
                                                {PLATFORMS.find(p => p.value === platform)?.label} 프롬프트
                                            </span>
                                        </div>
                                        <button
                                            onClick={() => handleCopy(result.music_prompt || "", "prompt")}
                                            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
                                            title="복사"
                                        >
                                            {copiedField === "prompt" ? (
                                                <Check className="w-4 h-4 text-rose-400" />
                                            ) : (
                                                <Copy className="w-4 h-4 text-white/60" />
                                            )}
                                        </button>
                                    </div>
                                    <p className="text-white font-mono text-sm leading-relaxed bg-black/30 p-4 rounded-xl">
                                        {result.music_prompt}
                                    </p>
                                </div>
                            )}

                            {/* Style Tags */}
                            {result.style_tags && result.style_tags.length > 0 && (
                                <div className="space-y-2">
                                    <h3 className="text-sm font-bold text-white/80">스타일 태그</h3>
                                    <div className="flex flex-wrap gap-2">
                                        {result.style_tags.map((tag, i) => (
                                            <span key={i} className="px-3 py-1 text-sm rounded-full bg-rose-500/20 text-rose-400">
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Technical Details */}
                            <div className="grid grid-cols-2 gap-4">
                                {result.bpm_range && (
                                    <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                        <span className="text-xs text-white/40 block mb-1">BPM</span>
                                        <span className="text-white font-medium">{result.bpm_range}</span>
                                    </div>
                                )}
                                {result.key_signature && (
                                    <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                        <span className="text-xs text-white/40 block mb-1">조성</span>
                                        <span className="text-white font-medium">{result.key_signature}</span>
                                    </div>
                                )}
                            </div>

                            {/* Instrumentation */}
                            {result.instrumentation && result.instrumentation.length > 0 && (
                                <div className="space-y-2">
                                    <h3 className="text-sm font-bold text-white/80">악기 구성</h3>
                                    <div className="flex flex-wrap gap-2">
                                        {result.instrumentation.map((inst, i) => (
                                            <span key={i} className="px-3 py-1 text-sm rounded-full bg-white/10 text-white/70">
                                                {inst}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Dynamics */}
                            {result.dynamics && (
                                <div className="space-y-2">
                                    <h3 className="text-sm font-bold text-white/80">다이나믹</h3>
                                    <p className="text-white/60 text-sm">{result.dynamics}</p>
                                </div>
                            )}

                            {/* Narration Script (if applicable) */}
                            {result.narration_script && (
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <h3 className="text-sm font-bold text-white/80">내레이션 스크립트</h3>
                                        <button
                                            onClick={() => handleCopy(result.narration_script || "", "narration")}
                                            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
                                        >
                                            {copiedField === "narration" ? (
                                                <Check className="w-4 h-4 text-rose-400" />
                                            ) : (
                                                <Copy className="w-4 h-4 text-white/60" />
                                            )}
                                        </button>
                                    </div>
                                    <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                        <p className="text-white/70 text-sm leading-relaxed whitespace-pre-wrap">
                                            {result.narration_script}
                                        </p>
                                    </div>
                                </div>
                            )}

                            {/* Voice Direction (if applicable) */}
                            {result.voice_direction && (
                                <div className="grid grid-cols-3 gap-3">
                                    <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                                        <span className="text-xs text-white/40 block mb-1">톤</span>
                                        <span className="text-white text-sm">{result.voice_direction.tone}</span>
                                    </div>
                                    <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                                        <span className="text-xs text-white/40 block mb-1">속도</span>
                                        <span className="text-white text-sm">{result.voice_direction.pace}</span>
                                    </div>
                                    <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                                        <span className="text-xs text-white/40 block mb-1">감정</span>
                                        <span className="text-white text-sm">{result.voice_direction.emotion}</span>
                                    </div>
                                </div>
                            )}

                            {/* SFX Cues */}
                            {result.sfx_cues && result.sfx_cues.length > 0 && (
                                <div className="space-y-2">
                                    <h3 className="text-sm font-bold text-white/80">효과음 큐</h3>
                                    <div className="space-y-2">
                                        {result.sfx_cues.map((cue, i) => (
                                            <div key={i} className="p-3 rounded-xl bg-white/5 border border-white/10 flex items-center gap-4">
                                                <span className="text-rose-400 font-mono text-sm">{cue.time}</span>
                                                <span className="text-white font-medium">{cue.sound}</span>
                                                <span className="text-white/50 text-sm">{cue.description}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Next Dimension */}
                            {result.next_dimension && (
                                <div className="p-4 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between">
                                    <span className="text-white/60 text-sm">다음 추천 단계</span>
                                    <span className="text-rose-400 font-medium">{result.next_dimension}</span>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Empty State */}
                    {!result && !error && (
                        <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center">
                            <Music className="w-16 h-16 text-rose-400/30 mb-4" />
                            <h3 className="text-xl font-bold text-white/60 mb-2">사운드 크래프터</h3>
                            <p className="text-white/40 text-sm max-w-md">
                                사운드 컨셉을 입력하면 Suno, Udio, ElevenLabs와 호환되는
                                음악 프롬프트와 내레이션 스크립트를 자동 생성합니다.
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
