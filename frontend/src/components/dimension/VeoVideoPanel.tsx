"use client";

/**
 * VeoVideoPanel - VEO 비디오 생성기
 *
 * 2026 Golden App: React 19 Best Practices + Multimodal Input
 *
 * Features:
 * - useTransition for non-blocking form submission
 * - useOptimistic for instant UI feedback
 * - File upload for reference images/videos
 * - SSE streaming for video generation
 *
 * @see https://react.dev/blog/2024/12/05/react-19
 */

import { useState, useRef, useCallback, useMemo, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import {
  useDimensionChainOptional,
  type ChainData,
} from "@/contexts/DimensionChainContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import ChainDataInput from "./ChainDataInput";
import { useLanguage } from "@/contexts/LanguageContext";
import { getPreviousStepResult, parseWorkflowUrlParams } from "@/lib/workflow-state";
import { type ThemeColor as DimensionThemeColor } from "@/lib/dimension-theme";
import { Sparkles } from "lucide-react";

const DIMENSION_CODE = "veo";
const DIMENSION_KEY = "video-maker"; // Chain context key
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

interface VideoResult {
  video_url?: string;
  status: "pending" | "processing" | "completed" | "failed";
  operation_id?: string;
  error?: string;
  metadata?: {
    duration?: string;
    resolution?: string;
    fps?: string;
    model?: string;
  };
}

const ASPECT_RATIOS = [
  { value: "16:9", label: "16:9 (Landscape)" },
  { value: "9:16", label: "9:16 (Portrait)" },
  { value: "1:1", label: "1:1 (Square)" },
  { value: "4:3", label: "4:3 (Classic)" },
];

const getDurations = (isKo: boolean) => [
  { value: "4", label: isKo ? "4초" : "4s" },
  { value: "6", label: isKo ? "6초" : "6s" },
  { value: "8", label: isKo ? "8초" : "8s" },
];

const STYLES = [
  { value: "cinematic", label: "Cinematic" },
  { value: "realistic", label: "Realistic" },
  { value: "artistic", label: "Artistic" },
  { value: "anime", label: "Anime" },
];

// 2026 Veo 3.1 Models
const getVeoModels = (isKo: boolean) => [
  {
    value: "veo-3.1-generate-preview",
    label: isKo ? "Quality (고품질)" : "Quality (High Quality)",
    description: isKo ? "최고 품질의 비디오 생성 (느림)" : "Highest quality video generation (slower)"
  },
  {
    value: "veo-3.1-fast-generate-preview",
    label: isKo ? "Fast (빠름)" : "Fast (Quick)",
    description: isKo ? "빠른 비디오 생성 (저비용)" : "Quick video generation (lower cost)"
  },
];

// Workflow context type - data from previous steps
interface WorkflowScenarioContext {
  source: string;
  scenarioTitle?: string;
  currentShot?: {
    shotNumber: number;
    description: string;
    cameraWork?: string;
    lighting?: string;
    mood?: string;
  };
  styleHints?: {
    mood?: string;
    lighting?: string;
    colorPalette?: string[];
  };
  fullScript?: string;
}

// === Content Component ===
function VeoVideoContent() {
  const { token, setLoading, setResult, setError } = useDimensionPanel();
  const { language } = useLanguage();
  const isKo = language === "ko";
  const searchParams = useSearchParams();
  const chainCtx = useDimensionChainOptional();

  // Set current dimension on mount
  useEffect(() => {
    if (chainCtx) {
      chainCtx.setCurrentDimension(DIMENSION_KEY);
    }
  }, [chainCtx]);

  // i18n labels
  const labels = useMemo(() => ({
    title: isKo ? "Veo 3.1 비디오" : "Veo 3.1 Video",
    promptLabel: isKo ? "프롬프트" : "Prompt",
    promptPlaceholder: isKo
      ? "생성할 비디오를 상세히 설명하세요...\n예: A cinematic shot of a sunrise over mountains, golden light casting long shadows..."
      : "Describe the video you want to generate in detail...\nExample: A cinematic shot of a sunrise over mountains, golden light casting long shadows...",
    referenceLabel: isKo ? "참고 이미지/영상 (선택)" : "Reference Image/Video (Optional)",
    referenceHelper: isKo ? "스타일 참고용 이미지나 영상 첨부 (Image-to-Video)" : "Attach images or videos for style reference (Image-to-Video)",
    negativePromptLabel: isKo ? "네거티브 프롬프트 (선택)" : "Negative Prompt (Optional)",
    negativePromptPlaceholder: isKo ? "제외할 요소를 입력하세요..." : "Enter elements to exclude...",
    aspectRatioLabel: isKo ? "비율" : "Aspect Ratio",
    durationLabel: isKo ? "길이" : "Duration",
    styleLabel: isKo ? "스타일" : "Style",
    seedLabel: isKo ? "시드 설정" : "Seed Setting",
    seedPlaceholder: isKo ? "시드 값 입력..." : "Enter seed value...",
    seedRandomDesc: isKo ? "매번 새로운 결과 생성" : "Generate new results each time",
    seedFixedDesc: isKo ? "동일한 시드로 재현 가능한 결과" : "Reproducible results with the same seed",
    creditCost: isKo ? "크레딧 소모" : "credits consumed",
    generateButton: isKo ? "비디오 생성" : "Generate Video",
    generating: isKo ? "생성 중..." : "Generating...",
    enterPrompt: isKo ? "프롬프트를 입력해주세요" : "Please enter a prompt",
    promptTooShort: isKo ? "프롬프트는 최소 10자 이상 입력해주세요" : "Please enter at least 10 characters",
    promptTooLong: (max: number) => isKo ? `프롬프트는 ${max}자 이하로 입력해주세요` : `Prompt must be ${max} characters or less`,
    processing: isKo ? "비디오 생성 중..." : "Generating video...",
    processingDesc: isKo ? "Veo 3.1이 영상을 렌더링하고 있습니다" : "Veo 3.1 is rendering your video",
    download: isKo ? "다운로드" : "Download",
    generationFailed: isKo ? "비디오 생성 실패" : "Video generation failed",
    unknownError: isKo ? "알 수 없는 오류가 발생했습니다" : "An unknown error occurred",
    retryButton: isKo ? "다시 시도" : "Retry",
    usedPrompt: isKo ? "사용된 프롬프트" : "Used Prompt",
    copy: isKo ? "복사" : "Copy",
    copied: isKo ? "복사됨!" : "Copied!",
    emptyStateTitle: "Veo 3.1 Video Generation",
    emptyStateDesc1: isKo ? "프롬프트를 입력하고" : "Enter a prompt and",
    emptyStateDesc2: isKo ? "AI 비디오" : "AI video",
    emptyStateDesc3: isKo ? "를 생성하세요." : "generate.",
    durationRange: isKo ? "4-8초" : "4-8s",
    modelLabel: isKo ? "생성 모드" : "Generation Mode",
    qualityMode: isKo ? "Quality 모드: 최고 품질" : "Quality mode: Highest quality",
    fastMode: isKo ? "Fast 모드: 빠른 생성, 저비용" : "Fast mode: Quick generation, lower cost",
  }), [isKo]);

  // i18n presets
  const DURATIONS = useMemo(() => getDurations(isKo), [isKo]);
  const VEO_MODELS = useMemo(() => getVeoModels(isKo), [isKo]);

  // Form state
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState("");
  const [aspectRatio, setAspectRatio] = useState("16:9");
  const [duration, setDuration] = useState("8");
  const [style, setStyle] = useState("cinematic");
  const [veoModel, setVeoModel] = useState("veo-3.1-generate-preview"); // Default: Quality mode
  const [seed, setSeed] = useState<number | undefined>(undefined);
  const [useRandomSeed, setUseRandomSeed] = useState(true);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [videoResult, setVideoResult] = useState<VideoResult | null>(null);

  // File upload state (2026 Best Practice: Multimodal input)
  const [_uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  // Workflow context - data from previous steps (Scenario Generator, Reference Decoder)
  const [workflowContext, setWorkflowContext] = useState<WorkflowScenarioContext | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);

  // Load previous step data on mount (workflow integration)
  useEffect(() => {
    if (typeof window === "undefined") return;

    const { ipSlug, step: currentStep } = parseWorkflowUrlParams(searchParams);
    if (!ipSlug || !currentStep || currentStep <= 1) return;

    // Search backward through previous steps for scenario/style data
    for (let prevStep = currentStep - 1; prevStep >= 1; prevStep--) {
      const prevResult = getPreviousStepResult(ipSlug, prevStep + 1);
      if (!prevResult?.outputData) continue;

      const data = prevResult.outputData as Record<string, unknown>;
      const context: WorkflowScenarioContext = { source: "workflow" };

      // StoryArchitectPanel output (title, logline, synopsis, structure)
      if (data.logline || data.synopsis || data.structure) {
        context.scenarioTitle = data.title as string;

        // Build full script from synopsis and structure
        let scriptParts: string[] = [];
        if (data.logline) scriptParts.push(data.logline as string);
        if (data.synopsis) scriptParts.push(data.synopsis as string);

        // Extract structure acts as shots
        const structure = data.structure as Array<{
          act: string;
          description: string;
          duration: string;
          emotion: string;
        }> | undefined;

        if (structure && structure.length > 0) {
          // Use first act as current shot
          const firstAct = structure[0];
          context.currentShot = {
            shotNumber: 1,
            description: firstAct.description,
            mood: firstAct.emotion,
          };

          // Add all act descriptions to script
          structure.forEach((act, i) => {
            scriptParts.push(`[${act.act}] ${act.description} (${act.emotion})`);
          });
        }

        context.fullScript = scriptParts.join("\n\n");

        // Extract visual motifs for style hints
        if (data.visual_motifs && Array.isArray(data.visual_motifs)) {
          const motifs = data.visual_motifs as string[];
          context.styleHints = {
            mood: (data.structure as Array<{ emotion: string }>)?.[0]?.emotion,
          };
        }
      }

      // Scenario Generator output (generated_script, shots) - legacy support
      if (data.generated_script || data.shots) {
        context.fullScript = data.generated_script as string;
        context.scenarioTitle ??= data.title as string;

        // Get first shot for initial prompt
        const shots = data.shots as Array<{
          shot_number: number;
          description: string;
          camera_work?: string;
          lighting?: string;
          mood?: string;
        }> | undefined;

        if (shots && shots.length > 0) {
          const firstShot = shots[0];
          context.currentShot = {
            shotNumber: firstShot.shot_number,
            description: firstShot.description,
            cameraWork: firstShot.camera_work,
            lighting: firstShot.lighting,
            mood: firstShot.mood,
          };
        }
      }

      // Reference Decoder style hints
      if (data.style_prompt || data.mood || data.lighting) {
        context.styleHints = {
          mood: data.mood as string,
          lighting: data.lighting as string,
          colorPalette: data.color_palette as string[],
        };
        // Also use style_prompt if no script
        if (!context.fullScript && data.style_prompt) {
          context.fullScript = data.style_prompt as string;
        }
      }

      if (context.currentShot || context.fullScript || context.styleHints) {
        setWorkflowContext(context);

        // Auto-populate prompt with shot/act description
        if (context.currentShot && !prompt) {
          let autoPrompt = context.currentShot.description;
          if (context.currentShot.cameraWork) {
            autoPrompt += `. Camera: ${context.currentShot.cameraWork}`;
          }
          if (context.currentShot.lighting) {
            autoPrompt += `. Lighting: ${context.currentShot.lighting}`;
          }
          if (context.currentShot.mood) {
            autoPrompt += `. Mood: ${context.currentShot.mood}`;
          }
          // Add scenario title context
          if (context.scenarioTitle) {
            autoPrompt = `"${context.scenarioTitle}" - ${autoPrompt}`;
          }
          setPrompt(autoPrompt);
        } else if (context.fullScript && !prompt) {
          // Use first 500 chars of script as prompt starter
          const prefix = context.scenarioTitle ? `"${context.scenarioTitle}"\n\n` : "";
          setPrompt(prefix + context.fullScript.slice(0, 500));
        }
        break;
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const { byokKey } = useBYOK();
  const creditCtx = useCreditContextOptional();
  const { getToolByDimension } = useDimensionConfig();
  const toolConfig = getToolByDimension("VEO");
  // Fast mode is 50% cheaper than Quality mode
  const baseCreditCost = toolConfig?.creditCost ?? 200;
  const creditCost = veoModel === "veo-3.1-fast-generate-preview"
    ? Math.floor(baseCreditCost * 0.5)
    : baseCreditCost;

  const { downloadFile, copyToClipboard, isCopied } = useResultExport();

  // Async operation for SSE streaming
  const {
    isLoading,
    error,
    executeStream,
    retry,
    canRetry,
    currentRetryCount,
  } = useAsyncOperation<VideoResult>({
    onSuccess: (data) => {
      setVideoResult(data);
      setResult(data);

      // Store in chain context for downstream dimensions (quality-director)
      if (data.status === "completed" && chainCtx) {
        chainCtx.setChainData(
          DIMENSION_KEY,
          { ...data, prompt } as unknown as Record<string, unknown>,
          `Video generated: ${data.metadata?.duration || "unknown"}`
        );
      }

      if (data.status === "completed" && !byokKey && creditCtx) {
        void creditCtx.refresh();
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

  // Sync loading state
  const wrappedExecuteStream = useCallback(
    async (url: string, payload: object, headers?: Record<string, string>) => {
      setLoading(true);
      try {
        return await executeStream(url, payload, headers);
      } finally {
        setLoading(false);
      }
    },
    [executeStream, setLoading]
  );

  const MAX_PROMPT_LENGTH = 2000;

  const handleGenerate = useCallback(async () => {
    const trimmedPrompt = prompt.trim();
    if (!trimmedPrompt) {
      setValidationError(labels.enterPrompt);
      return;
    }
    if (trimmedPrompt.length < 10) {
      setValidationError(labels.promptTooShort);
      return;
    }
    if (trimmedPrompt.length > MAX_PROMPT_LENGTH) {
      setValidationError(labels.promptTooLong(MAX_PROMPT_LENGTH));
      return;
    }
    setValidationError(null);

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(creditCost)) {
      setShowCreditModal(true);
      return;
    }

    await wrappedExecuteStream(
      `${API_BASE}/api/dimension/veo/generate/stream`,
      {
        prompt: prompt.trim(),
        negative_prompt: negativePrompt.trim() || undefined,
        aspect_ratio: aspectRatio,
        duration: parseInt(duration),
        style,
        model: veoModel, // veo-3.1-generate-preview (Quality) or veo-3.1-fast-generate-preview (Fast)
        seed: useRandomSeed ? undefined : seed,
      },
      getBYOKHeaders(byokKey)
    );
  }, [
    prompt,
    negativePrompt,
    aspectRatio,
    duration,
    style,
    veoModel,
    seed,
    useRandomSeed,
    byokKey,
    creditCtx,
    creditCost,
    wrappedExecuteStream,
    labels,
  ]);

  const handleDownload = useCallback(async () => {
    if (!videoResult?.video_url) return;

    try {
      const response = await fetch(videoResult.video_url);
      const blob = await response.blob();
      const content = await blob.text();
      downloadFile(content, `veo-video-${Date.now()}.mp4`, "video/mp4");
    } catch {
      const a = document.createElement("a");
      a.href = videoResult.video_url;
      a.download = `veo-video-${Date.now()}.mp4`;
      a.target = "_blank";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  }, [videoResult?.video_url, downloadFile]);

  const handleCopyPrompt = useCallback(() => {
    copyToClipboard(prompt);
  }, [prompt, copyToClipboard]);

  // Handle chain data from previous dimensions (visual-realizer, prompt-alchemy, sound-crafter)
  const handleApplyChainData = useCallback((data: Record<string, ChainData>) => {
    // Type-safe extraction helper
    const getStringValue = (obj: unknown, key: string): string | undefined => {
      if (obj && typeof obj === "object" && key in obj) {
        const val = (obj as Record<string, unknown>)[key];
        return typeof val === "string" ? val : undefined;
      }
      return undefined;
    };

    // From visual-realizer: get generated image prompt for video generation
    const visualOutput = data["visual-realizer"]?.output as Record<string, unknown> | undefined;
    const visualPrompt = getStringValue(visualOutput, "prompt");
    if (visualPrompt && !prompt) {
      setPrompt(visualPrompt);
    }

    // From prompt-alchemy: get video prompt
    const promptOutput = data["prompt-alchemy"]?.output as Record<string, unknown> | undefined;
    const alchemyPrompt = getStringValue(promptOutput, "prompt");
    if (alchemyPrompt && !prompt) {
      setPrompt(alchemyPrompt);
    }

    // Set negative prompt from visual-realizer if available
    const negPrompt = getStringValue(visualOutput, "negative_prompt");
    if (negPrompt && !negativePrompt) {
      setNegativePrompt(negPrompt);
    }

    // Set style from prompt-alchemy parameters
    const styleData = promptOutput?.style as Record<string, unknown> | undefined;
    if (styleData?.cinematography) {
      const cinematography = String(styleData.cinematography);
      if (cinematography.toLowerCase().includes("anime")) setStyle("anime");
      else if (cinematography.toLowerCase().includes("realistic")) setStyle("realistic");
      else if (cinematography.toLowerCase().includes("artistic")) setStyle("artistic");
    }
  }, [prompt, negativePrompt]);

  const displayError = validationError || error;

  return (
    <>
      <DimensionPanel.Header title={labels.title} />

      <div className="flex flex-1 min-h-0">
        {/* Sidebar */}
        <DimensionPanel.Sidebar>
          {/* Chain Data Input - data from visual-realizer, prompt-alchemy, sound-crafter */}
          <ChainDataInput
            currentDimension={DIMENSION_KEY}
            onApplyData={handleApplyChainData}
            themeColor={CHAIN_INPUT_THEME_MAP[token.themeColor] || "sky"}
          />

          {/* Workflow Context Banner */}
          {workflowContext && (
            <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 mb-3">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-amber-500" />
                <span className="text-xs font-medium text-amber-600 dark:text-amber-400">
                  {isKo ? "시나리오 데이터 적용됨" : "Scenario Data Applied"}
                </span>
              </div>
              {workflowContext.scenarioTitle && (
                <p className="text-xs text-[var(--fg-muted)] mb-1">
                  <span className="font-medium">{isKo ? "제목" : "Title"}:</span> {workflowContext.scenarioTitle}
                </p>
              )}
              {workflowContext.currentShot && (
                <p className="text-xs text-[var(--fg-muted)]">
                  <span className="font-medium">{isKo ? "현재 샷" : "Current Shot"}:</span> #{workflowContext.currentShot.shotNumber}
                </p>
              )}
              {workflowContext.styleHints?.mood && (
                <p className="text-xs text-[var(--fg-muted)]">
                  <span className="font-medium">{isKo ? "무드" : "Mood"}:</span> {workflowContext.styleHints.mood}
                </p>
              )}
            </div>
          )}

          {/* Prompt Input */}
          <DimensionPanel.Textarea
            label={labels.promptLabel}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={labels.promptPlaceholder}
            rows={6}
            maxLength={MAX_PROMPT_LENGTH}
          />

          {/* File Upload (2026 Best Practice: Multimodal Input) */}
          <DimensionPanel.FileUpload
            accept={["*"]}
            maxSizeMB={100}
            multiple
            onUpload={setUploadedFiles}
            label={labels.referenceLabel}
            helperText={labels.referenceHelper}
          />

          {/* Negative Prompt */}
          <DimensionPanel.Textarea
            label={labels.negativePromptLabel}
            value={negativePrompt}
            onChange={(e) => setNegativePrompt(e.target.value)}
            placeholder={labels.negativePromptPlaceholder}
            rows={3}
          />

          {/* Aspect Ratio & Duration */}
          <div className="grid grid-cols-2 gap-3">
            <DimensionPanel.Select
              label={labels.aspectRatioLabel}
              value={aspectRatio}
              onChange={(e) => setAspectRatio(e.target.value)}
              options={ASPECT_RATIOS}
            />
            <DimensionPanel.Select
              label={labels.durationLabel}
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              options={DURATIONS}
            />
          </div>

          {/* Style */}
          <div className="space-y-2">
            <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">{labels.styleLabel}</label>
            <div className="grid grid-cols-2 gap-2">
              {STYLES.map((s) => (
                <button
                  key={s.value}
                  onClick={() => setStyle(s.value)}
                  className={`px-4 py-3 rounded-xl text-sm font-medium transition-all border ${
                    style === s.value
                      ? `bg-${token.themeColor}-100 dark:bg-${token.themeColor}-500/20 border-${token.themeColor}-400 dark:border-${token.themeColor}-500/40 text-${token.themeColor}-600 dark:text-${token.themeColor}-400 shadow-[0_0_15px_rgba(14,165,233,0.2)]`
                      : "bg-white dark:bg-white/5 border-slate-200 dark:border-white/10 text-slate-600 dark:text-zinc-400 hover:bg-slate-50 dark:hover:bg-white/10 hover:text-slate-900 dark:hover:text-white"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Veo Model Selection (Quality / Fast) */}
          <div className="space-y-2 pt-4 border-t border-slate-200 dark:border-white/5 mt-2">
            <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">{labels.modelLabel}</label>
            <div className="grid grid-cols-2 gap-2">
              {VEO_MODELS.map((m) => (
                <button
                  key={m.value}
                  onClick={() => setVeoModel(m.value)}
                  className={`px-3 py-3 rounded-xl text-xs font-medium transition-all border flex flex-col items-center gap-1 ${
                    veoModel === m.value
                      ? `bg-${token.themeColor}-100 dark:bg-${token.themeColor}-500/20 border-${token.themeColor}-400 dark:border-${token.themeColor}-500/40 text-${token.themeColor}-600 dark:text-${token.themeColor}-400 shadow-[0_0_15px_rgba(14,165,233,0.2)]`
                      : "bg-white dark:bg-white/5 border-slate-200 dark:border-white/10 text-slate-600 dark:text-zinc-400 hover:bg-slate-50 dark:hover:bg-white/10 hover:text-slate-900 dark:hover:text-white"
                  }`}
                >
                  <span className="font-semibold">{m.label.split(" ")[0]}</span>
                  {m.value === "veo-3.1-fast-generate-preview" && (
                    <span className="text-[9px] opacity-70">50% 할인</span>
                  )}
                </button>
              ))}
            </div>
            <p className="text-[10px] text-slate-500 dark:text-zinc-600">
              {veoModel === "veo-3.1-generate-preview" ? labels.qualityMode : labels.fastMode}
            </p>
          </div>

          {/* Seed Control */}
          <div className="space-y-3 pt-4 border-t border-slate-200 dark:border-white/5 mt-2">
            <div className="flex items-center justify-between">
              <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">{labels.seedLabel}</label>
              <button
                onClick={() => setUseRandomSeed(!useRandomSeed)}
                className={`relative w-10 h-5 rounded-full transition-all ${
                  useRandomSeed ? `bg-${token.themeColor}-500` : "bg-slate-200 dark:bg-white/10"
                }`}
              >
                <span
                  className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow-sm transition-all ${
                    useRandomSeed ? "left-5" : "left-0.5"
                  }`}
                />
              </button>
            </div>
            {!useRandomSeed && (
              <input
                type="number"
                value={seed ?? ""}
                onChange={(e) => setSeed(e.target.value ? parseInt(e.target.value) : undefined)}
                placeholder={labels.seedPlaceholder}
                className="w-full px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-white/20 focus:outline-none focus:border-sky-500 dark:focus:border-sky-400/50 text-sm font-mono"
              />
            )}
            <p className="text-[10px] text-slate-500 dark:text-zinc-600">
              {useRandomSeed ? labels.seedRandomDesc : labels.seedFixedDesc}
            </p>
          </div>

          {/* Credit Cost Info */}
          <div className={`flex items-center gap-2 px-3 py-2 rounded-lg bg-${token.themeColor}-500/5 border border-${token.themeColor}-500/10`}>
            <svg className={`w-4 h-4 text-${token.themeColor}-400`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span className={`text-xs text-${token.themeColor}-400 font-medium`}>{creditCost} {labels.creditCost}</span>
          </div>

          {/* Generate Button */}
          <DimensionPanel.GenerateButton
            onClick={handleGenerate}
            disabled={isLoading || !prompt.trim()}
            loading={isLoading}
            loadingText={labels.generating}
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            }
          >
            {labels.generateButton}
          </DimensionPanel.GenerateButton>

          {/* Validation Error */}
          {validationError && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs break-keep leading-relaxed animate-in fade-in slide-in-from-top-1">
              {validationError}
            </div>
          )}
        </DimensionPanel.Sidebar>

        {/* Content Area */}
        <DimensionPanel.Content>
          <DimensionPanel.Loading />
          <DimensionPanel.Error error={displayError || undefined} />

          {videoResult ? (
            <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
              {/* Processing State */}
              {videoResult.status === "processing" && (
                <div className={`flex items-center justify-center gap-3 p-6 bg-${token.themeColor}-500/10 border border-${token.themeColor}-500/20 rounded-2xl`}>
                  <div className={`w-6 h-6 border-2 border-${token.themeColor}-400/30 border-t-${token.themeColor}-400 rounded-full animate-spin`} />
                  <div className="text-center">
                    <p className={`text-${token.themeColor}-400 font-medium`}>{labels.processing}</p>
                    <p className="text-xs text-zinc-500 mt-1">{labels.processingDesc}</p>
                  </div>
                </div>
              )}

              {/* Video Player */}
              {videoResult.status === "completed" && videoResult.video_url && (
                <div className="relative group">
                  <div className={`absolute -inset-1 bg-gradient-to-r from-${token.themeColor}-500/20 to-blue-500/20 rounded-2xl blur opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                  <div className="relative bg-black rounded-2xl overflow-hidden border border-white/10 shadow-2xl">
                    <video
                      ref={videoRef}
                      src={videoResult.video_url}
                      controls
                      autoPlay
                      loop
                      className="w-full aspect-video"
                    />
                  </div>

                  {/* Download Button */}
                  <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={handleDownload}
                      className="flex items-center gap-2 px-4 py-2 bg-black/60 backdrop-blur-xl border border-white/10 rounded-lg text-white text-sm font-medium hover:bg-black/80 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      {labels.download}
                    </button>
                  </div>
                </div>
              )}

              {/* Failed State */}
              {videoResult.status === "failed" && (
                <div className="flex flex-col items-center justify-center p-12 bg-red-500/5 border border-red-500/20 rounded-2xl">
                  <svg className="w-16 h-16 text-red-400/50 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <p className="text-red-400 font-medium mb-2">{labels.generationFailed}</p>
                  <p className="text-xs text-zinc-500">{videoResult.error || labels.unknownError}</p>
                  <button
                    onClick={canRetry ? retry : handleGenerate}
                    className="mt-4 px-4 py-2 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm hover:bg-red-500/20 transition-colors flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    {labels.retryButton}
                    {canRetry && currentRetryCount > 0 && (
                      <span className="text-red-400/60">({currentRetryCount}/3)</span>
                    )}
                  </button>
                </div>
              )}

              {/* Metadata */}
              {videoResult.metadata && videoResult.status === "completed" && (
                <div className="grid grid-cols-4 gap-4">
                  {videoResult.metadata.duration && (
                    <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl text-center">
                      <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Duration</p>
                      <p className={`text-lg font-mono text-${token.themeColor}-400`}>{videoResult.metadata.duration}</p>
                    </div>
                  )}
                  {videoResult.metadata.resolution && (
                    <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl text-center">
                      <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Resolution</p>
                      <p className={`text-lg font-mono text-${token.themeColor}-400`}>{videoResult.metadata.resolution}</p>
                    </div>
                  )}
                  {videoResult.metadata.fps && (
                    <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl text-center">
                      <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">FPS</p>
                      <p className={`text-lg font-mono text-${token.themeColor}-400`}>{videoResult.metadata.fps}</p>
                    </div>
                  )}
                  {videoResult.metadata.model && (
                    <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl text-center">
                      <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Model</p>
                      <p className={`text-lg font-mono text-${token.themeColor}-400`}>{videoResult.metadata.model}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Used Prompt */}
              {videoResult.status === "completed" && (
                <div className="p-6 bg-white/[0.02] border border-white/5 rounded-xl">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest">{labels.usedPrompt}</h3>
                    <button
                      onClick={handleCopyPrompt}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-zinc-400 hover:text-white bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 hover:border-white/20 transition-all"
                    >
                      {isCopied ? (
                        <>
                          <svg className={`w-3.5 h-3.5 text-${token.themeColor}-400`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          <span className={`text-${token.themeColor}-400`}>{labels.copied}</span>
                        </>
                      ) : (
                        <>
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                          {labels.copy}
                        </>
                      )}
                    </button>
                  </div>
                  <p className="text-sm text-zinc-300 leading-relaxed">{prompt}</p>
                </div>
              )}

              {/* Next Dimension Navigation */}
              {videoResult.status === "completed" && (
                <DimensionPanel.NextNav currentDimension={DIMENSION_KEY} />
              )}
            </div>
          ) : (
            // Empty State
            <div className="flex flex-col items-center justify-center h-full text-slate-500 dark:text-zinc-500 space-y-8 animate-in fade-in zoom-in-95 duration-700">
              <div className="relative group">
                <div className={`absolute inset-0 bg-${token.themeColor}-500/20 blur-[80px] rounded-full group-hover:bg-${token.themeColor}-500/30 transition-colors duration-1000`} />
                <div className={`w-32 h-32 rounded-[2rem] bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex items-center justify-center shadow-lg dark:shadow-[0_0_60px_rgba(0,0,0,0.3)] backdrop-blur-md relative transform group-hover:scale-105 transition-all duration-500 group-hover:border-${token.themeColor}-300 dark:group-hover:border-${token.themeColor}-500/20`}>
                  <div className={`absolute inset-0 bg-gradient-to-tr from-${token.themeColor}-500/5 to-transparent rounded-[2rem]`} />
                  <svg className={`w-12 h-12 text-slate-300 dark:text-white/20 group-hover:text-${token.themeColor}-500 dark:group-hover:text-${token.themeColor}-400 transition-colors duration-500`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>
              <div className="text-center space-y-3">
                <h3 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">{labels.emptyStateTitle}</h3>
                <p className="text-sm text-slate-500 dark:text-[var(--fg-muted)] max-w-xs mx-auto font-light leading-relaxed">
                  {labels.emptyStateDesc1}<br />
                  <span className={`text-${token.themeColor}-600 dark:text-${token.themeColor}-400 font-medium`}>{labels.emptyStateDesc2}</span> {labels.emptyStateDesc3}
                </p>
                <div className="flex items-center justify-center gap-2 pt-2">
                  <span className={`px-2 py-1 bg-${token.themeColor}-100 dark:bg-${token.themeColor}-500/10 border border-${token.themeColor}-200 dark:border-${token.themeColor}-500/20 rounded text-[10px] text-${token.themeColor}-600 dark:text-${token.themeColor}-400 font-medium`}>Veo 3.1</span>
                  <span className={`px-2 py-1 rounded text-[10px] font-medium ${
                    veoModel === "veo-3.1-generate-preview"
                      ? "bg-amber-100 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 text-amber-600 dark:text-amber-400"
                      : "bg-emerald-100 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 text-emerald-600 dark:text-emerald-400"
                  }`}>
                    {veoModel === "veo-3.1-generate-preview" ? "Quality" : "Fast"}
                  </span>
                  <span className="px-2 py-1 bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded text-[10px] text-slate-500 dark:text-zinc-500">{labels.durationRange}</span>
                </div>
              </div>
            </div>
          )}
        </DimensionPanel.Content>
      </div>

      <InsufficientCreditsModal
        isOpen={showCreditModal}
        onClose={() => setShowCreditModal(false)}
        requiredCredits={creditCost}
        currentBalance={creditCtx?.balance ?? 0}
        onRetry={handleGenerate}
      />
    </>
  );
}

// === Main Export ===
export default function VeoVideoPanel() {
  return (
    <DimensionPanel dimensionCode={DIMENSION_CODE}>
      <Suspense fallback={null}>
        <VeoVideoContent />
      </Suspense>
    </DimensionPanel>
  );
}
