"use client";

/**
 * KlingPanel - Kling 2.6 AI Video Generation
 *
 * 2026 Golden App: React 19 Best Practices
 *
 * Features:
 * - Text-to-Video & Image-to-Video generation
 * - Elements: Up to 4 reference images for character consistency
 * - Motion Control: Preset-based motion intensity
 * - Camera Control: Cinematic camera movements
 * - End Frame: Shot sequencing support
 * - Native Audio: Sound effects and ambient audio
 *
 * @see docs/PANEL_DESIGN_UNITY_SPEC.md
 * @see https://react.dev/blog/2024/12/05/react-19
 */

import { useState, useCallback, useTransition, useOptimistic, useEffect } from "react";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { getPreviousStepResult } from "@/lib/workflow-state";
import InsufficientCreditsModal from "./InsufficientCreditsModal";

// =============================================================================
// CONSTANTS
// =============================================================================

const DIMENSION_CODE = "veo" as const; // Shares color theme with VEO
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

// =============================================================================
// TYPES
// =============================================================================

interface KlingGenerateResponse {
  success: boolean;
  task_id: string;
  status: string;
  video_url?: string;
  thumbnail_url?: string;
  credits_used: number;
  error?: string;
}

// =============================================================================
// OPTIONS
// =============================================================================

const DURATIONS = [
  { value: "5", label: "5 seconds", credits720: 35, credits1080: 50 },
  { value: "10", label: "10 seconds", credits720: 70, credits1080: 100 },
];

const ASPECT_RATIOS = [
  { value: "16:9", label: "Landscape (16:9)", icon: "rectangle" },
  { value: "9:16", label: "Portrait (9:16)", icon: "phone" },
  { value: "1:1", label: "Square (1:1)", icon: "square" },
];

const RESOLUTIONS = [
  { value: "720p", label: "HD (720p)" },
  { value: "1080p", label: "Full HD (1080p)" },
];

const MODES = [
  { value: "std", label: "Standard", description: "Faster generation" },
  { value: "pro", label: "Professional", description: "Best quality" },
];

const MOTION_PRESETS = [
  { value: "", label: "Auto" },
  { value: "slow", label: "Slow Motion" },
  { value: "normal", label: "Normal" },
  { value: "fast", label: "Fast Motion" },
  { value: "dramatic", label: "Dramatic" },
];

const CAMERA_PRESETS = [
  { value: "", label: "None" },
  { value: "static", label: "Static" },
  { value: "pan_left", label: "Pan Left" },
  { value: "pan_right", label: "Pan Right" },
  { value: "tilt_up", label: "Tilt Up" },
  { value: "tilt_down", label: "Tilt Down" },
  { value: "zoom_in", label: "Zoom In" },
  { value: "zoom_out", label: "Zoom Out" },
  { value: "dolly_in", label: "Dolly In" },
  { value: "dolly_out", label: "Dolly Out" },
  { value: "orbit", label: "Orbit" },
];

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function KlingPanel() {
  return (
    <DimensionPanel dimensionCode={DIMENSION_CODE}>
      <KlingContent />
    </DimensionPanel>
  );
}

// =============================================================================
// CONTENT COMPONENT
// =============================================================================

function KlingContent() {
  const { classes, styles: _styles, setLoading, setError, setResult } = useDimensionPanel();

  // Form state
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState("");
  const [duration, setDuration] = useState("5");
  const [aspectRatio, setAspectRatio] = useState("16:9");
  const [resolution, setResolution] = useState("1080p");
  const [mode, setMode] = useState("std");
  const [enableAudio, setEnableAudio] = useState(false);
  const [imageUrl, setImageUrl] = useState("");
  const [endImageUrl, setEndImageUrl] = useState("");
  const [motionPreset, setMotionPreset] = useState("");
  const [cameraPreset, setCameraPreset] = useState("");
  const [_files, setFiles] = useState<File[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // React 19: useTransition for non-blocking submission
  const [isTransitionPending, startTransition] = useTransition();

  // ==========================================================================
  // Session Context Inheritance (2026 Best Practice)
  // Inject character refs/image URL from previous step (VisualRealizer → Kling)
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

    // Auto-set imageUrl from previous step character refs
    if (Array.isArray(data.keyframes) && data.keyframes.length > 0 && !imageUrl) {
      const firstKeyframe = (data.keyframes as Array<Record<string, unknown>>)[0];
      if (firstKeyframe?.url) {
        setImageUrl(firstKeyframe.url as string);
      }
    }

    // Auto-set prompt from scene description
    if (data.scene_prompt && !prompt) {
      setPrompt(data.scene_prompt as string);
    }

    // Handle motion hints from style guide
    if (data.style_guide && typeof data.style_guide === "object" && !motionPreset) {
      const styleGuide = data.style_guide as Record<string, unknown>;
      if (styleGuide.pacing?.toString().toLowerCase().includes("slow")) {
        setMotionPreset("slow");
      } else if (styleGuide.pacing?.toString().toLowerCase().includes("fast")) {
        setMotionPreset("fast");
      } else if (styleGuide.pacing?.toString().toLowerCase().includes("dramatic")) {
        setMotionPreset("dramatic");
      }
    }

    // Handle camera hints
    if (data.camera_movement && !cameraPreset) {
      const cam = (data.camera_movement as string).toLowerCase();
      const matchingPreset = CAMERA_PRESETS.find((p) =>
        cam.includes(p.value.replace("_", " "))
      );
      if (matchingPreset) {
        setCameraPreset(matchingPreset.value);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Initial mount only
  }, []);

  // React 19: useOptimistic for instant UI feedback
  const [optimisticResult, setOptimisticResult] = useOptimistic<KlingGenerateResponse | null>(null);

  // Credits
  const creditCtx = useCreditContextOptional();

  // Export utilities
  const { copyToClipboard, isCopied, exportJSON: _exportJSON } = useResultExport();

  // Calculate credit cost
  const creditCost = (() => {
    const durationInfo = DURATIONS.find((d) => d.value === duration);
    if (!durationInfo) return 50;
    return resolution === "1080p" ? durationInfo.credits1080 : durationInfo.credits720;
  })();

  // Async operation hook
  const {
    isLoading,
    progress: _progress,
    error,
    data: result,
    execute,
    cancel: _cancel,
    retry,
  } = useAsyncOperation<KlingGenerateResponse>({
    onSuccess: (data) => {
      if (data.success) {
        setResult(data);
        if (creditCtx) {
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
    retryCount: 2,
    retryDelay: 2000,
    nonRetryableErrors: ["400", "401", "402", "403", "404", "credit"],
  });

  const combinedLoading = isLoading || isTransitionPending;
  const MAX_PROMPT_LENGTH = 2500;

  const handleGenerate = useCallback(async () => {
    const trimmedPrompt = prompt.trim();
    if (!trimmedPrompt) {
      setValidationError("Please enter a video description");
      return;
    }
    if (trimmedPrompt.length > MAX_PROMPT_LENGTH) {
      setValidationError(`Description must be less than ${MAX_PROMPT_LENGTH} characters`);
      return;
    }
    setValidationError(null);
    setError(null);
    setResult(null);

    if (creditCtx && !creditCtx.hasEnoughCredits(creditCost)) {
      setShowCreditModal(true);
      return;
    }

    setLoading(true);

    // React 19: Optimistic UI
    startTransition(() => {
      setOptimisticResult({
        success: false,
        task_id: "pending",
        status: "processing",
        credits_used: 0,
      });
    });

    try {
      const payload: Record<string, unknown> = {
        prompt: trimmedPrompt,
        duration,
        aspect_ratio: aspectRatio,
        resolution,
        mode,
        enable_audio: enableAudio,
      };

      if (negativePrompt.trim()) {
        payload.negative_prompt = negativePrompt.trim();
      }
      if (imageUrl.trim()) {
        payload.image_url = imageUrl.trim();
      }
      if (endImageUrl.trim()) {
        payload.end_image_url = endImageUrl.trim();
      }
      if (motionPreset) {
        payload.motion_preset = motionPreset;
      }
      if (cameraPreset) {
        payload.camera_preset = cameraPreset;
      }

      await execute(`${API_BASE}/api/dimension/kling/generate`, payload);
    } finally {
      setLoading(false);
      startTransition(() => {
        setOptimisticResult(null);
      });
    }
  }, [
    prompt,
    negativePrompt,
    duration,
    aspectRatio,
    resolution,
    mode,
    enableAudio,
    imageUrl,
    endImageUrl,
    motionPreset,
    cameraPreset,
    creditCost,
    creditCtx,
    execute,
    setLoading,
    setError,
    setResult,
    startTransition,
    setOptimisticResult,
  ]);

  const displayResult = result || optimisticResult;
  const isOptimistic = !!optimisticResult && !result;

  return (
    <>
      {/* Header */}
      <DimensionPanel.Header
        title="Kling 2.6"
        titleKo="AI Video Generator"
        creditCost={creditCost}
      />

      {/* Sidebar */}
      <DimensionPanel.Sidebar>
        {/* Prompt */}
        <DimensionPanel.Textarea
          label="Video Description"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe your video scene in detail...&#10;&#10;Example: A cinematic shot of waves crashing against rocks at golden hour, with seagulls flying overhead"
          maxLength={MAX_PROMPT_LENGTH}
          showCount
          error={validationError || undefined}
          disabled={combinedLoading}
          rows={5}
        />

        {/* File Upload */}
        <DimensionPanel.FileUpload
          accept={["*"]}
          maxSizeMB={100}
          multiple
          onUpload={setFiles}
          label="참고 이미지 (선택)"
          helperText="스타일 참고 이미지 첨부"
        />

        {/* Duration & Resolution */}
        <div className="grid grid-cols-2 gap-3">
          <DimensionPanel.Select
            label="Duration"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            options={DURATIONS.map((d) => ({
              value: d.value,
              label: d.label,
            }))}
            disabled={combinedLoading}
          />
          <DimensionPanel.Select
            label="Resolution"
            value={resolution}
            onChange={(e) => setResolution(e.target.value)}
            options={RESOLUTIONS}
            disabled={combinedLoading}
          />
        </div>

        {/* Aspect Ratio */}
        <div className="space-y-2">
          <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">
            Aspect Ratio
          </label>
          <div className="grid grid-cols-3 gap-2">
            {ASPECT_RATIOS.map((ar) => (
              <button
                key={ar.value}
                onClick={() => setAspectRatio(ar.value)}
                disabled={combinedLoading}
                className={`py-2 px-3 rounded-lg text-xs font-medium transition-all ${aspectRatio === ar.value
                  ? `${classes.bg} text-white`
                  : "bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-zinc-400 hover:bg-slate-200 dark:hover:bg-white/10"
                  } disabled:opacity-50`}
              >
                {ar.value}
              </button>
            ))}
          </div>
        </div>

        {/* Mode & Audio */}
        <div className="grid grid-cols-2 gap-3">
          <DimensionPanel.Select
            label="Quality Mode"
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            options={MODES.map((m) => ({
              value: m.value,
              label: m.label,
            }))}
            disabled={combinedLoading}
          />
          <div className="space-y-2">
            <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">
              Audio
            </label>
            <button
              onClick={() => setEnableAudio(!enableAudio)}
              disabled={combinedLoading}
              className={`w-full py-2.5 rounded-lg text-xs font-medium transition-all ${enableAudio
                ? `${classes.bg} text-white`
                : "bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-zinc-400"
                } disabled:opacity-50`}
            >
              {enableAudio ? "Enabled" : "Disabled"}
            </button>
          </div>
        </div>

        {/* Advanced Options Toggle */}
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full py-2 text-xs text-slate-500 dark:text-zinc-500 hover:text-slate-700 dark:hover:text-zinc-300 transition-colors flex items-center justify-center gap-1"
        >
          <span>{showAdvanced ? "Hide" : "Show"} Advanced Options</span>
          <svg
            className={`w-3 h-3 transition-transform ${showAdvanced ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {/* Advanced Options */}
        {showAdvanced && (
          <div className="space-y-4 pt-2 border-t border-slate-200 dark:border-white/5">
            {/* Negative Prompt */}
            <DimensionPanel.Textarea
              label="Negative Prompt"
              value={negativePrompt}
              onChange={(e) => setNegativePrompt(e.target.value)}
              placeholder="Elements to avoid..."
              maxLength={500}
              disabled={combinedLoading}
              rows={2}
            />

            {/* Image URLs */}
            <DimensionPanel.Input
              label="Start Image URL (Image-to-Video)"
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              placeholder="https://..."
              disabled={combinedLoading}
            />

            <DimensionPanel.Input
              label="End Image URL (Shot Sequencing)"
              value={endImageUrl}
              onChange={(e) => setEndImageUrl(e.target.value)}
              placeholder="https://..."
              disabled={combinedLoading}
            />

            {/* Motion & Camera Control */}
            <div className="grid grid-cols-2 gap-3">
              <DimensionPanel.Select
                label="Motion Control"
                value={motionPreset}
                onChange={(e) => setMotionPreset(e.target.value)}
                options={MOTION_PRESETS}
                disabled={combinedLoading}
              />
              <DimensionPanel.Select
                label="Camera Control"
                value={cameraPreset}
                onChange={(e) => setCameraPreset(e.target.value)}
                options={CAMERA_PRESETS}
                disabled={combinedLoading}
              />
            </div>
          </div>
        )}

        {/* Generate Button */}
        <DimensionPanel.GenerateButton
          onClick={handleGenerate}
          loading={combinedLoading}
          disabled={!prompt.trim()}
          className="mt-6"
        >
          Generate Video ({creditCost} credits)
        </DimensionPanel.GenerateButton>
      </DimensionPanel.Sidebar>

      {/* Content */}
      <DimensionPanel.Content>
        {/* Loading State */}
        <DimensionPanel.Loading message="Generating video with Kling 2.6... This may take 1-3 minutes." />

        {/* Error State */}
        <DimensionPanel.Error onRetry={retry} />

        {/* Result */}
        {displayResult && displayResult.success && displayResult.video_url && (
          <div
            className={`max-w-4xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10 ${isOptimistic ? "opacity-70" : ""
              }`}
          >
            <DimensionPanel.Result forceShow>
              <div className="space-y-4">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${classes.bg}`} />
                    <span className="text-xs font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest">
                      Generated Video
                    </span>
                    <span className="px-2 py-0.5 text-[10px] rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                      {displayResult.credits_used} credits
                    </span>
                  </div>
                  <button
                    onClick={() => copyToClipboard(displayResult.video_url || "")}
                    className={`p-2 rounded-lg bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-zinc-400 hover:${classes.bgSubtle} hover:${classes.text} transition-all`}
                  >
                    {isCopied ? (
                      <span className="text-green-500 font-bold text-xs">COPIED</span>
                    ) : (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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

                {/* Video Player */}
                <div className="relative rounded-xl overflow-hidden bg-black">
                  <video
                    src={displayResult.video_url}
                    controls
                    className="w-full"
                    poster={displayResult.thumbnail_url}
                  />
                </div>

                {/* Download Button */}
                <a
                  href={displayResult.video_url}
                  download
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg ${classes.bg} text-white text-sm font-medium hover:opacity-90 transition-opacity`}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                    />
                  </svg>
                  Download Video
                </a>
              </div>
            </DimensionPanel.Result>

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
                <span className="text-5xl">🎬</span>
              </div>
            </div>
            <div className="text-center space-y-3">
              <h3 className="text-2xl font-bold text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-b dark:from-white dark:to-white/40 tracking-tight">
                Kling 2.6
              </h3>
              <p className="text-sm text-slate-500 dark:text-zinc-500 max-w-xs mx-auto font-light leading-relaxed">
                Generate high-quality cinematic videos
                <br />
                with <span className={`${classes.text} font-medium`}>motion & camera control</span>
              </p>
              <div className="flex items-center justify-center gap-3 pt-4">
                <span className="px-3 py-1 text-xs rounded-full bg-violet-500/10 text-violet-500">
                  Elements
                </span>
                <span className="px-3 py-1 text-xs rounded-full bg-cyan-500/10 text-cyan-500">
                  Motion Control
                </span>
                <span className="px-3 py-1 text-xs rounded-full bg-emerald-500/10 text-emerald-500">
                  Native Audio
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
        requiredCredits={creditCost}
        currentBalance={creditCtx?.balance ?? 0}
        onRetry={handleGenerate}
      />
    </>
  );
}
