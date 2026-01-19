"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Clock, Coins, Sparkles, AlertTriangle, Ban, ChevronRight } from "lucide-react";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";
import { LicenseStatusInfo } from "@/components/ip/LicenseStatusBadge";
import GenerationProgress from "./GenerationProgress";
import { EvidenceCard } from "@/components/ui/EvidenceCard";
import { ToolRecommendationCard } from "@/components/ui/ToolRecommendationCard";
import { useToolRecommendations } from "@/hooks/useToolRecommendations";

interface PresetItem {
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

interface IPDetail {
  id: string;
  slug: string;
  name_ko: string;
  name_en: string;
  description_ko: string | null;
  description_en: string | null;
  thumbnail_url: string | null;
  banner_url: string | null;
  genre: string[];
  tags: string[];
  worldbuilding: Record<string, unknown>;
  license_status: "allowed" | "restricted" | "prohibited";
  preset_count: number;
  generation_count: number;
  presets: PresetItem[];
}

interface IPRights {
  license_status: "allowed" | "restricted" | "prohibited";
  territory: string[];
  blocked_territory: string[];
  scope: string;
  commercial_ok: boolean;
  expiry: string | null;
}

interface IPDetailClientProps {
  slug: string;
}

export default function IPDetailClient({ slug }: IPDetailClientProps) {
  const router = useRouter();
  const { language, t } = useLanguage();

  // State
  const [ip, setIP] = useState<IPDetail | null>(null);
  const [rights, setRights] = useState<IPRights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Generation state
  const [selectedPreset, setSelectedPreset] = useState<PresetItem | null>(null);
  const [userPrompt, setUserPrompt] = useState("");
  const [showLicenseWarning, setShowLicenseWarning] = useState(false);
  const [licenseAccepted, setLicenseAccepted] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generationId, setGenerationId] = useState<string | null>(null);

  // Tool recommendations (Phase 2.5)
  const {
    recommendations,
    response: recResponse,
    isLoading: recLoading,
    error: recError,
    totalCredits,
    workflowSuggested,
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

  // Fetch IP detail
  useEffect(() => {
    async function fetchIPDetail() {
      setLoading(true);
      setError(null);

      try {
        const [detailRes, rightsRes] = await Promise.all([
          fetch("/api/v1/ip/catalog/" + slug),
          fetch("/api/v1/ip/catalog/" + slug + "/rights"),
        ]);

        if (!detailRes.ok) {
          throw new Error("IP not found");
        }

        const detail = await detailRes.json();
        setIP(detail);

        if (rightsRes.ok) {
          const rightsData = await rightsRes.json();
          setRights(rightsData);
        }

        // Select first preset by default
        if (detail.presets && detail.presets.length > 0) {
          setSelectedPreset(detail.presets[0]);
        }
      } catch (err) {
        setError("Failed to load IP details");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchIPDetail();
  }, [slug]);

  // Fetch recommendations when IP is loaded
  useEffect(() => {
    if (ip && slug) {
      fetchByIPSlug(slug);
    }
  }, [ip, slug, fetchByIPSlug]);

  // Fetch updated recommendations when preset is selected
  useEffect(() => {
    if (ip && selectedPreset) {
      fetchRecommendations({
        ip_id: ip.id,
        preset_id: selectedPreset.id,
        max_results: 3,
      });
    }
  }, [ip, selectedPreset, fetchRecommendations]);

  const handleGenerate = useCallback(async () => {
    if (!selectedPreset || !ip) return;

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
      const response = await fetch("/api/v1/ip/" + slug + "/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preset_id: selectedPreset.id,
          user_prompt: userPrompt || null,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Generation failed");
      }

      const result = await response.json();
      setGenerationId(result.generation_id);
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

        {/* Content */}
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row">
            {/* Main content (left) */}
            <div className="flex-1 p-6 lg:pr-0">
              {/* Hero section */}
              <div className="flex gap-6 mb-8">
                {/* Thumbnail */}
                <div className="w-48 h-64 rounded-2xl overflow-hidden bg-slate-100 dark:bg-slate-800 flex-shrink-0">
                  {ip.thumbnail_url ? (
                    <img
                      src={ip.thumbnail_url}
                      alt={name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-5xl">
                      🎬
                    </div>
                  )}
                </div>

                {/* Info */}
                <div className="flex-1">
                  <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                    {name}
                  </h1>

                  {/* Genre tags */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {ip.genre.map((g) => (
                      <span
                        key={g}
                        className="px-2 py-1 text-sm rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                      >
                        {g}
                      </span>
                    ))}
                  </div>

                  {/* Description */}
                  {description && (
                    <p className="text-slate-600 dark:text-slate-400 mb-4">
                      {description}
                    </p>
                  )}

                  {/* Stats */}
                  <div className="flex items-center gap-6 text-sm text-slate-500 dark:text-slate-400">
                    <span>{ip.preset_count} presets</span>
                    <span>{ip.generation_count.toLocaleString()} created</span>
                  </div>
                </div>
              </div>

              {/* Worldbuilding (if available) */}
              {ip.worldbuilding && Object.keys(ip.worldbuilding).length > 0 && (
                <div className="mb-8">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                    {language === "ko" ? "세계관" : "Worldbuilding"}
                  </h2>
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-400">
                    <pre className="whitespace-pre-wrap text-sm">
                      {JSON.stringify(ip.worldbuilding, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Sample gallery placeholder */}
              <div className="mb-8">
                <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                  {language === "ko" ? "샘플 갤러리" : "Sample Gallery"}
                </h2>
                <div className="grid grid-cols-3 gap-4">
                  {[1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className="aspect-video rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-2xl"
                    >
                      🎬
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Sidebar (right) - Generation panel */}
            <div className="lg:w-96 p-6 lg:border-l border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
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
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                    {language === "ko" ? "프리셋 선택" : "Select Preset"}
                  </h2>

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
                        {recResponse && (
                          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                            {workflowSuggested && (
                              <span className="evidence-badge">
                                {t("workflowSuggested")}
                              </span>
                            )}
                            {totalCredits > 0 && (
                              <span>
                                {totalCredits} {t("credits")}
                              </span>
                            )}
                          </div>
                        )}
                      </div>

                      {recLoading && (
                        <div className="rounded-lg border border-slate-200 dark:border-slate-700 p-4 animate-pulse space-y-2">
                          <div className="h-3 w-1/3 bg-slate-200 dark:bg-slate-700 rounded" />
                          <div className="h-3 w-2/3 bg-slate-200 dark:bg-slate-700 rounded" />
                          <div className="h-3 w-1/2 bg-slate-200 dark:bg-slate-700 rounded" />
                        </div>
                      )}

                      {!recLoading && recError && (
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

                      {!recLoading && recResponse && recommendations.length === 0 && (
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

                      {!recLoading && recResponse && recommendations.length > 0 && (
                        <>
                          <EvidenceCard
                            confidenceLevel={recommendations[0]?.confidence_level || "medium"}
                            confidence={recommendations[0]?.confidence}
                            reasonCodes={recommendations[0]?.reason_codes || []}
                            evidenceRefs={recommendations[0]?.evidence_refs || []}
                            reasonSummary={recResponse.reason_summary}
                            isCollapsible={true}
                          />
                          {recommendations.length > 1 && (
                            <div className="mt-3 grid gap-2">
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
                          )}
                        </>
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
                    className={"w-full py-3 px-4 rounded-xl font-medium flex items-center justify-center gap-2 transition-all " + (isProhibited ? "bg-slate-200 dark:bg-slate-800 text-slate-400 cursor-not-allowed" : "bg-violet-600 hover:bg-violet-700 text-white")}
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
                  className="flex-1 py-2 px-4 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  {language === "ko" ? "취소" : "Cancel"}
                </button>
                <button
                  onClick={handleAcceptLicense}
                  className="flex-1 py-2 px-4 rounded-lg bg-violet-600 text-white hover:bg-violet-700"
                >
                  {language === "ko" ? "동의하고 계속" : "Accept & Continue"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
