"use client";

/**
 * PromptAlchemyPanel - AI Video Platform Prompt Translator
 *
 * 2026 Golden App: React 19 Best Practices
 *
 * Features:
 * - Translates scene descriptions to platform-specific prompts
 * - Supports 3 AI video platforms: Veo 3.1, Kling 2.6, Sora Max 2 Pro
 * - Auto-selection based on content analysis
 * - Batch translation to all platforms
 * - UQSL multi-candidate generation
 * - useTransition for non-blocking form submission
 * - useOptimistic for instant UI feedback
 *
 * @see docs/PANEL_DESIGN_UNITY_SPEC.md
 * @see https://react.dev/blog/2024/12/05/react-19
 */

import { useState, useEffect, useCallback, useTransition, useOptimistic, useMemo } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";
import { useChainDataInjection } from "@/hooks/useChainDataInjection";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import ChainDataInput from "./ChainDataInput";
import { type EvidenceRef } from "./EvidenceDisplay";
import { Sparkles } from "lucide-react";
import { type ThemeColor as DimensionThemeColor } from "@/lib/dimension-theme";

// =============================================================================
// CONSTANTS
// =============================================================================

const DIMENSION_CODE = "1d" as const;
const DIMENSION_KEY = "prompt-alchemy";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";
const CREDIT_COST = 5;

// Map tokens ThemeColor to dimension-theme ThemeColor
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

/** AI Video Platform Definition */
interface PlatformInfo {
  id: string;
  name: string;
  nameShort: string;
  useCase: string;
  maxDuration: number;
  nativeAudio: boolean;
  recommended?: boolean;
  icon: string;
  gradient: string;
}

/** Translation Result */
interface TranslationResult {
  translated_prompt: string;
  quality_score: number;
  platform_tips?: string[];
  style_analysis?: {
    cinematography?: string;
    lighting?: string;
    color_grade?: string;
    mood?: string;
  };
  evidence_refs?: EvidenceRef[];
}

/** API Response */
interface TranslateResponse {
  success: boolean;
  output: {
    translated_prompt: string;
    quality_score: number;
    target_platform: string;
    platform_name: string;
    native_audio: boolean;
    platform_tips?: string[];
  };
  metrics?: {
    platform: string;
    latency_ms: number;
  };
  error?: string;
}

/** Batch Response */
interface BatchResponse {
  success: boolean;
  translations: Array<{
    platform: string;
    platform_name: string;
    result: TranslateResponse;
  }>;
  errors?: string[];
  total_platforms: number;
  successful_platforms: number;
}

// =============================================================================
// PLATFORM DEFINITIONS
// =============================================================================

const PLATFORMS: PlatformInfo[] = [
  {
    id: "veo_31",
    name: "Google Veo 3.1",
    nameShort: "Veo 3.1",
    useCase: "Dialogue & Narration viral videos",
    maxDuration: 8,
    nativeAudio: true,
    icon: "M",
    gradient: "from-blue-500 to-cyan-500",
  },
  {
    id: "kling_26",
    name: "Kling 2.6",
    nameShort: "Kling 2.6",
    useCase: "High-quality silent cinematic videos",
    maxDuration: 120,
    nativeAudio: false,
    recommended: true,
    icon: "K",
    gradient: "from-violet-500 to-purple-500",
  },
  {
    id: "sora_max_2pro",
    name: "Sora Max 2 Pro",
    nameShort: "Sora Max",
    useCase: "Animation style videos",
    maxDuration: 20,
    nativeAudio: true,
    icon: "S",
    gradient: "from-rose-500 to-pink-500",
  },
];

const STYLES = [
  { value: "cinematic", label: "Cinematic" },
  { value: "documentary", label: "Documentary" },
  { value: "commercial", label: "Commercial" },
  { value: "artistic", label: "Artistic" },
  { value: "anime", label: "Anime" },
  { value: "realistic", label: "Realistic" },
];

const getModels = (isKo: boolean) => [
  { value: "gemini-3-flash-preview", label: isKo ? "Flash (빠름)" : "Flash (Fast)" },
  { value: "gemini-3-pro-preview", label: isKo ? "Pro (고품질)" : "Pro (High Quality)" },
];

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function PromptAlchemyPanel() {
  return (
    <DimensionPanel dimensionCode={DIMENSION_CODE}>
      <PromptAlchemyContent />
    </DimensionPanel>
  );
}

// =============================================================================
// CONTENT COMPONENT
// =============================================================================

function PromptAlchemyContent() {
  const { token, classes, styles: _styles, setLoading, setError, setResult } = useDimensionPanel();
  const { language: appLanguage } = useLanguage();
  const isKo = appLanguage === "ko";

  // Chain context for storing output
  const chainCtx = useDimensionChainOptional();

  // Chain data injection for upstream data (Story→Production flow)
  const { logicVector: _logicVector, hasUpstreamData, rawInputData: _rawInputData, evidenceRefs } =
    useChainDataInjection(DIMENSION_KEY);

  // Set current dimension when mounted
  useEffect(() => {
    if (chainCtx) {
      chainCtx.setCurrentDimension(DIMENSION_KEY);
    }
  }, [chainCtx]);

  // Model options with i18n
  const MODELS = useMemo(() => getModels(isKo), [isKo]);

  // Form state
  const [sceneDescription, setSceneDescription] = useState("");
  const [targetPlatform, setTargetPlatform] = useState<string | null>(null); // null = auto
  const [style, setStyle] = useState("cinematic");
  const [duration, setDuration] = useState<number>(15);
  const [language, setLanguage] = useState<"ko" | "en">("ko");
  const [model, setModel] = useState("gemini-3-flash-preview");
  const [_files, setFiles] = useState<File[]>([]);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [mode, setMode] = useState<"single" | "batch">("single");

  // React 19: useTransition for non-blocking form submission
  const [isTransitionPending, startTransition] = useTransition();

  // React 19: useOptimistic for instant UI feedback
  const [optimisticResult, setOptimisticResult] = useOptimistic<TranslationResult | null>(null);

  // BYOK and credits
  const { byokKey } = useBYOK();
  const creditCtx = useCreditContextOptional();

  // Export utilities
  const { copyToClipboard, isCopied, exportJSON } = useResultExport();

  // Async operation hook
  const {
    isLoading,
    progress: _progress,
    error,
    data: result,
    execute,
    cancel: _cancel,
    retry,
    canRetry: _canRetry,
    currentRetryCount: _currentRetryCount,
  } = useAsyncOperation<TranslateResponse | BatchResponse>({
    onSuccess: (data) => {
      if (data.success) {
        setResult(data);

        // Store in chain context for downstream dimensions
        if (chainCtx && "output" in data) {
          const outputRefs = (data.output as { evidence_refs?: EvidenceRef[] }).evidence_refs?.map((ref) => ref.ref_id) || [];
          chainCtx.setChainData(
            DIMENSION_KEY,
            data.output as unknown as Record<string, unknown>,
            data.output.translated_prompt?.slice(0, 50) || "Prompt translated",
            outputRefs.length > 0 ? outputRefs : evidenceRefs
          );
        }

        if (!byokKey && creditCtx) {
          void creditCtx.refresh();
        }
      }
    },
    onError: (err) => {
      setError(err);
      if (err.message.includes("Credit") || err.message.includes("402")) {
        setShowCreditModal(true);
      }
    },
    retryCount: 3,
    retryDelay: 1000,
    nonRetryableErrors: ["400", "401", "402", "403", "404", "credit"],
  });

  const combinedLoading = isLoading || isTransitionPending;
  const MAX_DESCRIPTION_LENGTH = 2000;

  // Get auto-selected platform hint
  const getAutoSelectHint = useCallback((text: string): string => {
    const lowerText = text.toLowerCase();
    if (
      lowerText.includes("dialogue") ||
      lowerText.includes("narration") ||
      lowerText.includes("speech") ||
      lowerText.includes("talk") ||
      lowerText.includes("conversation")
    ) {
      return "veo_31";
    }
    if (
      lowerText.includes("anime") ||
      lowerText.includes("animation") ||
      lowerText.includes("cartoon") ||
      lowerText.includes("animated")
    ) {
      return "sora_max_2pro";
    }
    return "kling_26";
  }, []);

  const predictedPlatform = targetPlatform || getAutoSelectHint(sceneDescription);

  const handleTranslate = useCallback(async () => {
    const trimmedDescription = sceneDescription.trim();
    if (!trimmedDescription) {
      setValidationError("Please enter a scene description");
      return;
    }
    if (trimmedDescription.length < 10) {
      setValidationError("Description must be at least 10 characters");
      return;
    }
    if (trimmedDescription.length > MAX_DESCRIPTION_LENGTH) {
      setValidationError(`Description must be less than ${MAX_DESCRIPTION_LENGTH} characters`);
      return;
    }
    setValidationError(null);
    setError(null);
    setResult(null);

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST * (mode === "batch" ? 3 : 1))) {
      setShowCreditModal(true);
      return;
    }

    setLoading(true);

    // React 19: Optimistic UI
    startTransition(() => {
      setOptimisticResult({
        translated_prompt: "Translating...",
        quality_score: 0,
        style_analysis: {
          cinematography: "Analyzing...",
          lighting: "Analyzing...",
          color_grade: "Analyzing...",
          mood: "Analyzing...",
        },
      });
    });

    try {
      const endpoint = mode === "batch"
        ? `${API_BASE}/api/dimension/prompt/translate/batch`
        : `${API_BASE}/api/dimension/prompt/translate`;

      const payload = mode === "batch"
        ? {
            scene_description: trimmedDescription,
            target_platforms: PLATFORMS.map((p) => p.id),
            style,
            language,
            model,
          }
        : {
            scene_description: trimmedDescription,
            target_platform: targetPlatform,
            style,
            duration,
            language,
            model,
          };

      await execute(endpoint, payload, getBYOKHeaders(byokKey));
    } finally {
      setLoading(false);
      startTransition(() => {
        setOptimisticResult(null);
      });
    }
  }, [
    sceneDescription,
    targetPlatform,
    style,
    duration,
    language,
    model,
    mode,
    byokKey,
    creditCtx,
    execute,
    setLoading,
    setError,
    setResult,
    startTransition,
    setOptimisticResult,
  ]);

  const handleCopy = useCallback(
    (text: string) => {
      copyToClipboard(text);
    },
    [copyToClipboard]
  );

  const handleExportJSON = useCallback(() => {
    if (result) {
      exportJSON(result, `prompt-alchemy-${Date.now()}.json`);
    }
  }, [result, exportJSON]);

  // Display logic
  const isBatchResult = result && "translations" in result;
  const singleResult = result && "output" in result ? (result as TranslateResponse) : null;
  const batchResult = result as BatchResponse | null;

  const displayResult = optimisticResult || (singleResult?.success ? singleResult.output : null);
  const isOptimistic = !!optimisticResult && !singleResult?.success;

  return (
    <>
      {/* Header */}
      <DimensionPanel.Header
        title="Prompt Alchemy"
        titleKo="AI Video Prompt Translator"
        creditCost={CREDIT_COST}
      />

      {/* Sidebar */}
      <DimensionPanel.Sidebar>
        {/* Chain Data Input - data from story-architect, reference-decoder */}
        <ChainDataInput
          currentDimension={DIMENSION_KEY}
          themeColor={CHAIN_INPUT_THEME_MAP[token.themeColor] || "violet"}
        />

        {/* Upstream Data Banner */}
        {hasUpstreamData && !combinedLoading && !result && (
          <div className="mb-4 p-3 bg-violet-500/10 border border-violet-500/20 rounded-lg">
            <div className="flex items-center gap-2 text-sm text-violet-600 dark:text-violet-400">
              <Sparkles className="w-4 h-4" />
              <span>이전 단계 데이터가 자동 적용됩니다</span>
            </div>
          </div>
        )}

        {/* Mode Toggle */}
        <div className="space-y-2" role="radiogroup" aria-label="Translation mode">
          <label
            id="mode-label"
            className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1"
          >
            Mode
          </label>
          <div className="flex bg-slate-100 dark:bg-white/5 rounded-lg p-0.5 border border-slate-200 dark:border-white/10">
            <button
              onClick={() => setMode("single")}
              disabled={combinedLoading}
              role="radio"
              aria-checked={mode === "single"}
              aria-label="Single platform translation"
              className={`flex-1 py-2.5 rounded-md text-xs font-medium transition-all ${
                mode === "single"
                  ? `${classes.bg} text-white shadow-sm`
                  : "text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white"
              } disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-violet-500/50`}
            >
              Single
            </button>
            <button
              onClick={() => setMode("batch")}
              disabled={combinedLoading}
              role="radio"
              aria-checked={mode === "batch"}
              aria-label="Batch translation to all 3 platforms"
              className={`flex-1 py-2.5 rounded-md text-xs font-medium transition-all ${
                mode === "batch"
                  ? `${classes.bg} text-white shadow-sm`
                  : "text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white"
              } disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-violet-500/50`}
            >
              Batch (All 3)
            </button>
          </div>
        </div>

        {/* Scene Description */}
        <DimensionPanel.Textarea
          label="Scene Description"
          value={sceneDescription}
          onChange={(e) => setSceneDescription(e.target.value)}
          placeholder="Describe your video scene in detail...&#10;&#10;Example: A cinematic shot of waves crashing against rocks at golden hour, with seagulls flying overhead"
          maxLength={MAX_DESCRIPTION_LENGTH}
          showCount
          error={validationError || undefined}
          disabled={combinedLoading}
          rows={6}
        />

        {/* File Upload */}
        <DimensionPanel.FileUpload
          accept={["*"]}
          maxSizeMB={100}
          multiple
          onUpload={setFiles}
          label="참고 이미지 (선택)"
          helperText="스타일/분위기 참고 이미지 첨부"
        />

        {/* Platform Selection (Single Mode Only) */}
        {mode === "single" && (
          <div className="space-y-3" role="radiogroup" aria-label="Target AI video platform">
            <div className="flex items-center justify-between">
              <label
                id="platform-label"
                className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1"
              >
                Target Platform
              </label>
              <button
                onClick={() => setTargetPlatform(null)}
                aria-label="Enable auto-selection based on content"
                className={`text-[10px] px-2 py-0.5 rounded-full transition-all focus:outline-none focus:ring-2 focus:ring-violet-500/50 ${
                  targetPlatform === null
                    ? `${classes.bgSubtle} ${classes.text} font-medium`
                    : "text-slate-400 dark:text-zinc-600 hover:text-slate-600 dark:hover:text-zinc-400"
                }`}
              >
                Auto-select
              </button>
            </div>

            <div className="grid gap-2">
              {PLATFORMS.map((platform) => (
                <button
                  key={platform.id}
                  onClick={() => setTargetPlatform(platform.id)}
                  disabled={combinedLoading}
                  role="radio"
                  aria-checked={targetPlatform === platform.id}
                  aria-label={`${platform.name}: ${platform.useCase}${platform.recommended ? " (Recommended)" : ""}`}
                  className={`relative p-3 rounded-xl border transition-all text-left focus:outline-none focus:ring-2 focus:ring-violet-500/50 ${
                    targetPlatform === platform.id
                      ? `border-${DIMENSION_CODE === "1d" ? "violet" : "cyan"}-500/50 ${classes.bgSubtle}`
                      : targetPlatform === null && predictedPlatform === platform.id
                      ? "border-dashed border-violet-500/30 bg-violet-500/5"
                      : "border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/20"
                  } disabled:opacity-50`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-10 h-10 rounded-lg bg-gradient-to-br ${platform.gradient} flex items-center justify-center text-white font-bold text-sm shadow-lg`}
                    >
                      {platform.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-slate-800 dark:text-white">
                          {platform.nameShort}
                        </span>
                        {platform.recommended && (
                          <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-emerald-500/10 text-emerald-500 uppercase">
                            Recommended
                          </span>
                        )}
                        {platform.nativeAudio && (
                          <span className="px-1.5 py-0.5 text-[9px] rounded bg-blue-500/10 text-blue-500">
                            Audio
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-zinc-400 truncate">
                        {platform.useCase}
                      </p>
                    </div>
                  </div>
                  {targetPlatform === null && predictedPlatform === platform.id && (
                    <div className="absolute top-1 right-1 px-1.5 py-0.5 text-[9px] rounded bg-violet-500/20 text-violet-400">
                      Predicted
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Style & Duration */}
        <div className="grid grid-cols-2 gap-3">
          <DimensionPanel.Select
            label="Style"
            value={style}
            onChange={(e) => setStyle(e.target.value)}
            options={STYLES}
            disabled={combinedLoading}
          />
          {mode === "single" && (
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">
                Duration
              </label>
              <input
                type="number"
                min={1}
                max={120}
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                disabled={combinedLoading}
                className="w-full px-3 py-2.5 rounded-lg border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 text-slate-800 dark:text-white text-sm focus:outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20 disabled:opacity-50"
              />
            </div>
          )}
          {mode === "batch" && (
            <DimensionPanel.Select
              label="Language"
              value={language}
              onChange={(e) => setLanguage(e.target.value as "ko" | "en")}
              options={[
                { value: "ko", label: "Korean" },
                { value: "en", label: "English" },
              ]}
              disabled={combinedLoading}
            />
          )}
        </div>

        {/* Model Select */}
        <div className="pt-4 border-t border-slate-200 dark:border-white/5 mt-4">
          <DimensionPanel.Select
            label="AI Engine"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            options={MODELS}
            disabled={combinedLoading}
          />
        </div>

        {/* Generate Button */}
        <DimensionPanel.GenerateButton
          onClick={handleTranslate}
          loading={combinedLoading}
          disabled={!sceneDescription.trim()}
          className="mt-6"
        >
          {mode === "batch" ? "Translate All Platforms" : "Translate Prompt"}
        </DimensionPanel.GenerateButton>
      </DimensionPanel.Sidebar>

      {/* Content */}
      <DimensionPanel.Content>
        {/* Screen reader announcements */}
        <div className="sr-only" role="status" aria-live="polite">
          {combinedLoading && "Translating prompt, please wait..."}
          {error && `Error: ${error}`}
          {result && !isBatchResult && "Translation complete"}
          {isBatchResult && batchResult && `Batch translation complete. ${batchResult.successful_platforms} of ${batchResult.total_platforms} platforms successful.`}
        </div>

        {/* Loading State */}
        <DimensionPanel.Loading message="Translating to platform-optimized prompt..." />

        {/* Error State */}
        <DimensionPanel.Error onRetry={retry} />

        {/* Batch Results */}
        {isBatchResult && batchResult && (
          <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
            {/* Summary */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                  <svg className="w-5 h-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                    Batch Translation Complete
                  </p>
                  <p className="text-xs text-emerald-500/70">
                    {batchResult.successful_platforms}/{batchResult.total_platforms} platforms successful
                  </p>
                </div>
              </div>
              <button
                onClick={handleExportJSON}
                aria-label="Export all batch results as JSON"
                className="px-3 py-1.5 text-xs font-medium rounded-md bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/30 transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
              >
                Export All
              </button>
            </div>

            {/* Platform Results */}
            <div className="space-y-4">
              {batchResult.translations.map((translation) => {
                const platform = PLATFORMS.find((p) => p.id === translation.platform);
                if (!platform || !translation.result.success) return null;

                return (
                  <div
                    key={translation.platform}
                    className="p-5 rounded-2xl bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/10"
                  >
                    {/* Platform Header */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-8 h-8 rounded-lg bg-gradient-to-br ${platform.gradient} flex items-center justify-center text-white font-bold text-xs shadow-md`}
                        >
                          {platform.icon}
                        </div>
                        <div>
                          <span className="font-semibold text-sm text-slate-800 dark:text-white">
                            {platform.name}
                          </span>
                          {platform.nativeAudio && (
                            <span className="ml-2 px-1.5 py-0.5 text-[9px] rounded bg-blue-500/10 text-blue-500">
                              Native Audio
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-500 dark:text-zinc-500">
                          Quality: {(translation.result.output.quality_score * 100).toFixed(0)}%
                        </span>
                        <button
                          onClick={() => handleCopy(translation.result.output.translated_prompt)}
                          aria-label={`Copy ${platform.name} prompt to clipboard`}
                          className="p-1.5 rounded-md hover:bg-slate-100 dark:hover:bg-white/5 transition-colors focus:outline-none focus:ring-2 focus:ring-violet-500/50"
                        >
                          <svg
                            className="w-4 h-4 text-slate-500 dark:text-zinc-400"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            aria-hidden="true"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                            />
                          </svg>
                        </button>
                      </div>
                    </div>

                    {/* Prompt Content */}
                    <div className="bg-slate-50 dark:bg-black/50 rounded-xl p-4 border border-slate-100 dark:border-white/5 font-mono text-sm leading-relaxed text-slate-700 dark:text-white/90 whitespace-pre-wrap">
                      {translation.result.output.translated_prompt}
                    </div>

                    {/* Platform Tips */}
                    {translation.result.output.platform_tips && translation.result.output.platform_tips.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {translation.result.output.platform_tips.map((tip, i) => (
                          <span
                            key={i}
                            className="px-2 py-1 text-[10px] rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400"
                          >
                            {tip}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Single Result */}
        {!isBatchResult && displayResult && (
          <div
            className={`max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10 ${
              isOptimistic ? "opacity-70" : ""
            }`}
          >
            {/* Optimistic Loading Indicator */}
            {isOptimistic && (
              <div className="flex items-center justify-center gap-2 py-2 px-4 bg-violet-500/10 rounded-lg border border-violet-500/20">
                <div className="w-3 h-3 rounded-full bg-violet-500 animate-pulse" />
                <span className="text-sm text-violet-600 dark:text-violet-300">Translating prompt...</span>
              </div>
            )}

            {/* Main Result Card */}
            <DimensionPanel.Result forceShow>
              <div className="space-y-4">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${classes.bg} ${isOptimistic ? "animate-pulse" : ""}`} />
                    <span className="text-xs font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest">
                      {isOptimistic ? "Translating..." : "Translated Prompt"}
                    </span>
                    {singleResult?.output?.target_platform && (
                      <span className="px-2 py-0.5 text-[10px] rounded-full bg-violet-500/10 text-violet-600 dark:text-violet-400">
                        {PLATFORMS.find((p) => p.id === singleResult.output.target_platform)?.nameShort ||
                          singleResult.output.platform_name}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {singleResult?.output?.quality_score && (
                      <span className="text-xs text-slate-500 dark:text-zinc-500">
                        Quality: {(singleResult.output.quality_score * 100).toFixed(0)}%
                      </span>
                    )}
                    <button
                      onClick={handleExportJSON}
                      aria-label="Export result as JSON file"
                      className="px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-200 dark:border-white/5 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                        />
                      </svg>
                      Export
                    </button>
                    <button
                      onClick={() => handleCopy(displayResult.translated_prompt || singleResult?.output?.translated_prompt || "")}
                      aria-label={isCopied ? "Prompt copied to clipboard" : "Copy translated prompt to clipboard"}
                      className={`p-2 rounded-lg bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-zinc-400 hover:${classes.bgSubtle} hover:${classes.text} transition-all focus:outline-none focus:ring-2 focus:ring-violet-500/50`}
                    >
                      {isCopied ? (
                        <span className="text-green-500 font-bold text-xs" role="status">COPIED</span>
                      ) : (
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                          />
                        </svg>
                      )}
                    </button>
                  </div>
                </div>

                {/* Prompt Content */}
                <div className="bg-slate-50 dark:bg-black/50 rounded-xl p-4 border border-slate-100 dark:border-white/5 font-mono text-sm leading-relaxed text-slate-700 dark:text-white/90 whitespace-pre-wrap">
                  {displayResult.translated_prompt || singleResult?.output?.translated_prompt || ""}
                </div>

                {/* Platform Tips */}
                {singleResult?.output?.platform_tips && singleResult.output.platform_tips.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-[10px] font-bold text-amber-500 uppercase tracking-wider">Platform Tips</span>
                    <div className="flex flex-wrap gap-2">
                      {singleResult.output.platform_tips.map((tip, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 text-xs rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20"
                        >
                          {tip}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Style Analysis */}
                {'style_analysis' in displayResult && displayResult.style_analysis && (
                  <div className="grid grid-cols-2 gap-3 pt-4 border-t border-slate-100 dark:border-white/5">
                    {Object.entries(displayResult.style_analysis).map(([key, value]) => (
                      <div
                        key={key}
                        className="bg-slate-50 dark:bg-white/5 rounded-lg p-2 text-center border border-slate-100 dark:border-white/5"
                      >
                        <span className="text-[10px] text-slate-400 dark:text-zinc-500 block mb-1 uppercase">{key}</span>
                        <span className={`text-xs ${classes.text} font-medium`}>{value as string}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </DimensionPanel.Result>

            {/* Evidence */}
            <DimensionPanel.Evidence refs={'evidence_refs' in displayResult ? displayResult.evidence_refs : undefined} />

            {/* Next Navigation */}
            <DimensionPanel.NextNav />
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && !result && !optimisticResult && (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 dark:text-zinc-500 space-y-8 animate-in fade-in zoom-in-95 duration-700">
            <div className="relative group">
              <div
                className={`absolute inset-0 ${classes.bg}/20 blur-[80px] rounded-full group-hover:${classes.bg}/30 transition-colors duration-1000`}
              />
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
                    d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
                  />
                </svg>
              </div>
            </div>
            <div className="text-center space-y-3">
              <h3 className="text-2xl font-bold text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-b dark:from-white dark:to-white/40 tracking-tight">
                Prompt Alchemy
              </h3>
              <p className="text-sm text-slate-500 dark:text-zinc-500 max-w-xs mx-auto font-light leading-relaxed">
                Transform your scene descriptions into
                <br />
                <span className={`${classes.text} font-medium`}>platform-optimized AI video prompts</span>
              </p>
              <div className="flex items-center justify-center gap-3 pt-4">
                {PLATFORMS.map((platform) => (
                  <div
                    key={platform.id}
                    className={`w-8 h-8 rounded-lg bg-gradient-to-br ${platform.gradient} flex items-center justify-center text-white font-bold text-xs shadow-md opacity-60 hover:opacity-100 transition-opacity`}
                    title={platform.name}
                  >
                    {platform.icon}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </DimensionPanel.Content>

      {/* Credit Modal */}
      <InsufficientCreditsModal
        isOpen={showCreditModal}
        onClose={() => setShowCreditModal(false)}
        requiredCredits={CREDIT_COST * (mode === "batch" ? 3 : 1)}
        currentBalance={creditCtx?.balance ?? 0}
        onRetry={handleTranslate}
      />
    </>
  );
}
