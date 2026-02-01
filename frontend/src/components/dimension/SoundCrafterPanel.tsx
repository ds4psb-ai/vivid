"use client";

/**
 * SoundCrafterPanel - 사운드 디자인 스튜디오 (SC)
 *
 * 2026 Golden App: React 19 Best Practices
 *
 * 4-Stage Sound Design Workflow:
 * 1. Intro: 컨셉 입력
 * 2. Mood: Audio Direction 선택
 * 3. Layers: Mix Recipe 조절
 * 4. Mastering: 최종 결과 표시
 *
 * Features:
 * - useTransition for non-blocking form submission
 * - useOptimistic for instant UI feedback
 *
 * @see https://react.dev/blog/2024/12/05/react-19
 * @see docs/PANEL_DESIGN_UNITY_SPEC.md
 */

import { useState, useEffect, useCallback, useTransition, useOptimistic } from "react";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import {
  useDimensionChainOptional,
  type ChainData,
} from "@/contexts/DimensionChainContext";
import { useChainDataInjection } from "@/hooks/useChainDataInjection";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import ChainDataInput from "./ChainDataInput";
import { type ThemeColor as DimensionThemeColor } from "@/lib/dimension-theme";
import {
  Music,
  ArrowRight,
  Copy,
  Check,
  Download,
  Layers,
  Activity,
  Disc,
  Sliders,
  Zap,
  Link2,
} from "lucide-react";

// ============================================================================
// Constants & Types
// ============================================================================

const DIMENSION_CODE = "2d"; // Sound Crafter uses 2d

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
const DIMENSION_KEY = "sound-crafter";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";
const MAX_CONCEPT_LENGTH = 2000;

type Stage = "intro" | "mood" | "layers" | "mastering";

interface AudioDirection {
  id: string;
  title: string;
  description: string;
  visual_style: {
    color: string;
    icon: string;
  };
  bpm_range: string;
  key_elements: string[];
}

interface MoodboardResult {
  directions: AudioDirection[];
}

interface SoundResult {
  music_prompt?: string;
  udio_prompt?: string;
  style_tags?: string[];
  bpm_range?: string;
  key_signature?: string;
  layers?: {
    melody: string;
    rhythm: string;
    texture: string;
  };
  mixing_guide?: string;
  visualization?: {
    energy_levels: number[];
    color_palette: string[];
  };
  next_dimension?: string;
}

interface MixRecipe {
  melody_focus: number;
  rhythm_intensity: number;
  texture_density: number;
}

// ============================================================================
// Main Panel Component
// ============================================================================

export default function SoundCrafterPanel() {
  return (
    <DimensionPanel dimensionCode={DIMENSION_CODE}>
      <SoundCrafterContent />
    </DimensionPanel>
  );
}

// ============================================================================
// Panel Content (Inner Component)
// ============================================================================

function SoundCrafterContent() {
  const { token, setLoading, setResult, setError: setContextError } =
    useDimensionPanel();

  // Stage Management
  const [currentStage, setCurrentStage] = useState<Stage>("intro");

  // Inputs
  const [concept, setConcept] = useState("");
  const [_files, setFiles] = useState<File[]>([]);
  const [selectedDirection, setSelectedDirection] =
    useState<AudioDirection | null>(null);
  const [mixRecipe, setMixRecipe] = useState<MixRecipe>({
    melody_focus: 5,
    rhythm_intensity: 5,
    texture_density: 5,
  });

  // Outputs
  const [moodResult, setMoodResult] = useState<MoodboardResult | null>(null);
  const [finalResult, setFinalResult] = useState<SoundResult | null>(null);

  // Platform State (for output display)
  const [activePlatform, setActivePlatform] = useState<"suno" | "udio">("suno");

  // UI State
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  // Hooks
  const { byokKey } = useBYOK();
  const creditCtx = useCreditContextOptional();
  const chainCtx = useDimensionChainOptional();
  const { getToolByDimension } = useDimensionConfig();
  const toolConfig = getToolByDimension("SOUND") ?? getToolByDimension("SC");
  const CREDIT_COST_CRAFT = toolConfig?.creditCost ?? 8;
  const CREDIT_COST_MOOD = Math.max(1, Math.round(CREDIT_COST_CRAFT * 0.625));

  const [requiredCredits, setRequiredCredits] = useState(CREDIT_COST_MOOD);

  // Export utilities
  const { exportJSON, copyToClipboard } = useResultExport();

  // React 19: useTransition for non-blocking operations
  const [isTransitionPending, startTransition] = useTransition();

  // React 19: useOptimistic for instant UI feedback
  const [optimisticMoodResult, setOptimisticMoodResult] = useOptimistic<MoodboardResult | null>(null);
  const [optimisticFinalResult, setOptimisticFinalResult] = useOptimistic<SoundResult | null>(null);

  // Set current dimension on mount
  useEffect(() => {
    if (chainCtx) {
      chainCtx.setCurrentDimension(DIMENSION_KEY);
    }
  }, [chainCtx]);

  // Chain Data Injection - auto-inject from story-architect, system-prompt
  const {
    evidenceRefs: chainEvidenceRefs,
    hasUpstreamData,
    rawInputData,
  } = useChainDataInjection(DIMENSION_KEY);

  // Auto-apply upstream chain data (story-architect mood/logline)
  useEffect(() => {
    if (!hasUpstreamData || concept) return;

    // Type-safe access to rawInputData
    const typedInputData = rawInputData as Record<string, { output?: Record<string, unknown> } | undefined>;

    // Extract mood/logline from story-architect
    const storyOutput = typedInputData["story-architect"]?.output;
    if (storyOutput) {
      const logline = storyOutput.logline as string | undefined;
      const mood = storyOutput.mood as string | undefined;
      const tone = storyOutput.tone as string | undefined;

      if (logline) {
        setConcept(logline);
      } else if (mood) {
        setConcept(`Mood: ${mood}${tone ? `, Tone: ${tone}` : ""}`);
      }
    }

    // Extract system prompt tone if available
    const systemOutput = typedInputData["system-prompt"]?.output;
    if (systemOutput?.tone && !concept) {
      setConcept(`System tone: ${systemOutput.tone}`);
    }
  }, [hasUpstreamData, rawInputData, concept]);

  // ASYNC OP 1: Moodboard Generator
  const moodOp = useAsyncOperation<{
    success: boolean;
    output: MoodboardResult;
    error?: string;
  }>({
    onSuccess: (data) => {
      if (data.success && data.output) {
        setMoodResult(data.output);
        setCurrentStage("mood");
        if (!byokKey && creditCtx) void creditCtx.refresh();
      }
    },
    onError: (err) => {
      if (err.message.includes("크레딧") || err.message.includes("402")) {
        setRequiredCredits(CREDIT_COST_MOOD);
        setShowCreditModal(true);
      }
      setContextError(err);
    },
  });

  // ASYNC OP 2: Sound Crafter (Final)
  const craftOp = useAsyncOperation<{
    success: boolean;
    output: SoundResult;
    error?: string;
  }>({
    onSuccess: (data) => {
      if (data.success && data.output) {
        setFinalResult(data.output);
        setCurrentStage("mastering");
        setResult(data.output);

        // Chain Data Update
        if (chainCtx) {
          // Combine upstream evidence refs with current output refs
          const outputRefs = (data.output as unknown as { evidence_refs?: string[] }).evidence_refs || [];
          const combinedRefs = [...new Set([...chainEvidenceRefs, ...outputRefs])];

          chainCtx.setChainData(
            DIMENSION_KEY,
            data.output as unknown as Record<string, unknown>,
            data.output.music_prompt?.slice(0, 50) || concept.slice(0, 50),
            combinedRefs
          );
        }
        if (!byokKey && creditCtx) void creditCtx.refresh();
      }
    },
    onError: (err) => {
      if (err.message.includes("크레딧") || err.message.includes("402")) {
        setRequiredCredits(CREDIT_COST_CRAFT);
        setShowCreditModal(true);
      }
      setContextError(err);
    },
  });

  // Combined loading state (React 19: includes transition pending)
  const combinedLoading = moodOp.isLoading || craftOp.isLoading || isTransitionPending;

  // Update context loading state
  useEffect(() => {
    setLoading(combinedLoading);
  }, [combinedLoading, setLoading]);

  // --- Handlers ---

  const handleApplyChainData = (data: Record<string, ChainData>) => {
    if (data["story-architect"]?.output?.logline && !concept) {
      setConcept(data["story-architect"].output.logline as string);
    } else if (data["aesthetic-director"]?.output?.mood && !concept) {
      setConcept(`Mood: ${data["aesthetic-director"].output.mood}`);
    }
  };

  const handleGenerateMood = useCallback(() => {
    const trimmed = concept.trim();
    if (trimmed.length < 5) {
      setValidationError("컨셉을 5자 이상 입력해주세요.");
      return;
    }
    setValidationError(null);

    if (
      !byokKey &&
      creditCtx &&
      !creditCtx.hasEnoughCredits(CREDIT_COST_MOOD)
    ) {
      setRequiredCredits(CREDIT_COST_MOOD);
      setShowCreditModal(true);
      return;
    }

    // React 19: Non-blocking transition with optimistic UI
    startTransition(async () => {
      // Optimistic: Show placeholder directions immediately
      setOptimisticMoodResult({
        directions: Array.from({ length: 3 }, (_, i) => ({
          id: `placeholder-${i}`,
          title: "분석 중...",
          description: "사운드 디렉션을 생성하고 있습니다...",
          visual_style: { color: "#f43f5e", icon: "music" },
          bpm_range: "...",
          key_elements: ["분석 중..."],
        })),
      });

      await moodOp.execute(
        `${API_BASE}/api/dimension/sound/moodboard`,
        { concept: trimmed, model: "gemini-3-pro-preview" },
        getBYOKHeaders(byokKey)
      );

      setOptimisticMoodResult(null);
    });
  }, [concept, byokKey, creditCtx, moodOp, CREDIT_COST_MOOD, startTransition, setOptimisticMoodResult]);

  const handleSelectDirection = (direction: AudioDirection) => {
    setSelectedDirection(direction);
    setCurrentStage("layers");
  };

  const handleGenerateFinal = useCallback(() => {
    if (!selectedDirection) return;

    if (
      !byokKey &&
      creditCtx &&
      !creditCtx.hasEnoughCredits(CREDIT_COST_CRAFT)
    ) {
      setRequiredCredits(CREDIT_COST_CRAFT);
      setShowCreditModal(true);
      return;
    }

    // React 19: Non-blocking transition with optimistic UI
    startTransition(async () => {
      // Optimistic: Show placeholder result immediately
      setOptimisticFinalResult({
        music_prompt: "프롬프트 생성 중...",
        udio_prompt: "프롬프트 생성 중...",
        style_tags: ["분석 중..."],
        bpm_range: "...",
        layers: {
          melody: "생성 중...",
          rhythm: "생성 중...",
          texture: "생성 중...",
        },
      });

      await craftOp.execute(
        `${API_BASE}/api/dimension/sound/craft`,
        {
          concept: `${concept} (Style: ${selectedDirection.title})`,
          sound_type: "full",
          mood: selectedDirection.description,
          mix_recipe: mixRecipe,
          target_platform: "suno",
          model: "gemini-3-flash-preview",
        },
        getBYOKHeaders(byokKey)
      );

      setOptimisticFinalResult(null);
    });
  }, [
    concept,
    selectedDirection,
    mixRecipe,
    byokKey,
    creditCtx,
    craftOp,
    CREDIT_COST_CRAFT,
    startTransition,
    setOptimisticFinalResult,
  ]);

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

  return (
    <>
      <DimensionPanel.Header
        title="사운드 디자인 스튜디오"
        creditCost={
          currentStage === "intro" ? CREDIT_COST_MOOD : CREDIT_COST_CRAFT
        }
      />

      <DimensionPanel.Sidebar>
        {/* Upstream Data Banner */}
        {hasUpstreamData && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg animate-in fade-in slide-in-from-top-2">
            <div className="flex items-center gap-2 text-rose-600 dark:text-rose-400">
              <Link2 className="w-4 h-4" />
              <span className="text-xs font-medium">
                Story Architect 데이터가 자동 적용됩니다
              </span>
            </div>
          </div>
        )}

        {/* Chain Data Input */}
        <ChainDataInput
          currentDimension={DIMENSION_KEY}
          onApplyData={handleApplyChainData}
          themeColor={CHAIN_INPUT_THEME_MAP[token.themeColor] || "cyan"}
        />

        {/* Stage Indicator */}
        <StageIndicator
          currentStage={currentStage}
          themeColor={token.themeColor}
        />

        {/* Concept Input - Only editable in intro stage */}
        {currentStage === "intro" && (
          <ConceptInput
            concept={concept}
            setConcept={setConcept}
            isLoading={moodOp.isLoading}
            onGenerate={handleGenerateMood}
            creditCost={CREDIT_COST_MOOD}
            byokKey={byokKey}
            setFiles={setFiles}
          />
        )}
      </DimensionPanel.Sidebar>

      <DimensionPanel.Content>
        {/* Loading State */}
        {combinedLoading && (
          <DimensionPanel.Loading
            variant="skeleton"
            onCancel={() => {
              if (moodOp.isLoading) moodOp.cancel();
              if (craftOp.isLoading) craftOp.cancel();
            }}
          />
        )}

        {/* Error State */}
        {(validationError || moodOp.error || craftOp.error) &&
          !combinedLoading && (
            <DimensionPanel.Error
              error={validationError || moodOp.error || craftOp.error || undefined}
              onRetry={
                moodOp.canRetry
                  ? () => void moodOp.retry()
                  : craftOp.canRetry
                    ? () => void craftOp.retry()
                    : undefined
              }
            />
          )}

        {/* Intro Stage */}
        {currentStage === "intro" && !combinedLoading && <IntroEmptyState />}

        {/* Optimistic Mood Stage (React 19) */}
        {currentStage === "intro" && combinedLoading && optimisticMoodResult && (
          <div className="space-y-6 animate-in fade-in duration-300 opacity-60">
            <div className="flex items-center justify-center gap-2 py-3 px-4 bg-rose-500/10 rounded-lg border border-rose-500/20">
              <div className="w-3 h-3 rounded-full bg-rose-500 animate-pulse" />
              <span className="text-sm text-rose-600 dark:text-rose-300">
                사운드 디렉션 분석 중...
              </span>
            </div>
            <div className="grid grid-cols-1 gap-4">
              {optimisticMoodResult.directions.map((dir, idx) => (
                <div key={idx} className="p-5 rounded-xl border border-[var(--border-muted)] bg-[var(--surface-1)] animate-pulse">
                  <div className="h-5 w-32 bg-[var(--bg-2)] rounded mb-3" />
                  <div className="space-y-2">
                    <div className="h-3 w-full bg-[var(--bg-2)] rounded" />
                    <div className="h-3 w-3/4 bg-[var(--bg-2)] rounded" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Mood Stage */}
        {currentStage === "mood" && !combinedLoading && moodResult && (
          <MoodStage
            directions={moodResult.directions}
            onSelectDirection={handleSelectDirection}
            onGoBack={() => {
              setMoodResult(null);
              setCurrentStage("intro");
            }}
          />
        )}

        {/* Layers Stage */}
        {currentStage === "layers" && !combinedLoading && selectedDirection && (
          <LayersStage
            selectedDirection={selectedDirection}
            mixRecipe={mixRecipe}
            setMixRecipe={setMixRecipe}
            isLoading={craftOp.isLoading || isTransitionPending}
            onGoBack={() => setCurrentStage("mood")}
            onGenerate={handleGenerateFinal}
            creditCost={CREDIT_COST_CRAFT}
            byokKey={byokKey}
          />
        )}

        {/* Optimistic Mastering Stage (React 19) */}
        {currentStage === "layers" && combinedLoading && optimisticFinalResult && (
          <div className="space-y-6 animate-in fade-in duration-300 opacity-60">
            <div className="flex items-center justify-center gap-2 py-3 px-4 bg-rose-500/10 rounded-lg border border-rose-500/20">
              <div className="w-3 h-3 rounded-full bg-rose-500 animate-pulse" />
              <span className="text-sm text-rose-600 dark:text-rose-300">
                사운드 테크 팩 생성 중...
              </span>
            </div>
            <div className="p-6 rounded-2xl bg-gradient-to-br from-rose-500/10 to-[var(--bg-0)] border border-rose-500/20 animate-pulse">
              <div className="h-4 w-24 bg-rose-500/20 rounded mb-4" />
              <div className="space-y-2">
                <div className="h-3 w-full bg-[var(--surface-2)] rounded" />
                <div className="h-3 w-5/6 bg-[var(--surface-2)] rounded" />
                <div className="h-3 w-4/6 bg-[var(--surface-2)] rounded" />
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {["멜로디", "리듬", "텍스처"].map((label, i) => (
                <div key={i} className="p-4 rounded-xl bg-[var(--surface-1)] border border-[var(--border-muted)] animate-pulse">
                  <div className="h-3 w-16 bg-rose-400/20 rounded mb-2" />
                  <div className="h-3 w-full bg-[var(--surface-2)] rounded" />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Mastering Stage */}
        {currentStage === "mastering" && !combinedLoading && finalResult && (
          <MasteringStage
            result={finalResult}
            activePlatform={activePlatform}
            setActivePlatform={setActivePlatform}
            copiedField={copiedField}
            onCopy={handleCopy}
            onExport={() =>
              exportJSON(finalResult, `sound-pack-${Date.now()}.json`)
            }
            onGoBack={() => {
              setFinalResult(null);
              setCurrentStage("layers");
            }}
          />
        )}

        {/* Evidence Display */}
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        {currentStage === "mastering" && <DimensionPanel.Evidence refs={(finalResult as any)?.evidence_refs} />}

        {/* NextNav for final result */}
        {currentStage === "mastering" && finalResult && (
          <DimensionPanel.NextNav />
        )}
      </DimensionPanel.Content>

      <InsufficientCreditsModal
        isOpen={showCreditModal}
        onClose={() => setShowCreditModal(false)}
        requiredCredits={requiredCredits}
        currentBalance={creditCtx?.balance || 0}
      />
    </>
  );
}

// ============================================================================
// Sub-Components
// ============================================================================

function StageIndicator({
  currentStage,
  themeColor,
}: {
  currentStage: Stage;
  themeColor: string;
}) {
  const stages = [
    { id: "intro", label: "컨셉", icon: Music },
    { id: "mood", label: "소닉 무드", icon: Activity },
    { id: "layers", label: "레이어 믹싱", icon: Layers },
    { id: "mastering", label: "마스터링", icon: Disc },
  ] as const;

  const currentIdx = stages.findIndex((s) => s.id === currentStage);

  return (
    <div className="space-y-4">
      <h4 className="text-xs font-bold text-[var(--fg-muted)] uppercase tracking-wider">
        제작 플로우
      </h4>
      <div className="space-y-0 relative">
        <div className="absolute left-[15px] top-2 bottom-2 w-0.5 bg-[var(--border-subtle)]" />
        {stages.map((step, idx) => {
          const isActive = currentStage === step.id;
          const isPast = currentIdx > idx;
          const Icon = step.icon;

          return (
            <div
              key={step.id}
              className={`relative flex items-center gap-3 p-2 rounded-lg transition-all ${isActive ? "bg-[var(--surface-1)]" : ""}`}
            >
              <div
                className={`relative z-10 w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all
                ${
                  isActive || isPast
                    ? "bg-[var(--bg-0)] border-[var(--stitch-primary)] text-[var(--stitch-primary)]"
                    : "bg-[var(--bg-0)] border-[var(--border-muted)] text-[var(--fg-subtle)]"
                }`}
              >
                <Icon className="w-4 h-4" />
              </div>
              <span
                className={`text-sm font-medium ${isActive ? "text-[var(--fg-0)]" : isPast ? "text-[var(--fg-muted)]" : "text-[var(--fg-subtle)]"}`}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ConceptInput({
  concept,
  setConcept,
  isLoading,
  onGenerate,
  creditCost,
  byokKey,
  setFiles,
}: {
  concept: string;
  setConcept: (v: string) => void;
  isLoading: boolean;
  onGenerate: () => void;
  creditCost: number;
  byokKey: string | null;
  setFiles: (files: File[]) => void;
}) {
  return (
    <div className="space-y-2 animate-in fade-in">
      <DimensionPanel.Textarea
        label="사운드 컨셉"
        value={concept}
        onChange={(e) => setConcept(e.target.value)}
        placeholder="어떤 분위기의 사운드가 필요한가요? (예: 비 오는 네오 도쿄의 사이버펑크 재즈)"
        rows={6}
        disabled={isLoading}
      />
      <div className="text-xs text-[var(--fg-subtle)] text-right">
        {concept.length}/{MAX_CONCEPT_LENGTH}
      </div>

      {/* File Upload */}
      <DimensionPanel.FileUpload
        accept={["*"]}
        maxSizeMB={100}
        multiple
        onUpload={setFiles}
        label="레퍼런스 (선택)"
        helperText="참고 음악, 분위기 이미지"
      />

      <DimensionPanel.GenerateButton
        onClick={onGenerate}
        disabled={isLoading || concept.length < 5}
        loading={isLoading}
        loadingText="분석 중..."
        icon={<ArrowRight className="w-4 h-4" />}
      >
        사운드 디렉션 생성
      </DimensionPanel.GenerateButton>

      {!byokKey && (
        <div className="text-xs text-center text-[var(--fg-subtle)] mt-2">
          예상 비용: {creditCost} 크레딧
        </div>
      )}
    </div>
  );
}

function IntroEmptyState() {
  return (
    <div className="flex flex-col items-center justify-center text-center opacity-50 h-full">
      <Music className="w-16 h-16 text-rose-500 dark:text-rose-400 mb-6" />
      <h2 className="text-2xl font-bold text-[var(--fg-0)] mb-2">
        사운드 디자인 스튜디오
      </h2>
      <p className="text-[var(--fg-muted)] max-w-md">
        추상적인 아이디어를 구체적인 사운드 텍스처로 변환하세요.
        <br />
        Suno 및 Udio 용 전문 프롬프트가 생성됩니다.
      </p>
    </div>
  );
}

function MoodStage({
  directions,
  onSelectDirection,
  onGoBack,
}: {
  directions: AudioDirection[];
  onSelectDirection: (dir: AudioDirection) => void;
  onGoBack: () => void;
}) {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <h3 className="text-lg font-bold text-[var(--fg-0)] flex items-center gap-2">
        <Activity className="w-5 h-5 text-rose-500 dark:text-rose-400" />
        1단계: 오디오 디렉션 선택
      </h3>

      <div className="grid grid-cols-1 gap-4">
        {directions.map((dir) => (
          <button
            key={dir.id}
            onClick={() => onSelectDirection(dir)}
            className="group relative p-5 rounded-xl border border-[var(--border-muted)] bg-[var(--surface-1)] hover:bg-[var(--surface-2)]
                     text-left transition-all hover:border-rose-300 dark:hover:border-rose-500/50 hover:shadow-lg hover:shadow-rose-500/10"
          >
            <div className="flex justify-between items-start mb-2">
              <h4 className="text-lg font-bold text-rose-600 dark:text-rose-400 group-hover:text-rose-500 dark:group-hover:text-rose-300 transition-colors">
                {dir.title}
              </h4>
              <span className="text-xs px-2 py-1 rounded-full bg-[var(--bg-1)] text-[var(--fg-muted)] border border-[var(--border-muted)]">
                {dir.bpm_range} BPM
              </span>
            </div>
            <p className="text-[var(--fg-muted)] text-sm mb-4 leading-relaxed">
              {dir.description}
            </p>
            <div className="flex flex-wrap gap-2">
              {dir.key_elements.map((el, i) => (
                <span
                  key={i}
                  className="text-xs px-2 py-1 rounded bg-rose-100 dark:bg-rose-500/10 text-rose-600 dark:text-rose-300/70"
                >
                  {el}
                </span>
              ))}
            </div>
          </button>
        ))}
      </div>

      <button
        onClick={onGoBack}
        className="text-sm text-[var(--fg-muted)] hover:text-[var(--fg-0)] underline"
      >
        다시 컨셉 입력하기
      </button>
    </div>
  );
}

function LayersStage({
  selectedDirection,
  mixRecipe,
  setMixRecipe,
  isLoading,
  onGoBack,
  onGenerate,
  creditCost,
  byokKey,
}: {
  selectedDirection: AudioDirection;
  mixRecipe: MixRecipe;
  setMixRecipe: (r: MixRecipe) => void;
  isLoading: boolean;
  onGoBack: () => void;
  onGenerate: () => void;
  creditCost: number;
  byokKey: string | null;
}) {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
      <h3 className="text-lg font-bold text-[var(--fg-0)] flex items-center gap-2">
        <Sliders className="w-5 h-5 text-rose-500 dark:text-rose-400" />
        2단계: 사운드 레이어 믹싱
      </h3>

      <div className="bg-[var(--surface-1)] border border-[var(--border-muted)] rounded-xl p-6 space-y-6">
        <div className="flex items-center gap-4 pb-4 border-b border-[var(--border-muted)]">
          <div className="w-12 h-12 rounded-lg bg-rose-100 dark:bg-rose-500/20 flex items-center justify-center">
            <Music className="w-6 h-6 text-rose-500 dark:text-rose-400" />
          </div>
          <div>
            <h4 className="font-bold text-[var(--fg-0)]">
              {selectedDirection.title}
            </h4>
            <p className="text-sm text-[var(--fg-muted)]">
              {selectedDirection.description}
            </p>
          </div>
        </div>

        {/* Mixing Sliders */}
        <MixSlider
          label="멜로디 포커스"
          value={mixRecipe.melody_focus}
          onChange={(v) => setMixRecipe({ ...mixRecipe, melody_focus: v })}
          description="높을수록 멜로디라인이 강조됩니다."
        />
        <MixSlider
          label="리듬 인텐시티"
          value={mixRecipe.rhythm_intensity}
          onChange={(v) => setMixRecipe({ ...mixRecipe, rhythm_intensity: v })}
          description="비트와 퍼커션의 강도를 조절합니다."
        />
        <MixSlider
          label="텍스처 밀도"
          value={mixRecipe.texture_density}
          onChange={(v) => setMixRecipe({ ...mixRecipe, texture_density: v })}
          description="배경음과 앨비언스의 풍부함을 조절합니다."
        />
      </div>

      <div className="flex gap-3">
        <button
          onClick={onGoBack}
          className="flex-1 py-4 rounded-xl border border-[var(--border-muted)] text-[var(--fg-muted)] hover:bg-[var(--surface-2)] transition-all font-medium"
        >
          이전
        </button>
        <button
          onClick={onGenerate}
          disabled={isLoading}
          className="flex-[2] py-4 rounded-xl bg-gradient-to-r from-rose-500 to-pink-500 text-[var(--fg-on-emphasis)] font-bold
                   hover:from-rose-400 hover:to-pink-400 transition-all flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="w-5 h-5 border-2 spinner-on-emphasis rounded-full animate-spin" />
              최종 프롬프트 생성 중...
            </>
          ) : (
            <>
              마스터링 시작
              <Zap className="w-4 h-4 fill-current" />
            </>
          )}
        </button>
      </div>

      {!byokKey && (
        <div className="text-xs text-center text-[var(--fg-subtle)]">
          최종 생성 비용: {creditCost} 크레딧
        </div>
      )}
    </div>
  );
}

function MixSlider({
  label,
  value,
  onChange,
  description,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  description: string;
}) {
  return (
    <div className="space-y-3">
      <div className="flex justify-between text-sm">
        <label className="text-[var(--fg-0)] font-medium">
          {label}
        </label>
        <span className="text-rose-600 dark:text-rose-400">{value * 10}%</span>
      </div>
      <input
        type="range"
        min="0"
        max="10"
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="w-full accent-rose-500 bg-[var(--bg-2)] h-2 rounded-lg appearance-none cursor-pointer"
      />
      <p className="text-xs text-[var(--fg-muted)]">{description}</p>
    </div>
  );
}

function MasteringStage({
  result,
  activePlatform,
  setActivePlatform,
  copiedField,
  onCopy,
  onExport,
  onGoBack,
}: {
  result: SoundResult;
  activePlatform: "suno" | "udio";
  setActivePlatform: (p: "suno" | "udio") => void;
  copiedField: string | null;
  onCopy: (text: string, field: string) => void;
  onExport: () => void;
  onGoBack: () => void;
}) {
  return (
    <div className="space-y-6 animate-in fade-in zoom-in-95 duration-500">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-[var(--fg-0)] flex items-center gap-2">
          <Disc className="w-5 h-5 text-rose-400 animate-spin" />
          사운드 테크 팩
        </h3>
        <div className="flex bg-[var(--surface-1)] rounded-lg p-1 border border-[var(--border-subtle)]">
          <button
            onClick={() => setActivePlatform("suno")}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activePlatform === "suno" ? "bg-[var(--accent)] text-[var(--fg-on-emphasis)] shadow-lg" : "text-[var(--fg-muted)] hover:text-[var(--fg-0)]"}`}
          >
            Suno v3
          </button>
          <button
            onClick={() => setActivePlatform("udio")}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activePlatform === "udio" ? "bg-[var(--accent)] text-[var(--fg-on-emphasis)] shadow-lg" : "text-[var(--fg-muted)] hover:text-[var(--fg-0)]"}`}
          >
            Udio
          </button>
        </div>
      </div>

      {/* Prompt Display */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-rose-500/10 to-[var(--bg-0)] border border-rose-500/20 relative group">
        <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() =>
              onCopy(
                activePlatform === "suno"
                  ? result.music_prompt || ""
                  : result.udio_prompt || "",
                "prompt"
              )
            }
            className="p-2 rounded-lg bg-[var(--surface-1)] hover:bg-[var(--surface-2)] text-[var(--fg-0)] transition-colors"
          >
            {copiedField === "prompt" ? (
              <Check className="w-4 h-4 text-green-400" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        </div>
        <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider mb-3">
          {activePlatform === "suno" ? "Suno v3.5 최적화" : "Udio Beta 최적화"}
        </h4>
        <p className="text-[var(--fg-0)] font-mono text-sm leading-relaxed whitespace-pre-wrap">
          {activePlatform === "suno"
            ? result.music_prompt
            : result.udio_prompt || "Udio 프롬프트가 생성되지 않았습니다."}
        </p>
      </div>

      {/* Layers Breakdown */}
      {result.layers && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <LayerCard label="멜로디" content={result.layers.melody} />
          <LayerCard label="리듬" content={result.layers.rhythm} />
          <LayerCard label="텍스처" content={result.layers.texture} />
        </div>
      )}

      {/* Mixing Guide */}
      {result.mixing_guide && (
        <div className="p-5 rounded-xl bg-[var(--surface-2)] border dashed border-[var(--border-muted)]">
          <h4 className="text-sm font-bold text-[var(--fg-muted)] mb-2 flex items-center gap-2">
            <Sliders className="w-4 h-4" />
            믹싱 가이드
          </h4>
          <p className="text-sm text-[var(--fg-subtle)]">{result.mixing_guide}</p>
        </div>
      )}

      <div className="flex justify-end gap-3 pt-4 border-t border-[var(--border-subtle)]">
        <button
          onClick={onExport}
          className="px-4 py-2 hover:bg-[var(--surface-2)] rounded-lg text-sm text-[var(--fg-muted)] hover:text-[var(--fg-0)] flex items-center gap-2 transition-colors"
        >
          <Download className="w-4 h-4" />
          JSON 내보내기
        </button>
        <button
          onClick={onGoBack}
          className="px-6 py-2 bg-[var(--surface-1)] hover:bg-[var(--surface-2)] rounded-lg text-sm font-medium text-[var(--fg-0)] transition-colors"
        >
          다시 믹싱하기
        </button>
      </div>
    </div>
  );
}

function LayerCard({ label, content }: { label: string; content: string }) {
  return (
    <div className="p-4 rounded-xl bg-[var(--surface-1)] border border-[var(--border-muted)]">
      <span className="text-xs text-rose-400 block mb-2">{label}</span>
      <p className="text-sm text-[var(--fg-muted)]">{content}</p>
    </div>
  );
}
