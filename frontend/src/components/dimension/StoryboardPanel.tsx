"use client";

/**
 * StoryboardPanel - 스토리보드 생성기
 *
 * 2026 Golden App: React 19 Best Practices
 *
 * Features:
 * - useTransition for non-blocking form submission
 * - useOptimistic for instant UI feedback
 * - Visual storyboard scene generation
 *
 * @see https://react.dev/blog/2024/12/05/react-19
 * @see docs/PANEL_DESIGN_UNITY_SPEC.md
 */

import { useState, useCallback, useTransition, useOptimistic } from "react";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import { Download, Layout } from "lucide-react";

// ============================================================================
// Constants & Types
// ============================================================================

const DIMENSION_CODE = "2d"; // Storyboard uses 2d dimension
const DIMENSION_KEY = "storyboard";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";
const MAX_SCRIPT_LENGTH = 3000;

interface StoryboardScene {
  scene_number: number;
  description: string;
  camera: string;
  duration: string;
  notes?: string;
  visual_prompt?: string;
  shot_type?: string;
  camera_movement?: string;
  audio_cues?: string;
  camera_angle?: string;
  midjourney_prompt?: string;
}

interface StoryboardResult {
  scenes: StoryboardScene[];
}

const MODELS = [{ value: "gemini-3-pro-preview", label: "Pro (고품질)" }];

const VISUAL_STYLES = [
  "Cinematic",
  "Anime",
  "3D Render",
  "Watercolor",
  "Cyberpunk",
  "Noir",
  "Realistic",
  "Fantasy",
];

// ============================================================================
// Main Export
// ============================================================================

export default function StoryboardPanel() {
  return (
    <DimensionPanel dimensionCode={DIMENSION_CODE}>
      <StoryboardContent />
    </DimensionPanel>
  );
}

// ============================================================================
// Content Component
// ============================================================================

function StoryboardContent() {
  const { token, setLoading, setResult, setError, classes } = useDimensionPanel();

  // Form state
  const [script, setScript] = useState("");
  const [style, setStyle] = useState("Cinematic");
  const [sceneCount, setSceneCount] = useState(5);
  const [language, setLanguage] = useState<"ko" | "en">("ko");
  const [model, setModel] = useState("gemini-3-flash-preview");
  const [files, setFiles] = useState<File[]>([]);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Result state
  const [storyboardResult, setStoryboardResult] = useState<StoryboardResult | null>(null);

  // React 19: useTransition for non-blocking form submission
  const [isTransitionPending, startTransition] = useTransition();

  // React 19: useOptimistic for instant UI feedback
  const [optimisticResult, setOptimisticResult] = useOptimistic<StoryboardResult | null>(null);

  // BYOK and credits
  const { byokKey } = useBYOK();
  const creditCtx = useCreditContextOptional();
  const { getToolByDimension } = useDimensionConfig();
  const toolConfig = getToolByDimension("2D");
  const CREDIT_COST = toolConfig?.creditCost ?? 10;

  // Export utilities
  const { exportJSON } = useResultExport();

  // Async operation hook
  const { isLoading, error, execute, retry, canRetry } = useAsyncOperation<{
    success: boolean;
    output: StoryboardResult;
    error?: string;
  }>({
    onSuccess: (data) => {
      if (data.success) {
        setStoryboardResult(data.output);
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

  // Combined loading state (React 19)
  const isPending = isLoading || isTransitionPending;

  // Generate storyboard
  const handleGenerate = useCallback(() => {
    const trimmedScript = script.trim();
    if (!trimmedScript) {
      setValidationError("스토리 컨셉을 입력해주세요");
      return;
    }
    if (trimmedScript.length > MAX_SCRIPT_LENGTH) {
      setValidationError(`스토리 컨셉은 ${MAX_SCRIPT_LENGTH}자 이하로 입력해주세요`);
      return;
    }
    setValidationError(null);

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
      setShowCreditModal(true);
      return;
    }

    // React 19: Non-blocking transition with optimistic UI
    startTransition(async () => {
      // Optimistic: Show placeholder scenes immediately
      setOptimisticResult({
        scenes: Array.from({ length: sceneCount }, (_, i) => ({
          scene_number: i + 1,
          description: "생성 중...",
          camera: "분석 중...",
          duration: "...",
        })),
      });

      await wrappedExecute(
        `${API_BASE}/api/dimension/2d/create`,
        { concept: script, scene_count: sceneCount, language, model },
        getBYOKHeaders(byokKey)
      );

      setOptimisticResult(null);
    });
  }, [script, sceneCount, language, model, byokKey, creditCtx, wrappedExecute, CREDIT_COST, startTransition, setOptimisticResult]);

  // Export result as JSON
  const handleExportJson = useCallback(() => {
    if (storyboardResult) {
      exportJSON(storyboardResult, `storyboard-${Date.now()}.json`);
    }
  }, [storyboardResult, exportJSON]);

  // Helper to format duration
  const formatTime = (duration: string | undefined) => {
    if (!duration) return "N/A";
    const match = duration.match(/(\d+)([smh])/);
    if (match) {
      const value = parseInt(match[1]);
      const unit = match[2];
      if (unit === "s") return `${value}s`;
      if (unit === "m") return `${value}m`;
      if (unit === "h") return `${value}h`;
    }
    return duration;
  };

  const displayError = validationError || error;

  return (
    <>
      <DimensionPanel.Header title="스토리보드 생성기" creditCost={CREDIT_COST} />

      <DimensionPanel.Sidebar>
        {/* Script Input */}
        <div className="space-y-2">
          <label className={`text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1`}>
            스크립트 입력
          </label>
          <textarea
            value={script}
            onChange={(e) => setScript(e.target.value)}
            placeholder="시각화할 스크립트나 시나리오를 입력하세요..."
            className={`w-full h-48 px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-white/30 resize-none focus:outline-none focus:ring-2 focus:ring-${token.themeColor}-500/50`}
            disabled={isLoading}
          />
          <div className="text-xs text-slate-400 dark:text-white/40 text-right">
            {script.length}/{MAX_SCRIPT_LENGTH}
          </div>
        </div>

        {/* File Upload */}
        <DimensionPanel.FileUpload
          accept={["*"]}
          maxSizeMB={100}
          multiple
          onUpload={setFiles}
          label="참고 자료 (선택)"
          helperText="기존 스토리보드, 무드보드 이미지 또는 PDF"
        />

        {/* Scene Count */}
        <DimensionPanel.Select
          label="장면 수"
          value={String(sceneCount)}
          onChange={(e) => setSceneCount(Number(e.target.value))}
          options={[
            { value: "4", label: "4 장면 (Short)" },
            { value: "6", label: "6 장면 (Standard)" },
            { value: "8", label: "8 장면 (Extended)" },
          ]}
        />

        {/* Visual Style */}
        <DimensionPanel.Select
          label="비주얼 스타일"
          value={style}
          onChange={(e) => setStyle(e.target.value)}
          options={VISUAL_STYLES.map((s) => ({ value: s, label: s }))}
        />

        {/* Language Toggle */}
        <div className="space-y-2 group">
          <label className={`text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1`}>
            언어
          </label>
          <div className="flex gap-1 p-1 bg-slate-100 dark:bg-white/5 rounded-xl border border-slate-200 dark:border-white/10">
            <button
              onClick={() => setLanguage("ko")}
              className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${
                language === "ko"
                  ? `${classes.bg} text-black shadow-sm`
                  : "text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/5"
              }`}
            >
              KO
            </button>
            <button
              onClick={() => setLanguage("en")}
              className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${
                language === "en"
                  ? `${classes.bg} text-black shadow-sm`
                  : "text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/5"
              }`}
            >
              EN
            </button>
          </div>
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
          onClick={handleGenerate}
          disabled={!script.trim()}
          loading={isPending}
          creditCost={CREDIT_COST}
          icon={<Layout className="w-5 h-5" />}
          loadingText="스토리보드 생성 중..."
        >
          Create Storyboard
        </DimensionPanel.GenerateButton>

        {/* Validation Error */}
        {validationError && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs break-keep leading-relaxed animate-in fade-in slide-in-from-top-1">
            {validationError}
          </div>
        )}
      </DimensionPanel.Sidebar>

      <DimensionPanel.Content>
        {/* Loading State - React 19: Shows during transition */}
        <DimensionPanel.Loading message="스토리보드 생성 중..." />

        {/* Error State */}
        {displayError && !isPending && (
          <DimensionPanel.Error
            error={displayError}
            onRetry={canRetry ? () => void retry() : undefined}
          />
        )}

        {/* Optimistic Result Display (React 19) */}
        {optimisticResult && isPending && (
          <div className="max-w-5xl mx-auto space-y-6 animate-in fade-in duration-300 pb-20 opacity-60">
            <div className="flex items-center justify-center gap-2 py-3 px-4 bg-cyan-500/10 rounded-lg border border-cyan-500/20">
              <div className="w-3 h-3 rounded-full bg-cyan-500 animate-pulse" />
              <span className="text-sm text-cyan-600 dark:text-cyan-300">
                {sceneCount}개 장면 생성 중...
              </span>
            </div>
            <div className="grid grid-cols-1 gap-4">
              {optimisticResult.scenes.map((scene, idx) => (
                <div key={idx} className="p-4 bg-white/50 dark:bg-black/20 border border-slate-200 dark:border-white/5 rounded-2xl animate-pulse">
                  <div className="flex justify-between mb-4">
                    <div className="h-4 w-24 bg-slate-200 dark:bg-white/10 rounded" />
                    <div className="h-4 w-12 bg-slate-200 dark:bg-white/10 rounded" />
                  </div>
                  <div className="space-y-2">
                    <div className="h-3 w-full bg-slate-200 dark:bg-white/10 rounded" />
                    <div className="h-3 w-3/4 bg-slate-200 dark:bg-white/10 rounded" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Result Display */}
        {storyboardResult && !isPending && (
          <StoryboardResultDisplay
            result={storyboardResult}
            onExport={handleExportJson}
            formatTime={formatTime}
            themeColor={token.themeColor}
          />
        )}

        {/* Empty State */}
        {!storyboardResult && !isPending && !displayError && !optimisticResult && (
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
        onRetry={handleGenerate}
      />
    </>
  );
}

// ============================================================================
// Sub-Components
// ============================================================================

function StoryboardResultDisplay({
  result,
  onExport,
  formatTime,
  themeColor,
}: {
  result: StoryboardResult;
  onExport: () => void;
  formatTime: (d: string | undefined) => string;
  themeColor: string;
}) {
  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <div className="flex items-center justify-between px-1">
        <h3 className="text-sm font-semibold text-slate-500 dark:text-zinc-400 uppercase tracking-wider flex items-center gap-2">
          <span className={`w-1.5 h-1.5 rounded-full bg-${themeColor}-400`}></span>
          Generated Scenes ({result.scenes.length})
        </h3>
        <button
          onClick={onExport}
          className="px-3 py-1.5 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 hover:bg-slate-100 dark:hover:bg-white/10 hover:border-slate-300 dark:hover:border-white/20 text-slate-600 dark:text-white text-xs font-medium rounded-lg transition-all flex items-center gap-2"
        >
          <Download className="w-4 h-4 text-slate-500 dark:text-zinc-400" />
          JSON Export
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {result.scenes.map((scene, idx) => (
          <div key={idx} className="group relative">
            <div
              className={`absolute inset-0 bg-${themeColor}-500/5 blur-xl rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500`}
            />
            <div
              className={`p-4 bg-white/80 dark:bg-black/40 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-2xl shadow-sm dark:shadow-[0_8px_32px_rgba(0,0,0,0.3)] font-mono text-base leading-relaxed text-slate-800 dark:text-zinc-100 group-hover:border-${themeColor}-400/50 dark:group-hover:border-${themeColor}-500/30 group-hover:bg-white dark:group-hover:bg-black/50 transition-all relative overflow-hidden h-full`}
            >
              <div
                className={`absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-${themeColor}-400 to-blue-500 dark:from-${themeColor}-500 dark:to-blue-500 shadow-[0_0_20px_#06b6d4]`}
              ></div>

              {/* Scene Header */}
              <div className="flex justify-between items-center mb-4 border-b border-slate-100 dark:border-white/5 pb-2">
                <h4
                  className={`text-[12px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest group-hover:text-${themeColor}-600 dark:group-hover:text-${themeColor}-400/80 transition-colors`}
                >
                  Scene #{scene.scene_number}
                </h4>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full bg-${themeColor}-100 dark:bg-${themeColor}-900/30 text-${themeColor}-700 dark:text-${themeColor}-300 border border-${themeColor}-200 dark:border-${themeColor}-500/30`}
                >
                  {formatTime(scene.duration)}
                </span>
              </div>

              {/* Content Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="space-y-4">
                  <div>
                    <span className="text-[10px] text-slate-400 dark:text-zinc-500 uppercase tracking-wider block mb-1">
                      Visual
                    </span>
                    <p className="text-sm text-slate-700 dark:text-white/90 leading-relaxed font-light">
                      {scene.description}
                    </p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 dark:text-zinc-500 uppercase tracking-wider block mb-1">
                      Audio
                    </span>
                    <div className="flex gap-2 items-start">
                      <span className="text-xs bg-slate-100 dark:bg-white/5 px-2 py-1 rounded text-slate-600 dark:text-zinc-400 whitespace-nowrap">
                        SFX
                      </span>
                      <p className="text-xs text-slate-600 dark:text-zinc-400 italic leading-relaxed pt-0.5">
                        {scene.audio_cues}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="space-y-3 pt-3 lg:pt-0 lg:pl-4 lg:border-l lg:border-slate-100 dark:lg:border-white/5">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-slate-50 dark:bg-white/5 rounded-lg p-2 text-center">
                      <span className="text-[10px] text-slate-400 dark:text-zinc-500 block mb-1">
                        Camera
                      </span>
                      <span className={`text-xs text-${themeColor}-700 dark:text-${themeColor}-300 font-medium`}>
                        {scene.camera_angle}
                      </span>
                    </div>
                    <div className="bg-slate-50 dark:bg-white/5 rounded-lg p-2 text-center">
                      <span className="text-[10px] text-slate-400 dark:text-zinc-500 block mb-1">
                        Movement
                      </span>
                      <span className={`text-xs text-${themeColor}-700 dark:text-${themeColor}-300 font-medium`}>
                        {scene.camera_movement}
                      </span>
                    </div>
                  </div>

                  <div className="bg-gradient-to-br from-slate-900/5 to-slate-900/10 dark:from-black/40 dark:to-black/60 rounded-lg p-3 border border-slate-200 dark:border-white/5">
                    <span className="text-[10px] text-slate-400 dark:text-zinc-600 block mb-1 text-center">
                      Prompt Preview
                    </span>
                    <p className="text-[10px] text-slate-500 dark:text-zinc-400 line-clamp-3 font-mono leading-tight opacity-70">
                      {scene.midjourney_prompt}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EmptyState({ themeColor }: { themeColor: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-8 animate-in fade-in zoom-in-95 duration-700">
      <div className="relative group">
        <div
          className={`absolute inset-0 bg-${themeColor}-500/20 blur-[80px] rounded-full group-hover:bg-${themeColor}-500/30 transition-colors duration-1000`}
        />
        <div
          className={`w-32 h-32 rounded-[2rem] bg-white/[0.02] border border-white/10 flex items-center justify-center shadow-[0_0_60px_rgba(0,0,0,0.3)] backdrop-blur-md relative transform group-hover:scale-105 transition-all duration-500 group-hover:border-${themeColor}-500/20`}
        >
          <div className="absolute inset-0 bg-gradient-to-tr from-white/5 to-transparent rounded-[2rem]" />
          <svg
            className={`w-12 h-12 text-white/20 group-hover:text-${themeColor}-400 transition-colors duration-500`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1}
              d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
            />
          </svg>
        </div>
      </div>
      <div className="text-center space-y-3">
        <h3 className="text-2xl font-bold text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-b dark:from-white dark:to-white/40 tracking-tight">
          Ready to Visualize
        </h3>
        <p className="text-sm text-slate-500 dark:text-zinc-500 max-w-xs mx-auto font-light leading-relaxed">
          스토리를 장면 단위로 시각화하고
          <br />
          <span className={`text-${themeColor}-600 dark:text-${themeColor}-500/80 font-medium`}>
            Midjourney & Runway 프롬프트
          </span>
          를 자동 생성합니다.
        </p>
      </div>
    </div>
  );
}
