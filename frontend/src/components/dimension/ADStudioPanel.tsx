"use client";

/**
 * ADStudioPanel - Assistant Director AI Studio
 *
 * Sequence-aware cinematic prompt generation from scenario text
 * or video reference. Produces Kling 3.0 / Seedance 2.0 prompts
 * with emotional arc, visual rhythm, and continuity analysis.
 *
 * React 19: useTransition, useOptimistic
 * @see docs/PANEL_DESIGN_UNITY_SPEC.md
 */

import { useState, useCallback, useEffect, useTransition, useOptimistic } from "react";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionChainOptional, type ChainData } from "@/contexts/DimensionChainContext";
import ChainDataInput from "./ChainDataInput";
import { useChainDataInjection } from "@/hooks/useChainDataInjection";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import SceneCard from "./ad-studio/SceneCard";
import SequenceTimeline from "./ad-studio/SequenceTimeline";
import TransitionConnector from "./ad-studio/TransitionConnector";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { Download, Copy, Film, FileText, Upload } from "lucide-react";

// =============================================================================
// CONSTANTS
// =============================================================================

const DIMENSION_CODE = "ad-studio" as const;
const DIMENSION_KEY = "ad-studio";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";
const MAX_SCENARIO_LENGTH = 10000;
const CREDIT_COST = 10;
const MODEL_OPTIONS = [
  { value: "gemini-3-pro-preview", label: "Gemini 3 Pro" },
  { value: "gemini-2.5-flash-preview-05-20", label: "Gemini 2.5 Flash (Fast)" },
  { value: "gemini-2.5-pro-preview-05-06", label: "Gemini 2.5 Pro" },
];

// =============================================================================
// TYPES
// =============================================================================

interface TechniqueTag {
  technique_id: string;
  category: string;
  name_ko: string;
  name_en: string;
  description_ko: string;
}

interface SceneTechniques {
  composition: TechniqueTag[];
  camera_movement: TechniqueTag[];
  camera_angle: TechniqueTag[];
  lighting: TechniqueTag[];
  color: TechniqueTag[];
}

interface SequenceContext {
  previous_exit?: string;
  transition_in?: string;
  transition_out_setup?: string;
  emotional_position: string;
  camera_distance_flow: string;
}

interface EnginePrompts {
  kling_3_0: string;
  seedance_2_0: string;
  veo_3_1?: string;
}

interface ContinuityAnchorsPerScene {
  character?: string;
  style?: string;
}

interface SceneAnalysisResult {
  scene_number: number;
  description: string;
  description_en?: string;
  techniques: SceneTechniques;
  sequence_context: SequenceContext;
  prompts: EnginePrompts;
  continuity_anchors?: ContinuityAnchorsPerScene;
}

interface EmotionalBeat {
  scene_number: number;
  emotion: string;
  intensity: number;
  description: string;
}

interface VisualRhythm {
  edit_tempo: string;
  camera_distance_curve: string[];
  average_shot_duration?: string;
}

interface ColorBeat {
  scene_number: number;
  temperature: string;
  palette: string;
  hex_hint?: string;
}

interface ContinuityAnchors {
  character_anchors: string[];
  style_anchors: string[];
  lighting_anchors: string[];
}

interface SequenceAnalysisResult {
  emotional_arc: EmotionalBeat[];
  visual_rhythm: VisualRhythm;
  color_progression: ColorBeat[];
  continuity_anchors: ContinuityAnchors;
}

interface ADStudioResult {
  sequence: SequenceAnalysisResult;
  scenes: SceneAnalysisResult[];
  evidence_refs: string[];
}

export type { SceneAnalysisResult, EmotionalBeat, SequenceAnalysisResult, ADStudioResult, TechniqueTag };

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function ADStudioPanel() {
  return (
    <DimensionPanel dimensionCode={DIMENSION_CODE}>
      <ADStudioContent />
    </DimensionPanel>
  );
}

// =============================================================================
// CONTENT COMPONENT
// =============================================================================

type InputTab = "scenario" | "video";

function ADStudioContent() {
  const { classes, setLoading, setError, setResult } = useDimensionPanel();

  // Chain context
  const chainCtx = useDimensionChainOptional();
  const { evidenceRefs, hasUpstreamData, rawInputData } = useChainDataInjection(DIMENSION_KEY);

  // Tab state
  const [activeTab, setActiveTab] = useState<InputTab>("scenario");

  // Scenario tab state
  const [scenario, setScenario] = useState("");
  const [styleHint, setStyleHint] = useState("");
  const [enableKling, setEnableKling] = useState(true);
  const [enableSeedance, setEnableSeedance] = useState(true);
  const [enableVeo, setEnableVeo] = useState(true);

  // Model state
  const [model, setModel] = useState("gemini-3-pro-preview");

  // Video tab state
  const [videoUrl, setVideoUrl] = useState("");
  const [sceneTimestamps, setSceneTimestamps] = useState("");

  // Result state
  const [adResult, setAdResult] = useState<ADStudioResult | null>(null);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // React 19
  const [isTransitionPending, startTransition] = useTransition();
  const [optimisticResult, setOptimisticResult] = useOptimistic<ADStudioResult | null>(null);

  // BYOK
  const { byokKey } = useBYOK();

  // Credits
  const creditCtx = useCreditContextOptional();

  // Export
  const { copyToClipboard, isCopied, exportJSON } = useResultExport();

  // Set current dimension on mount
  useEffect(() => {
    if (chainCtx) chainCtx.setCurrentDimension(DIMENSION_KEY);
  }, [chainCtx]);

  // Auto-inject upstream data
  useEffect(() => {
    if (!hasUpstreamData || scenario) return;
    const typedData = rawInputData as Record<string, { output?: Record<string, unknown> } | undefined>;

    const storyOutput = typedData["story-architect"]?.output;
    if (storyOutput) {
      const synopsis = storyOutput.synopsis as string | undefined;
      const logline = storyOutput.logline as string | undefined;
      if (synopsis) setScenario(synopsis);
      else if (logline) setScenario(logline);
    }
  }, [hasUpstreamData, rawInputData, scenario]);

  // Handle chain data apply
  const handleApplyChainData = useCallback((data: Record<string, ChainData>) => {
    const storyOutput = data["story-architect"]?.output;
    if (storyOutput) {
      const synopsis = storyOutput.synopsis as string | undefined;
      const logline = storyOutput.logline as string | undefined;
      if (synopsis && !scenario) setScenario(synopsis);
      else if (logline && !scenario) setScenario(logline);
    }
  }, [scenario]);

  // Async operation — backend returns ADStudioResponse (flat, not wrapped)
  const { isLoading, error, execute, retry } = useAsyncOperation<ADStudioResult>({
    onSuccess: (response) => {
      if (response.scenes?.length > 0) {
        setAdResult(response);
        setResult(response);

        if (chainCtx) {
          chainCtx.setChainData(
            DIMENSION_KEY,
            response as unknown as Record<string, unknown>,
            `${response.scenes.length} scenes analyzed`,
            response.evidence_refs || evidenceRefs,
          );
        }

        if (creditCtx) void creditCtx.refresh();
      }
    },
    onError: (err) => {
      setError(err);
      if (err.message.includes("Credit") || err.message.includes("402")) {
        setShowCreditModal(true);
      }
    },
    retryCount: 2,
    retryDelay: 2000,
    nonRetryableErrors: ["400", "401", "402", "403", "404", "credit"],
  });

  const combinedLoading = isLoading || isTransitionPending;

  // Handle scenario analyze
  const handleAnalyzeScenario = useCallback(async () => {
    const trimmed = scenario.trim();
    if (!trimmed) {
      setValidationError("시나리오를 입력하세요");
      return;
    }
    if (trimmed.length > MAX_SCENARIO_LENGTH) {
      setValidationError(`시나리오는 ${MAX_SCENARIO_LENGTH}자 이하로 입력해주세요`);
      return;
    }
    if (!enableKling && !enableSeedance && !enableVeo) {
      setValidationError("하나 이상의 엔진을 선택하세요");
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

    startTransition(() => {
      setOptimisticResult({
        sequence: {
          emotional_arc: [],
          visual_rhythm: { edit_tempo: "...", camera_distance_curve: [] },
          color_progression: [],
          continuity_anchors: { character_anchors: [], style_anchors: [], lighting_anchors: [] },
        },
        scenes: Array.from({ length: 3 }, (_, i) => ({
          scene_number: i + 1,
          description: "분석 중...",
          techniques: { composition: [], camera_movement: [], camera_angle: [], lighting: [], color: [] },
          sequence_context: { emotional_position: "...", camera_distance_flow: "..." },
          prompts: { kling_3_0: "생성 중...", seedance_2_0: "생성 중...", veo_3_1: "생성 중..." },
        })),
        evidence_refs: [],
      });
    });

    try {
      const engines: string[] = [];
      if (enableKling) engines.push("kling");
      if (enableSeedance) engines.push("seedance");
      if (enableVeo) engines.push("veo");

      const payload: Record<string, unknown> = {
        scenario: trimmed,
        target_engines: engines,
        model,
      };
      if (styleHint.trim()) payload.style_hint = styleHint.trim();

      await execute(`${API_BASE}/api/dimension/ad-studio/analyze`, payload, getBYOKHeaders(byokKey));
    } finally {
      setLoading(false);
      startTransition(() => {
        setOptimisticResult(null);
      });
    }
  }, [scenario, styleHint, model, enableKling, enableSeedance, byokKey, creditCtx, execute, setLoading, setError, setResult, startTransition, setOptimisticResult]);

  // Handle video analyze — backend expects JSON { video_url, scene_timestamps }
  const handleAnalyzeVideo = useCallback(async () => {
    const trimmedUrl = videoUrl.trim();
    if (!trimmedUrl) {
      setValidationError("영상 URL을 입력하세요 (씬 감지 결과에서 복사)");
      return;
    }
    if (!trimmedUrl.startsWith("http://") && !trimmedUrl.startsWith("https://")) {
      setValidationError("올바른 URL을 입력하세요 (http:// 또는 https://)");
      return;
    }
    if (!enableKling && !enableSeedance && !enableVeo) {
      setValidationError("하나 이상의 엔진을 선택하세요");
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

    try {
      const engines: string[] = [];
      if (enableKling) engines.push("kling");
      if (enableSeedance) engines.push("seedance");
      if (enableVeo) engines.push("veo");

      const timestamps = sceneTimestamps
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);

      const payload: Record<string, unknown> = {
        video_url: trimmedUrl,
        scene_timestamps: timestamps,
        target_engines: engines,
        model,
      };
      if (styleHint.trim()) payload.style_hint = styleHint.trim();

      await execute(`${API_BASE}/api/dimension/ad-studio/analyze-video`, payload, getBYOKHeaders(byokKey));
    } finally {
      setLoading(false);
    }
  }, [videoUrl, sceneTimestamps, styleHint, model, enableKling, enableSeedance, byokKey, creditCtx, execute, setLoading, setError, setResult]);

  // Copy all prompts
  const handleCopyAllPrompts = useCallback(() => {
    if (!adResult) return;
    const allPrompts = adResult.scenes.map((s) => {
      const lines = [`--- Scene ${s.scene_number} ---`];
      if (enableKling) lines.push(`[Kling 3.0]\n${s.prompts.kling_3_0}`);
      if (enableSeedance) lines.push(`[Seedance 2.0]\n${s.prompts.seedance_2_0}`);
      if (enableVeo && s.prompts.veo_3_1) lines.push(`[Veo 3.1]\n${s.prompts.veo_3_1}`);
      return lines.join("\n\n");
    }).join("\n\n");
    copyToClipboard(allPrompts);
  }, [adResult, enableKling, enableSeedance, enableVeo, copyToClipboard]);

  // Export JSON
  const handleExportJson = useCallback(() => {
    if (adResult) exportJSON(adResult, `ad-studio-${Date.now()}.json`);
  }, [adResult, exportJSON]);

  // Scroll to scene card
  const handleSceneClick = useCallback((index: number) => {
    const el = document.getElementById(`ad-scene-${index}`);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
  }, []);

  const displayResult = adResult || optimisticResult;
  const isOptimistic = !!optimisticResult && !adResult;

  return (
    <>
      {/* Header */}
      <DimensionPanel.Header
        title="AD Studio"
        titleKo="조감독 AI"
        creditCost={CREDIT_COST}
      />

      {/* Sidebar */}
      <DimensionPanel.Sidebar>
        {/* Chain Data Input */}
        <ChainDataInput
          currentDimension={DIMENSION_KEY}
          onApplyData={handleApplyChainData}
          themeColor="amber"
        />

        {/* Upstream Data Banner */}
        {hasUpstreamData && (
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 mb-3">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              <span className="text-xs font-medium text-amber-400">
                Story Engine 데이터 감지됨
              </span>
            </div>
          </div>
        )}

        {/* Tab Selector */}
        <div className="space-y-2">
          <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">
            입력 방식
          </label>
          <div className="flex gap-1 p-1 bg-slate-100 dark:bg-white/5 rounded-xl border border-slate-200 dark:border-white/10">
            <button
              onClick={() => setActiveTab("scenario")}
              disabled={combinedLoading}
              className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1.5 ${
                activeTab === "scenario"
                  ? `${classes.bg} text-white shadow-sm`
                  : "text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/5"
              } disabled:opacity-50`}
            >
              <FileText className="w-3.5 h-3.5" />
              시나리오
            </button>
            <button
              onClick={() => setActiveTab("video")}
              disabled={combinedLoading}
              className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1.5 ${
                activeTab === "video"
                  ? `${classes.bg} text-white shadow-sm`
                  : "text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/5"
              } disabled:opacity-50`}
            >
              <Upload className="w-3.5 h-3.5" />
              영상 레퍼런스
            </button>
          </div>
        </div>

        {/* Scenario Tab */}
        {activeTab === "scenario" && (
          <DimensionPanel.Textarea
            label="시나리오"
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            placeholder="시나리오를 입력하세요...&#10;&#10;예: 어두운 골목에서 주인공이 걸어나온다. 네온사인이 비추는 얼굴. 카메라는 천천히 줌인하며..."
            maxLength={MAX_SCENARIO_LENGTH}
            showCount
            error={validationError || undefined}
            disabled={combinedLoading}
            rows={8}
          />
        )}

        {/* Video Tab */}
        {activeTab === "video" && (
          <>
            <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20">
              <p className="text-xs text-blue-400 leading-relaxed">
                <strong>사용법:</strong> Academy &gt; 씬 감지에서 영상을 업로드하고,
                결과에서 영상 URL과 타임스탬프를 복사하세요.
              </p>
            </div>
            <DimensionPanel.Input
              label="영상 URL"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              placeholder="https://... (씬 감지 결과 URL)"
              disabled={combinedLoading}
            />
            <DimensionPanel.Textarea
              label="씬 타임스탬프 (선택)"
              value={sceneTimestamps}
              onChange={(e) => setSceneTimestamps(e.target.value)}
              placeholder={"00:00, 00:15, 00:30\n(씬 감지 결과에서 복사)"}
              disabled={combinedLoading}
              rows={3}
            />
            {validationError && activeTab === "video" && (
              <p className="text-xs text-red-400 ml-1">{validationError}</p>
            )}
          </>
        )}

        {/* Style Hint */}
        <DimensionPanel.Input
          label="스타일 힌트 (선택)"
          value={styleHint}
          onChange={(e) => setStyleHint(e.target.value)}
          placeholder="dark and moody, bright pop, neo-noir..."
          disabled={combinedLoading}
        />

        {/* AI Model */}
        <DimensionPanel.Select
          label="AI 모델"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          options={MODEL_OPTIONS}
          disabled={combinedLoading}
        />

        {/* Target Engines */}
        <div className="space-y-2">
          <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">
            타겟 엔진
          </label>
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => setEnableKling(!enableKling)}
              disabled={combinedLoading}
              className={`py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                enableKling
                  ? `${classes.bg} text-white`
                  : "bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-zinc-400 hover:bg-slate-200 dark:hover:bg-white/10"
              } disabled:opacity-50`}
            >
              Kling 3.0
            </button>
            <button
              onClick={() => setEnableSeedance(!enableSeedance)}
              disabled={combinedLoading}
              className={`py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                enableSeedance
                  ? `${classes.bg} text-white`
                  : "bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-zinc-400 hover:bg-slate-200 dark:hover:bg-white/10"
              } disabled:opacity-50`}
            >
              Seedance 2.0
            </button>
            <button
              onClick={() => setEnableVeo(!enableVeo)}
              disabled={combinedLoading}
              className={`py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                enableVeo
                  ? `${classes.bg} text-white`
                  : "bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-zinc-400 hover:bg-slate-200 dark:hover:bg-white/10"
              } disabled:opacity-50`}
            >
              Veo 3.1
            </button>
          </div>
        </div>

        {/* BYOK Guide */}
        {!byokKey && (
          <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/10">
            <p className="text-xs text-amber-400/80 leading-relaxed">
              <strong>Tip:</strong> Google API 키가 있으면 크레딧 없이 무료 사용 가능!{" "}
              <a href="/api-key-guide" className="underline hover:text-amber-300">
                $300 무료 크레딧 받기 →
              </a>
            </p>
          </div>
        )}

        {/* Generate Button */}
        <DimensionPanel.GenerateButton
          onClick={activeTab === "scenario" ? handleAnalyzeScenario : handleAnalyzeVideo}
          loading={combinedLoading}
          disabled={activeTab === "scenario" ? !scenario.trim() : !videoUrl.trim()}
          className="mt-6"
          icon={<Film className="w-5 h-5" />}
        >
          분석 시작{!byokKey && ` (${CREDIT_COST} credits)`}
        </DimensionPanel.GenerateButton>
      </DimensionPanel.Sidebar>

      {/* Content */}
      <DimensionPanel.Content>
        {/* Loading State */}
        <DimensionPanel.Loading
          message={
            activeTab === "scenario"
              ? "시나리오를 분석하고 시퀀스 컨텍스트를 추출합니다..."
              : "영상 레퍼런스를 분석하고 시네마틱 기법을 매칭합니다..."
          }
        />

        {/* Error State */}
        <DimensionPanel.Error onRetry={retry} />

        {/* Result */}
        {displayResult && displayResult.scenes.length > 0 && (
          <div
            className={`max-w-5xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10 ${
              isOptimistic ? "opacity-60" : ""
            }`}
          >
            {/* Optimistic Progress */}
            {isOptimistic && (
              <div className="flex items-center gap-3 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
                <div className="w-5 h-5 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
                <div>
                  <p className="text-sm font-medium text-amber-400">분석 중...</p>
                  <p className="text-xs text-amber-400/60">Gemini가 시나리오를 분석하고 프롬프트를 생성합니다</p>
                </div>
              </div>
            )}

            {/* Toolbar */}
            {!isOptimistic && (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${classes.bg}`} />
                  <span className="text-xs font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest">
                    {displayResult.scenes.length}개 장면 분석 완료
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCopyAllPrompts}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-zinc-400 hover:bg-slate-200 dark:hover:bg-white/10 transition-colors"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    {isCopied ? "복사됨!" : "전체 프롬프트 복사"}
                  </button>
                  <button
                    onClick={handleExportJson}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-zinc-400 hover:bg-slate-200 dark:hover:bg-white/10 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    JSON
                  </button>
                </div>
              </div>
            )}

            {/* Sequence Timeline */}
            {!isOptimistic && displayResult.sequence?.emotional_arc && (
              <SequenceTimeline
                scenes={displayResult.scenes}
                emotionalArc={displayResult.sequence.emotional_arc}
                onSceneClick={handleSceneClick}
              />
            )}

            {/* Scene Cards with Transition Connectors */}
            <div className="space-y-2">
              {displayResult.scenes.map((scene, idx) => (
                <div key={scene.scene_number} id={`ad-scene-${idx}`}>
                  {idx > 0 && (
                    <TransitionConnector
                      fromScene={displayResult.scenes[idx - 1]}
                      toScene={scene}
                    />
                  )}
                  <SceneCard scene={scene} index={idx} />
                </div>
              ))}
            </div>

            {/* Evidence Display */}
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            <DimensionPanel.Evidence refs={(displayResult as any)?.evidence_refs} />

            {/* Next Navigation */}
            <DimensionPanel.NextNav />
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && !adResult && !optimisticResult && (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 dark:text-zinc-500 space-y-8 animate-in fade-in zoom-in-95 duration-700">
            <div className="relative group">
              <div
                className={`absolute inset-0 ${classes.bg}/20 blur-[80px] rounded-full group-hover:${classes.bg}/30 transition-colors duration-1000`}
              />
              <div className="w-32 h-32 rounded-[2rem] bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex items-center justify-center shadow-lg dark:shadow-[0_0_60px_rgba(0,0,0,0.3)] backdrop-blur-md relative transform group-hover:scale-105 transition-all duration-500">
                <Film className="w-14 h-14 text-amber-500/60" />
              </div>
            </div>
            <div className="text-center space-y-3">
              <h3 className="text-2xl font-bold text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-b dark:from-white dark:to-white/40 tracking-tight">
                AD Studio
              </h3>
              <p className="text-sm text-slate-500 dark:text-zinc-500 max-w-xs mx-auto font-light leading-relaxed">
                시나리오에서 시퀀스 컨텍스트를 분석하고
                <br />
                <span className={`${classes.text} font-medium`}>시네마틱 프롬프트</span>를 자동 생성합니다
              </p>
              <div className="flex items-center justify-center gap-3 pt-4">
                <span className="px-3 py-1 text-xs rounded-full bg-amber-500/10 text-amber-500">
                  감정 아크
                </span>
                <span className="px-3 py-1 text-xs rounded-full bg-emerald-500/10 text-emerald-500">
                  시각 리듬
                </span>
                <span className="px-3 py-1 text-xs rounded-full bg-violet-500/10 text-violet-500">
                  연속성
                </span>
              </div>
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
        onRetry={activeTab === "scenario" ? handleAnalyzeScenario : handleAnalyzeVideo}
      />
    </>
  );
}
