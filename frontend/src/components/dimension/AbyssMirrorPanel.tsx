"use client";

/**
 * AbyssMirrorPanel - 심연의 거울 메인 패널
 *
 * 2026 Golden App: React 19 Best Practices + Multi-phase Chat Interface
 *
 * Features:
 * - useTransition for non-blocking form submission
 * - useOptimistic for instant UI feedback
 * - Multi-phase flow: input → chat → complete
 * - RAG integration with EvidenceDisplay
 * - trace_id history tracking
 *
 * @see https://react.dev/blog/2024/12/05/react-19
 */

import { useState, useCallback, useEffect, useRef, useTransition, useOptimistic } from "react";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useResultExport } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import PersonaGenome from "./PersonaGenome";
import EvidenceDisplay from "./EvidenceDisplay";
import { RAGSuggestionCard } from "@/components/rag/RAGSuggestionCard";
import { useRAGSuggestion, type EvidenceRef } from "@/hooks/useRAGSuggestion";
import { usePersonaPreset, type PersonaPreset } from "@/hooks/usePersonaPreset";
import { initMirror, chatMirror, type MirrorChatResponse } from "@/lib/mirrorApi";
import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";
import { Send, User, Bot, Sparkles, Download, ArrowLeft, Zap, Upload, RefreshCw, AlertTriangle } from "lucide-react";

const DIMENSION_CODE = "mirror";
const DIMENSION_KEY = "abyss-mirror";

// ============================================================================
// Types
// ============================================================================

interface Message {
  role: "user" | "assistant";
  content: string;
  trace_id?: string;
  evidence_refs?: EvidenceRef[];
  confidence?: number;
  isCrisis?: boolean;
}

type Phase = "input" | "chat" | "complete";

const STAGE_LABELS: Record<string, string> = {
  intro: "기본 정보",
  saju: "사주 분석",
  psychology: "심리 탐구",
  creativity: "창작 DNA",
  summary: "종합 정리",
};

const MODELS = [
  { value: "gemini-3-flash-preview", label: "Flash (빠름)" },
  { value: "gemini-3-pro-preview", label: "Pro (깊이)" },
];

// ============================================================================
// Content Component
// ============================================================================

function AbyssMirrorContent() {
  const { token, setLoading } = useDimensionPanel();

  // Phase state
  const [phase, setPhase] = useState<Phase>("input");
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Input form state
  const [birthInfo, setBirthInfo] = useState({
    year: "",
    month: "",
    day: "",
    hour: "12",
    mbti: "",
    bloodType: "",
    gender: "",
  });

  // Chat state
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [currentStage, setCurrentStage] = useState("intro");
  const [completionRate, setCompletionRate] = useState(0);
  const [personaData, setPersonaData] = useState<Record<string, unknown>>({});
  const [model, setModel] = useState("gemini-3-flash-preview");

  // UI state
  const [isLoading, setIsLoadingLocal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [showPresetList, setShowPresetList] = useState(false);

  // React 19: useTransition for non-blocking operations
  const [isTransitionPending, startTransition] = useTransition();

  // React 19: useOptimistic for instant UI feedback on messages
  const [optimisticMessages, addOptimisticMessage] = useOptimistic(
    messages,
    (currentMessages: Message[], newMessage: Message) => [...currentMessages, newMessage]
  );

  // Combined pending state
  const isPending = isLoading || isTransitionPending;

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Hooks
  const { byokKey } = useBYOK();
  const creditCtx = useCreditContextOptional();
  const { getToolByDimension } = useDimensionConfig();
  const toolConfig = getToolByDimension("AI");
  const creditCost = toolConfig?.creditCost ?? 5;
  const { exportJSON } = useResultExport();

  // RAG
  const ragEnabled = false;
  const {
    suggestion: ragSuggestion,
    isLoading: ragLoading,
    isOverridden: ragOverridden,
    fetchSuggestion,
    dismissSuggestion,
    applyContext,
    markAsOverridden,
    restoreSuggestion,
  } = useRAGSuggestion({ appKey: "dimension.mirror" });

  // Preset management
  const {
    presets,
    traces,
    saveLocal,
    clearLocal,
    addTrace,
    listPresets,
    resumeSession,
  } = usePersonaPreset({});

  // ChainContext for workflow integration
  const chainContext = useDimensionChainOptional();

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ========================================================================
  // Handlers
  // ========================================================================

  const handleStartAnalysis = useCallback((quick = false) => {
    if (!quick && (!birthInfo.year || !birthInfo.month || !birthInfo.day)) {
      setError("생년월일을 입력해주세요");
      return;
    }

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(creditCost)) {
      setShowCreditModal(true);
      return;
    }

    // React 19: Non-blocking transition
    startTransition(async () => {
      setIsLoadingLocal(true);
      setLoading(true);
      setError(null);

      try {
        const response = await initMirror({
          birth_year: quick ? 1990 : parseInt(birthInfo.year),
          birth_month: quick ? 1 : parseInt(birthInfo.month),
          birth_day: quick ? 1 : parseInt(birthInfo.day),
          birth_hour: parseInt(birthInfo.hour) || 12,
          mbti: birthInfo.mbti.toUpperCase(),
          blood_type: birthInfo.bloodType.toUpperCase(),
          gender: birthInfo.gender,
          model,
        }, byokKey);

        if (response.success) {
          setSessionId(response.session_id);
          setPersonaData(response.persona_data);
          setCompletionRate(response.completion_rate);
          setMessages([{
            role: "assistant",
            content: response.initial_message,
          }]);
          setPhase("chat");

          if (!byokKey && creditCtx) {
            void creditCtx.refresh();
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "초기화 실패");
      } finally {
        setIsLoadingLocal(false);
        setLoading(false);
      }
    });
  }, [birthInfo, byokKey, creditCtx, model, creditCost, setLoading, startTransition]);

  const handleSendMessage = useCallback(() => {
    if (!inputMessage.trim() || isPending || !sessionId) return;

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(creditCost)) {
      setShowCreditModal(true);
      return;
    }

    const userMessage = inputMessage.trim();
    setInputMessage("");

    // React 19: Optimistic update - show user message immediately
    const userMessageObj: Message = { role: "user", content: userMessage };
    addOptimisticMessage(userMessageObj);
    setMessages(prev => [...prev, userMessageObj]);

    if (ragEnabled) {
      void fetchSuggestion(userMessage, messages.map(m => m.content).join("\n").slice(-500));
    }

    // React 19: Non-blocking transition
    startTransition(async () => {
      setIsLoadingLocal(true);
      setError(null);

      try {
        const response: MirrorChatResponse = await chatMirror({
          session_id: sessionId,
          user_message: userMessage,
          persona_data: personaData,
          chat_history: messages.map(m => ({ role: m.role, content: m.content })),
          current_stage: currentStage,
          model,
        }, byokKey);

        if (response.success) {
          const isCrisis = response.is_crisis ?? false;
          if (isCrisis) {
            const crisisMessage: Message = {
              role: "assistant",
              content: response.ai_response,
              isCrisis: true,
            };
            setMessages(prev => [...prev, crisisMessage]);
            setIsLoadingLocal(false);
            return;
          }

          const assistantMessage: Message = {
            role: "assistant",
            content: response.ai_response,
            trace_id: response.trace_id,
            evidence_refs: response.evidence_refs,
            confidence: response.confidence,
          };

          setMessages(prev => [...prev, assistantMessage]);
          setPersonaData(response.persona_data);
          setCompletionRate(response.completion_rate);
          setCurrentStage(response.current_stage);

          addTrace({
            trace_id: response.trace_id,
            timestamp: new Date().toISOString(),
            stage: response.current_stage,
            evidence_refs: response.evidence_refs,
            user_message_preview: userMessage.slice(0, 50),
          });

          if (response.is_complete) {
            setPhase("complete");
            if (chainContext) {
              const personaSummary = (response.persona_data as Record<string, Record<string, string>>)?.persona?.summary;
              chainContext.setChainData(
                "abyss-mirror",
                response.persona_data,
                personaSummary || "심연의 거울 분석 완료"
              );
            }
            saveLocal({
              meta: {
                id: sessionId,
                created_at: new Date().toISOString(),
                version: "1.0",
                completion_rate: response.completion_rate,
                schema_version: "2026-01-14",
              },
              ...response.persona_data,
              _messages: [...messages, { role: "assistant", content: response.ai_response }],
              _current_stage: response.current_stage,
            } as PersonaPreset);
          }

          if (!byokKey && creditCtx) {
            void creditCtx.refresh();
          }
        } else {
          setError(response.error || "분석 실패");
        }
      } catch (err) {
        if (err instanceof Error) {
          if (err.message.includes("401") || err.message.includes("Unauthorized")) {
            setError("인증 오류가 발생했습니다. 다시 시작해주세요.");
          } else if (err.message.includes("402")) {
            setError("크레딧이 부족합니다.");
            setShowCreditModal(true);
          } else {
            setError(err.message);
          }
        } else {
          setError("알 수 없는 오류");
        }
      } finally {
        setIsLoadingLocal(false);
      }
    });
  }, [inputMessage, isPending, sessionId, byokKey, creditCtx, messages, personaData, currentStage, model, creditCost, fetchSuggestion, addTrace, saveLocal, chainContext, ragEnabled, addOptimisticMessage, startTransition]);

  const handleExportJson = useCallback(() => {
    if (Object.keys(personaData).length === 0) return;
    exportJSON({
      messages,
      persona_data: personaData,
      completion_rate: completionRate,
      traces,
    }, `abyss-mirror-${Date.now()}.json`);
  }, [messages, personaData, completionRate, traces, exportJSON]);

  const handleResumePreset = useCallback((presetId: string) => {
    const found = resumeSession(presetId);
    if (found) {
      setPersonaData(found);
      setCompletionRate(found.meta.completion_rate);
      const savedMessages = (found as Record<string, unknown>)._messages as Message[] | undefined;
      if (savedMessages && savedMessages.length > 0) {
        setMessages(savedMessages);
      }
      const savedStage = (found as Record<string, unknown>)._current_stage as string | undefined;
      if (savedStage) {
        setCurrentStage(savedStage);
      }
      setSessionId(found.meta.id);
      setPhase("chat");
      setShowPresetList(false);
    }
  }, [resumeSession]);

  const handleReset = useCallback(() => {
    setPhase("input");
    setSessionId(null);
    setMessages([]);
    setPersonaData({});
    setCompletionRate(0);
    setCurrentStage("intro");
    setError(null);
  }, []);

  // ========================================================================
  // Render: Input Form
  // ========================================================================

  const renderInputForm = () => (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="max-w-md w-full space-y-6">
        <div className="text-center mb-8">
          <div className={`w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-${token.themeColor}-500 to-purple-600 flex items-center justify-center`}>
            <Sparkles className="w-10 h-10 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">심연의 거울</h2>
          <p className="text-sm text-slate-500 dark:text-white/50 mt-2">
            당신의 심층 페르소나를 탐구합니다
          </p>
        </div>

        {/* Birth Date */}
        <div className="space-y-2">
          <label className="text-xs font-bold text-slate-500 dark:text-white/50 uppercase">
            생년월일 (필수)
          </label>
          <div className="grid grid-cols-4 gap-2">
            <input
              type="text"
              placeholder="년"
              value={birthInfo.year}
              onChange={e => setBirthInfo(prev => ({ ...prev, year: e.target.value }))}
              className={`px-3 py-2.5 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white text-center focus:outline-none focus:border-${token.themeColor}-500`}
            />
            <input
              type="text"
              placeholder="월"
              value={birthInfo.month}
              onChange={e => setBirthInfo(prev => ({ ...prev, month: e.target.value }))}
              className={`px-3 py-2.5 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white text-center focus:outline-none focus:border-${token.themeColor}-500`}
            />
            <input
              type="text"
              placeholder="일"
              value={birthInfo.day}
              onChange={e => setBirthInfo(prev => ({ ...prev, day: e.target.value }))}
              className={`px-3 py-2.5 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white text-center focus:outline-none focus:border-${token.themeColor}-500`}
            />
            <input
              type="text"
              placeholder="시"
              value={birthInfo.hour}
              onChange={e => setBirthInfo(prev => ({ ...prev, hour: e.target.value }))}
              className={`px-3 py-2.5 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white text-center focus:outline-none focus:border-${token.themeColor}-500`}
            />
          </div>
        </div>

        {/* MBTI & Blood Type */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 dark:text-white/50 uppercase">
              MBTI (선택)
            </label>
            <input
              type="text"
              placeholder="예: INTJ"
              maxLength={4}
              value={birthInfo.mbti}
              onChange={e => setBirthInfo(prev => ({ ...prev, mbti: e.target.value }))}
              className={`w-full px-3 py-2.5 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white text-center uppercase focus:outline-none focus:border-${token.themeColor}-500`}
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 dark:text-white/50 uppercase">
              혈액형 (선택)
            </label>
            <select
              value={birthInfo.bloodType}
              onChange={e => setBirthInfo(prev => ({ ...prev, bloodType: e.target.value }))}
              className={`w-full px-3 py-2.5 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:border-${token.themeColor}-500`}
            >
              <option value="">선택</option>
              <option value="A">A형</option>
              <option value="B">B형</option>
              <option value="O">O형</option>
              <option value="AB">AB형</option>
            </select>
          </div>
        </div>

        {/* Buttons - React 19: Use isPending for combined state */}
        <div className="flex gap-3 pt-4">
          <button
            onClick={() => handleStartAnalysis(false)}
            disabled={isPending}
            className={`flex-1 py-3 bg-gradient-to-r from-${token.themeColor}-500 to-purple-600 hover:from-${token.themeColor}-600 hover:to-purple-700 text-white font-medium rounded-xl transition-all disabled:opacity-50 flex items-center justify-center gap-2`}
          >
            {isPending ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                분석 중...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                분석 시작
              </>
            )}
          </button>
          <button
            onClick={() => handleStartAnalysis(true)}
            disabled={isPending}
            className="px-4 py-3 bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 text-slate-700 dark:text-white/70 font-medium rounded-xl transition-all disabled:opacity-50 flex items-center gap-2"
            title="기본값으로 빠르게 시작"
          >
            <Zap className="w-4 h-4" />
          </button>
        </div>

        {/* Load Preset */}
        {presets.length > 0 && (
          <button
            onClick={() => setShowPresetList(!showPresetList)}
            className={`w-full py-2 text-sm text-${token.themeColor}-600 dark:text-${token.themeColor}-400 hover:underline flex items-center justify-center gap-2`}
          >
            <Upload className="w-4 h-4" />
            기존 프리셋 불러오기 ({presets.length}개)
          </button>
        )}

        {showPresetList && (
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {listPresets().map(p => (
              <button
                key={p.meta.id}
                onClick={() => handleResumePreset(p.meta.id)}
                className="w-full px-4 py-2 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-lg text-left hover:bg-slate-50 dark:hover:bg-white/10 transition-all"
              >
                <div className="text-sm font-medium text-slate-900 dark:text-white">
                  {p.persona?.archetype as string || "페르소나"}
                </div>
                <div className="text-xs text-slate-500 dark:text-white/40">
                  {Math.round(p.meta.completion_rate)}% • {new Date(p.meta.created_at).toLocaleDateString()}
                </div>
              </button>
            ))}
          </div>
        )}

        {error && (
          <div className="p-3 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-lg text-red-600 dark:text-red-400 text-sm">
            {error}
          </div>
        )}
      </div>
    </div>
  );

  // ========================================================================
  // Render: Chat Interface
  // ========================================================================

  const renderChatInterface = () => (
    <div className="flex h-full">
      {/* Chat Area */}
      <div className="flex-1 flex flex-col overflow-hidden border-r border-slate-200 dark:border-white/5">
        {/* Progress Bar */}
        <div className="flex-shrink-0 px-6 py-3 border-b border-slate-200 dark:border-white/5 bg-slate-50 dark:bg-slate-900/40">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 dark:text-white/50 uppercase">
              {STAGE_LABELS[currentStage] || currentStage}
            </span>
            <span className={`text-xs font-mono text-${token.themeColor}-600 dark:text-${token.themeColor}-400`}>
              {Math.round(completionRate)}%
            </span>
          </div>
          <div className="h-1.5 bg-slate-200 dark:bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full bg-gradient-to-r from-${token.themeColor}-500 to-purple-500 rounded-full transition-all duration-500`}
              style={{ width: `${completionRate}%` }}
            />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-[10px] text-slate-400 dark:text-white/30">
              {messages.filter(m => m.role === "user").length} 답변
            </span>
            <span className="text-[10px] text-slate-400 dark:text-white/30">
              {traces.length} traces
            </span>
          </div>
        </div>

        {/* Messages - React 19: Use optimisticMessages for instant feedback */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
          {optimisticMessages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "assistant" && (
                <div className={`w-8 h-8 rounded-full bg-${token.themeColor}-100 dark:bg-${token.themeColor}-500/20 border border-${token.themeColor}-300 dark:border-${token.themeColor}-500/30 flex items-center justify-center flex-shrink-0`}>
                  <Bot className={`w-4 h-4 text-${token.themeColor}-600 dark:text-${token.themeColor}-400`} />
                </div>
              )}
              <div className="max-w-[85%] space-y-2">
                <div className={`p-4 rounded-2xl ${msg.isCrisis
                  ? "bg-red-500/20 border-2 border-red-500/50"
                  : msg.role === "user"
                    ? `bg-${token.themeColor}-500/20 border border-${token.themeColor}-500/30`
                    : "bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10"
                  }`}>
                  {msg.isCrisis && (
                    <div className="flex items-center gap-2 mb-2 text-red-400">
                      <AlertTriangle className="w-4 h-4" />
                      <span className="text-xs font-medium">안전 알림</span>
                    </div>
                  )}
                  <p className={`text-sm leading-relaxed whitespace-pre-wrap ${msg.isCrisis ? "text-red-50" : "text-slate-700 dark:text-zinc-200"}`}>
                    {msg.content}
                  </p>
                  {msg.isCrisis && (
                    <a
                      href="https://www.mentalhealth.go.kr"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block mt-3 text-sm text-red-300 hover:text-red-200 underline"
                    >
                      전문 상담 바로가기 →
                    </a>
                  )}
                </div>
                {msg.role === "assistant" && msg.evidence_refs && msg.evidence_refs.length > 0 && (
                  <EvidenceDisplay
                    refs={msg.evidence_refs}
                    confidence={msg.confidence}
                    themeColor="violet"
                    maxVisible={2}
                  />
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-white/10 border border-slate-300 dark:border-white/20 flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-slate-500 dark:text-zinc-400" />
                </div>
              )}
            </div>
          ))}

          {/* React 19: Show loading during transition */}
          {isPending && (
            <div className="flex gap-3">
              <div className={`w-8 h-8 rounded-full bg-${token.themeColor}-100 dark:bg-${token.themeColor}-500/20 border border-${token.themeColor}-300 dark:border-${token.themeColor}-500/30 flex items-center justify-center animate-pulse`}>
                <Bot className={`w-4 h-4 text-${token.themeColor}-600 dark:text-${token.themeColor}-400`} />
              </div>
              <div className="flex-1 max-w-[70%] p-4 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-2xl">
                <div className="animate-pulse space-y-2">
                  <div className={`h-3 bg-${token.themeColor}-200 dark:bg-${token.themeColor}-500/30 rounded w-3/4`}></div>
                  <div className={`h-3 bg-${token.themeColor}-200 dark:bg-${token.themeColor}-500/30 rounded w-1/2`}></div>
                  <div className={`h-3 bg-${token.themeColor}-200 dark:bg-${token.themeColor}-500/30 rounded w-2/3`}></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        {phase !== "complete" && (
          <div className="flex-shrink-0 p-4 border-t border-slate-200 dark:border-white/5 bg-white/80 dark:bg-slate-900/90 backdrop-blur-md">
            {ragEnabled && (ragSuggestion?.has_suggestion || ragLoading || ragOverridden) && (
              <div className="mb-4">
                <RAGSuggestionCard
                  suggestion={ragSuggestion}
                  isLoading={ragLoading}
                  isOverridden={ragOverridden}
                  onDismiss={dismissSuggestion}
                  onRestore={restoreSuggestion}
                  onChipClick={(text) => setInputMessage(prev => prev + text)}
                  onApply={(context) => {
                    applyContext(context);
                    setInputMessage(prev => prev + "\n(RAG 컨텍스트 적용)");
                  }}
                />
              </div>
            )}

            {/* React 19: Use isPending for combined state */}
            <div className="flex gap-3">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => {
                  setInputMessage(e.target.value);
                  markAsOverridden();
                }}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && void handleSendMessage()}
                placeholder="답변을 입력하세요..."
                disabled={isPending}
                className={`flex-1 px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-white/30 focus:outline-none focus:border-${token.themeColor}-500 transition-all disabled:opacity-50`}
              />
              <button
                onClick={handleSendMessage}
                disabled={isPending || !inputMessage.trim()}
                className={`px-6 py-3 bg-${token.themeColor}-500 hover:bg-${token.themeColor}-600 disabled:bg-slate-200 dark:disabled:bg-white/10 text-white disabled:text-slate-400 dark:disabled:text-white/30 rounded-xl transition-all`}
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}

        {/* Complete State */}
        {phase === "complete" && (
          <div className={`flex-shrink-0 p-6 border-t border-slate-200 dark:border-white/5 bg-gradient-to-r from-${token.themeColor}-50 to-purple-50 dark:from-${token.themeColor}-500/10 dark:to-purple-500/10`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Sparkles className={`w-6 h-6 text-${token.themeColor}-600 dark:text-${token.themeColor}-400`} />
                <span className="font-bold text-slate-900 dark:text-white">페르소나 분석 완료!</span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleExportJson}
                  className="px-4 py-2 bg-white dark:bg-white/10 border border-slate-200 dark:border-white/10 rounded-lg flex items-center gap-2 text-sm hover:bg-slate-50 dark:hover:bg-white/20 transition-all"
                >
                  <Download className="w-4 h-4" />
                  JSON 내보내기
                </button>
                <button
                  onClick={handleReset}
                  className={`px-4 py-2 bg-${token.themeColor}-500 hover:bg-${token.themeColor}-600 text-white rounded-lg flex items-center gap-2 text-sm transition-all`}
                >
                  <RefreshCw className="w-4 h-4" />
                  새로 시작
                </button>
              </div>
            </div>
            {/* Next Dimension Navigation */}
            <div className="mt-4 px-6">
              <DimensionPanel.NextNav currentDimension={DIMENSION_KEY} />
            </div>
          </div>
        )}
      </div>

      {/* PersonaGenome Sidebar */}
      <div className="w-[380px] flex-shrink-0 hidden xl:block">
        <PersonaGenome data={personaData} stage={currentStage} />
      </div>
    </div>
  );

  // ========================================================================
  // Main Render
  // ========================================================================

  // React 19: Combined pending state for fullscreen loading
  const showFullscreenLoading = phase === "input" && isPending;

  return (
    <>
      <DimensionPanel.Header title="심연의 거울" />

      <div className="flex flex-1 min-h-0">
        <DimensionPanel.Sidebar>
          {phase !== "input" && (
            <button
              onClick={handleReset}
              className="flex items-center gap-2 text-sm text-slate-500 dark:text-white/50 hover:text-slate-700 dark:hover:text-white/70 mb-4"
            >
              <ArrowLeft className="w-4 h-4" />
              처음으로
            </button>
          )}

          {/* Model Select */}
          <DimensionPanel.Select
            label="AI 모델"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            options={MODELS}
            disabled={phase !== "input"}
          />

          {/* Trace History */}
          {traces.length > 0 && (
            <div className="space-y-2 mt-6">
              <label className="text-[10px] font-bold text-slate-500 dark:text-white/50 uppercase tracking-widest">
                Trace 히스토리
              </label>
              <div className="max-h-40 overflow-y-auto space-y-1">
                {traces.slice(0, 5).map((t, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      const latestPreset = presets[0];
                      if (latestPreset) {
                        handleResumePreset(latestPreset.meta.id);
                      }
                    }}
                    className={`w-full px-3 py-2 bg-white dark:bg-white/5 rounded-lg text-xs hover:bg-${token.themeColor}-50 dark:hover:bg-${token.themeColor}-500/10 transition-colors cursor-pointer text-left`}
                  >
                    <div className="flex justify-between">
                      <span className={`text-${token.themeColor}-600 dark:text-${token.themeColor}-400 font-mono`}>
                        {t.trace_id.slice(0, 8)}...
                      </span>
                      <span className="text-slate-400 dark:text-white/30">
                        {t.stage}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* History Management */}
          {(presets.length > 0 || messages.length > 0) && (
            <div className="mt-6 space-y-2">
              <label className="text-[10px] font-bold text-slate-500 dark:text-white/50 uppercase tracking-widest">
                히스토리 관리
              </label>
              <div className="flex gap-2">
                {presets.length > 0 && (
                  <button
                    onClick={() => {
                      const latestPreset = presets[0];
                      if (latestPreset) {
                        handleResumePreset(latestPreset.meta.id);
                      }
                    }}
                    className={`flex-1 px-3 py-2 bg-${token.themeColor}-500/20 hover:bg-${token.themeColor}-500/30 border border-${token.themeColor}-500/30 rounded-lg text-xs text-${token.themeColor}-600 dark:text-${token.themeColor}-400 transition-colors`}
                  >
                    ⏪ 이전 세션
                  </button>
                )}
                <button
                  onClick={() => {
                    if (confirm("모든 히스토리를 삭제하고 처음부터 시작하시겠습니까?")) {
                      clearLocal();
                      handleReset();
                    }
                  }}
                  className="flex-1 px-3 py-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-lg text-xs text-red-500 dark:text-red-400 transition-colors"
                >
                  🗑️ 초기화
                </button>
              </div>
              {presets.length > 1 && (
                <p className="text-[10px] text-slate-400 dark:text-white/30">
                  저장된 세션: {presets.length}개
                </p>
              )}
            </div>
          )}

          {error && (
            <div className="mt-4 p-3 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-lg text-red-600 dark:text-red-400 text-xs">
              {error}
            </div>
          )}
        </DimensionPanel.Sidebar>

        <DimensionPanel.Content>
          {showFullscreenLoading && <DimensionPanel.Loading />}
          {phase === "input" ? renderInputForm() : renderChatInterface()}
        </DimensionPanel.Content>
      </div>

      <InsufficientCreditsModal
        isOpen={showCreditModal}
        onClose={() => setShowCreditModal(false)}
        requiredCredits={creditCost}
        currentBalance={creditCtx?.balance ?? 0}
        onRetry={phase === "input" ? () => handleStartAnalysis(false) : handleSendMessage}
      />
    </>
  );
}

// ============================================================================
// Main Export
// ============================================================================

export default function AbyssMirrorPanel() {
  return (
    <DimensionPanel dimensionCode={DIMENSION_CODE}>
      <AbyssMirrorContent />
    </DimensionPanel>
  );
}
