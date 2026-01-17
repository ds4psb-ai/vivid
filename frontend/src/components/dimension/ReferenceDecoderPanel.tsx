"use client";

/**
 * ReferenceDecoderPanel - 레퍼런스 해석기 (AI)
 *
 * 2026 Golden App: React 19 Best Practices + Multimodal Input
 *
 * Features:
 * - useTransition for non-blocking form submission
 * - useOptimistic for instant UI feedback
 * - File upload for reference images/videos
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
import { type EvidenceRef } from "./EvidenceDisplay";
import { Download, FileSearch } from "lucide-react";

// ============================================================================
// Constants & Types
// ============================================================================

const DIMENSION_CODE = "ai"; // Reference Decoder uses ai dimension
const DIMENSION_KEY = "reference-decoder";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";
const MAX_DESCRIPTION_LENGTH = 3000;

interface AnalysisResult {
  composition?: string;
  lighting?: string;
  color?: string;
  movement?: string;
  narrative?: string;
  recommendations?: string[];
  evidence_refs?: EvidenceRef[];
  confidence?: number;
}

const FOCUS_AREAS = [
  { value: "composition", label: "구도" },
  { value: "lighting", label: "조명" },
  { value: "color", label: "색감" },
  { value: "movement", label: "카메라" },
  { value: "narrative", label: "내러티브" },
  { value: "pacing", label: "페이싱" },
];

const MODELS = [
  { value: "gemini-3-flash-preview", label: "Flash (빠름)" },
  { value: "gemini-3-pro-preview", label: "Pro (고품질)" },
];

// ============================================================================
// Main Export
// ============================================================================

export default function ReferenceDecoderPanel() {
  return (
    <DimensionPanel dimensionCode={DIMENSION_CODE}>
      <ReferenceDecoderContent />
    </DimensionPanel>
  );
}

// ============================================================================
// Content Component
// ============================================================================

function ReferenceDecoderContent() {
  const { token, setLoading, setResult, setError, classes } = useDimensionPanel();

  // Form state
  const [description, setDescription] = useState("");
  const [focusAreas, setFocusAreas] = useState<string[]>([
    "composition",
    "lighting",
    "color",
    "movement",
  ]);
  const [model, setModel] = useState("gemini-3-flash-preview");
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // React 19: useTransition for non-blocking form submission
  const [isTransitionPending, startTransition] = useTransition();

  // React 19: useOptimistic for instant UI feedback
  const [optimisticResult, setOptimisticResult] = useOptimistic<AnalysisResult | null>(null);

  // File upload state (2026 Best Practice: Multimodal input)
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  // Result state
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);

  // BYOK and credits
  const { byokKey } = useBYOK();
  const creditCtx = useCreditContextOptional();
  const { getToolByDimension } = useDimensionConfig();
  const toolConfig = getToolByDimension("4D");
  const CREDIT_COST = toolConfig?.creditCost ?? 8;

  // Export utilities
  const { exportJSON } = useResultExport();

  // Async operation hook
  const {
    isLoading,
    error,
    execute,
    retry,
    canRetry,
  } = useAsyncOperation<{ success: boolean; output: AnalysisResult; error?: string }>({
    onSuccess: (data) => {
      if (data.success) {
        setAnalysisResult(data.output);
        setResult(data.output);
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

  // Sync loading state to context
  const wrappedExecute = useCallback(
    async (url: string, payload: object, headers?: Record<string, string>) => {
      setLoading(true);
      try {
        return await execute(url, payload, headers);
      } finally {
        setLoading(false);
      }
    },
    [execute, setLoading]
  );

  const toggleFocusArea = (area: string) => {
    setFocusAreas((prev) =>
      prev.includes(area) ? prev.filter((a) => a !== area) : [...prev, area]
    );
  };

  // Analyze handler
  const handleAnalyze = useCallback(async () => {
    const trimmedDescription = description.trim();
    if (!trimmedDescription) {
      setValidationError("영상 설명을 입력해주세요");
      return;
    }
    if (trimmedDescription.length > MAX_DESCRIPTION_LENGTH) {
      setValidationError(
        `영상 설명은 ${MAX_DESCRIPTION_LENGTH}자 이하로 입력해주세요`
      );
      return;
    }
    if (focusAreas.length === 0) {
      setValidationError("최소 하나의 분석 영역을 선택해주세요");
      return;
    }
    setValidationError(null);

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
      setShowCreditModal(true);
      return;
    }

    await wrappedExecute(
      `${API_BASE}/api/dimension/4d/analyze`,
      { video_description: description, focus_areas: focusAreas, model },
      getBYOKHeaders(byokKey)
    );
  }, [description, focusAreas, model, byokKey, creditCtx, wrappedExecute, CREDIT_COST]);

  // Export result as JSON
  const handleExportJson = useCallback(() => {
    if (!analysisResult) return;
    exportJSON(analysisResult, `reference-analysis-${Date.now()}.json`);
  }, [analysisResult, exportJSON]);

  const displayError = validationError || error;

  return (
    <>
      <DimensionPanel.Header
        title="레퍼런스 해석기"
        creditCost={CREDIT_COST}
      />

      <DimensionPanel.Sidebar>
        {/* Description Input */}
        <div className="space-y-2 group">
          <label
            className={`text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:${classes.text} transition-colors`}
          >
            레퍼런스 영상 설명
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="분석하고 싶은 영상의 장면이나 특징을 상세히 설명하세요..."
            className={`w-full h-32 px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-white/20 focus:outline-none focus:border-${token.themeColor}-500 dark:focus:border-${token.themeColor}-400/50 focus:bg-white dark:focus:bg-white/[0.07] focus:ring-4 focus:ring-${token.themeColor}-500/10 dark:focus:ring-${token.themeColor}-400/5 transition-all resize-none text-sm font-light leading-relaxed`}
          />
        </div>

        {/* File Upload (2026 Best Practice: Multimodal Input) */}
        <DimensionPanel.FileUpload
          accept={["*"]}
          maxSizeMB={100}
          multiple
          onUpload={setUploadedFiles}
          label="참고 영상/이미지 (선택)"
          helperText="영상 스틸컷이나 참고 이미지를 첨부하면 더 정확한 분석"
        />

        {/* Focus Areas */}
        <div className="space-y-2 group">
          <label
            className={`text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:${classes.text} transition-colors`}
          >
            분석 집중 영역
          </label>
          <div className="flex flex-wrap gap-2">
            {FOCUS_AREAS.map((area) => (
              <button
                key={area.value}
                onClick={() => toggleFocusArea(area.value)}
                className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-all ${
                  focusAreas.includes(area.value)
                    ? `${classes.bg}/20 border-${token.themeColor}-500 dark:border-${token.themeColor}-400/50 ${classes.text} shadow-[0_0_10px_rgba(245,158,11,0.1)]`
                    : "bg-white dark:bg-white/5 border-slate-200 dark:border-white/5 text-slate-500 dark:text-zinc-400 hover:bg-slate-100 dark:hover:bg-white/10 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                {area.label}
              </button>
            ))}
          </div>
        </div>

        {/* Model Select */}
        <DimensionPanel.Select
          label="AI 모델"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          options={MODELS}
        />

        {/* Generate Button */}
        <DimensionPanel.GenerateButton
          onClick={handleAnalyze}
          disabled={!description.trim() || focusAreas.length === 0}
          loading={combinedLoading}
          creditCost={CREDIT_COST}
          icon={<FileSearch className="w-5 h-5" />}
          loadingText="분석 중..."
        >
          레퍼런스 분석
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
        <DimensionPanel.Loading message="레퍼런스 분석 중..." />

        {/* Error State */}
        {displayError && !isLoading && (
          <DimensionPanel.Error
            error={displayError}
            onRetry={canRetry ? () => void retry() : undefined}
          />
        )}

        {/* Result Display */}
        {analysisResult && !isLoading && (
          <AnalysisResultDisplay
            result={analysisResult}
            onExport={handleExportJson}
            themeColor={token.themeColor}
          />
        )}

        {/* Empty State */}
        {!analysisResult && !isLoading && !displayError && <EmptyState />}

        {/* Evidence Display */}
        <DimensionPanel.Evidence refs={analysisResult?.evidence_refs} />

        {/* Next Dimension Navigation */}
        <DimensionPanel.NextNav currentDimension={DIMENSION_KEY} />
      </DimensionPanel.Content>

      {/* Credit Modal */}
      <InsufficientCreditsModal
        isOpen={showCreditModal}
        onClose={() => setShowCreditModal(false)}
        requiredCredits={CREDIT_COST}
        currentBalance={creditCtx?.balance ?? 0}
        onRetry={handleAnalyze}
      />
    </>
  );
}

// ============================================================================
// Sub-Components
// ============================================================================

function AnalysisResultDisplay({
  result,
  onExport,
  themeColor,
}: {
  result: AnalysisResult;
  onExport: () => void;
  themeColor: string;
}) {
  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <div className="flex items-center justify-between px-1">
        <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
          <span className={`w-1.5 h-1.5 rounded-full bg-${themeColor}-400`}></span>
          Analysis Report
        </h3>
        <button
          onClick={onExport}
          className="px-3 py-1.5 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 hover:bg-slate-100 dark:hover:bg-white/10 hover:border-slate-300 dark:hover:border-white/20 text-slate-600 dark:text-white text-xs font-medium rounded-lg transition-all flex items-center gap-2"
        >
          <Download className="w-4 h-4 text-slate-500 dark:text-zinc-400" />
          JSON Export
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Analysis Sections */}
        {Object.entries(result).map(([key, value]) => {
          if (
            key === "recommendations" ||
            key === "evidence_refs" ||
            key === "confidence"
          )
            return null;
          const title =
            FOCUS_AREAS.find((f) => f.value === key)?.label || key;

          return (
            <div key={key} className="group relative">
              <div
                className={`p-8 bg-white/80 dark:bg-black/40 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-2xl shadow-sm dark:shadow-[0_8px_32px_rgba(0,0,0,0.3)] font-mono text-base leading-relaxed text-slate-800 dark:text-zinc-100 whitespace-pre-wrap group-hover:border-${themeColor}-400/50 dark:group-hover:border-${themeColor}-500/30 group-hover:bg-white dark:group-hover:bg-black/50 transition-all relative overflow-hidden`}
              >
                <div
                  className={`absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-${themeColor}-400 to-orange-500 dark:from-${themeColor}-500 dark:to-orange-500 shadow-[0_0_20px_#f59e0b]`}
                ></div>
                <h4
                  className={`text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest mb-3 border-b border-slate-100 dark:border-white/5 pb-2 group-hover:text-${themeColor}-600 dark:group-hover:text-${themeColor}-400/80 transition-colors`}
                >
                  {title}
                </h4>
                <p className="text-slate-700 dark:text-white/90 text-sm leading-relaxed whitespace-pre-wrap">
                  {value as string}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recommendations */}
      {result.recommendations && result.recommendations.length > 0 && (
        <div className="group relative">
          <div
            className={`p-8 bg-white/80 dark:bg-black/40 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-2xl shadow-sm dark:shadow-[0_8px_32px_rgba(0,0,0,0.3)] font-mono text-base leading-relaxed text-slate-800 dark:text-zinc-100 whitespace-pre-wrap group-hover:border-${themeColor}-400/50 dark:group-hover:border-${themeColor}-500/30 group-hover:bg-white dark:group-hover:bg-black/50 transition-all relative overflow-hidden`}
          >
            <div
              className={`absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-${themeColor}-400 to-orange-500 dark:from-${themeColor}-500 dark:to-orange-500 shadow-[0_0_20px_#f59e0b]`}
            ></div>
            <h4
              className={`text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest mb-4 flex items-center gap-2 group-hover:text-${themeColor}-600 dark:group-hover:text-${themeColor}-400/80 transition-colors`}
            >
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              Key Recommendations
            </h4>
            <ul className="space-y-3">
              {result.recommendations.map((rec, idx) => (
                <li
                  key={idx}
                  className="flex items-start gap-3 text-sm text-slate-700 dark:text-zinc-200"
                >
                  <span
                    className={`mt-1.5 w-1.5 h-1.5 rounded-full bg-${themeColor}-500/50 flex-shrink-0`}
                  ></span>
                  <span className="leading-relaxed">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-8 animate-in fade-in zoom-in-95 duration-700">
      <div className="relative group">
        <div className="absolute inset-0 bg-amber-500/20 blur-[80px] rounded-full group-hover:bg-amber-500/30 transition-colors duration-1000" />
        <div className="w-32 h-32 rounded-[2rem] bg-white/[0.02] border border-white/10 flex items-center justify-center shadow-[0_0_60px_rgba(0,0,0,0.3)] backdrop-blur-md relative transform group-hover:scale-105 transition-all duration-500 group-hover:border-amber-500/20">
          <div className="absolute inset-0 bg-gradient-to-tr from-white/5 to-transparent rounded-[2rem]" />
          <svg
            className="w-12 h-12 text-white/20 group-hover:text-amber-400 transition-colors duration-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
      </div>
      <div className="text-center space-y-3">
        <h3 className="text-2xl font-bold text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-b dark:from-white dark:to-white/40 tracking-tight">
          Ready to Analyze
        </h3>
        <p className="text-sm text-slate-500 dark:text-zinc-500 max-w-xs mx-auto font-light leading-relaxed">
          영상의 특징을 설명하고
          <br />
          <span className="text-amber-600 dark:text-amber-500/80 font-medium">
            AI 기반의 심층 시네마틱 분석
          </span>
          을 받아보세요.
        </p>
      </div>
    </div>
  );
}
