"use client";

/**
 * AestheticDirectorPanel - 미학디렉터 (AD)
 *
 * 2026 Golden App: UQSL Full Integration
 *
 * 3-Stage Visual Identity Workshop:
 * 1. Moodboard: UQSL Multi-Generate → 3 Visual Directions (SSE Streaming)
 * 2. Palette: Direction Selection → Thompson Sampling Feedback
 * 3. Guide: Final Style Guide → useOptimistic + Evidence Display
 *
 * Features:
 * - SSE Streaming for real-time progress
 * - Quality Scores (5-Dimension) visualization
 * - Thompson Sampling feedback loop
 * - Optimistic UI updates (React 19)
 * - Evidence refs display
 *
 * @see UQSL_SPEC.md
 * @see docs/PANEL_DESIGN_UNITY_SPEC.md
 */

import {
  useState,
  useCallback,
  useOptimistic,
  useTransition,
  useMemo,
} from "react";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import { useLanguage } from "@/contexts/LanguageContext";
import { useUQSLGenerate, useUQSLFeedback } from "@/hooks/useUQSL";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import {
  Palette,
  Copy,
  Check,
  Download,
  Sparkles,
  Eye,
  Wand2,
  Code,
  Type,
  Layers,
  TrendingUp,
  Zap,
} from "lucide-react";
import { EvidenceCard } from "@/components/ui/EvidenceCard";

// ============================================================================
// Constants & Types
// ============================================================================

const DIMENSION_CODE = "ad";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

interface AestheticResult {
  visual_guidelines: {
    composition?: string;
    lighting?: string;
    camera?: string;
    pacing?: string;
  };
  color_palette: string[];
  style_keywords: string[];
  avoid_elements: string[];
  auteur_influence?: {
    name: string;
    style_summary: string;
    signature_elements: string[];
  };
  textures?: string[];
  typography?: {
    primary: string;
    secondary: string;
    description: string;
  };
  generative_prompts?: {
    midjourney: string;
    veo: string;
  };
  evidence_refs?: string[];
}

interface VisualDirection {
  id: string;
  idx: number;
  title: string;
  description: string;
  keywords: string[];
  suggested_auteur: string;
  color_preview: string[];
  qualityScore?: {
    groundedness: number;
    relevance: number;
    coherence: number;
    creativity: number;
    safety: number;
    total_score: number;
  };
  isRecommended?: boolean;
}

type Stage = "moodboard" | "palette" | "guide";

const getMoods = (isKo: boolean) => [
  { value: "neutral", label: isKo ? "중립" : "Neutral" },
  { value: "dramatic", label: isKo ? "드라마틱" : "Dramatic" },
  { value: "calm", label: isKo ? "차분함" : "Calm" },
  { value: "energetic", label: isKo ? "에너지틱" : "Energetic" },
  { value: "melancholic", label: isKo ? "멜랑콜릭" : "Melancholic" },
  { value: "mysterious", label: isKo ? "미스터리" : "Mysterious" },
  { value: "romantic", label: isKo ? "로맨틱" : "Romantic" },
];

const getTargetMediums = (isKo: boolean) => [
  { value: "video", label: isKo ? "비디오" : "Video" },
  { value: "image", label: isKo ? "이미지" : "Image" },
  { value: "animation", label: isKo ? "애니메이션" : "Animation" },
];

// ============================================================================
// Main Panel Component
// ============================================================================

export default function AestheticDirectorPanel() {
  return (
    <DimensionPanel dimensionCode={DIMENSION_CODE}>
      <AestheticDirectorContent />
    </DimensionPanel>
  );
}

// ============================================================================
// Panel Content (Inner Component)
// ============================================================================

function AestheticDirectorContent() {
  const { token, setLoading, setResult, setError: setContextError } =
    useDimensionPanel();
  const { language } = useLanguage();
  const isKo = language === "ko";

  // i18n presets
  const MOODS = useMemo(() => getMoods(isKo), [isKo]);
  const TARGET_MEDIUMS = useMemo(() => getTargetMediums(isKo), [isKo]);

  // i18n labels
  const labels = useMemo(() => ({
    // Header
    title: isKo ? "미학디렉터" : "Aesthetic Director",

    // Stages
    stageInspiration: isKo ? "영감" : "Inspiration",
    stagePalette: isKo ? "팔레트" : "Palette",
    stageGuide: isKo ? "가이드" : "Guide",

    // Inputs
    conceptLabel: isKo ? "컨셉 / 주제" : "Concept / Theme",
    conceptPlaceholder: isKo ? "시각적 스타일을 정의할 컨셉을 입력하세요..." : "Enter a concept to define the visual style...",
    referenceLabel: isKo ? "레퍼런스 (선택)" : "Reference (Optional)",
    referenceHelper: isKo ? "무드보드, 컬러 레퍼런스, 영상 스틸" : "Moodboards, color references, video stills",
    moodLabel: isKo ? "분위기" : "Mood",
    mediaLabel: isKo ? "미디어" : "Media",

    // RAG Toggle
    ragContext: isKo ? "RAG 컨텍스트" : "RAG Context",
    ragDescription: isKo ? "레퍼런스 검색 활성화" : "Enable reference search",

    // Quality Scores Toggle
    qualityScores: isKo ? "5차원 품질 점수 표시" : "Show 5D Quality Scores",

    // Buttons
    exploreDirections: isKo ? "비주얼 방향 탐색 (UQSL)" : "Explore Visual Directions (UQSL)",
    findingInspiration: isKo ? "영감 찾는 중..." : "Finding inspiration...",
    completeStyleGuide: isKo ? "스타일 가이드 완성" : "Complete Style Guide",
    generatingStyleGuide: isKo ? "스타일 가이드 생성 중..." : "Generating style guide...",
    selectOtherDirection: isKo ? "다른 방향 선택하기" : "Select Another Direction",
    cancel: isKo ? "취소" : "Cancel",

    // Credit Cost
    estimatedCost: (cost: string | number) => isKo ? `예상 비용: ${cost} 크레딧` : `Estimated cost: ${cost} credits`,

    // Selected Direction Card
    selectedDirection: isKo ? "선택된 방향" : "Selected Direction",
    aiRecommended: isKo ? "AI 추천" : "AI Recommended",
    likeIt: isKo ? "좋아요" : "Like",
    notGreat: isKo ? "아쉬워요" : "Not Great",

    // Palette Lab
    selectVisualDirection: isKo ? "시각적 방향을 선택하세요" : "Select a Visual Direction",
    aiRecommendedDirection: (idx: number) => isKo ? `AI 추천: Direction ${idx + 1}` : `AI Recommended: Direction ${idx + 1}`,
    suggestedDirector: isKo ? "추천 감독:" : "Suggested director:",
    recommended: isKo ? "추천" : "Recommended",

    // Quality Score Labels
    groundedness: isKo ? "근거" : "Groundedness",
    relevance: isKo ? "관련" : "Relevance",
    coherence: isKo ? "일관" : "Coherence",
    creativity: isKo ? "창의" : "Creativity",
    safety: isKo ? "안전" : "Safety",

    // Feedback Section
    feedbackSaved: isKo ? "피드백이 저장되었습니다" : "Feedback saved",
    satisfiedWithResults: isKo ? "결과가 만족스러우셨나요?" : "Were you satisfied with the results?",

    // Style Guide
    generatingGuide: isKo ? "스타일 가이드 생성 중..." : "Generating style guide...",
    exportJson: isKo ? "JSON 내보내기" : "Export JSON",
    avoidElements: isKo ? "피해야 할 요소" : "Elements to Avoid",

    // Validation
    enterConcept: isKo ? "컨셉을 입력해주세요" : "Please enter a concept",

    // Empty State
    emptyStateTitle: isKo ? "Visual Identity Workshop" : "Visual Identity Workshop",
    emptyStateDescription: isKo ? "컨셉을 입력하면 AI가" : "Enter a concept and AI will",
    emptyStateHighlight: isKo ? "UQSL로 3가지 시각적 방향" : "suggest 3 visual directions with UQSL",
    emptyStateSuffix: isKo ? "을 제안합니다." : ".",
  }), [isKo]);

  // Form state
  const [concept, setConcept] = useState("");
  const [mood, setMood] = useState("neutral");
  const [targetMedium, setTargetMedium] = useState("video");
  const [useRag, setUseRag] = useState(true);

  // Visual Identity Workshop State
  const [stage, setStage] = useState<Stage>("moodboard");
  const [directions, setDirections] = useState<VisualDirection[]>([]);
  const [selectedDirection, setSelectedDirection] =
    useState<VisualDirection | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  // React 19: useTransition for non-blocking stage transitions
  const [isTransitionPending, startTransition] = useTransition();

  // Optimistic UI state (React 19)
  const [optimisticResult, setOptimisticResult] = useOptimistic<AestheticResult | null>(null);

  // UI state
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [_files, setFiles] = useState<File[]>([]); // Reference files for moodboard
  const [showQualityScores, setShowQualityScores] = useState(true);

  // Hooks
  const { byokKey } = useBYOK();
  const creditCtx = useCreditContextOptional();
  const { getToolByDimension } = useDimensionConfig();
  const toolConfig = getToolByDimension("AD");
  const CREDIT_COST = toolConfig?.creditCost ?? 10;

  // Export utilities
  const { exportJSON, copyToClipboard } = useResultExport();

  // UQSL Hooks (2026 Best Practice)
  const {
    progress: uqslProgress,
    message: uqslMessage,
    stage: uqslStage,
    candidates: uqslCandidates,
    qualityScores: uqslQualityScores,
    recommendedIdx,
    armsStats,
    isLoading: isUqslLoading,
    error: uqslError,
    generate: generateUQSL,
    abort: abortUQSL,
    reset: resetUQSL,
  } = useUQSLGenerate({
    onComplete: (response) => {
      // Transform UQSL candidates to VisualDirections
      const newDirections: VisualDirection[] = response.candidates.map(
        (candidate, idx) => {
          // Parse the content to extract visual direction data
          const content =
            typeof candidate.content === "string"
              ? JSON.parse(candidate.content)
              : candidate.content;

          return {
            id: `direction-${idx}`,
            idx,
            title: content.title || `Direction ${idx + 1}`,
            description: content.description || "",
            keywords: content.keywords || [],
            suggested_auteur: content.suggested_auteur || "",
            color_preview: content.color_preview || [
              "#3B82F6",
              "#8B5CF6",
              "#EC4899",
            ],
            qualityScore: response.quality_scores[idx]
              ? {
                  groundedness: response.quality_scores[idx].groundedness,
                  relevance: response.quality_scores[idx].relevance,
                  coherence: response.quality_scores[idx].coherence,
                  creativity: response.quality_scores[idx].creativity,
                  safety: response.quality_scores[idx].safety,
                  total_score:
                    response.quality_scores[idx].weighted_score ||
                    response.quality_scores[idx].total_score,
                }
              : undefined,
            isRecommended: idx === response.recommended_idx,
          };
        }
      );

      setDirections(newDirections);
      setSessionId(response.session_id);
      setStage("palette");
    },
    onError: (error) => {
      if (error.includes("크레딧") || error.includes("402")) {
        setShowCreditModal(true);
      }
      setContextError(new Error(error));
    },
  });

  // UQSL Feedback Hook (Thompson Sampling)
  const { selectCandidate, submitFeedback, isSubmitting: _isFeedbackSubmitting } =
    useUQSLFeedback();

  // Async operation for final guide
  const {
    isLoading,
    progress: _progress,
    error,
    data: result,
    execute,
    cancel,
    retry,
    canRetry,
    currentRetryCount: _currentRetryCount,
  } = useAsyncOperation<{
    success: boolean;
    output: AestheticResult;
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

  // Sync loading state with context (include transition pending for 2026 UX)
  const combinedLoading = isLoading || isUqslLoading || isTransitionPending;

  // Stage 1: Generate Moodboard with UQSL (2026 Best Practice)
  const handleGenerateMoodboard = async () => {
    const trimmedConcept = concept.trim();
    if (!trimmedConcept) {
      setValidationError(labels.enterConcept);
      return;
    }
    setValidationError(null);
    setLoading(true);
    resetUQSL();

    // Use UQSL Multi-Generate for 3 Visual Directions
    // React 19: async transitions with automatic isPending handling
    await generateUQSL({
      prompt: `Create 3 distinct visual directions for the following creative concept.

Concept: ${trimmedConcept}
Mood: ${mood}

For each direction, provide:
- title: A compelling 2-4 word title
- description: 2-3 sentences describing the visual approach
- keywords: 4-6 style keywords
- suggested_auteur: A film director whose style matches this direction
- color_preview: 3 hex color codes that represent this direction

Output as JSON array with 3 objects.`,
      app_key: "dimension.ad.moodboard",
      n_candidates: 3,
      strategy: "hitl",
    });

    setLoading(false);
  };

  // Stage 2: Handle Direction Selection with Thompson Sampling Feedback
  // React 19: useTransition for non-blocking selection updates
  const handleSelectDirection = useCallback(
    async (dir: VisualDirection) => {
      // Use transition for smooth UI update
      startTransition(() => {
        setSelectedDirection(dir);
      });

      // Record selection for Thompson Sampling (2026 Best Practice)
      // Fire-and-forget pattern for feedback - don't block UI
      if (sessionId) {
        selectCandidate(sessionId, dir.idx).catch(() => {
          // Non-blocking - continue even if feedback fails
          console.warn("Thompson Sampling feedback failed");
        });
      }
    },
    [sessionId, selectCandidate, startTransition]
  );

  // Stage 2 -> 3: Generate Full Style Guide with Optimistic UI
  const handleGenerateGuide = useCallback(async () => {
    if (!selectedDirection) return;
    setValidationError(null);

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
      setShowCreditModal(true);
      return;
    }

    setLoading(true);

    // Optimistic UI Update (React 19 Best Practice)
    setOptimisticResult({
      visual_guidelines: {
        composition: "Generating...",
        lighting: "Generating...",
        camera: "Generating...",
        pacing: "Generating...",
      },
      color_palette: selectedDirection.color_preview,
      style_keywords: selectedDirection.keywords,
      avoid_elements: [],
      auteur_influence: {
        name: selectedDirection.suggested_auteur,
        style_summary: "Loading style analysis...",
        signature_elements: [],
      },
    });
    setStage("guide");

    // Use the selected direction to generate the full guide
    const enrichedConcept = `${concept}

Selected Visual Direction: ${selectedDirection.title}
${selectedDirection.description}
Keywords: ${selectedDirection.keywords.join(", ")}
Suggested Auteur: ${selectedDirection.suggested_auteur}`;

    const res = await execute(
      `${API_BASE}/api/dimension/aesthetic/direct`,
      {
        concept: enrichedConcept,
        reference_style:
          selectedDirection.suggested_auteur.toLowerCase().split(" ")[0] || "",
        mood,
        target_medium: targetMedium,
        model: "gemini-3-pro-preview",
        use_rag: useRag,
      },
      getBYOKHeaders(byokKey)
    );

    if (!res || !res.success) {
      // Revert optimistic update on failure
      setOptimisticResult(null);
      setStage("palette");
    }

    setLoading(false);
  }, [
    concept,
    mood,
    targetMedium,
    useRag,
    byokKey,
    creditCtx,
    execute,
    selectedDirection,
    CREDIT_COST,
    setLoading,
    setOptimisticResult,
  ]);

  // Handle feedback submission (P6 Feedback API)
  const handleFeedback = useCallback(
    async (type: "positive" | "negative") => {
      if (sessionId && selectedDirection) {
        try {
          await submitFeedback(sessionId, type);
        } catch {
          // Non-blocking
        }
      }
    },
    [sessionId, selectedDirection, submitFeedback]
  );

  const handleCopy = useCallback(
    async (text: string, field: string) => {
      const success = await copyToClipboard(text);
      if (success) {
        setCopiedField(field);
        setTimeout(() => setCopiedField(null), 2000);
      }
    },
    [copyToClipboard]
  );

  // Export result as JSON
  const handleExportJson = () => {
    if (!result?.output) return;
    exportJSON(result.output, `aesthetic-director-${Date.now()}.json`);
  };

  // Extracted result data for display
  const displayResult = optimisticResult || (result?.success ? result.output : null);
  const displayError =
    validationError ||
    uqslError ||
    (result && !result.success ? result.error : error);

  return (
    <>
      <DimensionPanel.Header title={labels.title} creditCost={CREDIT_COST} />

      <DimensionPanel.Sidebar>
        {/* Stage Indicator with UQSL Progress */}
        <StageIndicator
          stage={stage}
          themeColor={token.themeColor}
          uqslProgress={isUqslLoading ? uqslProgress : undefined}
          uqslMessage={isUqslLoading ? uqslMessage : undefined}
          labels={{
            inspiration: labels.stageInspiration,
            palette: labels.stagePalette,
            guide: labels.stageGuide,
          }}
        />

        {/* Concept Input */}
        <DimensionPanel.Textarea
          label={labels.conceptLabel}
          value={concept}
          onChange={(e) => setConcept(e.target.value)}
          placeholder={labels.conceptPlaceholder}
          rows={5}
          disabled={combinedLoading || stage !== "moodboard"}
        />

        {/* File Upload (Stage 1 only) */}
        {stage === "moodboard" && (
          <DimensionPanel.FileUpload
            accept={["*"]}
            maxSizeMB={100}
            multiple
            onUpload={setFiles}
            label={labels.referenceLabel}
            helperText={labels.referenceHelper}
          />
        )}

        {/* Mood Selector (Stage 1 only) */}
        {stage === "moodboard" && (
          <DimensionPanel.Select
            label={labels.moodLabel}
            value={mood}
            onChange={(e) => setMood(e.target.value)}
            options={MOODS}
          />
        )}

        {/* Selected Direction Display (Stage 2) */}
        {stage === "palette" && selectedDirection && (
          <SelectedDirectionCard
            direction={selectedDirection}
            onFeedback={handleFeedback}
            labels={{
              selectedDirection: labels.selectedDirection,
              aiRecommended: labels.aiRecommended,
              likeIt: labels.likeIt,
              notGreat: labels.notGreat,
            }}
          />
        )}

        {/* Medium Selector (Stage 2) */}
        {stage === "palette" && (
          <DimensionPanel.Select
            label={labels.mediaLabel}
            value={targetMedium}
            onChange={(e) => setTargetMedium(e.target.value)}
            options={TARGET_MEDIUMS}
          />
        )}

        {/* RAG Toggle (Stage 2) */}
        {stage === "palette" && (
          <RagToggle
            useRag={useRag}
            onToggle={() => setUseRag(!useRag)}
            labels={{
              ragContext: labels.ragContext,
              ragDescription: labels.ragDescription,
            }}
          />
        )}

        {/* Quality Scores Toggle (Stage 2) */}
        {stage === "palette" && directions.length > 0 && (
          <QualityScoresToggle
            showQualityScores={showQualityScores}
            onToggle={() => setShowQualityScores(!showQualityScores)}
            qualityScoresLabel={labels.qualityScores}
          />
        )}

        {/* Action Buttons */}
        {stage === "moodboard" && (
          <DimensionPanel.GenerateButton
            onClick={handleGenerateMoodboard}
            disabled={combinedLoading || !concept.trim()}
            loading={isUqslLoading}
            loadingText={uqslMessage || labels.findingInspiration}
            icon={<Sparkles className="w-4 h-4" />}
          >
            {labels.exploreDirections}
          </DimensionPanel.GenerateButton>
        )}

        {stage === "palette" && (
          <DimensionPanel.GenerateButton
            onClick={handleGenerateGuide}
            disabled={isLoading || !selectedDirection}
            loading={isLoading}
            loadingText={labels.generatingStyleGuide}
            icon={<Wand2 className="w-4 h-4" />}
          >
            {labels.completeStyleGuide}
          </DimensionPanel.GenerateButton>
        )}

        {stage === "guide" && (
          <button
            onClick={() => {
              // React 19: Use transition for smooth stage change
              startTransition(() => {
                setOptimisticResult(null);
                setStage("palette");
              });
            }}
            className="w-full py-3 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-white/5 dark:hover:bg-white/10 text-slate-700 dark:text-white border border-slate-200 dark:border-white/10 transition-all font-medium"
          >
            {`\u25C0 ${labels.selectOtherDirection}`}
          </button>
        )}

        {/* UQSL Progress Bar (when streaming) */}
        {isUqslLoading && (
          <UQSLProgressBar progress={uqslProgress} stage={uqslStage} />
        )}

        {/* Thompson Sampling Stats (Stage 2) */}
        {stage === "palette" && Object.keys(armsStats).length > 0 && (
          <ThompsonSamplingStats stats={armsStats} />
        )}

        {/* Validation error */}
        {validationError && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs">
            {validationError}
          </div>
        )}

        {/* Credit Cost */}
        {!byokKey && (
          <div className="text-xs text-slate-500 dark:text-white/40 text-center mt-4">
            {labels.estimatedCost(stage === "moodboard" ? "5" : CREDIT_COST)}
          </div>
        )}
      </DimensionPanel.Sidebar>

      <DimensionPanel.Content>
        {/* Stage 1: Moodboard (Initial State) */}
        {stage === "moodboard" && !isUqslLoading && (
          <MoodboardEmptyState
            labels={{
              title: labels.emptyStateTitle,
              description: labels.emptyStateDescription,
              highlight: labels.emptyStateHighlight,
              suffix: labels.emptyStateSuffix,
            }}
          />
        )}

        {/* UQSL Streaming Loading State */}
        {isUqslLoading && (
          <UQSLStreamingState
            progress={uqslProgress}
            message={uqslMessage}
            candidates={uqslCandidates}
            qualityScores={uqslQualityScores}
            onCancel={abortUQSL}
            cancelLabel={labels.cancel}
          />
        )}

        {/* Regular Loading State */}
        {isLoading && !isUqslLoading && (
          <DimensionPanel.Loading onCancel={cancel} variant="skeleton" />
        )}

        {/* Error State */}
        {displayError && !combinedLoading && (
          <DimensionPanel.Error
            error={displayError}
            onRetry={canRetry ? retry : undefined}
          />
        )}

        {/* Stage 2: Palette Lab (Select Direction) - UQSL Enhanced */}
        {stage === "palette" && !isLoading && !isUqslLoading && (
          <PaletteLabStageUQSL
            directions={directions}
            selectedDirection={selectedDirection}
            onSelectDirection={handleSelectDirection}
            recommendedIdx={recommendedIdx}
            showQualityScores={showQualityScores}
            labels={{
              selectVisualDirection: labels.selectVisualDirection,
              aiRecommendedDirection: labels.aiRecommendedDirection,
              recommended: labels.recommended,
              suggestedDirector: labels.suggestedDirector,
            }}
          />
        )}

        {/* Stage 3: Style Guide (Result) */}
        {stage === "guide" && displayResult && !isLoading && (
          <StyleGuideResult
            result={displayResult}
            copiedField={copiedField}
            onCopy={handleCopy}
            onExportJson={handleExportJson}
            isOptimistic={!!optimisticResult && !result?.success}
            labels={{
              generatingGuide: labels.generatingGuide,
              exportJson: labels.exportJson,
              avoidElements: labels.avoidElements,
            }}
          />
        )}

        {/* Feedback for Final Result */}
        {stage === "guide" && result?.success && (
          <FeedbackSection
            onFeedback={handleFeedback}
            labels={{
              feedbackSaved: labels.feedbackSaved,
              satisfiedWithResults: labels.satisfiedWithResults,
              likeIt: labels.likeIt,
              notGreat: labels.notGreat,
            }}
          />
        )}

        {/* NextNav for final result */}
        {stage === "guide" && result?.success && <DimensionPanel.NextNav />}
      </DimensionPanel.Content>

      <InsufficientCreditsModal
        isOpen={showCreditModal}
        onClose={() => setShowCreditModal(false)}
        requiredCredits={CREDIT_COST}
        currentBalance={creditCtx?.balance ?? 0}
        onRetry={handleGenerateGuide}
      />
    </>
  );
}

// ============================================================================
// Sub-Components (2026 Best Practice)
// ============================================================================

function StageIndicator({
  stage,
  themeColor,
  uqslProgress,
  uqslMessage,
  labels,
}: {
  stage: Stage;
  themeColor: string;
  uqslProgress?: number;
  uqslMessage?: string;
  labels: {
    inspiration: string;
    palette: string;
    guide: string;
  };
}) {
  const activeClass = `text-${themeColor}-400 font-bold`;
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs text-slate-500 dark:text-white/50">
        <span className={stage === "moodboard" ? activeClass : ""}>
          1. {labels.inspiration} {stage === "moodboard" && uqslProgress ? `(${uqslProgress}%)` : ""}
        </span>
        <span>→</span>
        <span className={stage === "palette" ? activeClass : ""}>2. {labels.palette}</span>
        <span>→</span>
        <span className={stage === "guide" ? activeClass : ""}>3. {labels.guide}</span>
      </div>
      {uqslMessage && (
        <div className="text-xs text-fuchsia-400 dark:text-fuchsia-300 animate-pulse">
          {uqslMessage}
        </div>
      )}
    </div>
  );
}

function UQSLProgressBar({
  progress,
  stage,
}: {
  progress: number;
  stage: string;
}) {
  return (
    <div className="space-y-2 p-3 bg-fuchsia-500/5 dark:bg-fuchsia-500/10 rounded-xl border border-fuchsia-500/20">
      <div className="flex items-center justify-between text-xs">
        <span className="text-fuchsia-600 dark:text-fuchsia-300 font-medium">
          UQSL Generation
        </span>
        <span className="text-fuchsia-500">{progress}%</span>
      </div>
      <div className="h-1.5 bg-fuchsia-500/20 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-fuchsia-500 to-violet-500 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className="text-[10px] text-fuchsia-400 capitalize">{stage}</div>
    </div>
  );
}

function ThompsonSamplingStats({
  stats,
}: {
  stats: Record<string, { alpha: number; beta: number; success_rate: number; confidence: number; total_trials: number }>;
}) {
  return (
    <div className="p-3 bg-emerald-500/5 dark:bg-emerald-500/10 rounded-xl border border-emerald-500/20">
      <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-300 font-medium mb-2">
        <TrendingUp className="w-3 h-3" />
        Thompson Sampling
      </div>
      <div className="space-y-1">
        {Object.entries(stats).slice(0, 3).map(([arm, data]) => (
          <div key={arm} className="flex items-center justify-between text-[10px]">
            <span className="text-slate-500 dark:text-white/50 truncate max-w-[var(--layout-max-width-xxs)]">
              {arm}
            </span>
            <span className="text-emerald-500">{(data.success_rate * 100).toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function UQSLStreamingState({
  progress,
  message,
  candidates,
  qualityScores,
  onCancel,
  cancelLabel,
}: {
  progress: number;
  message: string;
  candidates: Array<{ idx: number; content: string }>;
  qualityScores: Array<{ weighted_score?: number; total_score: number }>;
  onCancel: () => void;
  cancelLabel: string;
}) {
  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-500">
      {/* Progress Header */}
      <div className="text-center space-y-4">
        <div className="relative inline-flex">
          <div className="absolute inset-0 bg-fuchsia-500/20 blur-[40px] rounded-full" />
          <div className="relative w-24 h-24 rounded-full bg-gradient-to-br from-fuchsia-500/20 to-violet-500/20 border border-fuchsia-500/30 flex items-center justify-center">
            <span className="text-3xl font-bold text-fuchsia-400">{progress}%</span>
          </div>
        </div>
        <div className="space-y-1">
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">
            UQSL Multi-Generate
          </h3>
          <p className="text-sm text-slate-500 dark:text-fuchsia-300/70 animate-pulse">
            {message}
          </p>
        </div>
      </div>

      {/* Streaming Candidates Preview */}
      {candidates.length > 0 && (
        <div className="grid gap-4 md:grid-cols-3">
          {candidates.map((candidate, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-white/50 dark:bg-white/5 border border-slate-200 dark:border-white/10 animate-in slide-in-from-bottom-4 duration-500"
              style={{ animationDelay: `${idx * 100}ms` }}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-slate-500 dark:text-white/50">
                  Direction {idx + 1}
                </span>
                {qualityScores[idx] && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500">
                    {((qualityScores[idx].weighted_score ?? qualityScores[idx].total_score) * 100).toFixed(0)}%
                  </span>
                )}
              </div>
              <div className="h-2 bg-slate-200/50 dark:bg-white/10 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-fuchsia-500 to-violet-500 animate-pulse" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Cancel Button */}
      <div className="flex justify-center">
        <button
          onClick={onCancel}
          className="px-4 py-2 text-sm text-slate-500 dark:text-white/50 hover:text-slate-700 dark:hover:text-white border border-slate-200 dark:border-white/10 rounded-lg hover:bg-slate-50 dark:hover:bg-white/5 transition-all"
        >
          {cancelLabel}
        </button>
      </div>
    </div>
  );
}

function SelectedDirectionCard({
  direction,
  onFeedback,
  labels,
}: {
  direction: VisualDirection;
  onFeedback: (type: "positive" | "negative") => void;
  labels: {
    selectedDirection: string;
    aiRecommended: string;
    likeIt: string;
    notGreat: string;
  };
}) {
  return (
    <div className="p-4 bg-fuchsia-50 dark:bg-fuchsia-500/10 border border-fuchsia-200 dark:border-fuchsia-500/20 rounded-xl space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <h4 className="text-fuchsia-600 dark:text-fuchsia-400 text-sm font-bold">
            {labels.selectedDirection}
          </h4>
          <p className="text-slate-900 dark:text-white font-medium text-sm mt-1">
            {direction.title}
          </p>
        </div>
        {direction.isRecommended && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-600 dark:text-amber-400 font-medium">
            {labels.aiRecommended}
          </span>
        )}
      </div>

      {/* Color Preview */}
      <div className="flex gap-1">
        {direction.color_preview.map((color, i) => (
          <div
            key={i}
            className="w-6 h-6 rounded-full border border-slate-200 dark:border-white/10 shadow-sm"
            style={{ backgroundColor: color }}
          />
        ))}
      </div>

      {/* Quality Score Mini */}
      {direction.qualityScore && (
        <div className="flex items-center gap-2 text-[10px]">
          <span className="text-slate-500 dark:text-white/50">Quality:</span>
          <span className="text-emerald-500 font-medium">
            {(direction.qualityScore.total_score * 100).toFixed(0)}%
          </span>
        </div>
      )}

      {/* Feedback Buttons */}
      <div className="flex gap-2 pt-2 border-t border-fuchsia-200 dark:border-fuchsia-500/20">
        <button
          onClick={() => onFeedback("positive")}
          className="flex-1 py-1.5 text-xs rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/20 transition-colors"
        >
          👍 {labels.likeIt}
        </button>
        <button
          onClick={() => onFeedback("negative")}
          className="flex-1 py-1.5 text-xs rounded-lg bg-rose-500/10 text-rose-600 dark:text-rose-400 hover:bg-rose-500/20 transition-colors"
        >
          👎 {labels.notGreat}
        </button>
      </div>
    </div>
  );
}

function RagToggle({
  useRag,
  onToggle,
  labels,
}: {
  useRag: boolean;
  onToggle: () => void;
  labels: {
    ragContext: string;
    ragDescription: string;
  };
}) {
  return (
    <div className="flex items-center justify-between p-4 bg-white dark:bg-white/5 rounded-xl border border-slate-200 dark:border-white/10">
      <div>
        <div className="text-sm font-medium text-slate-900 dark:text-zinc-300">
          {labels.ragContext}
        </div>
        <div className="text-[10px] text-slate-500 dark:text-zinc-500">
          {labels.ragDescription}
        </div>
      </div>
      <button
        onClick={onToggle}
        className={`relative w-12 h-6 rounded-full transition-all ${
          useRag ? "bg-fuchsia-500" : "bg-slate-200 dark:bg-white/10"
        }`}
      >
        <div
          className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${
            useRag ? "left-7" : "left-1"
          }`}
        />
      </button>
    </div>
  );
}

function QualityScoresToggle({
  showQualityScores,
  onToggle,
  qualityScoresLabel,
}: {
  showQualityScores: boolean;
  onToggle: () => void;
  qualityScoresLabel: string;
}) {
  return (
    <div className="flex items-center justify-between p-4 bg-white dark:bg-white/5 rounded-xl border border-slate-200 dark:border-white/10">
      <div>
        <div className="text-sm font-medium text-slate-900 dark:text-zinc-300 flex items-center gap-2">
          <Zap className="w-3.5 h-3.5 text-amber-500" />
          Quality Scores
        </div>
        <div className="text-[10px] text-slate-500 dark:text-zinc-500">
          {qualityScoresLabel}
        </div>
      </div>
      <button
        onClick={onToggle}
        className={`relative w-12 h-6 rounded-full transition-all ${
          showQualityScores ? "bg-amber-500" : "bg-slate-200 dark:bg-white/10"
        }`}
      >
        <div
          className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${
            showQualityScores ? "left-7" : "left-1"
          }`}
        />
      </button>
    </div>
  );
}

function MoodboardEmptyState({
  labels,
}: {
  labels: {
    title: string;
    description: string;
    highlight: string;
    suffix: string;
  };
}) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-slate-500 dark:text-zinc-500 space-y-8">
      <div className="relative group">
        <div className="absolute inset-0 bg-fuchsia-500/20 blur-[80px] rounded-full" />
        <div className="w-32 h-32 rounded-[2rem] bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex items-center justify-center backdrop-blur-md relative">
          <Eye className="w-12 h-12 text-slate-300 dark:text-white/20 group-hover:text-fuchsia-500 dark:group-hover:text-fuchsia-400 transition-colors" />
        </div>
      </div>
      <div className="text-center space-y-3">
        <h3 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
          {labels.title}
        </h3>
        <p className="text-sm text-slate-500 dark:text-[var(--fg-muted)] max-w-xs mx-auto font-light leading-relaxed">
          {labels.description}
          <br />
          <span className="text-fuchsia-600 dark:text-fuchsia-400 font-medium">
            {labels.highlight}
          </span>
          {labels.suffix}
        </p>
        <div className="flex items-center justify-center gap-4 pt-4 text-[10px] text-slate-400 dark:text-white/30">
          <span className="flex items-center gap-1">
            <Zap className="w-3 h-3" />
            Quality Scores
          </span>
          <span className="flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            Thompson Sampling
          </span>
        </div>
      </div>
    </div>
  );
}

function PaletteLabStageUQSL({
  directions,
  selectedDirection,
  onSelectDirection,
  recommendedIdx,
  showQualityScores,
  labels,
}: {
  directions: VisualDirection[];
  selectedDirection: VisualDirection | null;
  onSelectDirection: (dir: VisualDirection) => void;
  recommendedIdx: number | null;
  showQualityScores: boolean;
  labels: {
    selectVisualDirection: string;
    aiRecommendedDirection: (idx: number) => string;
    recommended: string;
    suggestedDirector: string;
  };
}) {
  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <Eye className="w-5 h-5 text-fuchsia-500 dark:text-fuchsia-400" />
          {labels.selectVisualDirection}
        </h3>
        {recommendedIdx !== null && (
          <span className="text-xs px-3 py-1 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
            {labels.aiRecommendedDirection(recommendedIdx)}
          </span>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {directions.map((dir) => (
          <button
            key={dir.id}
            onClick={() => onSelectDirection(dir)}
            className={`text-left p-6 rounded-2xl border transition-all relative overflow-hidden group
              ${
                selectedDirection?.id === dir.id
                  ? "bg-fuchsia-50 dark:bg-fuchsia-500/20 border-fuchsia-400 dark:border-fuchsia-500/50 ring-2 ring-fuchsia-500/30"
                  : dir.isRecommended
                    ? "bg-amber-50/50 dark:bg-amber-500/5 border-amber-300 dark:border-amber-500/30 hover:border-amber-400 dark:hover:border-amber-500/50"
                    : "bg-white dark:bg-white/5 border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/20 hover:bg-slate-50 dark:hover:bg-white/10"
              }`}
          >
            {/* Recommended Badge */}
            {dir.isRecommended && (
              <div className="absolute top-3 right-3 z-10">
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-600 dark:text-amber-400 font-medium animate-pulse">
                  ⭐ {labels.recommended}
                </span>
              </div>
            )}

            {/* Color Preview Bar */}
            <div className="flex gap-1 mb-4">
              {dir.color_preview.map((color, i) => (
                <div
                  key={i}
                  className="w-8 h-8 rounded-lg border border-white/20 shadow-lg"
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>

            <h4
              className={`text-lg font-bold mb-2 ${
                selectedDirection?.id === dir.id
                  ? "text-fuchsia-700 dark:text-fuchsia-300"
                  : "text-slate-900 dark:text-white"
              }`}
            >
              {dir.title}
            </h4>
            <p className="text-sm text-slate-600 dark:text-white/70 leading-relaxed mb-4 line-clamp-3">
              {dir.description}
            </p>

            {/* Keywords */}
            <div className="flex flex-wrap gap-1 mb-3">
              {dir.keywords.slice(0, 3).map((kw, i) => (
                <span
                  key={i}
                  className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-white/10 text-slate-600 dark:text-white/60"
                >
                  {kw}
                </span>
              ))}
            </div>

            {/* Quality Score (2026 UQSL) */}
            {showQualityScores && dir.qualityScore && (
              <div className="mt-3 pt-3 border-t border-slate-200 dark:border-white/10 space-y-2">
                <QualityScoresMini scores={dir.qualityScore} />
              </div>
            )}

            {/* Auteur */}
            <div className="pt-3 border-t border-slate-200 dark:border-white/5">
              <p className="text-xs text-slate-400 dark:text-white/40 italic">
                {labels.suggestedDirector} {dir.suggested_auteur}
              </p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function QualityScoresMini({
  scores,
  labels,
}: {
  scores: {
    groundedness: number;
    relevance: number;
    coherence: number;
    creativity: number;
    safety: number;
    total_score: number;
  };
  labels?: {
    groundedness: string;
    relevance: string;
    coherence: string;
    creativity: string;
    safety: string;
  };
}) {
  const defaultLabels = {
    groundedness: "근거",
    relevance: "관련",
    coherence: "일관",
    creativity: "창의",
    safety: "안전",
  };
  const l = labels || defaultLabels;
  const dimensions = [
    { key: "groundedness", label: l.groundedness, color: "bg-emerald-500" },
    { key: "relevance", label: l.relevance, color: "bg-cyan-500" },
    { key: "coherence", label: l.coherence, color: "bg-violet-500" },
    { key: "creativity", label: l.creativity, color: "bg-amber-500" },
    { key: "safety", label: l.safety, color: "bg-rose-500" },
  ] as const;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-[10px]">
        <span className="text-slate-500 dark:text-white/50">Quality Score</span>
        <span className="font-medium text-emerald-500">
          {(scores.total_score * 100).toFixed(0)}%
        </span>
      </div>
      <div className="grid grid-cols-5 gap-1">
        {dimensions.map((dim) => (
          <div key={dim.key} className="space-y-0.5">
            <div className="h-1 bg-slate-200 dark:bg-white/10 rounded-full overflow-hidden">
              <div
                className={`h-full ${dim.color} transition-all duration-500`}
                style={{
                  width: `${scores[dim.key] * 100}%`,
                }}
              />
            </div>
            <div className="text-[8px] text-center text-slate-400 dark:text-white/40">
              {dim.label}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FeedbackSection({
  onFeedback,
  labels,
}: {
  onFeedback: (type: "positive" | "negative") => void;
  labels?: {
    feedbackSaved: string;
    satisfiedWithResults: string;
    likeIt: string;
    notGreat: string;
  };
}) {
  const [submitted, setSubmitted] = useState(false);
  const defaultLabels = {
    feedbackSaved: "피드백이 저장되었습니다",
    satisfiedWithResults: "결과가 만족스러우셨나요?",
    likeIt: "좋아요",
    notGreat: "아쉬워요",
  };
  const l = labels || defaultLabels;

  const handleFeedback = (type: "positive" | "negative") => {
    onFeedback(type);
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="flex items-center justify-center gap-2 py-4 text-sm text-emerald-500">
        <Check className="w-4 h-4" />
        {l.feedbackSaved}
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center gap-4 py-6 border-t border-slate-200 dark:border-white/10">
      <span className="text-sm text-slate-500 dark:text-white/50">
        {l.satisfiedWithResults}
      </span>
      <button
        onClick={() => handleFeedback("positive")}
        className="px-4 py-2 text-sm rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/20 transition-colors"
      >
        👍 {l.likeIt}
      </button>
      <button
        onClick={() => handleFeedback("negative")}
        className="px-4 py-2 text-sm rounded-lg bg-rose-500/10 text-rose-600 dark:text-rose-400 hover:bg-rose-500/20 transition-colors"
      >
        👎 {l.notGreat}
      </button>
    </div>
  );
}

function StyleGuideResult({
  result,
  copiedField,
  onCopy,
  onExportJson,
  isOptimistic,
  labels,
}: {
  result: AestheticResult;
  copiedField: string | null;
  onCopy: (text: string, field: string) => void;
  onExportJson: () => void;
  isOptimistic: boolean;
  labels?: {
    generatingGuide: string;
    exportJson: string;
    avoidElements: string;
  };
}) {
  const { language } = useLanguage();
  const isKo = language === "ko";
  const defaultLabels = {
    generatingGuide: "스타일 가이드 생성 중...",
    exportJson: "JSON 내보내기",
    avoidElements: "피해야 할 요소",
  };
  const l = labels || defaultLabels;

  return (
    <div
      className={`max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10 ${
        isOptimistic ? "opacity-70" : ""
      }`}
    >
      {/* Optimistic Loading Indicator */}
      {isOptimistic && (
        <div className="flex items-center justify-center gap-2 py-2 px-4 bg-fuchsia-500/10 rounded-lg border border-fuchsia-500/20">
          <div className="w-3 h-3 rounded-full bg-fuchsia-500 animate-pulse" />
          <span className="text-sm text-fuchsia-600 dark:text-fuchsia-300">
            {l.generatingGuide}
          </span>
        </div>
      )}

      {/* Export Button */}
      {!isOptimistic && (
        <div className="flex justify-end gap-2">
          <button
            onClick={onExportJson}
            className="px-4 py-2 bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-200 dark:border-white/10 rounded-lg flex items-center gap-2 text-sm text-slate-600 dark:text-white/70 hover:text-slate-900 dark:hover:text-white transition-all"
          >
            <Download className="w-4 h-4" />
            {l.exportJson}
          </button>
        </div>
      )}

      {/* Evidence Refs (2026 Best Practice) */}
      {result.evidence_refs && result.evidence_refs.length > 0 && (
        <EvidenceCard
          variant="evidence"
          title={isKo ? "근거 데이터" : "Evidence Data"}
          confidenceLevel="medium"
          reasonCodes={[]}
          evidenceRefs={result.evidence_refs}
          reasonSummary={
            isKo
              ? "이 결과는 아래 근거 데이터를 기반으로 생성되었습니다."
              : "This result was generated using the evidence below."
          }
          isCollapsible
        />
      )}

      {/* Auteur Influence */}
      {result.auteur_influence && (
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-fuchsia-500/10 to-purple-500/10 border border-fuchsia-500/20 p-6">
          <div className="absolute top-0 right-0 w-32 h-32 bg-fuchsia-500/20 blur-[60px] rounded-full" />
          <h3 className="text-lg font-bold text-fuchsia-600 dark:text-fuchsia-400 mb-2">
            {result.auteur_influence.name}
          </h3>
          <p className="text-sm text-slate-600 dark:text-zinc-300 mb-4">
            {result.auteur_influence.style_summary}
          </p>
          <div className="flex flex-wrap gap-2">
            {result.auteur_influence.signature_elements.map((elem, i) => (
              <span
                key={i}
                className="px-3 py-1 rounded-full bg-fuchsia-500/20 text-fuchsia-600 dark:text-fuchsia-300 text-xs"
              >
                {elem}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Color Palette */}
      <div className="p-6 bg-white dark:bg-black/40 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-2xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider flex items-center gap-2">
            <Palette className="w-4 h-4 text-fuchsia-500 dark:text-fuchsia-400" />
            Color Palette
          </h3>
          <button
            onClick={() => onCopy(result.color_palette.join(", "), "palette")}
            className="text-xs text-slate-400 dark:text-zinc-500 hover:text-slate-900 dark:hover:text-white flex items-center gap-1"
          >
            {copiedField === "palette" ? (
              <Check className="w-3 h-3" />
            ) : (
              <Copy className="w-3 h-3" />
            )}
            {copiedField === "palette" ? "Copied" : "Copy"}
          </button>
        </div>
        <div className="flex gap-3 flex-wrap">
          {result.color_palette.map((color, i) => (
            <div key={i} className="flex flex-col items-center gap-2">
              <div
                className="w-16 h-16 rounded-xl shadow-lg border border-slate-200 dark:border-white/10"
                style={{ backgroundColor: color }}
              />
              <span className="text-xs font-mono text-slate-500 dark:text-zinc-400">
                {color}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Visual Guidelines */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(result.visual_guidelines).map(([key, value]) => (
          <div
            key={key}
            className="p-5 bg-white dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 rounded-xl hover:border-fuchsia-500/30 transition-colors"
          >
            <h4 className="text-xs font-bold text-fuchsia-600 dark:text-fuchsia-400 uppercase tracking-wider mb-2 capitalize">
              {key.replace(/_/g, " ")}
            </h4>
            <p className="text-sm text-slate-600 dark:text-zinc-300 leading-relaxed">
              {value}
            </p>
          </div>
        ))}
      </div>

      {/* Style Keywords */}
      <div className="p-6 bg-white dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 rounded-2xl">
        <h3 className="text-sm font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider mb-4">
          Style Keywords
        </h3>
        <div className="flex flex-wrap gap-2">
          {result.style_keywords.map((keyword, i) => (
            <span
              key={i}
              className="px-4 py-2 rounded-full bg-fuchsia-500/10 border border-fuchsia-500/20 text-fuchsia-600 dark:text-fuchsia-300 text-sm"
            >
              {keyword}
            </span>
          ))}
        </div>
      </div>

      {/* Generative Tech Pack */}
      {result.generative_prompts && (
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider flex items-center gap-2">
            <Code className="w-4 h-4 text-fuchsia-500 dark:text-fuchsia-400" />
            Generative Tech Pack
          </h3>

          {/* Midjourney */}
          <div className="p-4 bg-white dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 rounded-xl">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-600 dark:text-zinc-300">
                Midjourney v6
              </span>
              <button
                onClick={() =>
                  onCopy(result.generative_prompts!.midjourney, "mj")
                }
                className="text-xs text-fuchsia-500 dark:text-fuchsia-400 hover:text-fuchsia-600 dark:hover:text-fuchsia-300 flex items-center gap-1"
              >
                {copiedField === "mj" ? (
                  <Check className="w-3 h-3" />
                ) : (
                  <Copy className="w-3 h-3" />
                )}
                {copiedField === "mj" ? "Copied" : "Copy"}
              </button>
            </div>
            <code className="block p-3 bg-slate-100 dark:bg-black/50 rounded-lg text-xs text-slate-600 dark:text-white/70 font-mono break-all leading-relaxed">
              {result.generative_prompts.midjourney}
            </code>
          </div>

          {/* Veo */}
          <div className="p-4 bg-white dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 rounded-xl">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-600 dark:text-zinc-300">
                Google Veo
              </span>
              <button
                onClick={() => onCopy(result.generative_prompts!.veo, "veo")}
                className="text-xs text-fuchsia-500 dark:text-fuchsia-400 hover:text-fuchsia-600 dark:hover:text-fuchsia-300 flex items-center gap-1"
              >
                {copiedField === "veo" ? (
                  <Check className="w-3 h-3" />
                ) : (
                  <Copy className="w-3 h-3" />
                )}
                {copiedField === "veo" ? "Copied" : "Copy"}
              </button>
            </div>
            <code className="block p-3 bg-slate-100 dark:bg-black/50 rounded-lg text-xs text-slate-600 dark:text-white/70 font-mono break-all leading-relaxed">
              {result.generative_prompts.veo}
            </code>
          </div>
        </div>
      )}

      {/* Texture & Typography */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Textures */}
        {result.textures && result.textures.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider flex items-center gap-2">
              <Layers className="w-4 h-4 text-fuchsia-500 dark:text-fuchsia-400" />
              Texture Elements
            </h3>
            <div className="space-y-2">
              {result.textures.map((texture, i) => (
                <div
                  key={i}
                  className="group relative p-4 bg-white dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 rounded-xl hover:bg-slate-50 dark:hover:bg-white/[0.05] transition-colors"
                >
                  <div className="absolute inset-x-0 bottom-0 h-[2px] bg-gradient-to-r from-transparent via-fuchsia-500/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-sm text-slate-600 dark:text-zinc-200">
                    {texture}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Typography */}
        {result.typography && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider flex items-center gap-2">
              <Type className="w-4 h-4 text-fuchsia-500 dark:text-fuchsia-400" />
              Typography
            </h3>
            <div className="p-5 bg-white dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 rounded-xl space-y-4">
              <div>
                <span className="text-[10px] text-slate-400 dark:text-zinc-500 uppercase tracking-widest">
                  Primary Title
                </span>
                <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                  {result.typography.primary}
                </p>
              </div>
              <div className="h-px bg-slate-200 dark:bg-white/5" />
              <div>
                <span className="text-[10px] text-slate-400 dark:text-zinc-500 uppercase tracking-widest">
                  Secondary Body
                </span>
                <p className="text-base text-slate-600 dark:text-zinc-300 mt-1 font-serif">
                  {result.typography.secondary}
                </p>
              </div>
              <p className="text-xs text-slate-400 dark:text-white/40 italic pt-2">
                &ldquo;{result.typography.description}&rdquo;
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Avoid Elements */}
      {result.avoid_elements.length > 0 && (
        <div className="p-6 bg-rose-50 dark:bg-rose-500/5 border border-rose-200 dark:border-rose-500/20 rounded-2xl">
          <h3 className="text-sm font-bold text-rose-600 dark:text-rose-400 uppercase tracking-wider mb-4">
            {l.avoidElements}
          </h3>
          <ul className="space-y-2">
            {result.avoid_elements.map((elem, i) => (
              <li
                key={i}
                className="text-sm text-slate-600 dark:text-zinc-300 flex items-start gap-2"
              >
                <span className="text-rose-500 dark:text-rose-400">✕</span>
                {elem}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
