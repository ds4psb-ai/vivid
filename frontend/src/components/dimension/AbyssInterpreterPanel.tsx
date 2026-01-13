"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import TeachingPanelLayout, {
    type ThemeColor,
    useAsyncOperation,
    useResultExport,
} from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import PersonaGenome from "./PersonaGenome";
import { RAGSuggestionCard } from "@/components/rag/RAGSuggestionCard";
import { useRAGSuggestion } from "@/hooks/useRAGSuggestion";
import { Send, User, Bot, Sparkles, Download } from "lucide-react";

// const CREDIT_COST = 5; // REMOVED
const THEME_COLOR: ThemeColor = "indigo";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

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
    [key: string]: unknown;
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
    intro: "기본 정보",
    self_expression: "자기 표현",
    maslow: "욕구 탐색",
    formative: "성장 배경",
    attachment: "애착 패턴",
    shadow: "그림자 탐색",
    archetype: "원형 매칭",
    synthesis: "창작 DNA",
};

const DEPTH_LEVELS = [
    { value: "quick", label: "간단 (3단계)", desc: "빠른 핵심 분석" },
    { value: "standard", label: "표준 (5단계)", desc: "균형 잡힌 분석" },
    { value: "deep", label: "심층 (7단계)", desc: "상세한 탐구" },
];

const MODELS = [
    { value: "gemini-3-flash-preview", label: "Flash (빠름)" },
    { value: "gemini-3-pro-preview", label: "Pro (깊이)" },
];

export default function AbyssInterpreterPanel() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputMessage, setInputMessage] = useState("");
    const [currentStage, setCurrentStage] = useState("intro");
    const [personaData, setPersonaData] = useState<PersonaData>({});
    const [depthLevel, setDepthLevel] = useState("standard");
    const [model, setModel] = useState("gemini-3-flash-preview");
    const [birthInfo, setBirthInfo] = useState({ year: "", month: "", day: "", hour: "" });

    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showCreditModal, setShowCreditModal] = useState(false);
    const [isComplete, setIsComplete] = useState(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();
    const { getToolByDimension } = useDimensionConfig();
    const toolConfig = getToolByDimension("AI");
    const CREDIT_COST = toolConfig?.creditCost ?? 5;

    // P1.6/P1.7: RAG Suggestion
    const {
        suggestion: ragSuggestion,
        isLoading: ragLoading,
        isOverridden: ragOverridden,
        fetchSuggestion,
        dismissSuggestion,
        applyContext,
        markAsOverridden,
        restoreSuggestion,
    } = useRAGSuggestion({ appKey: "dimension.persona.analyze" });

    // Export utilities
    const { exportJSON } = useResultExport();

    // Export conversation as JSON
    const handleExportJson = useCallback(() => {
        if (messages.length === 0 && !result?.final_persona) return;
        exportJSON({
            messages,
            final_persona: result?.final_persona,
            persona_data: personaData,
            analysis_stage: currentStage,
            completed_at: isComplete ? new Date().toISOString() : null,
        }, `persona-analysis-${Date.now()}.json`);
    }, [messages, result?.final_persona, personaData, currentStage, isComplete, exportJSON]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // Start analysis on mount - Wait for credits to load
    useEffect(() => {
        if (!byokKey && creditCtx?.isLoading) return;

        if (messages.length === 0) {
            void startAnalysis();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [byokKey, creditCtx?.isLoading]);

    const startAnalysis = useCallback(async () => {
        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
            setShowCreditModal(true);
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE}/api/dimension/persona/analyze`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...getBYOKHeaders(byokKey),
                },
                body: JSON.stringify({
                    subject: "심연해석 페르소나 분석",
                    user_message: "분석을 시작합니다",
                    current_stage: "intro",
                    persona_data: {},
                    birth_info: {},
                    model,
                    params: { depth_level: depthLevel },
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json() as { success: boolean; output: AnalysisResult; error?: string };

            if (data.success) {
                setMessages([{ role: "assistant", content: data.output.assistant_message }]);
                setCurrentStage(data.output.next_stage);
                if (!byokKey && creditCtx) {
                    void creditCtx.refresh();
                }
            } else {
                setError(data.error || "시작 실패");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "알 수 없는 오류");
        } finally {
            setIsLoading(false);
        }
    }, [byokKey, creditCtx, depthLevel, model]);

    const sendMessage = useCallback(async () => {
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

        // P1.6: Fetch RAG suggestion for context
        void fetchSuggestion(userMessage, messages.map(m => m.content).join("\n").slice(-500));

        try {
            const response = await fetch(`${API_BASE}/api/dimension/persona/analyze`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...getBYOKHeaders(byokKey),
                },
                body: JSON.stringify({
                    subject: "심연해석 페르소나 분석",
                    user_message: userMessage,
                    current_stage: currentStage,
                    persona_data: personaData,
                    birth_info: currentStage === "saju" ? birthInfo : {},
                    model,
                    params: { depth_level: depthLevel },
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json() as { success: boolean; output: AnalysisResult; error?: string };

            if (data.success) {
                setMessages(prev => [...prev, { role: "assistant", content: data.output.assistant_message }]);
                setCurrentStage(data.output.next_stage);
                if (data.output.persona_update) {
                    setPersonaData(prev => ({ ...prev, ...data.output.persona_update }));
                }
                if (data.output.analysis_complete) {
                    setIsComplete(true);
                    setResult(data.output);
                }
                if (!byokKey && creditCtx) {
                    void creditCtx.refresh();
                }
            } else {
                setError(data.error || "분석 실패");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "알 수 없는 오류");
        } finally {
            setIsLoading(false);
        }
    }, [inputMessage, isLoading, isComplete, byokKey, creditCtx, currentStage, personaData, birthInfo, depthLevel, model]);

    const resetAnalysis = useCallback(() => {
        setMessages([]);
        setCurrentStage("intro");
        setPersonaData({});
        setResult(null);
        setIsComplete(false);
        setError(null);
        // Trigger re-mount effect instead of directly calling startAnalysis
    }, []);

    const SidebarContent = (
        <>
            {/* Stage Progress */}
            {/* Stage Progress */}
            <div className="space-y-2">
                <label className="text-[10px] font-bold text-slate-500 dark:text-[var(--fg-muted)] uppercase tracking-widest ml-1">분석 단계</label>
                <div className="p-4 bg-white dark:bg-white/5 rounded-xl border border-slate-200 dark:border-white/10">
                    <div className="flex items-center gap-2 mb-3">
                        <div className={`w-2 h-2 rounded-full ${isComplete ? "bg-emerald-500 dark:bg-emerald-400" : "bg-indigo-500 dark:bg-indigo-400 animate-pulse"}`} />
                        <span className="text-sm font-medium text-slate-900 dark:text-white">
                            {STAGE_NAMES[currentStage] || currentStage}
                        </span>
                    </div>
                    <div className="flex gap-1">
                        {Object.keys(STAGE_NAMES).map((stage, i) => (
                            <div
                                key={stage}
                                className={`flex-1 h-1 rounded-full transition-all ${Object.keys(STAGE_NAMES).indexOf(currentStage) >= i
                                    ? "bg-indigo-500"
                                    : "bg-slate-200 dark:bg-white/10"
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
                            className="px-3 py-2 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white text-sm text-center focus:outline-none focus:border-indigo-500 dark:focus:border-indigo-400/50 placeholder-slate-400 dark:placeholder-white/30"
                        />
                        <input
                            type="text"
                            placeholder="월"
                            value={birthInfo.month}
                            onChange={(e) => setBirthInfo(prev => ({ ...prev, month: e.target.value }))}
                            className="px-3 py-2 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white text-sm text-center focus:outline-none focus:border-indigo-500 dark:focus:border-indigo-400/50 placeholder-slate-400 dark:placeholder-white/30"
                        />
                        <input
                            type="text"
                            placeholder="일"
                            value={birthInfo.day}
                            onChange={(e) => setBirthInfo(prev => ({ ...prev, day: e.target.value }))}
                            className="px-3 py-2 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white text-sm text-center focus:outline-none focus:border-indigo-500 dark:focus:border-indigo-400/50 placeholder-slate-400 dark:placeholder-white/30"
                        />
                        <input
                            type="text"
                            placeholder="시"
                            value={birthInfo.hour}
                            onChange={(e) => setBirthInfo(prev => ({ ...prev, hour: e.target.value }))}
                            className="px-3 py-2 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white text-sm text-center focus:outline-none focus:border-indigo-500 dark:focus:border-indigo-400/50 placeholder-slate-400 dark:placeholder-white/30"
                        />
                    </div>
                </div>
            )}

            {/* Depth Level */}
            <div className="space-y-2">
                <label className="text-[10px] font-bold text-slate-500 dark:text-[var(--fg-muted)] uppercase tracking-widest ml-1">분석 깊이</label>
                <div className="space-y-2">
                    {DEPTH_LEVELS.map((level) => (
                        <button
                            key={level.value}
                            onClick={() => setDepthLevel(level.value)}
                            disabled={messages.length > 0}
                            className={`w-full flex flex-col px-4 py-3 rounded-xl text-left transition-all ${depthLevel === level.value
                                ? "bg-indigo-500/10 border border-indigo-500/30"
                                : "bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/20"
                                } ${messages.length > 0 ? "opacity-50 cursor-not-allowed" : ""}`}
                        >
                            <span className={`text-sm font-medium ${depthLevel === level.value ? "text-indigo-600 dark:text-indigo-400" : "text-slate-700 dark:text-zinc-300"}`}>
                                {level.label}
                            </span>
                            <span className="text-[10px] text-slate-500 dark:text-zinc-500">{level.desc}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Model Select */}
            <div className="space-y-2 pt-4 border-t border-slate-200 dark:border-white/5">
                <label className="text-[10px] font-bold text-slate-500 dark:text-[var(--fg-muted)] uppercase tracking-widest ml-1">AI 모델</label>
                <div className="relative">
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        disabled={messages.length > 0}
                        className="w-full px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white text-sm focus:outline-none focus:border-indigo-500 dark:focus:border-indigo-400/50 transition-all appearance-none cursor-pointer font-mono disabled:opacity-50"
                    >
                        {MODELS.map((m) => (
                            <option key={m.value} value={m.value} className="bg-white dark:bg-[#0F0F1A] text-slate-900 dark:text-white">{m.label}</option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-500 dark:text-white/30">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            {/* Reset Button */}
            {messages.length > 0 && (
                <button
                    onClick={resetAnalysis}
                    className="w-full py-3 mt-4 border border-slate-200 dark:border-white/10 text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white hover:border-slate-300 dark:hover:border-white/30 rounded-xl transition-all text-sm"
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
                <div className="flex h-full">
                    {/* Left: Chat Interface */}
                    <div className="flex-1 flex flex-col h-full overflow-hidden border-r border-slate-200 dark:border-white/5 relative z-10">
                        {/* Messages Area */}
                        <div className="flex-1 overflow-y-auto space-y-4 p-8 custom-scrollbar">
                            {messages.map((msg, i) => (
                                <div
                                    key={i}
                                    className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                                >
                                    {msg.role === "assistant" && (
                                        <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center flex-shrink-0">
                                            <Bot className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                                        </div>
                                    )}
                                    <div
                                        className={`max-w-[90%] p-4 rounded-2xl ${msg.role === "user"
                                            ? "bg-indigo-500/20 border border-indigo-500/30"
                                            : "bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 shadow-sm dark:shadow-none"
                                            }`}
                                    >
                                        <p className="text-sm text-slate-700 dark:text-zinc-200 leading-relaxed whitespace-pre-wrap">
                                            {msg.content}
                                        </p>
                                    </div>
                                    {msg.role === "user" && (
                                        <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-white/10 border border-slate-300 dark:border-white/20 flex items-center justify-center flex-shrink-0">
                                            <User className="w-4 h-4 text-slate-500 dark:text-zinc-400" />
                                        </div>
                                    )}
                                </div>
                            ))}

                            {/* Final Persona Result */}
                            {isComplete && result?.final_persona && (
                                <div className="mt-8 p-6 bg-gradient-to-br from-indigo-100 to-violet-100 dark:from-indigo-500/10 dark:to-violet-500/10 border border-indigo-300 dark:border-indigo-500/30 rounded-3xl animate-in fade-in slide-in-from-bottom-4">
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="flex items-center gap-3">
                                            <Sparkles className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                                            <h3 className="text-lg font-bold text-slate-900 dark:text-white">페르소나 분석 완료</h3>
                                        </div>
                                        <button
                                            onClick={handleExportJson}
                                            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-white/5 dark:hover:bg-white/10 border border-slate-300 dark:border-white/10 rounded-lg flex items-center gap-2 text-xs text-slate-600 hover:text-slate-900 dark:text-white/70 dark:hover:text-white transition-all"
                                        >
                                            <Download className="w-3 h-3" />
                                            JSON 내보내기
                                        </button>
                                    </div>
                                    <p className="text-sm text-slate-600 dark:text-zinc-300 mb-6">{result.final_persona.summary}</p>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="p-4 bg-white/50 dark:bg-white/5 rounded-xl border border-slate-200 dark:border-transparent">
                                            <h4 className="text-xs font-bold text-indigo-600 dark:text-indigo-400 uppercase mb-2">핵심 특성</h4>
                                            <div className="flex flex-wrap gap-2">
                                                {result.final_persona.traits.map((trait, i) => (
                                                    <span key={i} className="px-3 py-1 bg-indigo-100 dark:bg-indigo-500/20 rounded-full text-xs text-indigo-700 dark:text-indigo-300">{trait}</span>
                                                ))}
                                            </div>
                                        </div>
                                        <div className="p-4 bg-white/50 dark:bg-white/5 rounded-xl border border-slate-200 dark:border-transparent">
                                            <h4 className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase mb-2">강점</h4>
                                            <ul className="space-y-1">
                                                {result.final_persona.strengths.map((s, i) => (
                                                    <li key={i} className="text-xs text-slate-600 dark:text-zinc-300 flex items-start gap-2">
                                                        <span className="text-emerald-600 dark:text-emerald-400">+</span>{s}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {isLoading && (
                                <div className="flex gap-3">
                                    <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-500/20 border border-indigo-300 dark:border-indigo-500/30 flex items-center justify-center">
                                        <Bot className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                                    </div>
                                    <div className="px-4 py-3 bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-2xl">
                                        <div className="flex gap-1">
                                            <span className="w-2 h-2 bg-indigo-500 dark:bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                                            <span className="w-2 h-2 bg-indigo-500 dark:bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                                            <span className="w-2 h-2 bg-indigo-500 dark:bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input Area (Sticky Bottom) */}
                        {!isComplete && (
                            <div className="flex-shrink-0 p-6 border-t border-slate-200 dark:border-white/5 bg-white/80 dark:bg-slate-900/90 backdrop-blur-md">
                                {/* P1.6/P1.7: RAG Suggestion Card */}
                                {(ragSuggestion?.has_suggestion || ragLoading || ragOverridden) && (
                                    <div className="max-w-4xl mx-auto mb-4">
                                        <RAGSuggestionCard
                                            suggestion={ragSuggestion}
                                            isLoading={ragLoading}
                                            isOverridden={ragOverridden}
                                            onDismiss={dismissSuggestion}
                                            onRestore={restoreSuggestion}
                                            onChipClick={(text) => setInputMessage(prev => prev + text)}
                                            onApply={(context) => {
                                                applyContext(context);
                                                setInputMessage(prev => prev + "\n(RAG 컨텍스트 적용됨)");
                                            }}
                                        />
                                    </div>
                                )}
                                <div className="flex gap-3 max-w-4xl mx-auto w-full">
                                    <input
                                        type="text"
                                        value={inputMessage}
                                        onChange={(e) => {
                                            setInputMessage(e.target.value);
                                            // P1.7: 적용 후 편집 시 override
                                            markAsOverridden();
                                        }}
                                        onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && void sendMessage()}
                                        placeholder="답변을 입력하세요..."
                                        disabled={isLoading}
                                        className="flex-1 px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-white/30 focus:outline-none focus:border-indigo-500 dark:focus:border-indigo-400/50 transition-all disabled:opacity-50 shadow-lg"
                                    />
                                    <button
                                        onClick={sendMessage}
                                        disabled={isLoading || !inputMessage.trim()}
                                        className="px-6 py-3 bg-indigo-500 hover:bg-indigo-600 dark:hover:bg-indigo-400 disabled:bg-slate-200 dark:disabled:bg-white/10 disabled:text-slate-400 dark:disabled:text-white/30 text-white rounded-xl transition-all shadow-lg hover:shadow-indigo-500/25"
                                    >
                                        <Send className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Right: Persona Genome (Live Data) */}
                    <div className="w-[400px] flex-shrink-0 hidden xl:block">
                        <PersonaGenome data={personaData} stage={currentStage} />
                    </div>
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
