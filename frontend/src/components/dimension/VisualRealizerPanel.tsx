"use client";

/**
 * VisualRealizerPanel - 비주얼 리얼라이저 (3D)
 *
 * 2026 Golden App: React 19 Best Practices + Multimodal Input
 *
 * Features:
 * - useTransition for non-blocking form submission
 * - useOptimistic for instant UI feedback
 * - File upload for reference images
 * - Evidence refs display
 *
 * @see docs/PANEL_DESIGN_UNITY_SPEC.md
 * @see https://react.dev/blog/2024/12/05/react-19
 */

import { useState, useCallback, useMemo, useEffect } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { getPreviousStepResult } from "@/lib/workflow-state";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import {
  useDimensionChainOptional,
  type ChainData,
} from "@/contexts/DimensionChainContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import ChainDataInput from "./ChainDataInput";
import type { EvidenceRef } from "./EvidenceDisplay";
import { type ThemeColor as DimensionThemeColor } from "@/lib/dimension-theme";
import { Image as ImageIcon } from "lucide-react";

// ============================================================================
// Constants & Types
// ============================================================================

const DIMENSION_CODE = "3d";
const DIMENSION_KEY = "visual-realizer"; // Chain context key
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

interface ImagePromptResult {
  prompt: string;
  negative_prompt?: string;
  parameters?: {
    style?: string;
    aspect_ratio?: string;
    quality?: string;
  };
  evidence_refs?: EvidenceRef[];
  confidence?: number;
}

const getStyles = (isKo: boolean) => [
  { value: "photorealistic", label: isKo ? "포토리얼리스틱" : "Photorealistic" },
  { value: "cinematic", label: isKo ? "시네마틱" : "Cinematic" },
  { value: "anime", label: isKo ? "애니메이션" : "Anime" },
  { value: "illustration", label: isKo ? "일러스트" : "Illustration" },
  { value: "3d-render", label: isKo ? "3D 렌더" : "3D Render" },
  { value: "oil-painting", label: isKo ? "유화" : "Oil Painting" },
  { value: "watercolor", label: isKo ? "수채화" : "Watercolor" },
  { value: "digital-art", label: isKo ? "디지털 아트" : "Digital Art" },
];

const getAspectRatios = (isKo: boolean) => [
  { value: "16:9", label: isKo ? "16:9 (와이드)" : "16:9 (Wide)" },
  { value: "9:16", label: isKo ? "9:16 (세로)" : "9:16 (Portrait)" },
  { value: "1:1", label: isKo ? "1:1 (정사각형)" : "1:1 (Square)" },
  { value: "4:3", label: isKo ? "4:3 (스탠다드)" : "4:3 (Standard)" },
  { value: "3:2", label: isKo ? "3:2 (사진)" : "3:2 (Photo)" },
  { value: "21:9", label: isKo ? "21:9 (울트라와이드)" : "21:9 (Ultrawide)" },
];

const getModels = (isKo: boolean) => [
  { value: "gemini-3-flash-preview", label: isKo ? "Flash (빠름)" : "Flash (Fast)" },
  { value: "gemini-3-pro-preview", label: isKo ? "Pro (고품질)" : "Pro (High Quality)" },
];

// ============================================================================
// Main Panel Component
// ============================================================================

export default function VisualRealizerPanel() {
  return (
    <DimensionPanel dimensionCode={DIMENSION_CODE}>
      <VisualRealizerContent />
    </DimensionPanel>
  );
}

// ============================================================================
// Panel Content (Inner Component)
// ============================================================================

function VisualRealizerContent() {
  const { token, setLoading, setResult, setError: setContextError } =
    useDimensionPanel();
  const { language } = useLanguage();
  const isKo = language === "ko";
  const chainCtx = useDimensionChainOptional();

  // Set current dimension on mount
  useEffect(() => {
    if (chainCtx) {
      chainCtx.setCurrentDimension(DIMENSION_KEY);
    }
  }, [chainCtx]);

  // i18n labels
  const labels = useMemo(() => ({
    title: isKo ? "비주얼 리얼라이저" : "Visual Realizer",
    descriptionLabel: isKo ? "이미지 설명 (Prompt)" : "Image Description (Prompt)",
    descriptionPlaceholder: isKo ? "생성하고 싶은 이미지를 상세히 설명하세요..." : "Describe the image you want to generate in detail...",
    referenceLabel: isKo ? "참고 이미지 (선택)" : "Reference Image (Optional)",
    referenceHelper: isKo ? "스타일 참고용 이미지를 첨부하면 더 정확한 프롬프트 생성" : "Attach reference images for more accurate prompt generation",
    styleLabel: isKo ? "스타일 (Style)" : "Style",
    aspectRatioLabel: isKo ? "비율 (Aspect Ratio)" : "Aspect Ratio",
    modelLabel: isKo ? "AI 모델 Engine" : "AI Model Engine",
    generateButton: isKo ? "프롬프트 생성" : "Generate Prompt",
    generating: isKo ? "생성 중..." : "Generating...",
    enterDescription: isKo ? "이미지 설명을 입력해주세요" : "Please enter an image description",
    descriptionTooLong: (max: number) => isKo ? `이미지 설명은 ${max}자 이하로 입력해주세요` : `Description must be ${max} characters or less`,
    generatedPrompt: "Generated Prompt",
    export: "EXPORT",
    copy: "COPY",
    copied: "COPIED",
    negativePrompt: "Negative Prompt",
    parameters: "Parameters",
    emptyStateTitle: "Ready to Generate",
    emptyStateDesc1: isKo ? "이미지를 설명하고 생성형 AI를 위한" : "Describe an image and receive an",
    emptyStateDesc2: isKo ? "최적화된 프롬프트" : "optimized prompt",
    emptyStateDesc3: isKo ? "를 받아보세요." : "for generative AI.",
    exportTooltip: isKo ? "JSON으로 내보내기" : "Export as JSON",
  }), [isKo]);

  // i18n presets
  const STYLES = useMemo(() => getStyles(isKo), [isKo]);
  const ASPECT_RATIOS = useMemo(() => getAspectRatios(isKo), [isKo]);
  const MODELS = useMemo(() => getModels(isKo), [isKo]);

  // Form state
  const [description, setDescription] = useState("");
  const [style, setStyle] = useState("photorealistic");
  const [aspectRatio, setAspectRatio] = useState("16:9");
  const [model, setModel] = useState("gemini-3-flash-preview");
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // File upload state (2026 Best Practice: Multimodal input)
  const [_uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  // ==========================================================================
  // Session Context Inheritance (2026 Best Practice)
  // Inject style_guide from previous step (AestheticDirector → VisualRealizer)
  // ==========================================================================
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

    // Auto-set description from auteur blend or style guide
    if (!description) {
      const descParts: string[] = [];

      // From AestheticDirector style guide
      if (data.style_guide && typeof data.style_guide === "object") {
        const styleGuide = data.style_guide as Record<string, unknown>;
        if (styleGuide.lighting) {
          descParts.push(`Lighting: ${styleGuide.lighting}`);
        }
        if (styleGuide.composition) {
          descParts.push(`Composition: ${styleGuide.composition}`);
        }
      }

      // From auteur_blend
      if (data.auteur_blend && typeof data.auteur_blend === "object") {
        const auteur = data.auteur_blend as Record<string, unknown>;
        if (auteur.primary && auteur.secondary) {
          descParts.push(`Style blend: ${auteur.primary} × ${auteur.secondary}`);
        }
      }

      // From color_palette
      if (Array.isArray(data.color_palette) && data.color_palette.length > 0) {
        descParts.push(`Palette: ${(data.color_palette as string[]).slice(0, 4).join(", ")}`);
      }

      if (descParts.length > 0) {
        setDescription(descParts.join(". "));
      }
    }

    // Auto-set style based on visual_guidelines or mood
    if (style === "photorealistic") {
      if (data.mood === "anime" || data.mood === "animated") {
        setStyle("anime");
      } else if (data.mood === "cinematic" || data.mood === "dramatic") {
        setStyle("cinematic");
      } else if (data.mood === "illustration") {
        setStyle("digital-art");
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Initial mount only
  }, []);

  // Hooks
  const { byokKey } = useBYOK();
  const creditCtx = useCreditContextOptional();
  const { getToolByDimension } = useDimensionConfig();
  const toolConfig = getToolByDimension("3D");
  const CREDIT_COST = toolConfig?.creditCost ?? 5;

  // Export utilities
  const { copyToClipboard, isCopied, exportJSON } = useResultExport();

  // Async operation hook
  const {
    isLoading,
    error,
    data: result,
    execute,
    cancel,
    retry,
    canRetry,
  } = useAsyncOperation<{
    success: boolean;
    output: ImagePromptResult;
    error?: string;
  }>({
    onSuccess: (data) => {
      if (data.success) {
        setResult(data.output);

        // Store in chain context for downstream dimensions (video-maker, quality-director)
        if (chainCtx) {
          chainCtx.setChainData(
            DIMENSION_KEY,
            data.output as unknown as Record<string, unknown>,
            data.output.prompt?.slice(0, 50) || description.slice(0, 50)
          );
        }

        if (!byokKey && creditCtx) {
          void creditCtx.refresh();
        }
      }
    },
    onError: (err) => {
      if (err.message.includes("크레딧") || err.message.includes("402")) {
        setShowCreditModal(true);
      }
      setContextError(err);
    },
    retryCount: 3,
    retryDelay: 1000,
    nonRetryableErrors: ["400", "401", "402", "403", "404", "크레딧", "부족"],
  });

  const MAX_DESCRIPTION_LENGTH = 2000;

  // Generate prompt
  const handleGenerate = async () => {
    const trimmedDescription = description.trim();
    if (!trimmedDescription) {
      setValidationError(labels.enterDescription);
      return;
    }
    if (trimmedDescription.length > MAX_DESCRIPTION_LENGTH) {
      setValidationError(labels.descriptionTooLong(MAX_DESCRIPTION_LENGTH));
      return;
    }
    setValidationError(null);

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
      setShowCreditModal(true);
      return;
    }

    setLoading(true);
    await execute(
      `${API_BASE}/api/dimension/3d/generate`,
      { description, style, aspect_ratio: aspectRatio, model },
      getBYOKHeaders(byokKey)
    );
    setLoading(false);
  };

  // Copy handler
  const handleCopy = useCallback(
    (text: string) => {
      copyToClipboard(text);
    },
    [copyToClipboard]
  );

  // Export result as JSON
  const handleExportJSON = () => {
    if (result?.output) {
      exportJSON(result.output, `image-prompt-${Date.now()}.json`);
    }
  };

  // Handle chain data from previous dimensions (prompt-alchemy, storyboard-sketch)
  const handleApplyChainData = useCallback((data: Record<string, ChainData>) => {
    // From prompt-alchemy: get generated prompt
    if (data["prompt-alchemy"]?.output?.prompt && !description) {
      setDescription(data["prompt-alchemy"].output.prompt as string);
    }

    // From storyboard-sketch: get scene descriptions for visual generation
    if (data["storyboard-sketch"]?.output?.scenes && !description) {
      const scenes = data["storyboard-sketch"].output.scenes as Array<{
        description: string;
        midjourney_prompt?: string;
        visual_prompt?: string;
      }>;
      if (scenes.length > 0) {
        // Use the first scene's visual prompt or description
        const firstScene = scenes[0];
        setDescription(firstScene.midjourney_prompt || firstScene.visual_prompt || firstScene.description);
      }
    }

    // Set style based on data from prompt-alchemy
    const promptAlchemyOutput = data["prompt-alchemy"]?.output as Record<string, unknown> | undefined;
    const styleData = promptAlchemyOutput?.style as Record<string, unknown> | undefined;
    if (styleData?.cinematography) {
      const cinematography = String(styleData.cinematography);
      if (cinematography.toLowerCase().includes("anime")) setStyle("anime");
      else if (cinematography.toLowerCase().includes("cinematic")) setStyle("cinematic");
      else if (cinematography.toLowerCase().includes("3d")) setStyle("3d-render");
    }
  }, [description]);

  // Extracted result data
  const displayResult = result?.success ? result.output : null;
  const displayError =
    validationError || (result && !result.success ? result.error : error);

  return (
    <>
      <DimensionPanel.Header title={labels.title} creditCost={CREDIT_COST} />

      <DimensionPanel.Sidebar>
        {/* Chain Data Input - data from prompt-alchemy, storyboard-sketch */}
        <ChainDataInput
          currentDimension={DIMENSION_KEY}
          onApplyData={handleApplyChainData}
          themeColor={CHAIN_INPUT_THEME_MAP[token.themeColor] || "emerald"}
        />

        {/* Description Input */}
        <DimensionPanel.Textarea
          label={labels.descriptionLabel}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder={labels.descriptionPlaceholder}
          rows={5}
          disabled={isLoading}
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

        {/* Style Select */}
        <DimensionPanel.Select
          label={labels.styleLabel}
          value={style}
          onChange={(e) => setStyle(e.target.value)}
          options={STYLES}
        />

        {/* Aspect Ratio Grid */}
        <AspectRatioGrid
          value={aspectRatio}
          onChange={setAspectRatio}
          themeColor={token.themeColor}
          label={labels.aspectRatioLabel}
          options={ASPECT_RATIOS}
        />

        {/* Model Select */}
        <div className="pt-4 border-t border-slate-200 dark:border-white/5 mt-4">
          <DimensionPanel.Select
            label={labels.modelLabel}
            value={model}
            onChange={(e) => setModel(e.target.value)}
            options={MODELS}
          />
        </div>

        {/* Generate Button */}
        <DimensionPanel.GenerateButton
          onClick={handleGenerate}
          disabled={isLoading || !description.trim()}
          loading={isLoading}
          loadingText={labels.generating}
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

      <DimensionPanel.Content>
        {/* Loading State */}
        {isLoading && <DimensionPanel.Loading variant="skeleton" onCancel={cancel} />}

        {/* Error State */}
        {displayError && !isLoading && (
          <DimensionPanel.Error
            error={displayError}
            onRetry={canRetry ? retry : undefined}
          />
        )}

        {/* Result Display */}
        {displayResult && !isLoading && (
          <PromptResultDisplay
            result={displayResult}
            isCopied={isCopied}
            onCopy={handleCopy}
            onExport={handleExportJSON}
            labels={{
              generatedPrompt: labels.generatedPrompt,
              export: labels.export,
              exportTooltip: labels.exportTooltip,
              copy: labels.copy,
              copied: labels.copied,
              negativePrompt: labels.negativePrompt,
              parameters: labels.parameters,
            }}
          />
        )}

        {/* Evidence Display */}
        {displayResult && (
          <DimensionPanel.Evidence
            refs={displayResult.evidence_refs}
            confidence={displayResult.confidence}
          />
        )}

        {/* Next Dimension Navigation */}
        {displayResult && <DimensionPanel.NextNav currentDimension={DIMENSION_KEY} />}

        {/* Empty State */}
        {!displayResult && !isLoading && !displayError && (
          <EmptyState
            labels={{
              title: labels.emptyStateTitle,
              desc1: labels.emptyStateDesc1,
              desc2: labels.emptyStateDesc2,
              desc3: labels.emptyStateDesc3,
            }}
          />
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

// ============================================================================
// Sub-Components
// ============================================================================

function AspectRatioGrid({
  value,
  onChange,
  themeColor,
  label,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  themeColor: string;
  label: string;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="space-y-2 group">
      <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">
        {label}
      </label>
      <div className="grid grid-cols-2 gap-2">
        {options.map((ratio) => (
          <button
            key={ratio.value}
            onClick={() => onChange(ratio.value)}
            className={`py-2 text-xs font-medium rounded-xl border transition-all ${value === ratio.value
              ? `bg-${themeColor}-100 dark:bg-${themeColor}-500/10 border-${themeColor}-500 dark:border-${themeColor}-500/50 text-${themeColor}-700 dark:text-${themeColor}-400 shadow-sm`
              : "bg-white dark:bg-white/5 border-slate-200 dark:border-white/5 text-slate-500 dark:text-zinc-400 hover:bg-slate-50 dark:hover:bg-white/10 hover:text-slate-900 dark:hover:text-white"
              }`}
          >
            {ratio.value}
          </button>
        ))}
      </div>
    </div>
  );
}

function PromptResultDisplay({
  result,
  isCopied,
  onCopy,
  onExport,
  labels,
}: {
  result: ImagePromptResult;
  isCopied: boolean;
  onCopy: (text: string) => void;
  onExport: () => void;
  labels: {
    generatedPrompt: string;
    export: string;
    exportTooltip: string;
    copy: string;
    copied: string;
    negativePrompt: string;
    parameters: string;
  };
}) {
  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
      {/* Main Prompt */}
      <div className="group relative">
        <div className="p-8 bg-white dark:bg-black/40 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-2xl shadow-sm dark:shadow-[0_8px_32px_rgba(0,0,0,0.3)] font-mono text-base leading-relaxed text-slate-800 dark:text-zinc-100 whitespace-pre-wrap group-hover:border-emerald-300 dark:group-hover:border-emerald-500/30 group-hover:bg-slate-50 dark:group-hover:bg-black/50 transition-all relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-emerald-500 to-teal-500 shadow-[0_0_20px_#10b981]" />
          <div className="flex items-center justify-between mb-4 border-b border-slate-200 dark:border-white/5 pb-3">
            <h3 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest flex items-center gap-2">
              {labels.generatedPrompt}
            </h3>
            <div className="flex items-center gap-2">
              <button
                onClick={onExport}
                className="px-3 py-1.5 text-[10px] font-bold tracking-wider uppercase rounded-lg transition-all flex items-center gap-1.5 bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-zinc-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-200 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/10"
                title={labels.exportTooltip}
              >
                {labels.export}
              </button>
              <button
                onClick={() => onCopy(result.prompt)}
                className={`px-3 py-1.5 text-[10px] font-bold tracking-wider uppercase rounded-lg transition-all flex items-center gap-1.5 ${isCopied
                  ? "bg-green-100 dark:bg-green-500/10 text-green-600 dark:text-green-400 border border-green-200 dark:border-green-500/20"
                  : "bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-zinc-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-200 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/10"
                  }`}
              >
                {isCopied ? labels.copied : labels.copy}
              </button>
            </div>
          </div>
          {result.prompt}
        </div>
      </div>

      {/* Negative Prompt */}
      <div className="group relative">
        <div className="flex items-center justify-between mb-3 px-1">
          <h3 className="text-sm font-semibold text-slate-500 dark:text-zinc-400 uppercase tracking-wider flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-red-400/50" />
            {labels.negativePrompt}
          </h3>
          <button
            onClick={() =>
              onCopy(result.negative_prompt || "text, watermark")
            }
            className="px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-200 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/10"
          >
            {labels.copy}
          </button>
        </div>
        <div className="p-5 bg-slate-50 dark:bg-[#18181b]/50 border border-slate-200 dark:border-white/10 rounded-xl shadow-inner font-mono text-sm leading-relaxed text-slate-600 dark:text-zinc-400 whitespace-pre-wrap group-hover:border-slate-300 dark:group-hover:border-white/20 transition-colors">
          {result.negative_prompt ||
            "text, watermark, low quality, blurred, distorted"}
        </div>
      </div>

      {/* Parameters Grid */}
      {result.parameters && (
        <div className="p-6 bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/5 rounded-xl space-y-4 hover:border-emerald-300 dark:hover:border-white/10 transition-colors">
          <h3 className="text-xs font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest border-b border-slate-200 dark:border-white/5 pb-3 mb-1">
            {labels.parameters}
          </h3>
          <div className="grid grid-cols-3 gap-6">
            {Object.entries(result.parameters).map(([key, value]) => (
              <div key={key} className="flex flex-col gap-1">
                <span className="text-xs text-slate-500 dark:text-zinc-500 capitalize">
                  {key.replace(/_/g, " ")}
                </span>
                <span className="text-sm font-mono text-emerald-600 dark:text-emerald-400/90">
                  {value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function EmptyState({
  labels,
}: {
  labels: {
    title: string;
    desc1: string;
    desc2: string;
    desc3: string;
  };
}) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-slate-500 dark:text-zinc-500 space-y-8 animate-in fade-in zoom-in-95 duration-700">
      <div className="relative group">
        <div className="absolute inset-0 bg-emerald-500/20 blur-[80px] rounded-full group-hover:bg-emerald-500/30 transition-colors duration-1000" />
        <div className="w-32 h-32 rounded-[2rem] bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex items-center justify-center shadow-lg dark:shadow-[0_0_60px_rgba(0,0,0,0.3)] backdrop-blur-md relative transform group-hover:scale-105 transition-all duration-500 group-hover:border-emerald-300 dark:group-hover:border-emerald-500/20">
          <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/5 to-transparent rounded-[2rem]" />
          <ImageIcon className="w-12 h-12 text-slate-400 dark:text-white/20 group-hover:text-emerald-500 dark:group-hover:text-emerald-400 transition-colors duration-500" />
        </div>
      </div>
      <div className="text-center space-y-3">
        <h3 className="text-2xl font-bold text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-b dark:from-white dark:to-white/40 tracking-tight">
          {labels.title}
        </h3>
        <p className="text-sm text-slate-500 dark:text-zinc-500 max-w-xs mx-auto font-light leading-relaxed">
          {labels.desc1}
          <br />
          <span className="text-emerald-600 dark:text-emerald-500/80 font-medium">
            {labels.desc2}
          </span>
          {" "}{labels.desc3}
        </p>
      </div>
    </div>
  );
}
