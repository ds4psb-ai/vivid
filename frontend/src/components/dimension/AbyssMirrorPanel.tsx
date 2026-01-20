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

import { useState, useCallback, useEffect, useRef, useTransition, useOptimistic, useMemo } from "react";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useResultExport } from "./DimensionPanelLayout";
import { useBYOK } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import { useLanguage } from "@/contexts/LanguageContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import PersonaGenome from "./PersonaGenome";
import EvidenceDisplay from "./EvidenceDisplay";
import { RAGSuggestionCard } from "@/components/rag/RAGSuggestionCard";
import { useRAGSuggestion, type EvidenceRef } from "@/hooks/useRAGSuggestion";
import { usePersonaPreset, type PersonaPreset } from "@/hooks/usePersonaPreset";
import { initMirror, chatMirror, type MirrorChatResponse } from "@/lib/mirrorApi";
import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";
import { getDemoIPOverride } from "@/lib/demo-ip-overrides";
import { getPreviousStepResult } from "@/lib/workflow-state";
import { Send, User, Bot, Sparkles, Download, ArrowLeft, Zap, Upload, RefreshCw, AlertTriangle, Film } from "lucide-react";

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

const getStageLabels = (isKo: boolean): Record<string, string> => ({
  intro: isKo ? "기본 정보" : "Basic Info",
  saju: isKo ? "사주 분석" : "Birth Chart Analysis",
  psychology: isKo ? "심리 탐구" : "Psychology Exploration",
  creativity: isKo ? "창작 DNA" : "Creative DNA",
  summary: isKo ? "종합 정리" : "Summary",
});

const getModels = (isKo: boolean) => [
  { value: "gemini-3-flash-preview", label: isKo ? "Flash (빠름)" : "Flash (Fast)" },
  { value: "gemini-3-pro-preview", label: isKo ? "Pro (고품질)" : "Pro (High Quality)" },
];

// ============================================================================
// Content Component
// ============================================================================

function AbyssMirrorContent() {
  const { token, setLoading } = useDimensionPanel();
  const { language } = useLanguage();
  const isKo = language === "ko";

  // Memoized presets based on language
  const STAGE_LABELS = useMemo(() => getStageLabels(isKo), [isKo]);
  const MODELS = useMemo(() => getModels(isKo), [isKo]);

  // i18n labels
  const labels = useMemo(() => ({
    // Header
    title: isKo ? "심연의 거울" : "Abyss Mirror",
    subtitle: isKo ? "당신의 심층 페르소나를 탐구합니다" : "Explore your deep persona",

    // Input Form
    birthDate: isKo ? "생년월일 (필수)" : "Birth Date (Required)",
    year: isKo ? "년" : "Year",
    month: isKo ? "월" : "Month",
    day: isKo ? "일" : "Day",
    hour: isKo ? "시" : "Hour",
    mbti: isKo ? "MBTI (선택)" : "MBTI (Optional)",
    mbtiPlaceholder: isKo ? "예: INTJ" : "e.g., INTJ",
    bloodType: isKo ? "혈액형 (선택)" : "Blood Type (Optional)",
    select: isKo ? "선택" : "Select",
    typeA: isKo ? "A형" : "Type A",
    typeB: isKo ? "B형" : "Type B",
    typeO: isKo ? "O형" : "Type O",
    typeAB: isKo ? "AB형" : "Type AB",

    // Buttons
    analyzing: isKo ? "분석 중..." : "Analyzing...",
    startAnalysis: isKo ? "분석 시작" : "Start Analysis",
    quickStartTooltip: isKo ? "기본값으로 빠르게 시작" : "Quick start with defaults",
    loadPreset: (count: number) => isKo ? `기존 프리셋 불러오기 (${count}개)` : `Load Existing Preset (${count})`,
    persona: isKo ? "페르소나" : "Persona",

    // Sidebar
    aiModel: isKo ? "AI 모델" : "AI Model",
    inspirationImage: isKo ? "영감 이미지 (선택)" : "Inspiration Image (Optional)",
    inspirationHelperText: isKo ? "취향이 담긴 이미지, 좋아하는 포스터 등" : "Images reflecting your taste, favorite posters, etc.",
    traceHistory: isKo ? "Trace 히스토리" : "Trace History",
    historyManagement: isKo ? "히스토리 관리" : "History Management",
    previousSession: isKo ? "⏪ 이전 세션" : "⏪ Previous Session",
    reset: isKo ? "🗑️ 초기화" : "🗑️ Reset",
    savedSessions: (count: number) => isKo ? `저장된 세션: ${count}개` : `Saved Sessions: ${count}`,
    goBack: isKo ? "처음으로" : "Go Back",

    // Chat Interface
    answers: isKo ? "답변" : "answers",
    traces: "traces",
    safetyAlert: isKo ? "안전 알림" : "Safety Alert",
    counselingLink: isKo ? "전문 상담 바로가기" : "Professional Counseling",

    // Complete State
    analysisComplete: isKo ? "페르소나 분석 완료!" : "Persona Analysis Complete!",
    exportJson: isKo ? "JSON 내보내기" : "Export JSON",
    newSession: isKo ? "새로 시작" : "New Session",

    // Input placeholder
    inputPlaceholder: isKo ? "답변을 입력하세요..." : "Enter your answer...",

    // Confirm dialogs
    confirmReset: isKo ? "모든 히스토리를 삭제하고 처음부터 시작하시겠습니까?" : "Delete all history and start over?",

    // Chain context message
    chainCompleteMessage: isKo ? "심연의 거울 분석 완료" : "Abyss Mirror analysis complete",

    // Error messages
    errorBirthDate: isKo ? "생년월일을 입력해주세요" : "Please enter your birth date",
    errorInit: isKo ? "초기화 실패" : "Initialization failed",
    errorAnalysis: isKo ? "분석 실패" : "Analysis failed",
    errorAuth: isKo ? "인증 오류가 발생했습니다. 다시 시작해주세요." : "Authentication error. Please start again.",
    errorCredits: isKo ? "크레딧이 부족합니다." : "Insufficient credits.",
    errorUnknown: isKo ? "알 수 없는 오류" : "Unknown error",
  }), [isKo]);

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
  const [_files, setFiles] = useState<File[]>([]);

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

  // IP context state for workflow integration
  const [ipContext, setIpContext] = useState<{
    slug: string;
    title: string;
    desc: string;
    videoUrl?: string;
  } | null>(null);

  // Workflow context from previous step (e.g., Reference Decoder)
  const [workflowContext, setWorkflowContext] = useState<{
    source: string;
    styleHints: {
      mood?: string;
      lighting?: string;
      colorPalette?: string[];
      referenceArtists?: string[];
      stylePrompt?: string;
    };
  } | null>(null);

  // URL parameter handling for workflow integration
  useEffect(() => {
    if (typeof window === "undefined") return;

    const params = new URLSearchParams(window.location.search);
    const ipParam = params.get("ip");

    if (ipParam) {
      const ipData = getDemoIPOverride(ipParam);
      if (ipData) {
        setIpContext({
          slug: ipParam,
          title: isKo ? ipData.titleKo : ipData.titleEn,
          desc: isKo ? ipData.descKo : ipData.descEn,
          videoUrl: ipData.previewVideoUrl,
        });
      }
    }
  }, [isKo]);

  // Load previous step result (e.g., Reference Decoder → Abyss Mirror inheritance)
  useEffect(() => {
    if (typeof window === "undefined") return;

    const params = new URLSearchParams(window.location.search);
    const ipSlug = params.get("ip");
    const stepParam = params.get("step");
    const currentStep = stepParam ? parseInt(stepParam, 10) : null;

    if (!ipSlug || !currentStep || currentStep <= 1) return;

    const prevResult = getPreviousStepResult(ipSlug, currentStep);
    if (!prevResult?.outputData) return;

    const data = prevResult.outputData;
    const styleHints: NonNullable<typeof workflowContext>["styleHints"] = {};

    // Style Extraction / Video Analysis / Image Analysis mode handling
    if (data.style_prompt) {
      styleHints.stylePrompt = data.style_prompt as string;
      styleHints.mood = data.mood as string;
      styleHints.lighting = data.lighting as string;
      styleHints.colorPalette = data.color_palette as string[];
      styleHints.referenceArtists = data.reference_artists as string[];
    }
    if (data.style && typeof data.style === "object") {
      const style = data.style as Record<string, unknown>;
      styleHints.mood ??= style.mood as string;
      styleHints.lighting ??= style.lighting as string;
    }
    if (data.recreation_prompt && !styleHints.stylePrompt) {
      styleHints.stylePrompt = data.recreation_prompt as string;
    }

    if (Object.values(styleHints).some(Boolean)) {
      setWorkflowContext({ source: "reference-decoder", styleHints });
    }
  }, []);

  // ========================================================================
  // Handlers
  // ========================================================================

  const handleStartAnalysis = useCallback((quick = false) => {
    if (!quick && (!birthInfo.year || !birthInfo.month || !birthInfo.day)) {
      setError(labels.errorBirthDate);
      return;
    }

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(creditCost)) {
      setShowCreditModal(true);
      return;
    }

    // Build seed_preset from workflow context (e.g., Reference Decoder → Abyss Mirror)
    const seedPreset = workflowContext?.styleHints
      ? {
          visual_preferences: {
            mood: workflowContext.styleHints.mood,
            lighting: workflowContext.styleHints.lighting,
            color_palette: workflowContext.styleHints.colorPalette,
          },
          style_prompt: workflowContext.styleHints.stylePrompt,
          suggested_auteurs: workflowContext.styleHints.referenceArtists,
        }
      : undefined;

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
          seed_preset: seedPreset,
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
        setError(err instanceof Error ? err.message : labels.errorInit);
      } finally {
        setIsLoadingLocal(false);
        setLoading(false);
      }
    });
  }, [birthInfo, byokKey, creditCtx, model, creditCost, setLoading, startTransition, labels, workflowContext]);

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
                personaSummary || labels.chainCompleteMessage
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
          setError(response.error || labels.errorAnalysis);
        }
      } catch (err) {
        if (err instanceof Error) {
          if (err.message.includes("401") || err.message.includes("Unauthorized")) {
            setError(labels.errorAuth);
          } else if (err.message.includes("402")) {
            setError(labels.errorCredits);
            setShowCreditModal(true);
          } else {
            setError(err.message);
          }
        } else {
          setError(labels.errorUnknown);
        }
      } finally {
        setIsLoadingLocal(false);
      }
    });
  }, [inputMessage, isPending, sessionId, byokKey, creditCtx, messages, personaData, currentStage, model, creditCost, fetchSuggestion, addTrace, saveLocal, chainContext, ragEnabled, addOptimisticMessage, startTransition, labels]);

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
            <Sparkles className="w-10 h-10 text-[var(--fg-on-emphasis)]" />
          </div>
          <h2 className="text-2xl font-bold text-[var(--fg-0)]">{labels.title}</h2>
          <p className="text-sm text-[var(--fg-muted)] mt-2">
            {labels.subtitle}
          </p>
        </div>

        {/* IP Context Banner (from workflow integration) */}
        {ipContext && (
          <div className="p-3 rounded-xl bg-violet-500/10 border border-violet-500/20">
            <div className="flex items-center gap-2 mb-2">
              <Film className="w-4 h-4 text-violet-500" />
              <span className="text-xs font-medium text-violet-600 dark:text-violet-400">
                {isKo ? "IP 레퍼런스" : "IP Reference"}
              </span>
              <span className="px-2 py-0.5 text-[9px] bg-violet-500/20 text-violet-600 dark:text-violet-400 rounded-full">
                {ipContext.slug}
              </span>
            </div>
            <p className="text-sm font-medium text-[var(--fg-0)]">{ipContext.title}</p>
            <p className="text-xs text-[var(--fg-muted)] mt-1">{ipContext.desc}</p>
          </div>
        )}

        {/* Workflow Context Banner (previous step result, e.g., Reference Decoder) */}
        {workflowContext && (
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              <span className="text-xs font-medium text-amber-600 dark:text-amber-400">
                {isKo ? "레퍼런스 분석 반영됨" : "Reference Analysis Applied"}
              </span>
            </div>
            {workflowContext.styleHints.mood && (
              <p className="text-xs text-[var(--fg-muted)]">
                <span className="font-medium">{isKo ? "무드" : "Mood"}:</span> {workflowContext.styleHints.mood}
              </p>
            )}
            {workflowContext.styleHints.lighting && (
              <p className="text-xs text-[var(--fg-muted)]">
                <span className="font-medium">{isKo ? "조명" : "Lighting"}:</span> {workflowContext.styleHints.lighting}
              </p>
            )}
            {workflowContext.styleHints.referenceArtists && workflowContext.styleHints.referenceArtists.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {workflowContext.styleHints.referenceArtists.slice(0, 3).map((artist, i) => (
                  <span key={i} className="px-2 py-0.5 text-[10px] bg-amber-500/20 text-amber-600 dark:text-amber-400 rounded-full capitalize">
                    {artist}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Birth Date */}
        <div className="space-y-2">
          <label className="text-xs font-bold text-[var(--fg-muted)] uppercase">
            {labels.birthDate}
          </label>
          <div className="grid grid-cols-4 gap-2">
            <input
              type="text"
              placeholder={labels.year}
              value={birthInfo.year}
              onChange={e => setBirthInfo(prev => ({ ...prev, year: e.target.value }))}
              className={`px-3 py-2.5 bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-xl text-[var(--fg-0)] text-center focus:outline-none focus:border-${token.themeColor}-500`}
            />
            <input
              type="text"
              placeholder={labels.month}
              value={birthInfo.month}
              onChange={e => setBirthInfo(prev => ({ ...prev, month: e.target.value }))}
              className={`px-3 py-2.5 bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-xl text-[var(--fg-0)] text-center focus:outline-none focus:border-${token.themeColor}-500`}
            />
            <input
              type="text"
              placeholder={labels.day}
              value={birthInfo.day}
              onChange={e => setBirthInfo(prev => ({ ...prev, day: e.target.value }))}
              className={`px-3 py-2.5 bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-xl text-[var(--fg-0)] text-center focus:outline-none focus:border-${token.themeColor}-500`}
            />
            <input
              type="text"
              placeholder={labels.hour}
              value={birthInfo.hour}
              onChange={e => setBirthInfo(prev => ({ ...prev, hour: e.target.value }))}
              className={`px-3 py-2.5 bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-xl text-[var(--fg-0)] text-center focus:outline-none focus:border-${token.themeColor}-500`}
            />
          </div>
        </div>

        {/* MBTI & Blood Type */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-xs font-bold text-[var(--fg-muted)] uppercase">
              {labels.mbti}
            </label>
            <input
              type="text"
              placeholder={labels.mbtiPlaceholder}
              maxLength={4}
              value={birthInfo.mbti}
              onChange={e => setBirthInfo(prev => ({ ...prev, mbti: e.target.value }))}
              className={`w-full px-3 py-2.5 bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-xl text-[var(--fg-0)] text-center uppercase focus:outline-none focus:border-${token.themeColor}-500`}
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-bold text-[var(--fg-muted)] uppercase">
              {labels.bloodType}
            </label>
            <select
              value={birthInfo.bloodType}
              onChange={e => setBirthInfo(prev => ({ ...prev, bloodType: e.target.value }))}
              className={`w-full px-3 py-2.5 bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-xl text-[var(--fg-0)] focus:outline-none focus:border-${token.themeColor}-500`}
            >
              <option value="">{labels.select}</option>
              <option value="A">{labels.typeA}</option>
              <option value="B">{labels.typeB}</option>
              <option value="O">{labels.typeO}</option>
              <option value="AB">{labels.typeAB}</option>
            </select>
          </div>
        </div>

        {/* Buttons - React 19: Use isPending for combined state */}
        <div className="flex gap-3 pt-4">
          <button
            onClick={() => handleStartAnalysis(false)}
            disabled={isPending}
            className={`flex-1 py-3 bg-gradient-to-r from-${token.themeColor}-500 to-purple-600 hover:from-${token.themeColor}-600 hover:to-purple-700 text-[var(--fg-on-emphasis)] font-medium rounded-xl transition-all disabled:opacity-50 flex items-center justify-center gap-2`}
          >
            {isPending ? (
              <>
                <div className="w-4 h-4 border-2 rounded-full animate-spin spinner-on-emphasis" />
                {labels.analyzing}
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                {labels.startAnalysis}
              </>
            )}
          </button>
          <button
            onClick={() => handleStartAnalysis(true)}
            disabled={isPending}
            className="px-4 py-3 bg-[var(--surface-1)] hover:bg-[var(--surface-2)] text-[var(--fg-muted)] font-medium rounded-xl transition-all disabled:opacity-50 flex items-center gap-2"
            title={labels.quickStartTooltip}
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
            {labels.loadPreset(presets.length)}
          </button>
        )}

        {showPresetList && (
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {listPresets().map(p => (
              <button
                key={p.meta.id}
                onClick={() => handleResumePreset(p.meta.id)}
                className="w-full px-4 py-2 bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-lg text-left hover:bg-[var(--surface-2)] transition-all"
              >
                <div className="text-sm font-medium text-[var(--fg-0)]">
                  {p.persona?.archetype as string || labels.persona}
                </div>
                <div className="text-xs text-[var(--fg-muted)]">
                  {Math.round(p.meta.completion_rate)}% • {new Date(p.meta.created_at).toLocaleDateString()}
                </div>
              </button>
            ))}
          </div>
        )}

        {error && (
          <div className="p-3 rounded-lg event-bg-error event-border-error event-tone-error text-sm">
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
      <div className="flex-1 flex flex-col overflow-hidden border-r border-[var(--border-subtle)]">
        {/* Progress Bar */}
        <div className="flex-shrink-0 px-6 py-3 border-b border-[var(--border-subtle)] bg-[var(--surface-1)]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-[var(--fg-muted)] uppercase">
              {STAGE_LABELS[currentStage] || currentStage}
            </span>
            <span className={`text-xs font-mono text-${token.themeColor}-600 dark:text-${token.themeColor}-400`}>
              {Math.round(completionRate)}%
            </span>
          </div>
          <div className="h-1.5 bg-[var(--surface-2)] rounded-full overflow-hidden">
            <div
              className={`h-full bg-gradient-to-r from-${token.themeColor}-500 to-purple-500 rounded-full transition-all duration-500`}
              style={{ width: `${completionRate}%` }}
            />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-[10px] text-[var(--fg-subtle)]">
              {messages.filter(m => m.role === "user").length} {labels.answers}
            </span>
            <span className="text-[10px] text-[var(--fg-subtle)]">
              {traces.length} {labels.traces}
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
              <div className="max-w-[var(--layout-bubble-max)] space-y-2">
                <div className={`p-4 rounded-2xl ${msg.isCrisis
                  ? "bg-red-500/20 border-2 border-red-500/50"
                  : msg.role === "user"
                    ? `bg-${token.themeColor}-500/20 border border-${token.themeColor}-500/30`
                    : "bg-[var(--surface-1)] border border-[var(--border-subtle)]"
                  }`}>
                  {msg.isCrisis && (
                    <div className="flex items-center gap-2 mb-2 text-red-400">
                      <AlertTriangle className="w-4 h-4" />
                      <span className="text-xs font-medium">{labels.safetyAlert}</span>
                    </div>
                  )}
                  <p className={`text-sm leading-relaxed whitespace-pre-wrap ${msg.isCrisis ? "text-red-50" : "text-[var(--fg-0)]"}`}>
                    {msg.content}
                  </p>
                  {msg.isCrisis && (
                    <a
                      href="https://www.mentalhealth.go.kr"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block mt-3 text-sm text-red-300 hover:text-red-200 underline"
                    >
                      {labels.counselingLink} →
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
                <div className="w-8 h-8 rounded-full bg-[var(--surface-2)] border border-[var(--border-subtle)] flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-[var(--fg-muted)]" />
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
              <div className="flex-1 max-w-[var(--layout-bubble-max-narrow)] p-4 bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-2xl">
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
          <div className="flex-shrink-0 p-4 border-t border-[var(--border-subtle)] bg-[var(--surface-1)] backdrop-blur-md">
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
                placeholder={labels.inputPlaceholder}
                disabled={isPending}
                className={`flex-1 px-4 py-3 bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-xl text-[var(--fg-0)] placeholder:text-[var(--fg-subtle)] focus:outline-none focus:border-${token.themeColor}-500 transition-all disabled:opacity-50`}
              />
              <button
                onClick={handleSendMessage}
                disabled={isPending || !inputMessage.trim()}
                className={`px-6 py-3 bg-${token.themeColor}-500 hover:bg-${token.themeColor}-600 disabled:bg-[var(--surface-2)] text-[var(--fg-on-emphasis)] disabled:text-[var(--fg-subtle)] rounded-xl transition-all`}
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}

        {/* Complete State */}
        {phase === "complete" && (
          <div className={`flex-shrink-0 p-6 border-t border-[var(--border-subtle)] bg-gradient-to-r from-${token.themeColor}-500/10 to-purple-500/10`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Sparkles className={`w-6 h-6 text-${token.themeColor}-600 dark:text-${token.themeColor}-400`} />
                <span className="font-bold text-[var(--fg-0)]">{labels.analysisComplete}</span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleExportJson}
                  className="px-4 py-2 bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-lg flex items-center gap-2 text-sm hover:bg-[var(--surface-2)] transition-all"
                >
                  <Download className="w-4 h-4" />
                  {labels.exportJson}
                </button>
                <button
                  onClick={handleReset}
                  className={`px-4 py-2 bg-${token.themeColor}-500 hover:bg-${token.themeColor}-600 text-[var(--fg-on-emphasis)] rounded-lg flex items-center gap-2 text-sm transition-all`}
                >
                  <RefreshCw className="w-4 h-4" />
                  {labels.newSession}
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
      <div className="w-[var(--layout-sidebar-width)] flex-shrink-0 hidden xl:block">
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
      <DimensionPanel.Header title={labels.title} />

      <div className="flex flex-1 min-h-0">
        <DimensionPanel.Sidebar>
          {phase !== "input" && (
            <button
              onClick={handleReset}
              className="flex items-center gap-2 text-sm text-[var(--fg-muted)] hover:text-[var(--fg-0)] mb-4"
            >
              <ArrowLeft className="w-4 h-4" />
              {labels.goBack}
            </button>
          )}

          {/* Model Select */}
          <DimensionPanel.Select
            label={labels.aiModel}
            value={model}
            onChange={(e) => setModel(e.target.value)}
            options={MODELS}
            disabled={phase !== "input"}
          />

          {/* File Upload (Input phase only) */}
          {phase === "input" && (
            <DimensionPanel.FileUpload
              accept={["*"]}
              maxSizeMB={100}
              multiple
              onUpload={setFiles}
              label={labels.inspirationImage}
              helperText={labels.inspirationHelperText}
            />
          )}

          {/* Trace History */}
          {traces.length > 0 && (
            <div className="space-y-2 mt-6">
              <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest">
                {labels.traceHistory}
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
                    className={`w-full px-3 py-2 bg-[var(--surface-1)] rounded-lg text-xs hover:bg-${token.themeColor}-500/10 transition-colors cursor-pointer text-left`}
                  >
                    <div className="flex justify-between">
                      <span className={`text-${token.themeColor}-600 dark:text-${token.themeColor}-400 font-mono`}>
                        {t.trace_id.slice(0, 8)}...
                      </span>
                      <span className="text-[var(--fg-subtle)]">
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
              <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest">
                {labels.historyManagement}
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
                    {labels.previousSession}
                  </button>
                )}
                <button
                  onClick={() => {
                    if (confirm(labels.confirmReset)) {
                      clearLocal();
                      handleReset();
                    }
                  }}
                  className="flex-1 px-3 py-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-lg text-xs text-red-500 dark:text-red-400 transition-colors"
                >
                  {labels.reset}
                </button>
              </div>
              {presets.length > 1 && (
                <p className="text-[10px] text-[var(--fg-subtle)]">
                  {labels.savedSessions(presets.length)}
                </p>
              )}
            </div>
          )}

          {error && (
            <div className="mt-4 p-3 rounded-lg event-bg-error event-border-error event-tone-error text-xs">
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
