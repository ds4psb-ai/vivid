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
import { Palette, Copy, Check, Download } from "lucide-react";

const CREDIT_COST = 10;
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
}

const AUTEUR_STYLES = [
    { value: "", label: "자동 추천" },
    { value: "bong", label: "봉준호 (Bong Joon-ho)", desc: "사회 비평, 장르 혼합" },
    { value: "park", label: "박찬욱 (Park Chan-wook)", desc: "미학적 폭력, 복수극" },
    { value: "shinkai", label: "신카이 마코토 (Shinkai)", desc: "아련한 풍경, 청춘" },
    { value: "lee", label: "이창동 (Lee Chang-dong)", desc: "리얼리즘, 인간 탐구" },
    { value: "na", label: "나홍진 (Na Hong-jin)", desc: "긴장감, 추격 서사" },
    { value: "hong", label: "홍상수 (Hong Sang-soo)", desc: "일상, 대화 중심" },
];

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

const MODELS = [
    { value: "gemini-3.0-flash-preview", label: "Flash (빠름)" },
    { value: "gemini-3.0-pro-preview", label: "Pro (상세)" },
];

export default function AestheticDirectorPanel() {
    const [concept, setConcept] = useState("");
    const [referenceStyle, setReferenceStyle] = useState("");
    const [mood, setMood] = useState("neutral");
    const [targetMedium, setTargetMedium] = useState("video");
    const [model, setModel] = useState("gemini-3.0-pro-preview");
    const [useRag, setUseRag] = useState(true);

    const [copiedField, setCopiedField] = useState<string | null>(null);
    const [showCreditModal, setShowCreditModal] = useState(false);
    const [validationError, setValidationError] = useState<string | null>(null);

    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();

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

    const handleGenerate = useCallback(async () => {
        const trimmedConcept = concept.trim();
        if (!trimmedConcept) {
            setValidationError("컨셉을 입력해주세요");
            return;
        }
        if (trimmedConcept.length > MAX_CONCEPT_LENGTH) {
            setValidationError(`컨셉은 ${MAX_CONCEPT_LENGTH}자 이하로 입력해주세요`);
            return;
        }
        setValidationError(null);

        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
            setShowCreditModal(true);
            return;
        }

        await execute(
            `${API_BASE}/api/dimension/aesthetic/direct`,
            {
                concept,
                reference_style: referenceStyle || undefined,
                mood,
                target_medium: targetMedium,
                model,
                use_rag: useRag,
            },
            getBYOKHeaders(byokKey)
        );
    }, [concept, referenceStyle, mood, targetMedium, model, useRag, byokKey, creditCtx, execute]);

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
            {/* Concept Input */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1">컨셉 / 주제</label>
                <textarea
                    value={concept}
                    onChange={(e) => setConcept(e.target.value)}
                    placeholder="시각적 스타일을 정의할 컨셉을 입력하세요..."
                    className="w-full h-32 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/20 focus:outline-none focus:border-fuchsia-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-fuchsia-400/5 transition-all resize-none text-sm font-light leading-relaxed"
                />
            </div>

            {/* Auteur Style */}
            <div className="space-y-2">
                <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1">감독 스타일</label>
                <div className="space-y-2 max-h-48 overflow-y-auto custom-scrollbar">
                    {AUTEUR_STYLES.map((style) => (
                        <button
                            key={style.value}
                            onClick={() => setReferenceStyle(style.value)}
                            className={`w-full flex flex-col px-4 py-3 rounded-xl text-left transition-all ${
                                referenceStyle === style.value
                                    ? "bg-fuchsia-500/10 border border-fuchsia-500/30"
                                    : "bg-white/5 border border-white/10 hover:border-white/20"
                            }`}
                        >
                            <span className={`text-sm font-medium ${referenceStyle === style.value ? "text-fuchsia-400" : "text-zinc-300"}`}>
                                {style.label}
                            </span>
                            {style.desc && (
                                <span className="text-[10px] text-zinc-500">{style.desc}</span>
                            )}
                        </button>
                    ))}
                </div>
            </div>

            {/* Mood & Medium */}
            <div className="grid grid-cols-2 gap-3">
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
            </div>

            {/* RAG Toggle */}
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

            {/* Model Select */}
            <div className="space-y-2 pt-4 border-t border-white/5">
                <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1">AI 모델</label>
                <div className="relative">
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-fuchsia-400/50 transition-all appearance-none cursor-pointer font-mono"
                    >
                        {MODELS.map((m) => (
                            <option key={m.value} value={m.value} className="bg-[#0F0F1A]">{m.label}</option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-white/30">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            {/* Generate Button */}
            <button
                onClick={handleGenerate}
                disabled={isLoading || !concept.trim()}
                className="w-full py-4 mt-6 bg-gradient-to-r from-fuchsia-600 to-purple-600 hover:from-fuchsia-500 hover:to-purple-500 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-600 text-white font-bold text-base rounded-xl shadow-[0_0_30px_rgba(217,70,239,0.3)] hover:shadow-[0_0_50px_rgba(217,70,239,0.5)] transition-all active:scale-[0.98]"
            >
                {isLoading ? (
                    <span className="flex items-center justify-center gap-2">
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        생성 중...
                    </span>
                ) : (
                    <span className="tracking-widest uppercase">스타일 가이드 생성</span>
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
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-8">
                        <div className="relative group">
                            <div className="absolute inset-0 bg-fuchsia-500/20 blur-[80px] rounded-full" />
                            <div className="w-32 h-32 rounded-[2rem] bg-white/[0.02] border border-white/10 flex items-center justify-center backdrop-blur-md relative">
                                <Palette className="w-12 h-12 text-white/20 group-hover:text-fuchsia-400 transition-colors" />
                            </div>
                        </div>
                        <div className="text-center space-y-3">
                            <h3 className="text-2xl font-bold text-white tracking-tight">스타일 가이드 생성</h3>
                            <p className="text-sm text-[var(--fg-muted)] max-w-xs mx-auto font-light leading-relaxed">
                                컨셉을 입력하고<br />
                                <span className="text-fuchsia-400 font-medium">6명의 감독 스타일</span>을 참고한 미학 가이드를 생성하세요.
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
                onRetry={handleGenerate}
            />
        </>
    );
}
