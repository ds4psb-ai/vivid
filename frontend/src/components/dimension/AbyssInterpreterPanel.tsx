"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import TeachingPanelLayout, { type ThemeColor } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import { Send, User, Bot, Sparkles } from "lucide-react";

const CREDIT_COST = 5;
const THEME_COLOR: ThemeColor = "indigo";

interface Message {
    role: "user" | "assistant";
    content: string;
}

interface PersonaData {
    saju?: Record<string, unknown>;
    mbti?: Record<string, unknown>;
    subconscious?: Record<string, unknown>;
    unconscious?: Record<string, unknown>;
    background?: Record<string, unknown>;
}

interface AnalysisResult {
    assistant_message: string;
    next_stage: string;
    persona_update?: PersonaData;
    analysis_complete: boolean;
    final_persona?: {
        summary: string;
        traits: string[];
        strengths: string[];
        growth_areas: string[];
        recommendations: string[];
    };
}

const STAGE_NAMES: Record<string, string> = {
    intro: "시작",
    saju: "사주 분석",
    mbti: "MBTI 탐색",
    subconscious: "잠재의식",
    unconscious: "무의식",
    background: "성장 배경",
    synthesis: "종합 분석",
};

const DEPTH_LEVELS = [
    { value: "quick", label: "간단 (3단계)", desc: "빠른 핵심 분석" },
    { value: "standard", label: "표준 (5단계)", desc: "균형 잡힌 분석" },
    { value: "deep", label: "심층 (7단계)", desc: "상세한 탐구" },
];

const MODELS = [
    { value: "gemini-3-flash-preview", label: "Flash (빠름)" },
    { value: "gemini-3.0-pro-preview", label: "Pro (깊이)" },
];

export default function AbyssInterpreterPanel() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputMessage, setInputMessage] = useState("");
    const [currentStage, setCurrentStage] = useState("intro");
    const [personaData, setPersonaData] = useState<PersonaData>({});
    const [depthLevel, setDepthLevel] = useState("standard");
    const [model, setModel] = useState("gemini-3.0-pro-preview");
    const [birthInfo, setBirthInfo] = useState({ year: "", month: "", day: "", hour: "" });

    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showCreditModal, setShowCreditModal] = useState(false);
    const [isComplete, setIsComplete] = useState(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // Start analysis on mount
    useEffect(() => {
        if (messages.length === 0) {
            startAnalysis();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const startAnalysis = async () => {
        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
            setShowCreditModal(true);
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await api.post<{
                success: boolean;
                output: AnalysisResult;
                error?: string;
            }>("/api/dimension/persona/analyze", {
                user_message: "분석을 시작합니다",
                analysis_stage: "intro",
                depth_level: depthLevel,
                model,
            }, getBYOKHeaders(byokKey));

            if (response.success) {
                setMessages([{ role: "assistant", content: response.output.assistant_message }]);
                setCurrentStage(response.output.next_stage);
                if (!byokKey && creditCtx) {
                    void creditCtx.refresh();
                }
            } else {
                setError(response.error || "시작 실패");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "알 수 없는 오류");
        } finally {
            setIsLoading(false);
        }
    };

    const sendMessage = async () => {
        if (!inputMessage.trim() || isLoading || isComplete) return;

        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
            setShowCreditModal(true);
            return;
        }

        const userMessage = inputMessage.trim();
        setInputMessage("");
        setMessages(prev => [...prev, { role: "user", content: userMessage }]);
        setIsLoading(true);
        setError(null);

        try {
            const response = await api.post<{
                success: boolean;
                output: AnalysisResult;
                error?: string;
            }>("/api/dimension/persona/analyze", {
                user_message: userMessage,
                analysis_stage: currentStage,
                persona_data: personaData,
                birth_info: currentStage === "saju" ? birthInfo : undefined,
                depth_level: depthLevel,
                model,
            }, getBYOKHeaders(byokKey));

            if (response.success) {
                setMessages(prev => [...prev, { role: "assistant", content: response.output.assistant_message }]);
                setCurrentStage(response.output.next_stage);
                if (response.output.persona_update) {
                    setPersonaData(prev => ({ ...prev, ...response.output.persona_update }));
                }
                if (response.output.analysis_complete) {
                    setIsComplete(true);
                    setResult(response.output);
                }
                if (!byokKey && creditCtx) {
                    void creditCtx.refresh();
                }
            } else {
                setError(response.error || "분석 실패");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "알 수 없는 오류");
        } finally {
            setIsLoading(false);
        }
    };

    const resetAnalysis = () => {
        setMessages([]);
        setCurrentStage("intro");
        setPersonaData({});
        setResult(null);
        setIsComplete(false);
        setTimeout(() => startAnalysis(), 100);
    };

    const SidebarContent = (
        <>
            {/* Stage Progress */}
            <div className="space-y-2">
                <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1">분석 단계</label>
                <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                    <div className="flex items-center gap-2 mb-3">
                        <div className={`w-2 h-2 rounded-full ${isComplete ? "bg-emerald-400" : "bg-indigo-400 animate-pulse"}`} />
                        <span className="text-sm font-medium text-white">
                            {STAGE_NAMES[currentStage] || currentStage}
                        </span>
                    </div>
                    <div className="flex gap-1">
                        {Object.keys(STAGE_NAMES).map((stage, i) => (
                            <div
                                key={stage}
                                className={`flex-1 h-1 rounded-full transition-all ${
                                    Object.keys(STAGE_NAMES).indexOf(currentStage) >= i
                                        ? "bg-indigo-500"
                                        : "bg-white/10"
                                }`}
                            />
                        ))}
                    </div>
                </div>
            </div>

            {/* Birth Info (for Saju stage) */}
            {currentStage === "saju" && (
                <div className="space-y-2">
                    <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1">생년월일시 (선택)</label>
                    <div className="grid grid-cols-4 gap-2">
                        <input
                            type="text"
                            placeholder="년"
                            value={birthInfo.year}
                            onChange={(e) => setBirthInfo(prev => ({ ...prev, year: e.target.value }))}
                            className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm text-center focus:outline-none focus:border-indigo-400/50"
                        />
                        <input
                            type="text"
                            placeholder="월"
                            value={birthInfo.month}
                            onChange={(e) => setBirthInfo(prev => ({ ...prev, month: e.target.value }))}
                            className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm text-center focus:outline-none focus:border-indigo-400/50"
                        />
                        <input
                            type="text"
                            placeholder="일"
                            value={birthInfo.day}
                            onChange={(e) => setBirthInfo(prev => ({ ...prev, day: e.target.value }))}
                            className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm text-center focus:outline-none focus:border-indigo-400/50"
                        />
                        <input
                            type="text"
                            placeholder="시"
                            value={birthInfo.hour}
                            onChange={(e) => setBirthInfo(prev => ({ ...prev, hour: e.target.value }))}
                            className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm text-center focus:outline-none focus:border-indigo-400/50"
                        />
                    </div>
                </div>
            )}

            {/* Depth Level */}
            <div className="space-y-2">
                <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1">분석 깊이</label>
                <div className="space-y-2">
                    {DEPTH_LEVELS.map((level) => (
                        <button
                            key={level.value}
                            onClick={() => setDepthLevel(level.value)}
                            disabled={messages.length > 0}
                            className={`w-full flex flex-col px-4 py-3 rounded-xl text-left transition-all ${
                                depthLevel === level.value
                                    ? "bg-indigo-500/10 border border-indigo-500/30"
                                    : "bg-white/5 border border-white/10 hover:border-white/20"
                            } ${messages.length > 0 ? "opacity-50 cursor-not-allowed" : ""}`}
                        >
                            <span className={`text-sm font-medium ${depthLevel === level.value ? "text-indigo-400" : "text-zinc-300"}`}>
                                {level.label}
                            </span>
                            <span className="text-[10px] text-zinc-500">{level.desc}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Model Select */}
            <div className="space-y-2 pt-4 border-t border-white/5">
                <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1">AI 모델</label>
                <div className="relative">
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        disabled={messages.length > 0}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-400/50 transition-all appearance-none cursor-pointer font-mono disabled:opacity-50"
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

            {/* Reset Button */}
            {messages.length > 0 && (
                <button
                    onClick={resetAnalysis}
                    className="w-full py-3 mt-4 border border-white/10 text-zinc-400 hover:text-white hover:border-white/30 rounded-xl transition-all text-sm"
                >
                    처음부터 다시 시작
                </button>
            )}

            {error && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs">
                    {error}
                </div>
            )}
        </>
    );

    return (
        <>
            <TeachingPanelLayout
                title="심연해석기"
                sidebarContent={SidebarContent}
                isLoading={isLoading}
                themeColor={THEME_COLOR}
            >
                <div className="flex flex-col h-full">
                    {/* Messages Area */}
                    <div className="flex-1 overflow-y-auto space-y-4 pb-4">
                        {messages.map((msg, i) => (
                            <div
                                key={i}
                                className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                            >
                                {msg.role === "assistant" && (
                                    <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center flex-shrink-0">
                                        <Bot className="w-4 h-4 text-indigo-400" />
                                    </div>
                                )}
                                <div
                                    className={`max-w-[80%] p-4 rounded-2xl ${
                                        msg.role === "user"
                                            ? "bg-indigo-500/20 border border-indigo-500/30"
                                            : "bg-white/5 border border-white/10"
                                    }`}
                                >
                                    <p className="text-sm text-zinc-200 leading-relaxed whitespace-pre-wrap">
                                        {msg.content}
                                    </p>
                                </div>
                                {msg.role === "user" && (
                                    <div className="w-8 h-8 rounded-full bg-white/10 border border-white/20 flex items-center justify-center flex-shrink-0">
                                        <User className="w-4 h-4 text-zinc-400" />
                                    </div>
                                )}
                            </div>
                        ))}

                        {/* Final Persona Result */}
                        {isComplete && result?.final_persona && (
                            <div className="mt-8 p-6 bg-gradient-to-br from-indigo-500/10 to-violet-500/10 border border-indigo-500/30 rounded-3xl animate-in fade-in slide-in-from-bottom-4">
                                <div className="flex items-center gap-3 mb-4">
                                    <Sparkles className="w-6 h-6 text-indigo-400" />
                                    <h3 className="text-lg font-bold text-white">페르소나 분석 완료</h3>
                                </div>
                                <p className="text-sm text-zinc-300 mb-6">{result.final_persona.summary}</p>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="p-4 bg-white/5 rounded-xl">
                                        <h4 className="text-xs font-bold text-indigo-400 uppercase mb-2">핵심 특성</h4>
                                        <div className="flex flex-wrap gap-2">
                                            {result.final_persona.traits.map((trait, i) => (
                                                <span key={i} className="px-3 py-1 bg-indigo-500/20 rounded-full text-xs text-indigo-300">{trait}</span>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="p-4 bg-white/5 rounded-xl">
                                        <h4 className="text-xs font-bold text-emerald-400 uppercase mb-2">강점</h4>
                                        <ul className="space-y-1">
                                            {result.final_persona.strengths.map((s, i) => (
                                                <li key={i} className="text-xs text-zinc-300 flex items-start gap-2">
                                                    <span className="text-emerald-400">+</span>{s}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        )}

                        {isLoading && (
                            <div className="flex gap-3">
                                <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center">
                                    <Bot className="w-4 h-4 text-indigo-400" />
                                </div>
                                <div className="px-4 py-3 bg-white/5 border border-white/10 rounded-2xl">
                                    <div className="flex gap-1">
                                        <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                                        <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                                        <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                                    </div>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    {!isComplete && (
                        <div className="flex-shrink-0 p-4 border-t border-white/10 bg-black/20 backdrop-blur-sm rounded-b-2xl">
                            <div className="flex gap-3">
                                <input
                                    type="text"
                                    value={inputMessage}
                                    onChange={(e) => setInputMessage(e.target.value)}
                                    onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
                                    placeholder="답변을 입력하세요..."
                                    disabled={isLoading}
                                    className="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-indigo-400/50 transition-all disabled:opacity-50"
                                />
                                <button
                                    onClick={sendMessage}
                                    disabled={isLoading || !inputMessage.trim()}
                                    className="px-6 py-3 bg-indigo-500 hover:bg-indigo-400 disabled:bg-white/10 disabled:text-white/30 text-white rounded-xl transition-all"
                                >
                                    <Send className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </TeachingPanelLayout>

            <InsufficientCreditsModal
                isOpen={showCreditModal}
                onClose={() => setShowCreditModal(false)}
                requiredCredits={CREDIT_COST}
                currentBalance={creditCtx?.balance ?? 0}
                onRetry={messages.length === 0 ? startAnalysis : sendMessage}
            />
        </>
    );
}
