"use client";

/**
 * QualityDirectorPanel - 퀄리티 디렉터 (QC)
 *
 * 2026 Golden App: React 19 Best Practices + Multi-criteria Assessment
 *
 * Features:
 * - useTransition for non-blocking form submission
 * - useOptimistic for instant UI feedback
 * - Multi-criteria quality assessment
 *
 * @see https://react.dev/blog/2024/12/05/react-19
 * @see docs/PANEL_DESIGN_UNITY_SPEC.md
 */

import { useState, useCallback, useEffect, useTransition, useOptimistic, useMemo } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import {
  useDimensionChainOptional,
  type ChainData,
} from "@/contexts/DimensionChainContext";
import { useChainDataInjection } from "@/hooks/useChainDataInjection";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import ChainDataInput from "./ChainDataInput";
import { type ThemeColor as DimensionThemeColor } from "@/lib/dimension-theme";
import { CheckCircle, XCircle, AlertTriangle, Download, Shield, Link2 } from "lucide-react";
import { useDNACardContextConsumer } from "@/hooks/useDNACardContextConsumer";
import { DNAContextBanner } from "@/components/dna-card/DNAContextBanner";
import { MASTER_AUTEURS } from "@/components/dna-card/constants";

// ============================================================================
// Constants & Types
// ============================================================================

const DIMENSION_CODE = "qc"; // Quality Director uses qc dimension
const DIMENSION_KEY = "quality-director"; // Chain context key
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";
const MAX_CONTENT_LENGTH = 5000;

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

interface CriterionResult {
  score: number;
  passed: boolean;
  details: string;
}

interface QualityResult {
  passed: boolean;
  score: number;
  criteria_results: Record<string, CriterionResult>;
  issues: string[];
  suggestions: string[];
}

const CONTENT_TYPES = [
  { value: "prompt", label: "프롬프트" },
  { value: "storyboard", label: "스토리보드" },
  { value: "script", label: "스크립트" },
  { value: "image_prompt", label: "이미지 프롬프트" },
];

const CRITERIA_OPTIONS = [
  { value: "aesthetic", label: "미적 품질", desc: "시각적 아름다움과 예술성" },
  { value: "ad_suitability", label: "광고 적합성", desc: "브랜드 및 광고 목적 부합" },
  { value: "consistency", label: "일관성", desc: "스타일 및 톤 일관성" },
  { value: "safety", label: "안전성", desc: "유해 콘텐츠 검출" },
  { value: "technical", label: "기술적 품질", desc: "해상도, 프레임 등" },
  { value: "narrative", label: "내러티브", desc: "스토리텔링 완성도" },
];

const getModels = (isKo: boolean) => [
  { value: "gemini-3-flash-preview", label: isKo ? "Flash (빠름)" : "Flash (Fast)" },
  { value: "gemini-3-pro-preview", label: isKo ? "Pro (고품질)" : "Pro (High Quality)" },
];

// ============================================================================
// Main Export
// ============================================================================

export default function QualityDirectorPanel() {
  return (
    <DimensionPanel dimensionCode={DIMENSION_CODE}>
      <QualityDirectorContent />
    </DimensionPanel>
  );
}

// ============================================================================
// Content Component
// ============================================================================

function QualityDirectorContent() {
  const { token, setLoading, setResult, setError, classes } = useDimensionPanel();
  const { language } = useLanguage();
  const isKo = language === "ko";
  const chainCtx = useDimensionChainOptional();

  // Set current dimension on mount
  useEffect(() => {
    if (chainCtx) {
      chainCtx.setCurrentDimension(DIMENSION_KEY);
    }
  }, [chainCtx]);

  // Chain Data Injection - auto-inject from video-maker, visual-realizer
  const {
    evidenceRefs: chainEvidenceRefs,
    hasUpstreamData,
    rawInputData,
  } = useChainDataInjection(DIMENSION_KEY);

  // DNA 카드 컨텍스트 상태
  const [dnaContextInfo, setDnaContextInfo] = useState<{
    type: "master" | "masterpiece" | null;
    name: string;
    auteurKey?: string;
  } | null>(null);

  // DNA 카드 컨텍스트 소비 - 거장 기준으로 품질 체크 기준 사전 설정
  const { dismissContext: dismissDNAContext } = useDNACardContextConsumer({
    onMasterContext: (auteurKey, metadata) => {
      const auteurInfo = MASTER_AUTEURS.find((a) => a.key === auteurKey);
      const auteurName = auteurInfo?.name ?? auteurKey;

      // 거장 특성에 따라 검수 기준 자동 설정
      const auteurCriteria: string[] = ["aesthetic", "consistency"];
      if (metadata.signatureTechniques?.some(t =>
        t.toLowerCase().includes("narrative") || t.toLowerCase().includes("story")
      )) {
        auteurCriteria.push("narrative");
      }
      if (metadata.signatureMoods?.some(m =>
        m.toLowerCase().includes("safe") || m.toLowerCase().includes("family")
      )) {
        auteurCriteria.push("safety");
      }
      setSelectedCriteria(auteurCriteria);

      setDnaContextInfo({
        type: "master",
        name: auteurName,
        auteurKey,
      });
    },
    autoConsume: false,
  });

  // DNA 컨텍스트 해제
  const handleDismissDNAContext = useCallback(() => {
    dismissDNAContext();
    setDnaContextInfo(null);
  }, [dismissDNAContext]);

  // Model options with i18n
  const MODELS = useMemo(() => getModels(isKo), [isKo]);

  // Form state
  const [content, setContent] = useState("");
  const [contentType, setContentType] = useState("prompt");
  const [selectedCriteria, setSelectedCriteria] = useState<string[]>([
    "aesthetic",
    "consistency",
    "safety",
  ]);
  const [_files, setFiles] = useState<File[]>([]);
  const [model, setModel] = useState("gemini-3-pro-preview");
  const [threshold, setThreshold] = useState(70);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Result state
  const [qualityResult, setQualityResult] = useState<QualityResult | null>(null);

  // Auto-apply upstream chain data (video-maker, visual-realizer prompts)
  useEffect(() => {
    if (!hasUpstreamData || content) return;

    // Type-safe access to rawInputData
    const typedInputData = rawInputData as Record<string, { output?: Record<string, unknown> } | undefined>;

    // Extract from visual-realizer
    const visualOutput = typedInputData["visual-realizer"]?.output;
    if (visualOutput?.prompt && typeof visualOutput.prompt === "string") {
      setContent(visualOutput.prompt);
      setContentType("image_prompt");
      return;
    }

    // Extract from video-maker
    const videoOutput = typedInputData["video-maker"]?.output;
    if (videoOutput?.prompt && typeof videoOutput.prompt === "string") {
      setContent(videoOutput.prompt);
      setContentType("prompt");
    }
  }, [hasUpstreamData, rawInputData, content]);

  // React 19: useTransition for non-blocking form submission
  const [isTransitionPending, startTransition] = useTransition();

  // React 19: useOptimistic for instant UI feedback
  const [optimisticStatus, setOptimisticStatus] = useOptimistic<"idle" | "checking" | "done">("idle");

  // BYOK and credits
  const { byokKey } = useBYOK();
  const creditCtx = useCreditContextOptional();
  const { getToolByDimension } = useDimensionConfig();
  const toolConfig = getToolByDimension("QC");
  const CREDIT_COST = toolConfig?.creditCost ?? 8;

  // Export utilities
  const { exportJSON } = useResultExport();

  // Async operation hook
  const { isLoading, error, execute, retry, canRetry } = useAsyncOperation<{
    success: boolean;
    output: QualityResult;
    error?: string;
  }>({
    onSuccess: (data) => {
      if (data.success) {
        setQualityResult(data.output);
        setResult(data.output);

        // Store QC result in chain context - completes the DNA→Story→Production chain
        if (chainCtx) {
          // Combine upstream evidence refs with any new refs
          const outputRefs = (data.output as unknown as { evidence_refs?: string[] }).evidence_refs || [];
          const combinedRefs = [...new Set([...chainEvidenceRefs, ...outputRefs])];

          chainCtx.setChainData(
            DIMENSION_KEY,
            {
              ...data.output,
              quality_score: data.output.score,
              quality_passed: data.output.passed,
            } as unknown as Record<string, unknown>,
            `QC ${data.output.passed ? "통과" : "미통과"}: ${data.output.score}점`,
            combinedRefs
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

  const toggleCriterion = (criterion: string) => {
    setSelectedCriteria((prev) =>
      prev.includes(criterion)
        ? prev.filter((c) => c !== criterion)
        : [...prev, criterion]
    );
  };

  const handleCheck = useCallback(() => {
    const trimmedContent = content.trim();
    if (!trimmedContent) {
      setValidationError("검수할 콘텐츠를 입력해주세요");
      return;
    }
    if (trimmedContent.length > MAX_CONTENT_LENGTH) {
      setValidationError(`콘텐츠는 ${MAX_CONTENT_LENGTH}자 이하로 입력해주세요`);
      return;
    }
    if (selectedCriteria.length === 0) {
      setValidationError("최소 하나의 검수 기준을 선택해주세요");
      return;
    }
    setValidationError(null);

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
      setShowCreditModal(true);
      return;
    }

    // React 19: Non-blocking transition with optimistic UI
    startTransition(async () => {
      setOptimisticStatus("checking");
      await wrappedExecute(
        `${API_BASE}/api/dimension/quality/check`,
        {
          content,
          content_type: contentType,
          criteria: selectedCriteria,
          model,
          threshold,
        },
        getBYOKHeaders(byokKey)
      );
      setOptimisticStatus("done");
    });
  }, [
    content,
    contentType,
    selectedCriteria,
    model,
    threshold,
    byokKey,
    creditCtx,
    wrappedExecute,
    CREDIT_COST,
    startTransition,
    setOptimisticStatus,
  ]);

  // Export result as JSON
  const handleExportJson = useCallback(() => {
    if (!qualityResult) return;
    exportJSON(qualityResult, `quality-check-${Date.now()}.json`);
  }, [qualityResult, exportJSON]);

  // Handle chain data from previous dimensions (video-maker, visual-realizer)
  const handleApplyChainData = useCallback((data: Record<string, ChainData>) => {
    // Type-safe extraction helper
    const getStringValue = (obj: unknown, key: string): string | undefined => {
      if (obj && typeof obj === "object" && key in obj) {
        const val = (obj as Record<string, unknown>)[key];
        return typeof val === "string" ? val : undefined;
      }
      return undefined;
    };

    // From visual-realizer: get generated image prompt for QC
    const visualOutput = data["visual-realizer"]?.output as Record<string, unknown> | undefined;
    const visualPrompt = getStringValue(visualOutput, "prompt");
    if (visualPrompt && !content) {
      setContent(visualPrompt);
      setContentType("image_prompt");
    }

    // From video-maker: get video info for QC
    const videoOutput = data["video-maker"]?.output as Record<string, unknown> | undefined;
    const videoPrompt = getStringValue(videoOutput, "prompt");
    if (videoPrompt && !content) {
      setContent(videoPrompt);
      setContentType("prompt");
    }
  }, [content]);

  // Combined loading state: async operation OR React 19 transition
  const isPending = isLoading || isTransitionPending;
  const displayError = validationError || error;

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-400";
    if (score >= 60) return "text-amber-400";
    return "text-rose-400";
  };

  return (
    <>
      <DimensionPanel.Header title="퀄리티 디렉터" creditCost={CREDIT_COST} />

      <DimensionPanel.Sidebar>
        {/* Upstream Data Banner */}
        {hasUpstreamData && (
          <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg animate-in fade-in slide-in-from-top-2">
            <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
              <Link2 className="w-4 h-4" />
              <span className="text-xs font-medium">
                Production 데이터가 자동 적용됩니다
              </span>
            </div>
            <p className="text-[10px] text-amber-500/70 mt-1 ml-6">
              Video Maker / Visual Realizer 결과물 검수
            </p>
          </div>
        )}

        {/* DNA Context Banner */}
        {dnaContextInfo && (
          <DNAContextBanner
            cardType={dnaContextInfo.type!}
            cardName={dnaContextInfo.name}
            onDismiss={handleDismissDNAContext}
            additionalInfo={`거장 품질 기준 적용됨`}
            className="mb-4"
          />
        )}

        {/* Chain Data Input - data from video-maker, visual-realizer */}
        <ChainDataInput
          currentDimension={DIMENSION_KEY}
          onApplyData={handleApplyChainData}
          themeColor={CHAIN_INPUT_THEME_MAP[token.themeColor] || "amber"}
        />

        {/* Content Input */}
        <DimensionPanel.Textarea
          label="검수 콘텐츠"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="검수할 프롬프트, 스크립트, 또는 스토리보드를 입력하세요..."
          rows={6}
        />

        {/* File Upload */}
        <DimensionPanel.FileUpload
          accept={["*"]}
          maxSizeMB={100}
          multiple
          onUpload={setFiles}
          label="검수 자료 (선택)"
          helperText="영상 스틸컷, 스크립트 PDF 등"
        />

        {/* Content Type */}
        <div className="space-y-2">
          <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">
            콘텐츠 유형
          </label>
          <div className="grid grid-cols-2 gap-2">
            {CONTENT_TYPES.map((type) => (
              <button
                key={type.value}
                onClick={() => setContentType(type.value)}
                className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  contentType === type.value
                    ? `${classes.bg}/20 ${classes.text} border border-${token.themeColor}-500/30`
                    : "bg-white dark:bg-white/5 text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/10 border border-transparent"
                }`}
              >
                {type.label}
              </button>
            ))}
          </div>
        </div>

        {/* Criteria Selection */}
        <div className="space-y-2">
          <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">
            검수 기준
          </label>
          <div className="space-y-2">
            {CRITERIA_OPTIONS.map((criterion) => (
              <button
                key={criterion.value}
                onClick={() => toggleCriterion(criterion.value)}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-left transition-all ${
                  selectedCriteria.includes(criterion.value)
                    ? `${classes.bg}/10 border border-${token.themeColor}-500/30`
                    : "bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/20"
                }`}
              >
                <div>
                  <div
                    className={`text-sm font-medium ${
                      selectedCriteria.includes(criterion.value)
                        ? classes.text
                        : "text-slate-700 dark:text-zinc-300"
                    }`}
                  >
                    {criterion.label}
                  </div>
                  <div className="text-[10px] text-slate-500 dark:text-zinc-500">
                    {criterion.desc}
                  </div>
                </div>
                <div
                  className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                    selectedCriteria.includes(criterion.value)
                      ? `border-${token.themeColor}-500 bg-${token.themeColor}-500`
                      : "border-slate-300 dark:border-white/20"
                  }`}
                >
                  {selectedCriteria.includes(criterion.value) && (
                    <svg
                      className="w-3 h-3 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={3}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Threshold Slider */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">
              통과 기준
            </label>
            <span className={`text-sm font-mono ${classes.text}`}>{threshold}점</span>
          </div>
          <input
            type="range"
            min="50"
            max="95"
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
            className={`w-full accent-${token.themeColor}-500`}
          />
        </div>

        {/* Model Select */}
        <DimensionPanel.Select
          label="AI 모델"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          options={MODELS}
        />

        {/* Generate Button - React 19: Combined pending state */}
        <DimensionPanel.GenerateButton
          onClick={handleCheck}
          disabled={!content.trim() || selectedCriteria.length === 0}
          loading={isPending}
          creditCost={CREDIT_COST}
          icon={<Shield className="w-5 h-5" />}
          loadingText={optimisticStatus === "checking" ? "품질 검수 중..." : "검수 중..."}
        >
          품질 검수 시작
        </DimensionPanel.GenerateButton>

        {/* Validation Error */}
        {validationError && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs">
            {validationError}
          </div>
        )}
      </DimensionPanel.Sidebar>

      <DimensionPanel.Content>
        {/* Loading State - React 19: Shows during transition */}
        <DimensionPanel.Loading message={optimisticStatus === "checking" ? "품질 기준별 검수 중..." : "품질 검수 중..."} />

        {/* Error State */}
        {displayError && !isPending && (
          <DimensionPanel.Error
            error={displayError}
            onRetry={canRetry ? () => void retry() : undefined}
          />
        )}

        {/* Result Display */}
        {qualityResult && !isPending && (
          <QualityResultDisplay
            result={qualityResult}
            onExport={handleExportJson}
            selectedCriteria={selectedCriteria}
            getScoreColor={getScoreColor}
            themeColor={token.themeColor}
          />
        )}

        {/* Evidence Display */}
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        <DimensionPanel.Evidence refs={(qualityResult as any)?.evidence_refs} />

        {/* Empty State */}
        {!qualityResult && !isPending && !displayError && (
          <EmptyState themeColor={token.themeColor} />
        )}

        {/* Next Dimension Navigation */}
        <DimensionPanel.NextNav currentDimension={DIMENSION_KEY} />
      </DimensionPanel.Content>

      {/* Credit Modal */}
      <InsufficientCreditsModal
        isOpen={showCreditModal}
        onClose={() => setShowCreditModal(false)}
        requiredCredits={CREDIT_COST}
        currentBalance={creditCtx?.balance ?? 0}
        onRetry={handleCheck}
      />
    </>
  );
}

// ============================================================================
// Sub-Components
// ============================================================================

function QualityResultDisplay({
  result,
  onExport,
  selectedCriteria,
  getScoreColor,
  themeColor,
}: {
  result: QualityResult;
  onExport: () => void;
  selectedCriteria: string[];
  getScoreColor: (score: number) => string;
  themeColor: string;
}) {
  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
      {/* Export Button */}
      <div className="flex justify-end">
        <button
          onClick={onExport}
          className="px-4 py-2 bg-white dark:bg-white/5 hover:bg-slate-100 dark:hover:bg-white/10 border border-slate-200 dark:border-white/10 rounded-lg flex items-center gap-2 text-sm text-slate-600 dark:text-white/70 hover:text-slate-900 dark:hover:text-white transition-all"
        >
          <Download className="w-4 h-4" />
          JSON 내보내기
        </button>
      </div>

      {/* Overall Score */}
      <div className="relative overflow-hidden rounded-3xl bg-white/80 dark:bg-black/40 backdrop-blur-xl border border-slate-200 dark:border-white/10 p-8">
        <div
          className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-${themeColor}-500 to-pink-500`}
        />
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {result.passed ? (
              <CheckCircle className="w-16 h-16 text-emerald-400" />
            ) : (
              <XCircle className="w-16 h-16 text-rose-400" />
            )}
            <div>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                {result.passed ? "검수 통과" : "검수 미통과"}
              </h2>
              <p className="text-sm text-slate-500 dark:text-zinc-400">
                {selectedCriteria.length}개 기준 검사 완료
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className={`text-5xl font-bold ${getScoreColor(result.score)}`}>
              {result.score}
            </div>
            <div className="text-xs text-slate-500 dark:text-zinc-500 uppercase tracking-wider">
              / 100
            </div>
          </div>
        </div>
      </div>

      {/* Criteria Results */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(result.criteria_results).map(([key, criterion]) => (
          <div
            key={key}
            className={`p-5 rounded-2xl border backdrop-blur-sm transition-all ${
              criterion.passed
                ? "bg-emerald-50 dark:bg-emerald-500/5 border-emerald-200 dark:border-emerald-500/20"
                : "bg-rose-50 dark:bg-rose-500/5 border-rose-200 dark:border-rose-500/20"
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                {criterion.passed ? (
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                )}
                <span className="text-sm font-semibold text-slate-900 dark:text-white capitalize">
                  {CRITERIA_OPTIONS.find((c) => c.value === key)?.label || key}
                </span>
              </div>
              <span className={`text-lg font-bold ${getScoreColor(criterion.score)}`}>
                {criterion.score}
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-zinc-400 leading-relaxed">
              {criterion.details}
            </p>
          </div>
        ))}
      </div>

      {/* Issues */}
      {result.issues.length > 0 && (
        <div className="p-6 bg-rose-50 dark:bg-rose-500/5 border border-rose-200 dark:border-rose-500/20 rounded-2xl">
          <h3 className="text-sm font-bold text-rose-600 dark:text-rose-400 uppercase tracking-wider mb-4 flex items-center gap-2">
            <XCircle className="w-4 h-4" />
            발견된 문제점
          </h3>
          <ul className="space-y-2">
            {result.issues.map((issue, i) => (
              <li
                key={i}
                className="text-sm text-slate-700 dark:text-zinc-300 flex items-start gap-2"
              >
                <span className="text-rose-500 dark:text-rose-400 mt-1">•</span>
                {issue}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Suggestions */}
      {result.suggestions.length > 0 && (
        <div className="p-6 bg-sky-50 dark:bg-sky-500/5 border border-sky-200 dark:border-sky-500/20 rounded-2xl">
          <h3 className="text-sm font-bold text-sky-600 dark:text-sky-400 uppercase tracking-wider mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            개선 제안
          </h3>
          <ul className="space-y-2">
            {result.suggestions.map((suggestion, i) => (
              <li
                key={i}
                className="text-sm text-slate-700 dark:text-zinc-300 flex items-start gap-2"
              >
                <span className="text-sky-500 dark:text-sky-400 mt-1">→</span>
                {suggestion}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function EmptyState({ themeColor }: { themeColor: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-8">
      <div className="relative group">
        <div
          className={`absolute inset-0 bg-${themeColor}-500/20 blur-[80px] rounded-full`}
        />
        <div
          className={`w-32 h-32 rounded-[2rem] bg-white/[0.02] border border-white/10 flex items-center justify-center backdrop-blur-md relative group-hover:border-${themeColor}-500/20 transition-all`}
        >
          <CheckCircle
            className={`w-12 h-12 text-white/20 group-hover:text-${themeColor}-400 transition-colors`}
          />
        </div>
      </div>
      <div className="text-center space-y-3">
        <h3 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
          품질 검수 대기
        </h3>
        <p className="text-sm text-slate-500 dark:text-zinc-500 max-w-xs mx-auto font-light leading-relaxed">
          좌측 패널에서 콘텐츠와 검수 기준을 설정하고
          <br />
          <span className={`text-${themeColor}-600 dark:text-${themeColor}-400 font-medium`}>
            6가지 기준
          </span>
          으로 품질을 검증하세요.
        </p>
      </div>
    </div>
  );
}
