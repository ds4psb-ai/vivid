"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import TeachingPanelLayout from "./TeachingPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";

const CREDIT_COST = 5;

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
    { value: "gemini-2.5-flash", label: "Flash (빠름)" },
    { value: "gemini-2.5-pro", label: "Pro (고품질)" },
];

export default function PromptGeneratorPanel() {
    const [topic, setTopic] = useState("");
    const [style, setStyle] = useState("cinematic");
    const [mood, setMood] = useState("neutral");
    const [duration, setDuration] = useState("15 seconds");
    const [language, setLanguage] = useState<"ko" | "en">("ko");
    const [model, setModel] = useState("gemini-2.5-flash");

    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<PromptResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [copiedField, setCopiedField] = useState<string | null>(null);
    const [showCreditModal, setShowCreditModal] = useState(false);

    // BYOK and credits
    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();

    // Map backend errors to user-friendly messages
    const getErrorMessage = (err: unknown): string => {
        if (err instanceof Error) {
            const msg = err.message.toLowerCase();
            if (msg.includes("timeout")) return "요청 시간이 초과되었습니다. 다시 시도해주세요.";
            if (msg.includes("api key")) return "서비스 설정 오류입니다. 관리자에게 문의하세요.";
            if (msg.includes("network") || msg.includes("fetch")) return "네트워크 오류입니다. 인터넷 연결을 확인해주세요.";
            if (msg.includes("insufficient") || msg.includes("402")) return "크레딧이 부족합니다.";
            return err.message;
        }
        return "알 수 없는 오류가 발생했습니다.";
    };

    const handleGenerate = async () => {
        if (!topic.trim()) {
            setError("주제를 입력해주세요");
            return;
        }

        // Credit check (only when not using BYOK)
        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
            setShowCreditModal(true);
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await api.post<{
                success: boolean;
                output: PromptResult;
                error?: string;
            }>("/api/teaching/prompt/generate", {
                topic,
                style,
                mood,
                duration,
                language,
                model,
            }, getBYOKHeaders(byokKey));

            if (response.success) {
                setResult(response.output);
                // Refresh credit balance after successful generation
                if (!byokKey && creditCtx) {
                    void creditCtx.refresh();
                }
            } else {
                setError(response.error || "생성 실패");
            }
        } catch (err) {
            const errorMsg = getErrorMessage(err);
            if (errorMsg.includes("크레딧")) {
                setShowCreditModal(true);
            } else {
                setError(errorMsg);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleCopy = async (text: string, field: string) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopiedField(field);
            setTimeout(() => setCopiedField(null), 2000);
        } catch {
            setError("클립보드 복사에 실패했습니다.");
        }
    };

    const SidebarContent = (
        <>
            {/* Topic Input */}
            <div className="space-y-2">
                <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">주제</label>
                <textarea
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="영상의 주제를 입력하세요..."
                    className="w-full h-24 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/20 focus:outline-none focus:border-amber-400/50 focus:ring-1 focus:ring-amber-400/20 transition-all resize-none text-sm"
                />
            </div>

            {/* Style & Mood */}
            <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                    <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">스타일</label>
                    <div className="relative">
                        <select
                            value={style}
                            onChange={(e) => setStyle(e.target.value)}
                            className="w-full px-2 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-amber-400/50 focus:ring-1 focus:ring-amber-400/20 transition-all appearance-none"
                        >
                            {STYLES.map((s) => (
                                <option key={s.value} value={s.value}>{s.label}</option>
                            ))}
                        </select>
                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-white/50">
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
                            className="w-full px-2 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-amber-400/50 focus:ring-1 focus:ring-amber-400/20 transition-all appearance-none"
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
                            className="w-full px-2 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-amber-400/50 focus:ring-1 focus:ring-amber-400/20 transition-all appearance-none"
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
                                ? "bg-amber-400 text-black shadow-sm"
                                : "text-zinc-400 hover:text-white hover:bg-white/5"
                                }`}
                        >
                            KO
                        </button>
                        <button
                            onClick={() => setLanguage("en")}
                            className={`flex-1 py-1 rounded-md text-xs font-medium transition-all ${language === "en"
                                ? "bg-amber-400 text-black shadow-sm"
                                : "text-zinc-400 hover:text-white hover:bg-white/5"
                                }`}
                        >
                            EN
                        </button>
                    </div>
                </div>
            </div>

            {/* Model Select */}
            <div className="space-y-2 pt-2 border-t border-white/5">
                <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">AI 모델</label>
                <div className="relative">
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="w-full px-2 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-amber-400/50 focus:ring-1 focus:ring-amber-400/20 transition-all appearance-none"
                    >
                        {MODELS.map((m) => (
                            <option key={m.value} value={m.value}>{m.label}</option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-white/50">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            {/* Generate Button */}
            <button
                onClick={handleGenerate}
                disabled={isLoading || !topic.trim()}
                className="w-full py-3 mt-4 bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-300 hover:to-amber-400 disabled:from-zinc-800 disabled:to-zinc-800 disabled:text-zinc-600 text-[#121212] font-bold rounded-lg shadow-lg shadow-amber-500/10 transition-all hover:shadow-amber-500/20 active:scale-[0.98] flex items-center justify-center gap-2"
            >
                {isLoading ? (
                    <span className="flex items-center gap-2">Generating...</span>
                ) : (
                    "프롬프트 생성"
                )}
            </button>

            {error && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs break-keep leading-relaxed animate-in fade-in slide-in-from-top-1">
                    {error}
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
            >
                {result ? (
                    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
                        {/* Main Prompt */}
                        <div className="group relative">
                            <div className="flex items-center justify-between mb-3 px-1">
                                <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                                    Generated Prompt
                                </h3>
                                <button
                                    onClick={() => handleCopy(result.prompt, "prompt")}
                                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 ${copiedField === "prompt"
                                        ? "bg-green-500/10 text-green-400 border border-green-500/20"
                                        : "bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 border border-white/5 hover:border-white/10"
                                        }`}
                                >
                                    {copiedField === "prompt" ? (
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
                            <div className="p-6 bg-[#18181b] border border-white/10 rounded-xl shadow-inner font-mono text-sm leading-relaxed text-zinc-100 whitespace-pre-wrap group-hover:border-white/20 transition-colors relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-amber-400/50 to-transparent opacity-50"></div>
                                {result.prompt}
                            </div>
                        </div>

                        {/* Negative Prompt */}
                        {result.negative_prompt && (
                            <div className="group relative">
                                <div className="flex items-center justify-between mb-3 px-1">
                                    <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                                        <span className="w-1.5 h-1.5 rounded-full bg-red-400/50"></span>
                                        Negative Prompt
                                    </h3>
                                    <button
                                        onClick={() => handleCopy(result.negative_prompt || "", "negative")}
                                        className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 ${copiedField === "negative"
                                            ? "bg-green-500/10 text-green-400 border border-green-500/20"
                                            : "bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 border border-white/5 hover:border-white/10"
                                            }`}
                                    >
                                        {copiedField === "negative" ? "Copied" : "Copy"}
                                    </button>
                                </div>
                                <div className="p-5 bg-[#18181b]/50 border border-white/10 rounded-xl shadow-inner font-mono text-sm leading-relaxed text-zinc-400 whitespace-pre-wrap group-hover:border-white/20 transition-colors">
                                    {result.negative_prompt}
                                </div>
                            </div>
                        )}

                        {/* Technical Details Grid */}
                        {(result.style || result.technical) && (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {result.style && (
                                    <div className="p-6 bg-white/[0.02] border border-white/5 rounded-xl space-y-4 hover:border-white/10 transition-colors">
                                        <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest border-b border-white/5 pb-3 mb-1">Style Parameters</h3>
                                        <div className="space-y-4">
                                            {Object.entries(result.style).map(([key, value]) => (
                                                <div key={key} className="flex flex-col gap-1">
                                                    <span className="text-xs text-zinc-500 capitalize">{key.replace(/_/g, " ")}</span>
                                                    <span className="text-sm text-zinc-200 font-medium">{value}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                {result.technical && (
                                    <div className="p-6 bg-white/[0.02] border border-white/5 rounded-xl space-y-4 hover:border-white/10 transition-colors">
                                        <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest border-b border-white/5 pb-3 mb-1">Technical Specs</h3>
                                        <div className="grid grid-cols-2 gap-6">
                                            {Object.entries(result.technical).map(([key, value]) => (
                                                <div key={key} className="flex flex-col gap-1">
                                                    <span className="text-xs text-zinc-500 capitalize">{key.replace(/_/g, " ")}</span>
                                                    <span className="text-sm font-mono text-amber-400/90">{value}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-6">
                        <div className="w-24 h-24 rounded-3xl bg-white/[0.03] border border-white/5 flex items-center justify-center shadow-2xl">
                            <svg className="w-10 h-10 opacity-20 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                            </svg>
                        </div>
                        <div className="text-center space-y-2">
                            <h3 className="text-lg font-medium text-white/40">Ready to Generate</h3>
                            <p className="text-sm text-zinc-600 max-w-xs mx-auto">
                                영상 주제와 스타일을 설정하고<br />최적화된 Veo 프롬프트를 생성해보세요.
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
            />
        </>
    );
}
