"use client";

/**
 * PromptGeneratorPanel - 1D Prompt Generation
 *
 * 2026 Golden App: React 19 Best Practices
 *
 * Features:
 * - useTransition for non-blocking form submission
 * - useOptimistic for instant UI feedback
 * - Skeleton loading with smooth transitions
 * - Evidence refs display
 *
 * @see docs/PANEL_DESIGN_UNITY_SPEC.md
 * @see https://react.dev/blog/2024/12/05/react-19
 */

import { useState, useCallback, useEffect, useTransition, useOptimistic } from "react";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import {
  useDimensionChainOptional,
  type ChainData,
} from "@/contexts/DimensionChainContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import ChainDataInput from "./ChainDataInput";
import { type EvidenceRef } from "./EvidenceDisplay";
import { type ThemeColor as DimensionThemeColor } from "@/lib/dimension-theme";

// =============================================================================
// CONSTANTS
// =============================================================================

const DIMENSION_CODE = "1d" as const;
const DIMENSION_KEY = "prompt-alchemy"; // Chain context key
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

// Map tokens.ts ThemeColor to dimension-theme.ts ThemeColor for ChainDataInput
const CHAIN_INPUT_THEME_MAP: Record<string, DimensionThemeColor> = {
  violet: "violet",
  cyan: "cyan",
  emerald: "emerald",
  amber: "amber",
  rose: "rose",
  fuchsia: "fuchsia",
  indigo: "indigo",
  sky: "sky",
  purple: "violet",
  red: "rose",
};

// =============================================================================
// TYPES
// =============================================================================

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
  evidence_refs?: EvidenceRef[];
  confidence?: number;
}

// =============================================================================
// OPTIONS
// =============================================================================

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
  { value: "gemini-3-flash-preview", label: "Flash (빠름)" },
  { value: "gemini-3-pro-preview", label: "Pro (고품질)" },
];

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function PromptGeneratorPanel() {
  return (
    <DimensionPanel dimensionCode={DIMENSION_CODE}>
      <PromptGeneratorContent />
    </DimensionPanel>
  );
}

// =============================================================================
// CONTENT COMPONENT (has access to DimensionPanel context)
// =============================================================================

function PromptGeneratorContent() {
  // Context
  const { token, classes, setLoading, setError, setResult } = useDimensionPanel();
  const chainCtx = useDimensionChainOptional();

  // Form state
  const [topic, setTopic] = useState("");
  const [style, setStyle] = useState("cinematic");
  const [mood, setMood] = useState("neutral");
  const [duration, setDuration] = useState("15 seconds");
  const [language, setLanguage] = useState<"ko" | "en">("ko");
  const [model, setModel] = useState("gemini-3-flash-preview");
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Set current dimension on mount
  useEffect(() => {
    if (chainCtx) {
      chainCtx.setCurrentDimension(DIMENSION_KEY);
    }
  }, [chainCtx]);

  // React 19: useTransition for non-blocking form submission
  const [isTransitionPending, startTransition] = useTransition();

  // React 19: useOptimistic for instant UI feedback
  const [optimisticResult, setOptimisticResult] = useOptimistic<PromptResult | null>(null);

  // File upload state (2026 Best Practice: Multimodal input)
  const [_uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  // BYOK and credits
  const { byokKey } = useBYOK();
  const creditCtx = useCreditContextOptional();
  const { getToolByDimension } = useDimensionConfig();
  const toolConfig = getToolByDimension("1D");
  const CREDIT_COST = toolConfig?.creditCost ?? 5;

  // Export utilities
  const { copyToClipboard, isCopied, exportJSON } = useResultExport();

  // Async operation hook
  const {
    isLoading,
    error,
    data: result,
    execute,
    retry,
  } = useAsyncOperation<{ success: boolean; output: PromptResult; error?: string }>({
    onSuccess: (data) => {
      if (data.success) {
        setResult(data.output);

        // Store in chain context for downstream dimensions
        if (chainCtx) {
          chainCtx.setChainData(
            DIMENSION_KEY,
            data.output as unknown as Record<string, unknown>,
            data.output.prompt?.slice(0, 50) || topic.slice(0, 50)
          );
        }

        if (!byokKey && creditCtx) {
          void creditCtx.refresh();
        }
      }
    },
    onError: (err) => {
      setError(err);
      if (err.message.includes("크레딧") || err.message.includes("402")) {
        setShowCreditModal(true);
      }
    },
    retryCount: 3,
    retryDelay: 1000,
    nonRetryableErrors: ["400", "401", "402", "403", "404", "크레딧", "부족"],
  });

  // Combined loading state (include transition pending for 2026 UX)
  const combinedLoading = isLoading || isTransitionPending;
  const MAX_TOPIC_LENGTH = 500;

  const handleGenerate = useCallback(async () => {
    const trimmedTopic = topic.trim();
    if (!trimmedTopic) {
      setValidationError("주제를 입력해주세요");
      return;
    }
    if (trimmedTopic.length > MAX_TOPIC_LENGTH) {
      setValidationError(`주제는 ${MAX_TOPIC_LENGTH}자 이하로 입력해주세요`);
      return;
    }
    setValidationError(null);
    setError(null);
    setResult(null);

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
      setShowCreditModal(true);
      return;
    }

    setLoading(true);

    // React 19: Optimistic UI - show skeleton result immediately
    startTransition(() => {
      setOptimisticResult({
        prompt: "프롬프트 생성 중...",
        style: {
          cinematography: "분석 중...",
          lighting: "분석 중...",
          color_grade: "분석 중...",
        },
        technical: {
          aspect_ratio: duration.includes("5") ? "9:16" : "16:9",
          duration,
          fps: "24",
        },
      });
    });

    try {
      await execute(
        `${API_BASE}/api/dimension/1d/generate`,
        { topic, style, mood, duration, language, model },
        getBYOKHeaders(byokKey)
      );
    } finally {
      setLoading(false);
      // Clear optimistic result after real result arrives
      startTransition(() => {
        setOptimisticResult(null);
      });
    }
  }, [topic, style, mood, duration, language, model, byokKey, creditCtx, execute, setLoading, setError, setResult, CREDIT_COST, startTransition, setOptimisticResult]);

  const handleCopy = useCallback((text: string) => {
    copyToClipboard(text);
  }, [copyToClipboard]);

  // Handle chain data from previous dimensions (story-architect, storyboard-sketch)
  const handleApplyChainData = useCallback((data: Record<string, ChainData>) => {
    // From story-architect: get logline or synopsis as topic hint
    if (data["story-architect"]?.output?.logline && !topic) {
      setTopic(data["story-architect"].output.logline as string);
    } else if (data["story-architect"]?.output?.synopsis && !topic) {
      setTopic((data["story-architect"].output.synopsis as string).slice(0, 500));
    }

    // From storyboard-sketch: get scene descriptions as topic hint
    if (data["storyboard-sketch"]?.output?.scenes && !topic) {
      const scenes = data["storyboard-sketch"].output.scenes as Array<{ description: string }>;
      if (scenes.length > 0) {
        setTopic(scenes.map(s => s.description).join("\n").slice(0, 500));
      }
    }

    // From aesthetic-director: get mood and style hints
    if (data["aesthetic-director"]?.output?.mood) {
      const adMood = data["aesthetic-director"].output.mood as string;
      const moodMap: Record<string, string> = {
        dramatic: "dramatic",
        calm: "calm",
        energetic: "energetic",
        melancholic: "melancholic",
      };
      if (moodMap[adMood.toLowerCase()]) {
        setMood(moodMap[adMood.toLowerCase()]);
      }
    }
  }, [topic]);

  const handleExportJSON = useCallback(() => {
    if (result?.output) {
      exportJSON(result.output, `veo-prompt-${Date.now()}.json`);
    }
  }, [result?.output, exportJSON]);

  // Display either optimistic result or actual result
  const displayResult = optimisticResult || (result?.success ? result.output : null);
  const isOptimistic = !!optimisticResult && !result?.success;

  return (
    <>
      {/* Header */}
      <DimensionPanel.Header
        title="Veo 프롬프트 생성"
        titleKo="1D Prompt Alchemy"
        creditCost={CREDIT_COST}
      />

      {/* Sidebar */}
      <DimensionPanel.Sidebar>
        {/* Chain Data Input - data from story-architect, storyboard-sketch */}
        <ChainDataInput
          currentDimension={DIMENSION_KEY}
          onApplyData={handleApplyChainData}
          themeColor={CHAIN_INPUT_THEME_MAP[token.themeColor] || "violet"}
        />

        {/* Topic Textarea */}
        <DimensionPanel.Textarea
          label="주제 (Topic)"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="영상의 핵심 주제를 입력하세요..."
          maxLength={MAX_TOPIC_LENGTH}
          showCount
          error={validationError || undefined}
          disabled={combinedLoading}
        />

        {/* File Upload (2026 Best Practice: Multimodal Input) */}
        <DimensionPanel.FileUpload
          accept={["*"]}
          maxSizeMB={100}
          multiple
          onUpload={setUploadedFiles}
          label="참고 자료 (선택)"
          helperText="이미지, 영상, PDF를 첨부하면 더 정확한 프롬프트 생성"
        />

        {/* Style & Mood */}
        <div className="grid grid-cols-2 gap-3">
          <DimensionPanel.Select
            label="스타일"
            value={style}
            onChange={(e) => setStyle(e.target.value)}
            options={STYLES}
            disabled={combinedLoading}
          />
          <DimensionPanel.Select
            label="무드"
            value={mood}
            onChange={(e) => setMood(e.target.value)}
            options={MOODS}
            disabled={combinedLoading}
          />
        </div>

        {/* Duration & Language */}
        <div className="grid grid-cols-2 gap-3">
          <DimensionPanel.Select
            label="길이"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            options={DURATIONS}
            disabled={combinedLoading}
          />
          <div className="space-y-2">
            <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">
              언어
            </label>
            <div className="flex bg-slate-100 dark:bg-white/5 rounded-lg p-0.5 border border-slate-200 dark:border-white/10">
              <button
                onClick={() => setLanguage("ko")}
                disabled={combinedLoading}
                className={`flex-1 py-2.5 rounded-md text-xs font-medium transition-all ${
                  language === "ko"
                    ? `${classes.bg} text-white shadow-sm`
                    : "text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/5"
                } disabled:opacity-50`}
              >
                KO
              </button>
              <button
                onClick={() => setLanguage("en")}
                disabled={combinedLoading}
                className={`flex-1 py-2.5 rounded-md text-xs font-medium transition-all ${
                  language === "en"
                    ? `${classes.bg} text-white shadow-sm`
                    : "text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/5"
                } disabled:opacity-50`}
              >
                EN
              </button>
            </div>
          </div>
        </div>

        {/* Model Select */}
        <div className="pt-4 border-t border-slate-200 dark:border-white/5 mt-4">
          <DimensionPanel.Select
            label="AI 모델 Engine"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            options={MODELS}
            disabled={combinedLoading}
          />
        </div>

        {/* Generate Button */}
        <DimensionPanel.GenerateButton
          onClick={handleGenerate}
          loading={combinedLoading}
          disabled={!topic.trim()}
          className="mt-6"
        >
          Generate Prompt
        </DimensionPanel.GenerateButton>
      </DimensionPanel.Sidebar>

      {/* Content */}
      <DimensionPanel.Content>
        {/* Loading State */}
        <DimensionPanel.Loading message="프롬프트 생성 중..." />

        {/* Error State */}
        <DimensionPanel.Error onRetry={retry} />

        {/* Result */}
        {displayResult ? (
          <div className={`max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10 ${isOptimistic ? "opacity-70" : ""}`}>
            {/* Optimistic Loading Indicator (React 19 Best Practice) */}
            {isOptimistic && (
              <div className="flex items-center justify-center gap-2 py-2 px-4 bg-violet-500/10 rounded-lg border border-violet-500/20">
                <div className="w-3 h-3 rounded-full bg-violet-500 animate-pulse" />
                <span className="text-sm text-violet-600 dark:text-violet-300">
                  프롬프트 생성 중...
                </span>
              </div>
            )}

            {/* Main Prompt Card */}
            <DimensionPanel.Result forceShow>
              <div className="space-y-4">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${classes.bg} ${isOptimistic ? "animate-pulse" : ""}`} />
                    <span className="text-xs font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest">
                      {isOptimistic ? "Generating..." : "Generated Prompt"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleExportJSON}
                      className="px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-200 dark:border-white/5"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      Export
                    </button>
                    <button
                      onClick={() => handleCopy(displayResult.prompt)}
                      className={`p-2 rounded-lg bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-zinc-400 hover:${classes.bgSubtle} hover:${classes.text} transition-all`}
                    >
                      {isCopied ? (
                        <span className="text-green-500 font-bold text-xs">COPIED</span>
                      ) : (
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      )}
                    </button>
                  </div>
                </div>

                {/* Prompt Content */}
                <div className="bg-slate-50 dark:bg-black/50 rounded-xl p-4 border border-slate-100 dark:border-white/5 font-mono text-sm leading-relaxed text-slate-700 dark:text-white/90">
                  {displayResult.prompt}
                </div>

                {/* Negative Prompt */}
                {displayResult.negative_prompt && (
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-red-500 dark:text-red-400 uppercase tracking-wider">
                      Negative
                    </span>
                    <div className="bg-red-50 dark:bg-red-500/5 rounded-xl p-3 border border-red-100 dark:border-red-500/10 font-mono text-xs leading-relaxed text-red-600 dark:text-red-200/70">
                      {displayResult.negative_prompt}
                    </div>
                  </div>
                )}

                {/* Technical Details */}
                {displayResult.technical && (
                  <div className="grid grid-cols-2 gap-3 pt-4 border-t border-slate-100 dark:border-white/5">
                    {Object.entries(displayResult.technical).map(([key, value]) => (
                      <div
                        key={key}
                        className="bg-slate-50 dark:bg-white/5 rounded-lg p-2 text-center border border-slate-100 dark:border-white/5"
                      >
                        <span className="text-[10px] text-slate-400 dark:text-zinc-500 block mb-1 uppercase">
                          {key}
                        </span>
                        <span className={`text-xs ${classes.text} font-medium`}>
                          {value as string}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </DimensionPanel.Result>

            {/* Evidence */}
            <DimensionPanel.Evidence
              refs={displayResult.evidence_refs}
              confidence={displayResult.confidence}
            />

            {/* Next Navigation */}
            <DimensionPanel.NextNav />
          </div>
        ) : !isLoading && !error && (
          /* Empty State */
          <div className="flex flex-col items-center justify-center h-full text-slate-500 dark:text-zinc-500 space-y-8 animate-in fade-in zoom-in-95 duration-700">
            <div className="relative group">
              <div className={`absolute inset-0 ${classes.bg}/20 blur-[80px] rounded-full group-hover:${classes.bg}/30 transition-colors duration-1000`} />
              <div className="w-32 h-32 rounded-[2rem] bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex items-center justify-center shadow-lg dark:shadow-[0_0_60px_rgba(0,0,0,0.3)] backdrop-blur-md relative transform group-hover:scale-105 transition-all duration-500">
                <svg
                  className={`w-12 h-12 text-slate-300 dark:text-white/20 group-hover:${classes.text} transition-colors duration-500`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1}
                    d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                  />
                </svg>
              </div>
            </div>
            <div className="text-center space-y-3">
              <h3 className="text-2xl font-bold text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-b dark:from-white dark:to-white/40 tracking-tight">
                Ready to Generate
              </h3>
              <p className="text-sm text-slate-500 dark:text-zinc-500 max-w-xs mx-auto font-light leading-relaxed">
                상상을 현실로 만드는 프롬프트.
                <br />
                <span className={`${classes.text} font-medium`}>최적화된 AI 프롬프트</span>를 생성해보세요.
              </p>
            </div>
          </div>
        )}
      </DimensionPanel.Content>

      {/* Credit Modal */}
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
