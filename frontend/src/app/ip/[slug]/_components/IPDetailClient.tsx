"use client";

import React, { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Clock,
  Coins,
  Sparkles,
  AlertTriangle,
  Ban,
  ChevronRight,
  BookOpen,
  Palette,
  Brain,
  GitBranch,
  Image,
  Users,
  Wand2,
  Globe,
  Clapperboard,
  Video,
  Zap,
  Layers,
  Heart,
  Music,
  Eye,
  ArrowRight,
  CheckCircle2,
  Volume2,
  VolumeX,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";
import { LicenseStatusInfo } from "@/components/ip/LicenseStatusBadge";
import GenerationProgress from "./GenerationProgress";
import { EvidenceCard } from "@/components/ui/EvidenceCard";
import { ToolRecommendationCard } from "@/components/ui/ToolRecommendationCard";
import { WorkflowPreviewModal, type WorkflowData } from "@/components/WorkflowPreviewModal";
import { useToolRecommendations } from "@/hooks/useToolRecommendations";
import {
  getDemoIPOverride,
  getDemoIPData,
  isDemoIP,
  resolveVideoUrl,
  type DemoWorkflow,
  type ContentType,
} from "@/lib/demo-ip-overrides";
import {
  saveWorkflowState,
  buildStepUrl,
  type WorkflowStep as WorkflowStateStep,
} from "@/lib/workflow-state";

// =============================================================================
// Types (exported for server component)
// =============================================================================

export interface PresetItem {
  id: string;
  name_ko: string;
  name_en: string;
  description_ko: string | null;
  description_en: string | null;
  thumbnail_url: string | null;
  preset_type: string;
  estimated_credits: number;
  estimated_duration_seconds: number;
  is_featured: boolean;
}

export interface IPDetail {
  id: string;
  slug: string;
  name_ko: string;
  name_en: string;
  description_ko: string | null;
  description_en: string | null;
  thumbnail_url: string | null;
  banner_url: string | null;
  preview_video_url?: string | null; // 비디오 URL (실제 데이터용)
  genre: string[];
  tags: string[];
  worldbuilding: Record<string, unknown>;
  license_status: "allowed" | "restricted" | "prohibited";
  preset_count: number;
  generation_count: number;
  presets: PresetItem[];
}

export interface IPRights {
  license_status: "allowed" | "restricted" | "prohibited";
  territory: string[];
  blocked_territory: string[];
  scope: string;
  commercial_ok: boolean;
  expiry: string | null;
}

// =============================================================================
// Props
// =============================================================================

export interface IPDetailClientProps {
  slug: string;
  /** Pre-fetched IP detail from server (Phase 6 ISR) */
  initialIP?: IPDetail | null;
  /** Pre-fetched IP rights from server (Phase 6 ISR) */
  initialRights?: IPRights | null;
}

// =============================================================================
// Component
// =============================================================================

export default function IPDetailClient({
  slug,
  initialIP,
  initialRights,
}: IPDetailClientProps) {
  const router = useRouter();
  const { language, t } = useLanguage();

  // State - use initial data from server if provided (Phase 6 ISR)
  const [ip, setIP] = useState<IPDetail | null>(initialIP || null);
  const [rights, setRights] = useState<IPRights | null>(initialRights || null);
  const [loading, setLoading] = useState(!initialIP); // Skip loading if server data provided
  const [error, setError] = useState<string | null>(null);

  // Generation state
  const [selectedPreset, setSelectedPreset] = useState<PresetItem | null>(null);
  const [userPrompt, setUserPrompt] = useState("");
  const [showLicenseWarning, setShowLicenseWarning] = useState(false);
  const [licenseAccepted, setLicenseAccepted] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generationId, setGenerationId] = useState<string | null>(null);
  const [showRecommendations, setShowRecommendations] = useState(true);
  const [traceIdCopied, setTraceIdCopied] = useState(false);
  const [showRecommendationWhy, setShowRecommendationWhy] = useState(false);
  const [showWorkflowModal, setShowWorkflowModal] = useState(false);
  const [workflowData, setWorkflowData] = useState<WorkflowData | null>(null);

  // Video player state
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isMuted, setIsMuted] = useState(true);

  // Sync muted state with video element
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.muted = isMuted;
    }
  }, [isMuted]);

  // Mute toggle handler
  const handleMuteToggle = useCallback(() => {
    setIsMuted((prev) => !prev);
  }, []);

  // Tool recommendations (Phase 2.5)
  const {
    recommendations,
    response: recResponse,
    isLoading: recLoading,
    error: recError,
    totalCredits,
    workflowSuggested,
    ipContextUsed,
    traceId,
    fetchByIPSlug,
    fetchRecommendations,
  } = useToolRecommendations();

  const handleRetryRecommendations = useCallback(() => {
    if (ip && selectedPreset) {
      fetchRecommendations({
        ip_id: ip.id,
        preset_id: selectedPreset.id,
        max_results: 3,
      });
      return;
    }
    if (slug) {
      fetchByIPSlug(slug);
    }
  }, [ip, selectedPreset, slug, fetchRecommendations, fetchByIPSlug]);

  // Select first preset when IP data is available (from server or client fetch)
  useEffect(() => {
    if (ip && ip.presets && ip.presets.length > 0 && !selectedPreset) {
      setSelectedPreset(ip.presets[0]);
    }
  }, [ip, selectedPreset]);

  // Fetch IP detail (skip if server-provided via ISR or if demo IP)
  useEffect(() => {
    // Phase 6: Skip fetch if initial data provided from server
    if (initialIP) {
      return;
    }

    // Demo IP: Use synthetic data without backend fetch
    if (isDemoIP(slug)) {
      const demoData = getDemoIPData(slug);
      if (demoData) {
        setIP(demoData.ipDetail as IPDetail);
        setRights(demoData.ipRights as IPRights);
        setLoading(false);
        return;
      }
    }

    async function fetchIPDetail() {
      setLoading(true);
      setError(null);

      try {
        const [detailRes, rightsRes] = await Promise.all([
          fetch("/api/v1/ip/catalog/" + slug),
          fetch("/api/v1/ip/catalog/" + slug + "/rights"),
        ]);

        if (!detailRes.ok) {
          // Fallback to demo data if backend fails
          const demoData = getDemoIPData(slug);
          if (demoData) {
            setIP(demoData.ipDetail as IPDetail);
            setRights(demoData.ipRights as IPRights);
            setLoading(false);
            return;
          }
          throw new Error("IP not found");
        }

        const detail = await detailRes.json();
        setIP(detail);

        if (rightsRes.ok) {
          const rightsData = await rightsRes.json();
          setRights(rightsData);
        }
      } catch (err) {
        // Final fallback attempt to demo data
        const demoData = getDemoIPData(slug);
        if (demoData) {
          setIP(demoData.ipDetail as IPDetail);
          setRights(demoData.ipRights as IPRights);
          setLoading(false);
          return;
        }
        setError("Failed to load IP details");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchIPDetail();
  }, [slug, initialIP]);

  // Fetch recommendations when IP is loaded (skip for demo IPs)
  useEffect(() => {
    if (ip && slug && !isDemoIP(slug)) {
      fetchByIPSlug(slug);
    }
  }, [ip, slug, fetchByIPSlug]);

  // Fetch updated recommendations when preset is selected (skip for demo IPs)
  useEffect(() => {
    if (ip && selectedPreset && !isDemoIP(slug)) {
      fetchRecommendations({
        ip_id: ip.id,
        preset_id: selectedPreset.id,
        max_results: 3,
      });
    }
  }, [ip, selectedPreset, slug, fetchRecommendations]);

  const handleGenerate = useCallback(async () => {
    if (!ip) return;

    const effectiveStatus = rights?.license_status || ip.license_status;

    // Check license status
    if (effectiveStatus === "prohibited") {
      return; // Button should be disabled
    }

    if (effectiveStatus === "restricted" && !licenseAccepted) {
      setShowLicenseWarning(true);
      return;
    }

    setGenerating(true);

    try {
      // Demo mode: Call demo endpoint for workflow recommendation
      const response = await fetch("/api/v1/ip/" + slug + "/generate-demo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: userPrompt || null,
          preset_id: selectedPreset?.id || null,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Workflow recommendation failed");
      }

      const result: WorkflowData = await response.json();

      // Show workflow preview modal instead of starting generation
      setWorkflowData(result);
      setShowWorkflowModal(true);
      setGenerating(false);
    } catch (err) {
      console.error("Generation error:", err);
      setError(err instanceof Error ? err.message : "Generation failed");
      setGenerating(false);
    }
  }, [selectedPreset, ip, rights, licenseAccepted, userPrompt, slug]);

  const handleAcceptLicense = useCallback(() => {
    setLicenseAccepted(true);
    setShowLicenseWarning(false);
    handleGenerate();
  }, [handleGenerate]);

  const handleCopyTraceId = useCallback(async () => {
    if (!traceId) return;
    try {
      await navigator.clipboard?.writeText(traceId);
      setTraceIdCopied(true);
      setTimeout(() => setTraceIdCopied(false), 1500);
    } catch (err) {
      console.warn("Failed to copy trace id", err);
    }
  }, [traceId]);

  // ==========================================================================
  // IMPORTANT: All useMemo/useCallback hooks MUST be called before early returns
  // to comply with React's Rules of Hooks (same order on every render)
  // ==========================================================================

  // Demo overlay - slug 기반으로 데모 데이터 조회
  const demoOverride = useMemo(() => getDemoIPOverride(slug), [slug]);

  // Video URL 우선순위: demo.detailVideoUrl → ip.preview_video_url → poster fallback
  const { videoUrl, posterUrl } = useMemo(
    () => ip ? resolveVideoUrl(ip, demoOverride) : { videoUrl: null, posterUrl: null },
    [ip, demoOverride]
  );

  // 워크플로우 카드 데이터 (데모 오버라이드 우선)
  const workflowCards = useMemo(() => {
    if (demoOverride?.workflows && demoOverride.workflows.length > 0) {
      return demoOverride.workflows;
    }
    // Fallback - 기본 워크플로우 (실제 데이터 연동 시 대체)
    return null;
  }, [demoOverride]);

  // 콘텐츠 유형 가져오기 (hooks 이후에 파생 값 계산)
  const contentType: ContentType = demoOverride?.contentType || "default";
  const isComplexWorkflow = contentType === "horizontal-anime-mv";
  const isVerticalShortform = contentType === "vertical-shortform";

  // Workflow icon 매핑 (static - 렌더링 때마다 동일)
  const workflowIconMap: Record<string, React.ElementType> = useMemo(() => ({
    BookOpen,
    Palette,
    Brain,
    Sparkles,
    GitBranch,
    Image,
    Users,
    Wand2,
    Globe,
    Clapperboard,
    Video,
    Zap,
    Layers,
    Heart,
    Music,
    Eye,
  }), []);

  // ==========================================================================
  // Early returns - AFTER all hooks
  // ==========================================================================

  if (loading) {
    return (
      <AppShell showTopBar={false}>
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full" />
        </div>
      </AppShell>
    );
  }

  if (error || !ip) {
    return (
      <AppShell showTopBar={false}>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <p className="text-red-500 mb-4">{error || "IP not found"}</p>
            <button
              onClick={() => router.push("/ip")}
              className="px-4 py-2 bg-violet-600 text-white rounded-lg"
            >
              {language === "ko" ? "목록으로 돌아가기" : "Back to Gallery"}
            </button>
          </div>
        </div>
      </AppShell>
    );
  }

  const name = language === "ko" ? ip.name_ko : ip.name_en;
  const description = language === "ko" ? ip.description_ko : ip.description_en;
  const effectiveStatus = rights?.license_status || ip.license_status;
  const isProhibited = effectiveStatus === "prohibited";
  const isRestricted = effectiveStatus === "restricted";
  const recommendedDimensions = Array.from(
    new Set(recommendations.map((rec) => rec.dimension))
  );
  const evidenceRefCount = recommendations.reduce(
    (sum, rec) => sum + (rec.evidence_refs?.length || 0),
    0
  );
  const reasonCodeCount = recommendations.reduce(
    (sum, rec) => sum + (rec.reason_codes?.length || 0),
    0
  );
  const historyReasonCount = recommendations.reduce(
    (sum, rec) =>
      sum +
      (rec.reason_codes || []).filter((code) => code.startsWith("history:")).length,
    0
  );
  const hasEvidenceSignals = recommendations.some(
    (rec) => (rec.evidence_refs || []).length > 0
  );
  const hasHistorySignals = recommendations.some((rec) =>
    (rec.reason_codes || []).some((code) => code.startsWith("history:"))
  );

  return (
    <AppShell showTopBar={false}>
      <div className="min-h-screen bg-white dark:bg-slate-950">
        {/* Header */}
        <div className="border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/80 backdrop-blur-xl sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <button
                onClick={() => router.push("/ip")}
                className="flex items-center gap-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>{language === "ko" ? "뒤로" : "Back"}</span>
              </button>

              {/* License status */}
              {effectiveStatus !== "allowed" && (
                <div className={"flex items-center gap-2 px-3 py-1.5 rounded-full " + (isProhibited ? "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400" : "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400")}>
                  {isProhibited ? <Ban className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                  <span className="text-sm font-medium">
                    {language === "ko"
                      ? isProhibited ? "생성 불가" : "제한된 라이선스"
                      : isProhibited ? "Not Available" : "Restricted License"}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Content - 시연용 2-Column 레이아웃 */}
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row">
            {/* 좌측: 영상 플레이어 + IP 정보 */}
            <div className="flex-1 p-6 lg:pr-6">
              {/* 메인 영상 플레이어 - 비율에 따라 동적 조정 */}
              <div className="mb-6">
                {/* 세로 숏폼 (9:16) */}
                {isVerticalShortform ? (
                  <div className="flex justify-center">
                    <div className="relative w-full max-w-[320px] aspect-[9/16] rounded-2xl overflow-hidden bg-gradient-to-br from-slate-900 to-slate-800 shadow-2xl ring-1 ring-white/10">
                      {videoUrl ? (
                        <video
                          ref={videoRef}
                          autoPlay
                          muted={isMuted}
                          loop
                          playsInline
                          className="w-full h-full object-cover"
                          poster={posterUrl || undefined}
                        >
                          <source src={videoUrl} type="video/mp4" />
                        </video>
                      ) : (
                        <div
                          className="w-full h-full bg-cover bg-center"
                          style={{ backgroundImage: posterUrl ? `url(${posterUrl})` : undefined }}
                        >
                          <div className="w-full h-full flex items-center justify-center bg-black/40">
                            <span className="text-white/60 text-sm">
                              {language === "ko" ? "영상 준비 중" : "Video coming soon"}
                            </span>
                          </div>
                        </div>
                      )}

                      {/* Mute/Unmute 토글 버튼 */}
                      {videoUrl && (
                        <button
                          onClick={handleMuteToggle}
                          className="absolute left-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/60 backdrop-blur-sm flex items-center justify-center text-white hover:bg-black/80 transition-all z-10 shadow-lg"
                          aria-label={isMuted ? "Unmute" : "Mute"}
                        >
                          {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                        </button>
                      )}

                      {/* 세로 영상 오버레이 */}
                      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent">
                        <div className="text-center">
                          <p className="text-white font-bold text-base">{name}</p>
                          <div className="flex items-center justify-center gap-2 mt-1">
                            <span className="px-2 py-0.5 rounded-full bg-violet-500/80 text-white text-[10px] font-medium">
                              9:16 {language === "ko" ? "세로 숏폼" : "Vertical"}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* 세로 영상 상단 배지 */}
                      <div className="absolute top-3 left-3 right-3 flex justify-between">
                        <span className="px-2 py-0.5 rounded-full bg-black/50 backdrop-blur-sm text-white text-[10px] font-medium">
                          {language === "ko" ? "웹드라마" : "Web Drama"}
                        </span>
                        <span className="px-2 py-0.5 rounded-full bg-rose-500/90 text-white text-[10px] font-bold">
                          SHORTS
                        </span>
                      </div>
                    </div>
                  </div>
                ) : (
                  /* 가로 영상 (16:9 - 기본) */
                  <div className="relative aspect-video rounded-2xl overflow-hidden bg-gradient-to-br from-slate-900 to-slate-800 shadow-2xl ring-1 ring-white/10">
                    {videoUrl ? (
                      <video
                        ref={videoRef}
                        autoPlay
                        muted={isMuted}
                        loop
                        playsInline
                        className="w-full h-full object-cover"
                        poster={posterUrl || undefined}
                      >
                        <source src={videoUrl} type="video/mp4" />
                      </video>
                    ) : (
                      <div
                        className="w-full h-full bg-cover bg-center"
                        style={{ backgroundImage: posterUrl ? `url(${posterUrl})` : undefined }}
                      >
                        <div className="w-full h-full flex items-center justify-center bg-black/40">
                          <span className="text-white/60 text-sm">
                            {language === "ko" ? "영상 준비 중" : "Video coming soon"}
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Mute/Unmute 토글 버튼 */}
                    {videoUrl && (
                      <button
                        onClick={handleMuteToggle}
                        className="absolute left-4 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-black/60 backdrop-blur-sm flex items-center justify-center text-white hover:bg-black/80 transition-all z-10 shadow-lg"
                        aria-label={isMuted ? "Unmute" : "Mute"}
                      >
                        {isMuted ? <VolumeX className="w-6 h-6" /> : <Volume2 className="w-6 h-6" />}
                      </button>
                    )}

                    {/* 가로 영상 오버레이 */}
                    <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white font-bold text-lg">{name}</p>
                          <p className="text-white/70 text-sm">
                            {language === "ko" ? "대표 영상 미리보기" : "Featured Preview"}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          {isComplexWorkflow && (
                            <span className="px-2 py-1 rounded-full bg-emerald-500/80 text-white text-xs font-medium">
                              {language === "ko" ? "씬 일관성" : "Scene Consistency"}
                            </span>
                          )}
                          <span className="px-3 py-1 rounded-full bg-violet-500/80 text-white text-xs font-medium">
                            {language === "ko" ? "자동 재생" : "Auto Play"}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* 애니 MV 상단 배지 */}
                    {isComplexWorkflow && (
                      <div className="absolute top-3 left-3 flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded-full bg-black/50 backdrop-blur-sm text-white text-[10px] font-medium">
                          {language === "ko" ? "애니메이션 MV" : "Animation MV"}
                        </span>
                        <span className="px-2 py-0.5 rounded-full bg-gradient-to-r from-violet-500 to-blue-500 text-white text-[10px] font-bold">
                          16:9
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* IP 정보 헤더 */}
              <div className="flex gap-4 mb-6">
                {/* 작은 썸네일 */}
                <div className="w-20 h-28 rounded-xl overflow-hidden bg-slate-100 dark:bg-slate-800 flex-shrink-0 ring-2 ring-violet-500/20">
                  {ip.thumbnail_url ? (
                    <img
                      src={ip.thumbnail_url}
                      alt={name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-3xl">
                      🎬
                    </div>
                  )}
                </div>

                {/* 정보 */}
                <div className="flex-1">
                  <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                    {name}
                  </h1>

                  {/* 장르 태그 */}
                  <div className="flex flex-wrap gap-2 mb-3">
                    {ip.genre.map((g) => (
                      <span
                        key={g}
                        className="px-2 py-0.5 text-xs rounded-full bg-violet-500/10 text-violet-600 dark:text-violet-400 font-medium"
                      >
                        {g}
                      </span>
                    ))}
                  </div>

                  {/* 통계 */}
                  <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                      {ip.preset_count} {language === "ko" ? "프리셋" : "presets"}
                    </span>
                    <span>{ip.generation_count.toLocaleString()} {language === "ko" ? "생성됨" : "created"}</span>
                  </div>
                </div>
              </div>

              {/* 설명 */}
              {description && (
                <p className="text-slate-600 dark:text-slate-400 mb-6 text-sm leading-relaxed">
                  {description}
                </p>
              )}

              {/* 이 IP로 만들 수 있는 것 - 워크플로우 추천 */}
              {workflowCards && workflowCards.length > 0 && (
                <div className="mb-6">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-violet-500" />
                    {language === "ko" ? "이 IP로 만들 수 있는 것" : "Create with this IP"}
                    {/* 콘텐츠 유형 배지 */}
                    {isVerticalShortform && (
                      <span className="px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-600 dark:text-violet-400 text-[10px] font-medium">
                        9:16 {language === "ko" ? "세로" : "Vertical"}
                      </span>
                    )}
                    {isComplexWorkflow && (
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-[10px] font-medium">
                        16:9 {language === "ko" ? "씬 일관성" : "Scene Consistency"}
                      </span>
                    )}
                  </h2>

                  {/* 복잡한 워크플로우 (애니 MV) - 스텝퍼 스타일 */}
                  {isComplexWorkflow ? (
                    <div className="space-y-2">
                      {workflowCards
                        .sort((a, b) => (a.stepNumber || 0) - (b.stepNumber || 0))
                        .map((workflow: DemoWorkflow, index: number) => {
                          const IconComponent = workflowIconMap[workflow.icon] || Sparkles;
                          const title = language === "ko" ? workflow.titleKo : workflow.title;
                          const desc = language === "ko" ? workflow.descriptionKo : workflow.description;
                          const isLast = index === workflowCards.length - 1;

                          return (
                            <div key={workflow.id} className="relative">
                              {/* 연결선 */}
                              {!isLast && (
                                <div className="absolute left-5 top-14 w-0.5 h-6 bg-gradient-to-b from-slate-300 to-slate-200 dark:from-slate-600 dark:to-slate-700" />
                              )}
                              <button
                                onClick={() => {
                                  // 워크플로우 상태 저장 및 컨텍스트 전달
                                  const stepNumber = workflow.stepNumber || index + 1;
                                  const workflowKey = demoOverride?.contentType || "default";

                                  // 워크플로우 상태 저장 (전체 워크플로우)
                                  saveWorkflowState({
                                    ipSlug: slug,
                                    workflowKey,
                                    currentStep: stepNumber,
                                    totalSteps: workflowCards?.length || 1,
                                    steps: (workflowCards || []).map((wf) => ({
                                      app: wf.id,
                                      href: wf.href,
                                      badge: wf.badge || "",
                                      name_ko: wf.titleKo,
                                      name_en: wf.title,
                                      titleKo: wf.titleKo,
                                      title: wf.title,
                                    })),
                                    startedAt: new Date().toISOString(),
                                    results: {},
                                    userPrompt: userPrompt || undefined,
                                  });

                                  // URL에 쿼리 파라미터 추가
                                  const url = buildStepUrl(
                                    {
                                      app: workflow.id,
                                      href: workflow.href,
                                      badge: workflow.badge || "",
                                      name_ko: workflow.titleKo,
                                      name_en: workflow.title,
                                    },
                                    slug,
                                    stepNumber,
                                    workflowKey,
                                    userPrompt || undefined
                                  );
                                  router.push(url);
                                }}
                                className="w-full p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 hover:border-violet-500/50 hover:bg-violet-50 dark:hover:bg-violet-900/10 transition-all text-left group"
                              >
                                <div className="flex items-center gap-3">
                                  {/* 단계 번호 + 아이콘 */}
                                  <div className="relative flex-shrink-0">
                                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
                                      <IconComponent className="w-5 h-5 text-white" />
                                    </div>
                                    <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-[10px] font-bold flex items-center justify-center">
                                      {workflow.stepNumber || index + 1}
                                    </div>
                                  </div>

                                  {/* 콘텐츠 */}
                                  <div className="min-w-0 flex-1">
                                    <div className="flex items-center gap-2">
                                      <p className="font-semibold text-slate-900 dark:text-white text-sm group-hover:text-violet-600 dark:group-hover:text-violet-400 transition-colors">
                                        {title}
                                      </p>
                                      {workflow.badge && (
                                        <span className="px-1.5 py-0.5 rounded-full bg-violet-500/20 text-violet-600 dark:text-violet-400 text-[9px] font-medium">
                                          {workflow.badge}
                                        </span>
                                      )}
                                    </div>
                                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-1">
                                      {desc}
                                    </p>
                                  </div>

                                  {/* 화살표 */}
                                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-violet-500 group-hover:translate-x-1 transition-all flex-shrink-0" />
                                </div>
                              </button>
                            </div>
                          );
                        })}
                    </div>
                  ) : (
                    /* 기본 워크플로우 (숏폼 포함) - 그리드 스타일 */
                    <div className="grid grid-cols-2 gap-3">
                      {workflowCards.map((workflow: DemoWorkflow, index: number) => {
                        const IconComponent = workflowIconMap[workflow.icon] || Sparkles;
                        const title = language === "ko" ? workflow.titleKo : workflow.title;
                        const desc = language === "ko" ? workflow.descriptionKo : workflow.description;

                        return (
                          <button
                            key={workflow.id}
                            onClick={() => {
                              // 워크플로우 상태 저장 및 컨텍스트 전달
                              const stepNumber = workflow.stepNumber || index + 1;
                              const workflowKey = demoOverride?.contentType || "default";

                              // 워크플로우 상태 저장 (전체 워크플로우)
                              saveWorkflowState({
                                ipSlug: slug,
                                workflowKey,
                                currentStep: stepNumber,
                                totalSteps: workflowCards?.length || 1,
                                steps: (workflowCards || []).map((wf) => ({
                                  app: wf.id,
                                  href: wf.href,
                                  badge: wf.badge || "",
                                  name_ko: wf.titleKo,
                                  name_en: wf.title,
                                  titleKo: wf.titleKo,
                                  title: wf.title,
                                })),
                                startedAt: new Date().toISOString(),
                                results: {},
                                userPrompt: userPrompt || undefined,
                              });

                              // URL에 쿼리 파라미터 추가
                              const url = buildStepUrl(
                                {
                                  app: workflow.id,
                                  href: workflow.href,
                                  badge: workflow.badge || "",
                                  name_ko: workflow.titleKo,
                                  name_en: workflow.title,
                                },
                                slug,
                                stepNumber,
                                workflowKey,
                                userPrompt || undefined
                              );
                              router.push(url);
                            }}
                            className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 hover:border-violet-500/50 hover:bg-violet-50 dark:hover:bg-violet-900/10 transition-all text-left group"
                          >
                            <div className="flex items-start gap-3">
                              {/* 단계 번호 표시 (숏폼) */}
                              {isVerticalShortform && workflow.stepNumber && (
                                <div className="relative">
                                  <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center flex-shrink-0">
                                    <IconComponent className="w-5 h-5 text-violet-500" />
                                  </div>
                                  <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-violet-500 text-white text-[9px] font-bold flex items-center justify-center">
                                    {workflow.stepNumber}
                                  </div>
                                </div>
                              )}
                              {/* 기본 아이콘 */}
                              {(!isVerticalShortform || !workflow.stepNumber) && (
                                <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center flex-shrink-0">
                                  <IconComponent className="w-5 h-5 text-violet-500" />
                                </div>
                              )}
                              <div className="min-w-0 flex-1">
                                <div className="flex items-center gap-2">
                                  <p className="font-semibold text-slate-900 dark:text-white text-sm group-hover:text-violet-600 dark:group-hover:text-violet-400 transition-colors truncate">
                                    {title}
                                  </p>
                                  {workflow.badge && (
                                    <span className="px-1.5 py-0.5 rounded-full bg-violet-500/20 text-violet-600 dark:text-violet-400 text-[9px] font-medium flex-shrink-0">
                                      {workflow.badge}
                                    </span>
                                  )}
                                </div>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">
                                  {desc}
                                </p>
                              </div>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* 세계관 (있는 경우) */}
              {ip.worldbuilding && Object.keys(ip.worldbuilding).length > 0 && (() => {
                // Type-safe worldbuilding extraction
                const wb = ip.worldbuilding as {
                  logline?: string;
                  setting?: string;
                  mood?: string;
                  episode_count?: number;
                  episode_length?: string;
                  duration?: string;
                  music_style?: string;
                  themes?: string[];
                  characters?: Array<{
                    name: string;
                    role?: string;
                    age?: string;
                    job?: string;
                    specialty?: string;
                    traits?: string[];
                    backstory?: string;
                  }>;
                };
                return (
                <div className="mb-6">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                    <Globe className="w-5 h-5 text-violet-500" />
                    {language === "ko" ? "세계관" : "Worldbuilding"}
                  </h2>
                  <div className="space-y-4">
                    {/* 로그라인 (핵심 한 줄 요약) */}
                    {wb.logline && (
                      <div className="p-4 rounded-xl bg-gradient-to-r from-violet-500/10 to-blue-500/10 border border-violet-500/20">
                        <p className="text-base font-medium text-slate-800 dark:text-slate-200 italic leading-relaxed">
                          "{wb.logline}"
                        </p>
                      </div>
                    )}

                    {/* 배경 설정 + 분위기 */}
                    {wb.setting && (
                      <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                        <p className="text-xs font-semibold text-violet-600 dark:text-violet-400 mb-2 uppercase tracking-wider">
                          {language === "ko" ? "배경" : "Setting"}
                        </p>
                        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                          {wb.setting}
                        </p>
                        {wb.mood && (
                          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                            <span className="font-medium">무드:</span> {wb.mood}
                          </p>
                        )}
                      </div>
                    )}

                    {/* 콘텐츠 정보 (에피소드/길이) */}
                    {(wb.episode_count || wb.duration || wb.music_style) && (
                      <div className="flex flex-wrap gap-2">
                        {wb.episode_count && (
                          <span className="px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 flex items-center gap-1.5">
                            <Clapperboard className="w-3.5 h-3.5" />
                            {wb.episode_count}화 × {wb.episode_length || "60초"}
                          </span>
                        )}
                        {wb.duration && (
                          <span className="px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 flex items-center gap-1.5">
                            <Clock className="w-3.5 h-3.5" />
                            {wb.duration}
                          </span>
                        )}
                        {wb.music_style && (
                          <span className="px-3 py-1.5 text-xs font-medium rounded-lg bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300 flex items-center gap-1.5">
                            <Music className="w-3.5 h-3.5" />
                            {wb.music_style}
                          </span>
                        )}
                      </div>
                    )}

                    {/* 테마 */}
                    {wb.themes && wb.themes.length > 0 && (
                      <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                        <p className="text-xs font-semibold text-violet-600 dark:text-violet-400 mb-3 uppercase tracking-wider">
                          {language === "ko" ? "테마" : "Themes"}
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {wb.themes.map((theme, i) => (
                            <span key={i} className="px-3 py-1.5 text-sm font-medium rounded-full bg-gradient-to-r from-violet-100 to-purple-100 dark:from-violet-900/40 dark:to-purple-900/40 text-violet-700 dark:text-violet-300 border border-violet-200 dark:border-violet-800">
                              {theme}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 캐릭터 */}
                    {wb.characters && wb.characters.length > 0 && (
                      <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                        <p className="text-xs font-semibold text-violet-600 dark:text-violet-400 mb-3 uppercase tracking-wider flex items-center gap-1.5">
                          <Users className="w-3.5 h-3.5" />
                          {language === "ko" ? "등장인물" : "Characters"}
                        </p>
                        <div className="space-y-4">
                          {wb.characters.map((char, i) => (
                            <div key={i} className="p-3 rounded-lg bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700">
                              <div className="flex items-start justify-between mb-2">
                                <div>
                                  <span className="text-base font-bold text-slate-800 dark:text-slate-200">{char.name}</span>
                                  {char.role && (
                                    <span className="ml-2 px-2 py-0.5 text-[11px] font-medium rounded-full bg-violet-100 dark:bg-violet-900/40 text-violet-600 dark:text-violet-400">
                                      {char.role}
                                    </span>
                                  )}
                                </div>
                                {char.age && (
                                  <span className="text-xs text-slate-500 dark:text-slate-400">{char.age}</span>
                                )}
                              </div>
                              {(char.job || char.specialty) && (
                                <p className="text-xs text-slate-600 dark:text-slate-400 mb-2">
                                  {char.job || char.specialty}
                                </p>
                              )}
                              {char.traits && char.traits.length > 0 && (
                                <div className="flex flex-wrap gap-1 mb-2">
                                  {char.traits.map((trait, j) => (
                                    <span key={j} className="px-2 py-0.5 text-[10px] rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                                      #{trait}
                                    </span>
                                  ))}
                                </div>
                              )}
                              {char.backstory && (
                                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed border-t border-slate-100 dark:border-slate-800 pt-2 mt-2">
                                  {char.backstory}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                );
              })()}
            </div>

            {/* 우측 사이드바 - 생성 패널 */}
            <div className="lg:w-[420px] p-6 lg:border-l border-slate-200 dark:border-slate-800 bg-gradient-to-b from-slate-50 to-white dark:from-slate-900/50 dark:to-slate-900/80">
              {generationId ? (
                <GenerationProgress
                  slug={slug}
                  generationId={generationId}
                  onComplete={() => {
                    // Handle completion
                  }}
                  onCancel={() => {
                    setGenerationId(null);
                    setGenerating(false);
                  }}
                />
              ) : (
                <>
                  {/* 시연용 헤더 섹션 */}
                  <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-violet-500/10 to-blue-500/10 border border-violet-500/20">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles className="w-5 h-5 text-violet-500" />
                      <h2 className="text-base font-bold text-slate-900 dark:text-white">
                        {language === "ko" ? "AI 콘텐츠 생성" : "AI Content Generation"}
                      </h2>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                      {language === "ko"
                        ? "이 IP의 세계관과 캐릭터를 활용한 새로운 콘텐츠를 AI로 생성하세요."
                        : "Create new content using this IP's worldbuilding and characters with AI."}
                    </p>
                  </div>

                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-violet-500"></span>
                    {language === "ko" ? "프리셋 선택" : "Select Preset"}
                  </h3>

                  {/* Preset list */}
                  <div className="space-y-3 mb-6">
                    {ip.presets.map((preset) => {
                      const presetName = language === "ko" ? preset.name_ko : preset.name_en;
                      const isSelected = selectedPreset?.id === preset.id;

                      return (
                        <button
                          key={preset.id}
                          onClick={() => setSelectedPreset(preset)}
                          className={"w-full p-4 rounded-xl border-2 text-left transition-all " + (isSelected ? "border-violet-500 bg-violet-50 dark:bg-violet-900/20" : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600")}
                          disabled={isProhibited}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-slate-900 dark:text-white">
                              {presetName}
                            </span>
                            {isSelected && (
                              <div className="w-5 h-5 rounded-full bg-violet-500 flex items-center justify-center">
                                <ChevronRight className="w-3 h-3 text-white" />
                              </div>
                            )}
                          </div>
                          <div className="flex items-center gap-4 mt-2 text-sm text-slate-500 dark:text-slate-400">
                            <span className="flex items-center gap-1">
                              <Coins className="w-4 h-4" />
                              {preset.estimated_credits}
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              {Math.floor(preset.estimated_duration_seconds / 60)}분
                            </span>
                          </div>
                        </button>
                      );
                    })}
                  </div>

                  {/* Tool Recommendations (Phase 2.5 Evidence Card) */}
                  {selectedPreset && (
                    <div className="mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300">
                      {t("recommendedTools")}
                    </h3>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                      <button
                        type="button"
                        onClick={() => setShowRecommendations((prev) => !prev)}
                        className="text-violet-500 hover:underline"
                        aria-pressed={showRecommendations}
                      >
                        {showRecommendations ? t("hideRecommendations") : t("showRecommendations")}
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowRecommendationWhy((prev) => !prev)}
                        className="text-slate-500 hover:text-slate-700 dark:hover:text-slate-200"
                        aria-pressed={showRecommendationWhy}
                        aria-controls="recommendation-why-panel"
                      >
                        {showRecommendationWhy ? t("hideRecommendationWhy") : t("showRecommendationWhy")}
                      </button>
                      {showRecommendations && recResponse && (
                        <>
                          {workflowSuggested && (
                            <span className="evidence-badge">
                              {t("workflowSuggested")}
                            </span>
                          )}
                          <span
                            className="evidence-badge text-[9px]"
                            data-tone="context"
                          >
                            {ipContextUsed ? t("ipContextUsed") : t("ipContextMissing")}
                          </span>
                          {traceId && (
                            <button
                              type="button"
                              onClick={handleCopyTraceId}
                              className="text-[9px] text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                            >
                              {traceIdCopied ? t("copied") : `${t("traceIdLabel")} · ${t("copyTraceId")}`}
                            </button>
                          )}
                          {recommendedDimensions.length > 0 && (
                            <div className="flex items-center gap-1">
                              <span className="text-[10px] uppercase tracking-[0.18em]">
                                {t("recommendedDimensions")}
                              </span>
                              {recommendedDimensions.map((dimension) => {
                                const dimensionKey = dimension.toLowerCase();
                                const dimensionClass = dimensionKey
                                  ? `bg-dimension-${dimensionKey}/20 text-dimension-${dimensionKey}`
                                  : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300";
                                return (
                                  <span
                                    key={dimension}
                                    className={`text-[9px] px-2 py-0.5 rounded-full ${dimensionClass}`}
                                  >
                                    {dimension}
                                  </span>
                                );
                              })}
                            </div>
                          )}
                          {totalCredits > 0 && (
                            <span>
                              {totalCredits} {t("credits")}
                            </span>
                          )}
                        </>
                      )}
                    </div>
                  </div>

                  {!showRecommendations && (
                    <div className="text-xs text-slate-400">
                      {t("recommendationsHidden")}
                    </div>
                  )}

                  {showRecommendationWhy && (
                    <div
                      id="recommendation-why-panel"
                      className="rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50/70 dark:bg-slate-900/40 px-3 py-2 text-xs text-slate-600 dark:text-slate-300 space-y-1"
                    >
                      <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                        {t("recommendationSignalsTitle")}
                      </div>
                      {reasonCodeCount > 0 && (
                        <div className="flex flex-wrap gap-1 text-[10px] text-slate-400">
                          <span className="evidence-badge" data-tone="context">
                            {t("evidenceReasonsTitle")} {reasonCodeCount}
                          </span>
                          {hasEvidenceSignals && (
                            <span className="evidence-badge" data-tone="source">
                              {t("evidenceSourcesTitle")} {evidenceRefCount}
                            </span>
                          )}
                        </div>
                      )}
                      <ul className="list-disc pl-4 space-y-0.5">
                        <li>
                          {ipContextUsed
                            ? t("signalIpContext")
                            : t("signalLimitedContext")}
                        </li>
                        {workflowSuggested && <li>{t("signalWorkflowFit")}</li>}
                        {hasEvidenceSignals && (
                          <li>
                            {t("signalEvidenceSources")}
                            {evidenceRefCount > 0 ? ` (${evidenceRefCount})` : ""}
                          </li>
                        )}
                        {hasHistorySignals && (
                          <li>
                            {t("signalUsageHistory")}
                            {historyReasonCount > 0 ? ` (${historyReasonCount})` : ""}
                          </li>
                        )}
                      </ul>
                    </div>
                  )}

                  {showRecommendations && recLoading && (
                    <div className="rounded-lg border border-slate-200 dark:border-slate-700 p-4 animate-pulse space-y-2">
                      <div className="h-3 w-1/3 bg-slate-200 dark:bg-slate-700 rounded" />
                      <div className="h-3 w-2/3 bg-slate-200 dark:bg-slate-700 rounded" />
                      <div className="h-3 w-1/2 bg-slate-200 dark:bg-slate-700 rounded" />
                    </div>
                  )}

                  {showRecommendations && !recLoading && recError && (
                    <div className="text-xs text-red-500 flex items-center gap-2">
                      <span>{t("recommendationLoadFailed")}</span>
                      <button
                        type="button"
                        onClick={handleRetryRecommendations}
                        className="text-violet-500 hover:underline"
                      >
                        {t("retry")}
                      </button>
                    </div>
                  )}

                  {showRecommendations && !recLoading && recResponse && recommendations.length === 0 && (
                    <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-2">
                      <span>{t("recommendationEmpty")}</span>
                      <button
                        type="button"
                        onClick={() => router.push("/dimension")}
                        className="text-violet-500 hover:underline"
                      >
                        {t("exploreOtherDimensions")}
                      </button>
                    </div>
                  )}

                      {showRecommendations && !recLoading && recResponse && recommendations.length > 0 && (
                        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.8fr)]">
                          <div className="space-y-2">
                            <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                              {t("topRecommendationTitle")}
                            </div>
                            <EvidenceCard
                              confidenceLevel={recommendations[0]?.confidence_level || "medium"}
                              confidence={recommendations[0]?.confidence}
                              reasonCodes={recommendations[0]?.reason_codes || []}
                              evidenceRefs={recommendations[0]?.evidence_refs || []}
                              reasonSummary={recResponse.reason_summary}
                              isCollapsible={true}
                            />
                            <div className="flex items-center gap-2 text-[10px] text-slate-400">
                              <span>{t("recommendationFeedbackLabel")}</span>
                              <button
                                type="button"
                                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-slate-200 dark:border-slate-700 text-slate-400 hover:text-emerald-500 hover:border-emerald-400"
                              >
                                👍 {t("feedbackHelpful")}
                              </button>
                              <button
                                type="button"
                                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-slate-200 dark:border-slate-700 text-slate-400 hover:text-rose-500 hover:border-rose-400"
                              >
                                👎 {t("feedbackNotHelpful")}
                              </button>
                            </div>
                          </div>
                          <div className="space-y-2">
                            <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                              {t("alternativeRecommendations")}
                            </div>
                            {recommendations.length > 1 ? (
                              <div className="grid gap-2">
                                {recommendations.slice(1).map((rec) => (
                                  <ToolRecommendationCard
                                    key={rec.tool_id}
                                    toolId={rec.tool_id}
                                    displayName={rec.display_name}
                                    dimension={rec.dimension}
                                    confidence={rec.confidence}
                                    confidenceLevel={rec.confidence_level}
                                    reasonCodes={rec.reason_codes}
                                    estimatedCredits={rec.estimated_credits}
                                    ipId={ip?.id}
                                    summary={rec.description}
                                  />
                                ))}
                              </div>
                            ) : (
                              <div className="text-xs text-slate-400">
                                {t("noAlternativeRecommendations")}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* User prompt */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      {language === "ko" ? "추가 프롬프트 (선택)" : "Additional Prompt (optional)"}
                    </label>
                    <textarea
                      value={userPrompt}
                      onChange={(e) => setUserPrompt(e.target.value)}
                      placeholder={language === "ko" ? "원하는 장면이나 스토리를 설명해주세요..." : "Describe your desired scene or story..."}
                      className="w-full h-24 p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 resize-none focus:outline-none focus:ring-2 focus:ring-violet-500"
                      disabled={isProhibited}
                    />
                  </div>

                  {/* Estimate */}
                  {selectedPreset && !isProhibited && (
                    <div className="p-4 rounded-xl bg-slate-100 dark:bg-slate-800 mb-6">
                      <div className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                        {language === "ko" ? "예상" : "Estimate"}
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-2 text-slate-900 dark:text-white">
                          <Coins className="w-5 h-5 text-violet-500" />
                          <span className="font-bold">{selectedPreset.estimated_credits}</span>
                          <span className="text-sm text-slate-500">{language === "ko" ? "크레딧" : "credits"}</span>
                        </span>
                        <span className="flex items-center gap-2 text-slate-900 dark:text-white">
                          <Clock className="w-5 h-5 text-violet-500" />
                          <span className="font-bold">{Math.floor(selectedPreset.estimated_duration_seconds / 60)}</span>
                          <span className="text-sm text-slate-500">{language === "ko" ? "분" : "min"}</span>
                        </span>
                      </div>
                    </div>
                  )}

                  {/* License warning for restricted */}
                  {isRestricted && !licenseAccepted && (
                    <div className="mb-4">
                      <LicenseStatusInfo status="restricted" />
                    </div>
                  )}

                  {/* Generate button */}
                  <button
                    onClick={handleGenerate}
                    disabled={!selectedPreset || isProhibited || generating}
                    className={"w-full py-3 px-4 rounded-[var(--cta-primary-radius)] font-medium flex items-center justify-center gap-2 transition-[var(--transition-interactive)] " + (isProhibited ? "bg-[var(--bg-interactive)] text-[var(--fg-disabled)] cursor-not-allowed" : "bg-[var(--bg-primary)] hover:bg-[var(--bg-primary-hover)] text-[var(--fg-on-primary)] shadow-[var(--cta-primary-shadow)] hover:shadow-[var(--cta-primary-shadow-hover)]")}
                  >
                    <Sparkles className="w-5 h-5" />
                    {isProhibited
                      ? (language === "ko" ? "생성 불가" : "Not Available")
                      : generating
                        ? (language === "ko" ? "시작 중..." : "Starting...")
                        : (language === "ko" ? "생성하기" : "Generate")}
                  </button>

                  {/* Prohibited message */}
                  {isProhibited && (
                    <div className="mt-4">
                      <LicenseStatusInfo status="prohibited" />
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>

        {/* License warning modal */}
        {showLicenseWarning && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 max-w-md mx-4 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-full bg-yellow-100 dark:bg-yellow-900/30">
                  <AlertTriangle className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  {language === "ko" ? "제한된 라이선스" : "Restricted License"}
                </h3>
              </div>

              <p className="text-slate-600 dark:text-slate-400 mb-6">
                {language === "ko"
                  ? "이 IP는 사용에 일부 제한이 있습니다. 팬 창작물 용도로만 사용 가능하며, 상업적 사용은 금지됩니다. 계속하시겠습니까?"
                  : "This IP has some usage restrictions. It can only be used for fan creation purposes, and commercial use is prohibited. Do you want to continue?"}
              </p>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowLicenseWarning(false)}
                  className="flex-1 py-2 px-4 rounded-[var(--cta-secondary-radius)] border border-[var(--cta-secondary-border)] bg-[var(--cta-secondary-bg)] text-[var(--cta-secondary-fg)] hover:bg-[var(--cta-secondary-bg-hover)] transition-[var(--transition-interactive)]"
                >
                  {language === "ko" ? "취소" : "Cancel"}
                </button>
                <button
                  onClick={handleAcceptLicense}
                  className="flex-1 py-2 px-4 rounded-[var(--cta-primary-radius)] bg-[var(--bg-primary)] text-[var(--fg-on-primary)] hover:bg-[var(--bg-primary-hover)] transition-[var(--transition-interactive)]"
                >
                  {language === "ko" ? "동의하고 계속" : "Accept & Continue"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Workflow Preview Modal (Demo) */}
        <WorkflowPreviewModal
          isOpen={showWorkflowModal}
          onClose={() => {
            setShowWorkflowModal(false);
            setWorkflowData(null);
          }}
          workflowData={workflowData}
          ipSlug={slug}
          ipName={name}
          userPrompt={userPrompt || undefined}
        />
      </div>
    </AppShell>
  );
}
