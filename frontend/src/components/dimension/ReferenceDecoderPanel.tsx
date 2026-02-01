"use client";

/**
 * ReferenceDecoderPanel - 레퍼런스 해석기 (4D)
 *
 * 2026 Expert Workflow Hardening:
 * - Style extraction from reference images
 * - Frame-by-frame video analysis
 * - Shot list generation for recreation
 * - Moodboard display
 *
 * Features:
 * - useTransition for non-blocking form submission
 * - useOptimistic for instant UI feedback
 * - Multimodal input (text/image/video)
 * - i18n support
 *
 * @see docs/DIMENSION_APP_AUDIT_REPORT_2026.md
 * @see docs/PANEL_DESIGN_UNITY_SPEC.md
 */

import { useState, useCallback, useTransition, useMemo, useEffect } from "react";
import Image from "next/image";
import { useLanguage } from "@/contexts/LanguageContext";
import { getDemoIPOverride } from "@/lib/demo-ip-overrides";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import { type EvidenceRef } from "./EvidenceDisplay";
import {
  Download,
  FileSearch,
  Image as ImageIcon,
  Video,
  FileText,
  Palette,
  Camera,
  Film,
  Sparkles,
  Copy,
  Check,
} from "lucide-react";

// ============================================================================
// Constants & Types
// ============================================================================

const DIMENSION_CODE = "4d";
const DIMENSION_KEY = "reference-decoder";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";
const MAX_DESCRIPTION_LENGTH = 3000;
const MAX_IMAGE_SIZE = 10 * 1024 * 1024; // 10MB
const MAX_VIDEO_SIZE = 100 * 1024 * 1024; // 100MB

type AnalysisMode = "text" | "style" | "video" | "image";

// Traditional text-based analysis result
interface TextAnalysisResult {
  composition?: string;
  lighting?: string;
  color?: string;
  movement?: string;
  narrative?: string;
  recommendations?: string[];
  evidence_refs?: EvidenceRef[];
  confidence?: number;
}

// Style extraction result (2026 Expert Workflow)
interface StyleExtractionResult {
  success: boolean;
  style_tags: string[];
  style_prompt: string;
  color_palette: string[];
  lighting: string;
  composition: string;
  mood: string;
  camera_angle?: string;
  reference_artists: string[];
  confidence: number;
  evidence_refs: string[];
}

// Video analysis result (2026 Expert Workflow)
interface VideoAnalysisResult {
  success: boolean;
  total_duration: number;
  frame_count: number;
  frames: Array<{
    timestamp: number;
    frame_number: number;
    description: string;
    objects: string[];
    actions: string[];
    camera_movement?: string;
    shot_type?: string;
    emotion?: string;
  }>;
  scenes: Array<{
    start_time: number;
    end_time: number;
    duration: number;
    description: string;
    key_frame_index: number;
  }>;
  style: {
    style_tags: string[];
    style_prompt: string;
    color_palette: string[];
    lighting: string;
    composition: string;
    mood: string;
  };
  suggested_shots: Array<{
    shot_number: number;
    duration_seconds: number;
    description: string;
    camera_setup: string;
    prompt: string;
    reference_frame_index: number;
  }>;
  moodboard_frames: string[];
  confidence: number;
  evidence_refs: string[];
}

// Image analysis result (2026 Expert Workflow)
interface ImageAnalysisResult {
  success: boolean;
  description: string;
  style: {
    style_tags: string[];
    style_prompt: string;
    color_palette: string[];
    lighting: string;
    composition: string;
    mood: string;
  };
  objects: string[];
  composition_analysis: string;
  recreation_prompt: string;
  similar_references: string[];
  evidence_refs: string[];
}

type AnalysisResult =
  | TextAnalysisResult
  | StyleExtractionResult
  | VideoAnalysisResult
  | ImageAnalysisResult;

// ============================================================================
// i18n Helpers
// ============================================================================

const getI18n = (isKo: boolean) => ({
  title: isKo ? "레퍼런스 해석기" : "Reference Decoder",
  modes: {
    text: isKo ? "텍스트 설명" : "Text Description",
    style: isKo ? "스타일 추출" : "Style Extraction",
    video: isKo ? "영상 분석" : "Video Analysis",
    image: isKo ? "이미지 분석" : "Image Analysis",
  },
  modeDescriptions: {
    text: isKo
      ? "영상의 특징을 텍스트로 설명하여 분석"
      : "Analyze by describing video features in text",
    style: isKo
      ? "레퍼런스 이미지에서 재사용 가능한 스타일 추출"
      : "Extract reusable style from reference image",
    video: isKo
      ? "영상을 프레임별로 분석하고 샷 리스트 생성"
      : "Analyze video frame-by-frame and generate shot list",
    image: isKo
      ? "이미지를 분석하고 재현 프롬프트 생성"
      : "Analyze image and generate recreation prompt",
  },
  labels: {
    description: isKo ? "레퍼런스 영상 설명" : "Reference Video Description",
    focusAreas: isKo ? "분석 집중 영역" : "Focus Areas",
    model: isKo ? "AI 모델" : "AI Model",
    uploadImage: isKo ? "이미지 업로드" : "Upload Image",
    uploadVideo: isKo ? "영상 업로드" : "Upload Video",
    analysisDepth: isKo ? "분석 깊이" : "Analysis Depth",
    context: isKo ? "추가 컨텍스트 (선택)" : "Additional Context (Optional)",
  },
  placeholders: {
    description: isKo
      ? "분석하고 싶은 영상의 장면이나 특징을 상세히 설명하세요..."
      : "Describe the scene or features of the video you want to analyze...",
    context: isKo
      ? "이 레퍼런스의 출처나 장르 정보 (예: SF 영화, 뮤직비디오)"
      : "Source or genre info (e.g., sci-fi film, music video)",
  },
  buttons: {
    analyze: isKo ? "분석하기" : "Analyze",
    analyzing: isKo ? "분석 중..." : "Analyzing...",
    extractStyle: isKo ? "스타일 추출" : "Extract Style",
    analyzeVideo: isKo ? "영상 분석" : "Analyze Video",
    analyzeImage: isKo ? "이미지 분석" : "Analyze Image",
    copyPrompt: isKo ? "프롬프트 복사" : "Copy Prompt",
    copied: isKo ? "복사됨!" : "Copied!",
    exportJson: isKo ? "JSON 내보내기" : "Export JSON",
  },
  focusAreas: [
    { value: "composition", label: isKo ? "구도" : "Composition" },
    { value: "lighting", label: isKo ? "조명" : "Lighting" },
    { value: "color", label: isKo ? "색감" : "Color" },
    { value: "movement", label: isKo ? "카메라" : "Camera" },
    { value: "narrative", label: isKo ? "내러티브" : "Narrative" },
    { value: "pacing", label: isKo ? "페이싱" : "Pacing" },
  ],
  depths: [
    { value: "quick", label: isKo ? "빠른 분석" : "Quick" },
    { value: "standard", label: isKo ? "상세 분석" : "Standard" },
    { value: "deep", label: isKo ? "종합 분석" : "Deep" },
  ],
  models: [
    { value: "gemini-3-flash-preview", label: isKo ? "Flash (빠름)" : "Flash (Fast)" },
    { value: "gemini-3-pro-preview", label: isKo ? "Pro (고품질)" : "Pro (High Quality)" },
  ],
  results: {
    styleExtraction: isKo ? "스타일 추출 결과" : "Style Extraction Result",
    styleTags: isKo ? "스타일 태그" : "Style Tags",
    stylePrompt: isKo ? "스타일 프롬프트" : "Style Prompt",
    colorPalette: isKo ? "컬러 팔레트" : "Color Palette",
    referenceArtists: isKo ? "유사 아티스트" : "Reference Artists",
    videoAnalysis: isKo ? "영상 분석 결과" : "Video Analysis Result",
    frameAnalysis: isKo ? "프레임 분석" : "Frame Analysis",
    sceneSegments: isKo ? "장면 구분" : "Scene Segments",
    shotList: isKo ? "샷 리스트" : "Shot List",
    moodboard: isKo ? "무드보드" : "Moodboard",
    imageAnalysis: isKo ? "이미지 분석 결과" : "Image Analysis Result",
    recreationPrompt: isKo ? "재현 프롬프트" : "Recreation Prompt",
    compositionAnalysis: isKo ? "구도 분석" : "Composition Analysis",
    detectedObjects: isKo ? "감지된 오브젝트" : "Detected Objects",
  },
  emptyState: {
    title: isKo ? "분석 대기 중" : "Ready to Analyze",
    description: isKo
      ? "레퍼런스를 업로드하거나 설명을 입력하세요"
      : "Upload a reference or enter a description",
  },
  errors: {
    noDescription: isKo ? "영상 설명을 입력해주세요" : "Please enter video description",
    descriptionTooLong: isKo
      ? `영상 설명은 ${MAX_DESCRIPTION_LENGTH}자 이하로 입력해주세요`
      : `Description must be less than ${MAX_DESCRIPTION_LENGTH} characters`,
    noFocusAreas: isKo
      ? "최소 하나의 분석 영역을 선택해주세요"
      : "Please select at least one focus area",
    noFile: isKo ? "파일을 업로드해주세요" : "Please upload a file",
    imageTooLarge: isKo
      ? `이미지 크기가 ${MAX_IMAGE_SIZE / (1024 * 1024)}MB를 초과합니다`
      : `Image size exceeds ${MAX_IMAGE_SIZE / (1024 * 1024)}MB`,
    videoTooLarge: isKo
      ? `영상 크기가 ${MAX_VIDEO_SIZE / (1024 * 1024)}MB를 초과합니다`
      : `Video size exceeds ${MAX_VIDEO_SIZE / (1024 * 1024)}MB`,
    invalidImageType: isKo
      ? "지원하지 않는 이미지 형식입니다 (JPEG, PNG, WebP 지원)"
      : "Unsupported image format (JPEG, PNG, WebP supported)",
    invalidVideoType: isKo
      ? "지원하지 않는 영상 형식입니다 (MP4, WebM 지원)"
      : "Unsupported video format (MP4, WebM supported)",
  },
});

const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
const ALLOWED_VIDEO_TYPES = ["video/mp4", "video/webm", "video/quicktime"];

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
  const { language } = useLanguage();
  const isKorean = language === "ko";
  const t = useMemo(() => getI18n(isKorean), [isKorean]);

  // Mode state
  const [mode, setMode] = useState<AnalysisMode>("text");

  // Form state
  const [description, setDescription] = useState("");
  const [focusAreas, setFocusAreas] = useState<string[]>([
    "composition",
    "lighting",
    "color",
    "movement",
  ]);
  const [model, setModel] = useState("gemini-3-flash-preview");
  const [analysisDepth, setAnalysisDepth] = useState("standard");
  const [context, setContext] = useState("");
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // File upload state
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);

  // IP reference state (for demo workflow integration)
  const [ipVideoUrl, setIpVideoUrl] = useState<string | null>(null);
  const [ipSlug, setIpSlug] = useState<string | null>(null);
  const [isLoadingIpVideo, setIsLoadingIpVideo] = useState(false);

  // URL parameter handling for workflow integration
  useEffect(() => {
    if (typeof window === "undefined") return;

    const params = new URLSearchParams(window.location.search);
    const ipParam = params.get("ip");
    const promptParam = params.get("prompt");

    if (ipParam) {
      setIpSlug(ipParam);
      const ipData = getDemoIPOverride(ipParam);
      if (ipData?.previewVideoUrl) {
        setIpVideoUrl(ipData.previewVideoUrl);
        // Auto-select video mode when IP has video reference
        setMode("video");
      }
      // Pre-fill context with IP info
      const ipContext = isKorean
        ? `IP: ${ipData?.titleKo || ipParam} - ${ipData?.descKo || ""}`
        : `IP: ${ipData?.titleEn || ipParam} - ${ipData?.descEn || ""}`;
      setContext(ipContext);
    }

    if (promptParam) {
      setDescription(decodeURIComponent(promptParam));
    }
  }, [isKorean]);

  // Auto-load IP video when switching to video mode
  useEffect(() => {
    if (mode !== "video" || !ipVideoUrl || uploadedFile) return;

    const loadIpVideo = async () => {
      setIsLoadingIpVideo(true);
      try {
        const response = await fetch(ipVideoUrl);
        if (!response.ok) throw new Error("Failed to fetch IP video");

        const blob = await response.blob();
        const fileName = ipVideoUrl.split("/").pop() || "ip-reference.mp4";
        // Determine correct MIME type from Content-Type header or file extension
        const contentType = response.headers.get("Content-Type");
        const mimeType = contentType?.startsWith("video/")
          ? contentType
          : fileName.endsWith(".mp4") ? "video/mp4"
          : fileName.endsWith(".webm") ? "video/webm"
          : "video/mp4";
        const file = new File([blob], fileName, { type: mimeType });

        setUploadedFile(file);
        setValidationError(null);
      } catch (err) {
        console.error("Failed to load IP video:", err);
        // Silently fail - user can still upload manually
      } finally {
        setIsLoadingIpVideo(false);
      }
    };

    void loadIpVideo();
  }, [mode, ipVideoUrl, uploadedFile]);

  // React 19: useTransition for non-blocking form submission
  const [isTransitionPending, startTransition] = useTransition();

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
  const { isLoading, error, execute, retry, canRetry } = useAsyncOperation<AnalysisResult>({
    onSuccess: (data) => {
      setAnalysisResult(data);
      setResult(data);
      if (!byokKey && creditCtx) {
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

  const combinedLoading = isLoading || isTransitionPending;

  // Sync loading state to context
  const wrappedExecute = useCallback(
    async (url: string, payload: object | FormData, headers?: Record<string, string>) => {
      setLoading(true);
      try {
        return await execute(url, payload, headers);
      } finally {
        setLoading(false);
      }
    },
    [execute, setLoading]
  );

  // File upload handler
  const handleFileUpload = useCallback(
    (file: File | null) => {
      if (!file) {
        setUploadedFile(null);
        setFilePreview(null);
        return;
      }

      // Validate based on mode
      if (mode === "style" || mode === "image") {
        if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
          setValidationError(t.errors.invalidImageType);
          return;
        }
        if (file.size > MAX_IMAGE_SIZE) {
          setValidationError(t.errors.imageTooLarge);
          return;
        }
      } else if (mode === "video") {
        if (!ALLOWED_VIDEO_TYPES.includes(file.type)) {
          setValidationError(t.errors.invalidVideoType);
          return;
        }
        if (file.size > MAX_VIDEO_SIZE) {
          setValidationError(t.errors.videoTooLarge);
          return;
        }
      }

      setValidationError(null);
      setUploadedFile(file);

      // Create preview for images
      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = (e) => setFilePreview(e.target?.result as string);
        reader.readAsDataURL(file);
      } else {
        setFilePreview(null);
      }
    },
    [mode, t.errors]
  );

  // Mode change handler
  const handleModeChange = useCallback((newMode: AnalysisMode) => {
    setMode(newMode);
    setUploadedFile(null);
    setFilePreview(null);
    setAnalysisResult(null);
    setValidationError(null);
  }, []);

  const toggleFocusArea = (area: string) => {
    setFocusAreas((prev) =>
      prev.includes(area) ? prev.filter((a) => a !== area) : [...prev, area]
    );
  };

  // Text analysis handler (existing)
  const handleTextAnalysis = useCallback(async () => {
    const trimmedDescription = description.trim();
    if (!trimmedDescription) {
      setValidationError(t.errors.noDescription);
      return;
    }
    if (trimmedDescription.length > MAX_DESCRIPTION_LENGTH) {
      setValidationError(t.errors.descriptionTooLong);
      return;
    }
    if (focusAreas.length === 0) {
      setValidationError(t.errors.noFocusAreas);
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
  }, [description, focusAreas, model, byokKey, creditCtx, wrappedExecute, CREDIT_COST, t.errors]);

  // Style extraction handler (2026 Expert Workflow)
  const handleStyleExtraction = useCallback(async () => {
    if (!uploadedFile) {
      setValidationError(t.errors.noFile);
      return;
    }
    setValidationError(null);

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
      setShowCreditModal(true);
      return;
    }

    const formData = new FormData();
    formData.append("file", uploadedFile);

    const url = context
      ? `${API_BASE}/api/dimension/4d/extract-style?context=${encodeURIComponent(context)}`
      : `${API_BASE}/api/dimension/4d/extract-style`;

    await wrappedExecute(url, formData, getBYOKHeaders(byokKey));
  }, [uploadedFile, context, byokKey, creditCtx, wrappedExecute, CREDIT_COST, t.errors]);

  // Video analysis handler (2026 Expert Workflow)
  const handleVideoAnalysis = useCallback(async () => {
    if (!uploadedFile) {
      setValidationError(t.errors.noFile);
      return;
    }
    setValidationError(null);

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
      setShowCreditModal(true);
      return;
    }

    const formData = new FormData();
    formData.append("file", uploadedFile);

    await wrappedExecute(
      `${API_BASE}/api/dimension/4d/analyze-video?analysis_depth=${encodeURIComponent(analysisDepth)}`,
      formData,
      getBYOKHeaders(byokKey)
    );
  }, [uploadedFile, analysisDepth, byokKey, creditCtx, wrappedExecute, CREDIT_COST, t.errors]);

  // Image analysis handler (2026 Expert Workflow)
  const handleImageAnalysis = useCallback(async () => {
    if (!uploadedFile) {
      setValidationError(t.errors.noFile);
      return;
    }
    setValidationError(null);

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
      setShowCreditModal(true);
      return;
    }

    const formData = new FormData();
    formData.append("file", uploadedFile);

    await wrappedExecute(
      `${API_BASE}/api/dimension/4d/analyze-image`,
      formData,
      getBYOKHeaders(byokKey)
    );
  }, [uploadedFile, byokKey, creditCtx, wrappedExecute, CREDIT_COST, t.errors]);

  // Main action handler based on mode
  const handleAnalyze = useCallback(() => {
    startTransition(() => {
      switch (mode) {
        case "text":
          void handleTextAnalysis();
          break;
        case "style":
          void handleStyleExtraction();
          break;
        case "video":
          void handleVideoAnalysis();
          break;
        case "image":
          void handleImageAnalysis();
          break;
      }
    });
  }, [mode, handleTextAnalysis, handleStyleExtraction, handleVideoAnalysis, handleImageAnalysis]);

  // Export result as JSON
  const handleExportJson = useCallback(() => {
    if (!analysisResult) return;
    exportJSON(analysisResult, `reference-analysis-${mode}-${Date.now()}.json`);
  }, [analysisResult, exportJSON, mode]);

  const displayError = validationError || error;
  const canSubmit =
    !isLoadingIpVideo &&
    (mode === "text"
      ? description.trim() && focusAreas.length > 0
      : !!uploadedFile);

  return (
    <>
      <DimensionPanel.Header title={t.title} creditCost={CREDIT_COST} />

      <DimensionPanel.Sidebar>
        {/* Mode Selector */}
        <div className="space-y-2">
          <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">
            {isKorean ? "분석 모드" : "Analysis Mode"}
          </label>
          <div className="grid grid-cols-2 gap-2">
            {(["text", "style", "video", "image"] as AnalysisMode[]).map((m) => {
              const icons = {
                text: FileText,
                style: Palette,
                video: Video,
                image: ImageIcon,
              };
              const Icon = icons[m];
              const isActive = mode === m;
              return (
                <button
                  key={m}
                  onClick={() => handleModeChange(m)}
                  className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? `${classes.bgSubtle} border ${classes.border} ${classes.text}`
                      : "bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 text-slate-600 dark:text-zinc-400 hover:bg-slate-100 dark:hover:bg-white/10"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{t.modes[m]}</span>
                </button>
              );
            })}
          </div>
          <p className="text-[10px] text-slate-400 dark:text-zinc-600 ml-1">
            {t.modeDescriptions[mode]}
          </p>
        </div>

        {/* IP Reference Preview (from workflow integration) */}
        {ipVideoUrl && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Film className="w-4 h-4 text-violet-500" />
              <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest">
                {isKorean ? "IP 레퍼런스" : "IP Reference"}
              </label>
              {ipSlug && (
                <span className="px-2 py-0.5 text-[9px] font-medium bg-violet-500/10 text-violet-600 dark:text-violet-400 rounded-full">
                  {ipSlug}
                </span>
              )}
            </div>
            <div className="relative rounded-xl overflow-hidden border border-slate-200 dark:border-white/10 bg-black/5">
              <video
                src={ipVideoUrl}
                controls
                className="w-full max-h-48 object-contain"
                preload="metadata"
              />
            </div>
            <p className="text-[10px] text-slate-400 dark:text-zinc-600 ml-1">
              {isKorean
                ? "이 레퍼런스 영상을 텍스트로 설명하여 분석할 수 있습니다"
                : "You can describe this reference video in text for analysis"}
            </p>
          </div>
        )}

        {/* Text Mode Inputs */}
        {mode === "text" && (
          <>
            <div className="space-y-2 group">
              <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">
                {t.labels.description}
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={t.placeholders.description}
                className="w-full h-32 px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-white/20 focus:outline-none focus:border-[var(--stitch-primary)] focus:ring-4 focus:ring-[var(--stitch-primary)]/10 transition-all resize-none text-sm font-light leading-relaxed"
              />
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">
                {t.labels.focusAreas}
              </label>
              <div className="flex flex-wrap gap-2">
                {t.focusAreas.map((area) => (
                  <button
                    key={area.value}
                    onClick={() => toggleFocusArea(area.value)}
                    className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-all ${
                      focusAreas.includes(area.value)
                        ? `${classes.bgSubtle} ${classes.border} ${classes.text}`
                        : "bg-white dark:bg-white/5 border-slate-200 dark:border-white/5 text-slate-500 dark:text-zinc-400 hover:bg-slate-100 dark:hover:bg-white/10"
                    }`}
                  >
                    {area.label}
                  </button>
                ))}
              </div>
            </div>

            <DimensionPanel.Select
              label={t.labels.model}
              value={model}
              onChange={(e) => setModel(e.target.value)}
              options={t.models}
            />
          </>
        )}

        {/* Style/Image Mode Inputs */}
        {(mode === "style" || mode === "image") && (
          <>
            <FileUploadArea
              accept={ALLOWED_IMAGE_TYPES.join(",")}
              file={uploadedFile}
              preview={filePreview}
              onUpload={handleFileUpload}
              label={t.labels.uploadImage}
              icon={<ImageIcon className="w-8 h-8" />}
              helperText={isKorean ? "JPEG, PNG, WebP (최대 10MB)" : "JPEG, PNG, WebP (max 10MB)"}
            />
            {mode === "style" && (
              <DimensionPanel.Input
                label={t.labels.context}
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder={t.placeholders.context}
              />
            )}
          </>
        )}

        {/* Video Mode Inputs */}
        {mode === "video" && (
          <>
            {/* IP Video Auto-loaded Banner */}
            {ipVideoUrl && uploadedFile && !isLoadingIpVideo && (
              <div className="p-3 rounded-xl bg-violet-500/10 border border-violet-500/20">
                <div className="flex items-center gap-2 mb-2">
                  <Film className="w-4 h-4 text-violet-500" />
                  <span className="text-xs font-medium text-violet-600 dark:text-violet-400">
                    {isKorean ? "IP 레퍼런스 영상 로드됨" : "IP Reference Video Loaded"}
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 dark:text-zinc-500">
                  {uploadedFile.name} ({(uploadedFile.size / (1024 * 1024)).toFixed(1)}MB)
                </p>
              </div>
            )}

            {/* Loading IP Video */}
            {isLoadingIpVideo && (
              <div className="p-4 rounded-xl bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10">
                <div className="flex items-center gap-3">
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-violet-500 border-t-transparent" />
                  <span className="text-sm text-slate-600 dark:text-zinc-400">
                    {isKorean ? "IP 레퍼런스 영상 로딩 중..." : "Loading IP reference video..."}
                  </span>
                </div>
              </div>
            )}

            {/* File Upload (hidden when IP video is loaded, show for manual override) */}
            {(!ipVideoUrl || !uploadedFile) && !isLoadingIpVideo && (
              <FileUploadArea
                accept={ALLOWED_VIDEO_TYPES.join(",")}
                file={uploadedFile}
                preview={null}
                onUpload={handleFileUpload}
                label={t.labels.uploadVideo}
                icon={<Video className="w-8 h-8" />}
                helperText={isKorean ? "MP4, WebM (최대 100MB)" : "MP4, WebM (max 100MB)"}
              />
            )}

            <DimensionPanel.Select
              label={t.labels.analysisDepth}
              value={analysisDepth}
              onChange={(e) => setAnalysisDepth(e.target.value)}
              options={t.depths}
            />
          </>
        )}

        {/* Generate Button */}
        <DimensionPanel.GenerateButton
          onClick={handleAnalyze}
          disabled={!canSubmit}
          loading={combinedLoading}
          creditCost={CREDIT_COST}
          icon={<FileSearch className="w-5 h-5" />}
          loadingText={t.buttons.analyzing}
        >
          {mode === "text" && t.buttons.analyze}
          {mode === "style" && t.buttons.extractStyle}
          {mode === "video" && t.buttons.analyzeVideo}
          {mode === "image" && t.buttons.analyzeImage}
        </DimensionPanel.GenerateButton>

        {validationError && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs animate-in fade-in">
            {validationError}
          </div>
        )}
      </DimensionPanel.Sidebar>

      <DimensionPanel.Content>
        <DimensionPanel.Loading message={t.buttons.analyzing} />

        {displayError && !isLoading && (
          <DimensionPanel.Error
            error={displayError}
            onRetry={canRetry ? () => void retry() : undefined}
          />
        )}

        {/* Result Display based on mode */}
        {analysisResult && !isLoading && (
          <>
            {mode === "text" && (
              <TextAnalysisDisplay
                result={analysisResult as TextAnalysisResult}
                onExport={handleExportJson}
                t={t}
                themeColor={token.themeColor}
              />
            )}
            {mode === "style" && (
              <StyleExtractionDisplay
                result={analysisResult as StyleExtractionResult}
                onExport={handleExportJson}
                t={t}
                themeColor={token.themeColor}
              />
            )}
            {mode === "video" && (
              <VideoAnalysisDisplay
                result={analysisResult as VideoAnalysisResult}
                onExport={handleExportJson}
                t={t}
                themeColor={token.themeColor}
              />
            )}
            {mode === "image" && (
              <ImageAnalysisDisplay
                result={analysisResult as ImageAnalysisResult}
                onExport={handleExportJson}
                t={t}
                themeColor={token.themeColor}
              />
            )}
          </>
        )}

        {!analysisResult && !isLoading && !displayError && <EmptyState t={t} />}

        <DimensionPanel.Evidence
          refs={
            analysisResult && "evidence_refs" in analysisResult
              ? (analysisResult.evidence_refs as EvidenceRef[])
              : undefined
          }
        />

        <DimensionPanel.NextNav currentDimension={DIMENSION_KEY} />
      </DimensionPanel.Content>

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
// File Upload Area Component
// ============================================================================

function FileUploadArea({
  accept,
  file,
  preview,
  onUpload,
  label,
  icon,
  helperText,
}: {
  accept: string;
  file: File | null;
  preview: string | null;
  onUpload: (file: File | null) => void;
  label: string;
  icon: React.ReactNode;
  helperText: string;
}) {
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) onUpload(droppedFile);
    },
    [onUpload]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile) onUpload(selectedFile);
    },
    [onUpload]
  );

  return (
    <div className="space-y-2">
      <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">
        {label}
      </label>
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="relative border-2 border-dashed border-slate-200 dark:border-white/10 rounded-xl p-6 text-center hover:border-amber-500/50 dark:hover:border-amber-400/30 transition-colors cursor-pointer group"
      >
        <input
          type="file"
          accept={accept}
          onChange={handleChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        {file ? (
          <div className="space-y-2">
            {preview ? (
              <div className="relative h-32 w-full">
                <Image
                  src={preview}
                  alt="Preview"
                  fill
                  sizes="(max-width: 768px) 100vw, 50vw"
                  className="object-cover rounded-lg"
                />
              </div>
            ) : (
              <div className="flex items-center justify-center h-20">
                <Video className="w-10 h-10 text-amber-500" />
              </div>
            )}
            <p className="text-sm text-slate-600 dark:text-zinc-300 truncate">
              {file.name}
            </p>
            <p className="text-xs text-slate-400 dark:text-zinc-500">
              {(file.size / (1024 * 1024)).toFixed(2)} MB
            </p>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onUpload(null);
              }}
              className="text-xs text-red-400 hover:text-red-300"
            >
              Remove
            </button>
          </div>
        ) : (
          <div className="space-y-2 text-slate-400 dark:text-zinc-500 group-hover:text-amber-500 dark:group-hover:text-amber-400 transition-colors">
            {icon}
            <p className="text-sm font-medium">
              {helperText}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Result Display Components
// ============================================================================

function TextAnalysisDisplay({
  result,
  onExport,
  t,
  themeColor,
}: {
  result: TextAnalysisResult;
  onExport: () => void;
  t: ReturnType<typeof getI18n>;
  themeColor: string;
}) {
  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in pb-20">
      <div className="flex items-center justify-between px-1">
        <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
          Analysis Report
        </h3>
        <button
          onClick={onExport}
          className="px-3 py-1.5 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 text-slate-600 dark:text-white text-xs rounded-lg hover:bg-slate-100 dark:hover:bg-white/10 flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          {t.buttons.exportJson}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Object.entries(result).map(([key, value]) => {
          // Skip non-string fields (objects, arrays, etc.)
          if (["recommendations", "evidence_refs", "confidence"].includes(key)) return null;
          if (typeof value !== "string" || !value) return null;
          const title = t.focusAreas.find((f) => f.value === key)?.label || key;
          return (
            <div key={key} className="p-6 bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl">
              <h4 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase mb-2">
                {title}
              </h4>
              <p className="text-sm text-slate-700 dark:text-zinc-200 leading-relaxed">
                {value}
              </p>
            </div>
          );
        })}
      </div>

      {result.recommendations && result.recommendations.length > 0 && (
        <div className="p-6 bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl">
          <h4 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase mb-3">
            Key Recommendations
          </h4>
          <ul className="space-y-2">
            {result.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-slate-700 dark:text-zinc-200">
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[var(--stitch-primary)]" />
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function StyleExtractionDisplay({
  result,
  onExport,
  t,
  themeColor,
}: {
  result: StyleExtractionResult;
  onExport: () => void;
  t: ReturnType<typeof getI18n>;
  themeColor: string;
}) {
  const [copied, setCopied] = useState(false);

  const copyPrompt = useCallback(() => {
    navigator.clipboard.writeText(result.style_prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [result.style_prompt]);

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in pb-20">
      <div className="flex items-center justify-between px-1">
        <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[var(--stitch-primary)]" />
          {t.results.styleExtraction}
        </h3>
        <button onClick={onExport} className="px-3 py-1.5 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 text-xs rounded-lg flex items-center gap-2">
          <Download className="w-4 h-4" />
          {t.buttons.exportJson}
        </button>
      </div>

      {/* Style Tags */}
      <div className="p-6 bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl">
        <h4 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase mb-3">
          {t.results.styleTags}
        </h4>
        <div className="flex flex-wrap gap-2">
          {result.style_tags.map((tag, idx) => (
            <span
              key={idx}
              className="px-3 py-1 bg-[var(--stitch-primary)]/10 text-[var(--stitch-primary)] text-sm rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* Style Prompt */}
      <div className="p-6 bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase">
            {t.results.stylePrompt}
          </h4>
          <button
            onClick={copyPrompt}
            className={`px-3 py-1 text-xs rounded-lg flex items-center gap-1 transition-colors ${
              copied
                ? "bg-green-500/20 text-green-600"
                : "bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-zinc-400 hover:bg-slate-200 dark:hover:bg-white/10"
            }`}
          >
            {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
            {copied ? t.buttons.copied : t.buttons.copyPrompt}
          </button>
        </div>
        <p className="text-sm text-slate-700 dark:text-zinc-200 leading-relaxed font-mono bg-slate-50 dark:bg-white/5 p-4 rounded-lg">
          {result.style_prompt}
        </p>
      </div>

      {/* Color Palette */}
      <div className="p-6 bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl">
        <h4 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase mb-3">
          {t.results.colorPalette}
        </h4>
        <div className="flex gap-2">
          {result.color_palette.map((color, idx) => (
            <div key={idx} className="flex flex-col items-center gap-1">
              <div
                className="w-12 h-12 rounded-lg shadow-md border border-white/20"
                style={{ backgroundColor: color }}
              />
              <span className="text-[10px] text-slate-500 dark:text-zinc-500 font-mono">
                {color}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Additional Info */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Lighting", value: result.lighting },
          { label: "Composition", value: result.composition },
          { label: "Mood", value: result.mood },
          { label: "Camera", value: result.camera_angle || "N/A" },
        ].map(({ label, value }) => (
          <div key={label} className="p-4 bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl">
            <h4 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase mb-1">
              {label}
            </h4>
            <p className="text-sm text-slate-700 dark:text-zinc-200 capitalize">{value}</p>
          </div>
        ))}
      </div>

      {/* Reference Artists */}
      {result.reference_artists.length > 0 && (
        <div className="p-6 bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl">
          <h4 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase mb-3">
            {t.results.referenceArtists}
          </h4>
          <div className="flex flex-wrap gap-2">
            {result.reference_artists.map((artist, idx) => (
              <span
                key={idx}
                className="px-3 py-1 bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-zinc-300 text-sm rounded-full"
              >
                {artist}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function VideoAnalysisDisplay({
  result,
  onExport,
  t,
  themeColor,
}: {
  result: VideoAnalysisResult;
  onExport: () => void;
  t: ReturnType<typeof getI18n>;
  themeColor: string;
}) {
  const [activeTab, setActiveTab] = useState<"frames" | "shots" | "moodboard">("shots");

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in pb-20">
      <div className="flex items-center justify-between px-1">
        <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
          <Film className="w-4 h-4 text-[var(--stitch-primary)]" />
          {t.results.videoAnalysis}
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 dark:text-zinc-500">
            {result.frame_count} frames • {result.total_duration.toFixed(1)}s
          </span>
          <button onClick={onExport} className="px-3 py-1.5 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 text-xs rounded-lg flex items-center gap-2">
            <Download className="w-4 h-4" />
            {t.buttons.exportJson}
          </button>
        </div>
      </div>

      {/* Style Summary */}
      <div className="p-6 bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl">
        <h4 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase mb-3">
          Extracted Style
        </h4>
        <div className="flex flex-wrap gap-2 mb-4">
          {result.style.style_tags.map((tag, idx) => (
            <span key={idx} className="px-3 py-1 bg-[var(--stitch-primary)]/10 text-[var(--stitch-primary)] text-sm rounded-full">
              {tag}
            </span>
          ))}
        </div>
        <p className="text-sm text-slate-600 dark:text-zinc-300 font-mono bg-slate-50 dark:bg-white/5 p-3 rounded-lg">
          {result.style.style_prompt}
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-slate-200 dark:border-white/10 pb-2">
        {[
          { key: "shots", label: t.results.shotList, icon: Camera },
          { key: "frames", label: t.results.frameAnalysis, icon: Film },
          { key: "moodboard", label: t.results.moodboard, icon: ImageIcon },
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key as typeof activeTab)}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg flex items-center gap-2 transition-colors ${
              activeTab === key
                ? "text-[var(--stitch-primary)] border-b-2 border-[var(--stitch-primary)]"
                : "text-slate-500 dark:text-zinc-500 hover:text-slate-700 dark:hover:text-zinc-300"
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Shot List */}
      {activeTab === "shots" && (
        <div className="space-y-4">
          {result.suggested_shots.map((shot) => (
            <ShotCard key={shot.shot_number} shot={shot} themeColor={themeColor} />
          ))}
        </div>
      )}

      {/* Frame Analysis */}
      {activeTab === "frames" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {result.frames.slice(0, 12).map((frame, idx) => (
            <div
              key={idx}
              className="p-4 bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-[var(--stitch-primary)]">
                  {frame.timestamp.toFixed(1)}s
                </span>
                {frame.shot_type && (
                  <span className="text-[10px] px-2 py-0.5 bg-slate-100 dark:bg-white/5 rounded-full">
                    {frame.shot_type}
                  </span>
                )}
              </div>
              <p className="text-sm text-slate-700 dark:text-zinc-200 mb-2">
                {frame.description}
              </p>
              {frame.camera_movement && (
                <p className="text-xs text-slate-500 dark:text-zinc-500">
                  📷 {frame.camera_movement}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Moodboard */}
      {activeTab === "moodboard" && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {result.moodboard_frames.map((frame, idx) => (
            <div
              key={idx}
              className="relative aspect-video rounded-xl overflow-hidden border border-slate-200 dark:border-white/10"
            >
              <Image
                src={`data:image/jpeg;base64,${frame}`}
                alt={`Moodboard frame ${idx + 1}`}
                fill
                sizes="(max-width: 768px) 50vw, 20vw"
                className="object-cover"
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ShotCard({
  shot,
  themeColor,
}: {
  shot: VideoAnalysisResult["suggested_shots"][0];
  themeColor: string;
}) {
  const [copied, setCopied] = useState(false);

  const copyPrompt = useCallback(() => {
    navigator.clipboard.writeText(shot.prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [shot.prompt]);

  return (
    <div className="p-6 bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="w-8 h-8 flex items-center justify-center rounded-full bg-[var(--stitch-primary)]/20 text-[var(--stitch-primary)] font-bold text-sm">
            {shot.shot_number}
          </span>
          <div>
            <h5 className="text-sm font-medium text-slate-800 dark:text-zinc-100">
              {shot.description}
            </h5>
            <p className="text-xs text-slate-500 dark:text-zinc-500">
              {shot.duration_seconds}s • {shot.camera_setup}
            </p>
          </div>
        </div>
        <button
          onClick={copyPrompt}
          className={`px-3 py-1 text-xs rounded-lg flex items-center gap-1 transition-colors ${
            copied
              ? "bg-green-500/20 text-green-600"
              : "bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-zinc-400"
          }`}
        >
          {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <div className="bg-slate-50 dark:bg-white/5 p-3 rounded-lg">
        <p className="text-xs text-slate-600 dark:text-zinc-300 font-mono leading-relaxed">
          {shot.prompt}
        </p>
      </div>
    </div>
  );
}

function ImageAnalysisDisplay({
  result,
  onExport,
  t,
  themeColor,
}: {
  result: ImageAnalysisResult;
  onExport: () => void;
  t: ReturnType<typeof getI18n>;
  themeColor: string;
}) {
  const [copied, setCopied] = useState(false);

  const copyPrompt = useCallback(() => {
    navigator.clipboard.writeText(result.recreation_prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [result.recreation_prompt]);

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in pb-20">
      <div className="flex items-center justify-between px-1">
        <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
          <ImageIcon className="w-4 h-4 text-[var(--stitch-primary)]" />
          {t.results.imageAnalysis}
        </h3>
        <button onClick={onExport} className="px-3 py-1.5 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 text-xs rounded-lg flex items-center gap-2">
          <Download className="w-4 h-4" />
          {t.buttons.exportJson}
        </button>
      </div>

      {/* Description */}
      <div className="p-6 bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl">
        <h4 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase mb-3">
          Description
        </h4>
        <p className="text-sm text-slate-700 dark:text-zinc-200 leading-relaxed">
          {result.description}
        </p>
      </div>

      {/* Recreation Prompt */}
      <div className="p-6 bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase">
            {t.results.recreationPrompt}
          </h4>
          <button
            onClick={copyPrompt}
            className={`px-3 py-1 text-xs rounded-lg flex items-center gap-1 transition-colors ${
              copied
                ? "bg-green-500/20 text-green-600"
                : "bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-zinc-400"
            }`}
          >
            {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
            {copied ? t.buttons.copied : t.buttons.copyPrompt}
          </button>
        </div>
        <p className="text-sm text-slate-700 dark:text-zinc-200 leading-relaxed font-mono bg-slate-50 dark:bg-white/5 p-4 rounded-lg">
          {result.recreation_prompt}
        </p>
      </div>

      {/* Style Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl">
          <h4 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase mb-3">
            {t.results.styleTags}
          </h4>
          <div className="flex flex-wrap gap-2">
            {result.style.style_tags.map((tag, idx) => (
              <span key={idx} className="px-3 py-1 bg-[var(--stitch-primary)]/10 text-[var(--stitch-primary)] text-sm rounded-full">
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div className="p-6 bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl">
          <h4 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase mb-3">
            {t.results.colorPalette}
          </h4>
          <div className="flex gap-2">
            {result.style.color_palette.map((color, idx) => (
              <div
                key={idx}
                className="w-8 h-8 rounded-lg shadow border border-white/20"
                style={{ backgroundColor: color }}
                title={color}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Composition & Objects */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl">
          <h4 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase mb-3">
            {t.results.compositionAnalysis}
          </h4>
          <p className="text-sm text-slate-700 dark:text-zinc-200 leading-relaxed">
            {result.composition_analysis}
          </p>
        </div>

        <div className="p-6 bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl">
          <h4 className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase mb-3">
            {t.results.detectedObjects}
          </h4>
          <div className="flex flex-wrap gap-2">
            {result.objects.map((obj, idx) => (
              <span key={idx} className="px-2 py-1 bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-zinc-400 text-xs rounded">
                {obj}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function EmptyState({ t }: { t: ReturnType<typeof getI18n> }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-8 animate-in fade-in">
      <div className="relative group">
        <div className="absolute inset-0 bg-amber-500/20 blur-[80px] rounded-full" />
        <div className="w-32 h-32 rounded-[2rem] bg-white/[0.02] border border-white/10 flex items-center justify-center backdrop-blur-md relative">
          <FileSearch className="w-12 h-12 text-white/20 group-hover:text-amber-400 transition-colors" />
        </div>
      </div>
      <div className="text-center space-y-3">
        <h3 className="text-2xl font-bold text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-b dark:from-white dark:to-white/40">
          {t.emptyState.title}
        </h3>
        <p className="text-sm text-slate-500 dark:text-zinc-500 max-w-xs mx-auto">
          {t.emptyState.description}
        </p>
      </div>
    </div>
  );
}
