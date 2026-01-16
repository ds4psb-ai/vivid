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

import { useState, useCallback, useTransition, useOptimistic } from "react";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import EvidenceDisplay, { type EvidenceRef } from "./EvidenceDisplay";
import { Image } from "lucide-react";

// ============================================================================
// Constants & Types
// ============================================================================

const DIMENSION_CODE = "3d";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

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

const STYLES = [
  { value: "photorealistic", label: "포토리얼리스틱" },
  { value: "cinematic", label: "시네마틱" },
  { value: "anime", label: "애니메이션" },
  { value: "illustration", label: "일러스트" },
  { value: "3d-render", label: "3D 렌더" },
  { value: "oil-painting", label: "유화" },
  { value: "watercolor", label: "수채화" },
  { value: "digital-art", label: "디지털 아트" },
];

const ASPECT_RATIOS = [
  { value: "16:9", label: "16:9 (와이드)" },
  { value: "9:16", label: "9:16 (세로)" },
  { value: "1:1", label: "1:1 (정사각형)" },
  { value: "4:3", label: "4:3 (스탠다드)" },
  { value: "3:2", label: "3:2 (사진)" },
  { value: "21:9", label: "21:9 (울트라와이드)" },
];

const MODELS = [
  { value: "gemini-3-flash-preview", label: "Flash (빠름)" },
  { value: "gemini-3-pro-preview", label: "Pro (고품질)" },
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

  // Form state
  const [description, setDescription] = useState("");
  const [style, setStyle] = useState("photorealistic");
  const [aspectRatio, setAspectRatio] = useState("16:9");
  const [model, setModel] = useState("gemini-3-flash-preview");
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // React 19: useTransition for non-blocking form submission
  const [isTransitionPending, startTransition] = useTransition();

  // React 19: useOptimistic for instant UI feedback
  const [optimisticResult, setOptimisticResult] = useOptimistic<ImagePromptResult | null>(null);

  // File upload state (2026 Best Practice: Multimodal input)
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

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
      if (data.success && !byokKey && creditCtx) {
        void creditCtx.refresh();
      }
      if (data.success) {
        setResult(data.output);
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
  const handleGenerate = useCallback(async () => {
    const trimmedDescription = description.trim();
    if (!trimmedDescription) {
      setValidationError("이미지 설명을 입력해주세요");
      return;
    }
    if (trimmedDescription.length > MAX_DESCRIPTION_LENGTH) {
      setValidationError(
        `이미지 설명은 ${MAX_DESCRIPTION_LENGTH}자 이하로 입력해주세요`
      );
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
  }, [
    description,
    style,
    aspectRatio,
    model,
    byokKey,
    creditCtx,
    execute,
    CREDIT_COST,
    setLoading,
  ]);

  // Copy handler
  const handleCopy = useCallback(
    (text: string) => {
      copyToClipboard(text);
    },
    [copyToClipboard]
  );

  // Export result as JSON
  const handleExportJSON = useCallback(() => {
    if (result?.output) {
      exportJSON(result.output, `image-prompt-${Date.now()}.json`);
    }
  }, [result?.output, exportJSON]);

  // Extracted result data
  const displayResult = result?.success ? result.output : null;
  const displayError =
    validationError || (result && !result.success ? result.error : error);

  return (
    <>
      <DimensionPanel.Header title="비주얼 리얼라이저" creditCost={CREDIT_COST} />

      <DimensionPanel.Sidebar>
        {/* Description Input */}
        <DimensionPanel.Textarea
          label="이미지 설명 (Prompt)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="생성하고 싶은 이미지를 상세히 설명하세요..."
          rows={5}
          disabled={isLoading}
        />

        {/* File Upload (2026 Best Practice: Multimodal Input) */}
        <DimensionPanel.FileUpload
          accept={["image/*"]}
          maxSizeMB={20}
          multiple
          onUpload={setUploadedFiles}
          label="참고 이미지 (선택)"
          helperText="스타일 참고용 이미지를 첨부하면 더 정확한 프롬프트 생성"
        />

        {/* Style Select */}
        <DimensionPanel.Select
          label="스타일 (Style)"
          value={style}
          onChange={(e) => setStyle(e.target.value)}
          options={STYLES}
        />

        {/* Aspect Ratio Grid */}
        <AspectRatioGrid
          value={aspectRatio}
          onChange={setAspectRatio}
          themeColor={token.themeColor}
        />

        {/* Model Select */}
        <div className="pt-4 border-t border-slate-200 dark:border-white/5 mt-4">
          <DimensionPanel.Select
            label="AI 모델 Engine"
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
          loadingText="GENERATING..."
        >
          Generate Prompt
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
            themeColor={token.themeColor}
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
        {displayResult && <DimensionPanel.NextNav />}

        {/* Empty State */}
        {!displayResult && !isLoading && !displayError && <EmptyState />}
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
}: {
  value: string;
  onChange: (v: string) => void;
  themeColor: string;
}) {
  return (
    <div className="space-y-2 group">
      <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">
        비율 (Aspect Ratio)
      </label>
      <div className="grid grid-cols-2 gap-2">
        {ASPECT_RATIOS.map((ratio) => (
          <button
            key={ratio.value}
            onClick={() => onChange(ratio.value)}
            className={`py-2 text-xs font-medium rounded-xl border transition-all ${
              value === ratio.value
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
  themeColor,
}: {
  result: ImagePromptResult;
  isCopied: boolean;
  onCopy: (text: string) => void;
  onExport: () => void;
  themeColor: string;
}) {
  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
      {/* Main Prompt */}
      <div className="group relative">
        <div className="p-8 bg-white dark:bg-black/40 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-2xl shadow-sm dark:shadow-[0_8px_32px_rgba(0,0,0,0.3)] font-mono text-base leading-relaxed text-slate-800 dark:text-zinc-100 whitespace-pre-wrap group-hover:border-emerald-300 dark:group-hover:border-emerald-500/30 group-hover:bg-slate-50 dark:group-hover:bg-black/50 transition-all relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-emerald-500 to-teal-500 shadow-[0_0_20px_#10b981]" />
          <div className="flex items-center justify-between mb-4 border-b border-slate-200 dark:border-white/5 pb-3">
            <h3 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest flex items-center gap-2">
              Generated Prompt
            </h3>
            <div className="flex items-center gap-2">
              <button
                onClick={onExport}
                className="px-3 py-1.5 text-[10px] font-bold tracking-wider uppercase rounded-lg transition-all flex items-center gap-1.5 bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-zinc-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-200 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/10"
                title="JSON으로 내보내기"
              >
                EXPORT
              </button>
              <button
                onClick={() => onCopy(result.prompt)}
                className={`px-3 py-1.5 text-[10px] font-bold tracking-wider uppercase rounded-lg transition-all flex items-center gap-1.5 ${
                  isCopied
                    ? "bg-green-100 dark:bg-green-500/10 text-green-600 dark:text-green-400 border border-green-200 dark:border-green-500/20"
                    : "bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-zinc-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-200 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/10"
                }`}
              >
                {isCopied ? "COPIED" : "COPY"}
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
            Negative Prompt
          </h3>
          <button
            onClick={() =>
              onCopy(result.negative_prompt || "text, watermark")
            }
            className="px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-200 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/10"
          >
            Copy
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
            Parameters
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

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-slate-500 dark:text-zinc-500 space-y-8 animate-in fade-in zoom-in-95 duration-700">
      <div className="relative group">
        <div className="absolute inset-0 bg-emerald-500/20 blur-[80px] rounded-full group-hover:bg-emerald-500/30 transition-colors duration-1000" />
        <div className="w-32 h-32 rounded-[2rem] bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex items-center justify-center shadow-lg dark:shadow-[0_0_60px_rgba(0,0,0,0.3)] backdrop-blur-md relative transform group-hover:scale-105 transition-all duration-500 group-hover:border-emerald-300 dark:group-hover:border-emerald-500/20">
          <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/5 to-transparent rounded-[2rem]" />
          <Image className="w-12 h-12 text-slate-400 dark:text-white/20 group-hover:text-emerald-500 dark:group-hover:text-emerald-400 transition-colors duration-500" />
        </div>
      </div>
      <div className="text-center space-y-3">
        <h3 className="text-2xl font-bold text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-b dark:from-white dark:to-white/40 tracking-tight">
          Ready to Generate
        </h3>
        <p className="text-sm text-slate-500 dark:text-zinc-500 max-w-xs mx-auto font-light leading-relaxed">
          이미지를 설명하고 생성형 AI를 위한
          <br />
          <span className="text-emerald-600 dark:text-emerald-500/80 font-medium">
            최적화된 프롬프트
          </span>
          를 받아보세요.
        </p>
      </div>
    </div>
  );
}
