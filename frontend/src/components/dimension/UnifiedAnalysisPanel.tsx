"use client";

/**
 * UnifiedAnalysisPanel - 통합 분석 패널 (VPE + AD)
 *
 * Phase 1-2: DNA Lab 단계 단순화
 * - VPE (Video Parsing Engine) + AD (Aesthetic Director) 통합
 * - 2-in-1 분석 플로우
 * - 기존 VPE → AD 순서를 단일 단계로 압축
 *
 * 워크플로우:
 * 1. 영상 업로드/URL 입력 (VPE 기능)
 * 2. 거장 선택 (AD 기능)
 * 3. 통합 분석 실행 (VPE + AD 동시 처리)
 * 4. 결과 표시 (Logic Vector + Aesthetic Guidelines)
 */

import { useState, useCallback, useTransition, useMemo, useEffect } from "react";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useResultExport } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import { useLanguage } from "@/contexts/LanguageContext";
import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";
import { useDNACardContextConsumer } from "@/hooks/useDNACardContextConsumer";
import { DNAContextBanner } from "@/components/dna-card/DNAContextBanner";
import { MASTER_AUTEURS } from "@/components/dna-card/constants";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import {
  Video,
  Palette,
  Sparkles,
  Upload,
  Link,
  CheckCircle,
  ArrowRight,
  Loader2,
  Download,
  RefreshCw,
  AlertCircle,
  Film,
} from "lucide-react";

// ============================================================================
// Constants & Types
// ============================================================================

const DIMENSION_CODE = "analysis";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

type AnalysisPhase = "input" | "processing" | "complete";

/** Disclosure level for progressive UI complexity */
type DisclosureLevel = "basic" | "intermediate" | "advanced";

interface UnifiedAnalysisResult {
  // VPE Output
  logic_vector?: {
    shot_count: number;
    dominant_style: string;
    color_palette: string[];
    mood_keywords: string[];
    pacing: string;
    technical_notes: string;
  };
  // AD Output
  aesthetic_guidelines?: {
    visual_style: string;
    composition: string;
    lighting: string;
    camera_work: string;
    color_grading: string;
  };
  auteur_influence?: {
    key: string;
    name: string;
    signature_elements: string[];
  };
  // Combined
  evidence_refs?: string[];
  confidence?: number;
  trace_id?: string;
}

// ============================================================================
// Component Props
// ============================================================================

interface UnifiedAnalysisPanelProps {
  disclosureLevel?: DisclosureLevel;
}

// ============================================================================
// Component
// ============================================================================

function UnifiedAnalysisContent({ disclosureLevel = "intermediate" }: UnifiedAnalysisPanelProps) {
  const { token, setLoading, setResult } = useDimensionPanel();
  const { language } = useLanguage();
  const isKo = language === "ko";

  // i18n labels
  const labels = useMemo(() => ({
    title: isKo ? "통합 분석" : "Unified Analysis",
    subtitle: isKo ? "영상 분석 + 미학 적용" : "Video Parsing + Aesthetic Direction",

    // Input phase
    videoInput: isKo ? "영상 입력" : "Video Input",
    uploadVideo: isKo ? "영상 업로드" : "Upload Video",
    orEnterUrl: isKo ? "또는 URL 입력" : "Or enter URL",
    urlPlaceholder: isKo ? "YouTube, Vimeo, 직접 링크..." : "YouTube, Vimeo, direct link...",

    // Auteur selection
    selectAuteur: isKo ? "거장 선택" : "Select Auteur",
    auteurHint: isKo ? "분석 스타일 방향 (선택)" : "Analysis style direction (optional)",

    // Processing
    analyzing: isKo ? "분석 중..." : "Analyzing...",
    parsingVideo: isKo ? "영상 파싱 중..." : "Parsing video...",
    applyingAesthetic: isKo ? "미학 적용 중..." : "Applying aesthetics...",

    // Complete
    analysisComplete: isKo ? "분석 완료" : "Analysis Complete",
    vpeResult: isKo ? "영상 분석 결과" : "Video Analysis Result",
    adResult: isKo ? "미학 가이드" : "Aesthetic Guide",
    newAnalysis: isKo ? "새 분석" : "New Analysis",
    exportResult: isKo ? "결과 내보내기" : "Export Result",

    // Actions
    startAnalysis: isKo ? "통합 분석 시작" : "Start Unified Analysis",

    // Errors
    errorNoInput: isKo ? "영상을 업로드하거나 URL을 입력해주세요" : "Please upload a video or enter a URL",
    errorCredits: isKo ? "크레딧이 부족합니다" : "Insufficient credits",
  }), [isKo]);

  // State
  const [phase, setPhase] = useState<AnalysisPhase>("input");
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState("");
  const [selectedAuteur, setSelectedAuteur] = useState<string>("");
  const [result, setLocalResult] = useState<UnifiedAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [processingStep, setProcessingStep] = useState<"vpe" | "ad" | null>(null);

  const [isPending, startTransition] = useTransition();

  // Hooks
  const { byokKey } = useBYOK();
  const creditCtx = useCreditContextOptional();
  const { getToolByDimension } = useDimensionConfig();
  const toolConfig = getToolByDimension("analysis") || getToolByDimension("VPE");
  const creditCost = 60; // VPE(50) + AD(10)
  const { exportJSON } = useResultExport();
  const chainContext = useDimensionChainOptional();

  // DNA Card Context
  const [auteurContext, setAuteurContext] = useState<{
    key: string;
    name: string;
  } | null>(null);

  useDNACardContextConsumer({
    onMasterContext: (auteurKey, _metadata) => {
      setSelectedAuteur(auteurKey);
      // Look up name from MASTER_AUTEURS (name = Korean, nameEn = English)
      const auteur = MASTER_AUTEURS.find(a => a.key === auteurKey);
      setAuteurContext({
        key: auteurKey,
        name: auteur ? (isKo ? auteur.name : auteur.nameEn) : auteurKey,
      });
    },
    autoConsume: false,
  });

  // Handlers
  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setVideoFile(file);
      setVideoUrl(""); // Clear URL if file is selected
    }
  }, []);

  const handleStartAnalysis = useCallback(async () => {
    if (!videoFile && !videoUrl.trim()) {
      setError(labels.errorNoInput);
      return;
    }

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(creditCost)) {
      setShowCreditModal(true);
      return;
    }

    startTransition(async () => {
      setLoading(true);
      setPhase("processing");
      setError(null);

      try {
        // Step 1: VPE (Video Parsing)
        setProcessingStep("vpe");

        // In a real implementation, this would call the actual VPE endpoint
        // For now, we simulate the combined analysis
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Step 2: AD (Aesthetic Director)
        setProcessingStep("ad");
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Combined result
        const analysisResult: UnifiedAnalysisResult = {
          logic_vector: {
            shot_count: 12,
            dominant_style: "cinematic",
            color_palette: ["#1a1a2e", "#16213e", "#0f3460", "#e94560"],
            mood_keywords: ["dramatic", "mysterious", "emotional"],
            pacing: "medium-slow",
            technical_notes: "High contrast lighting, shallow depth of field",
          },
          aesthetic_guidelines: {
            visual_style: selectedAuteur ? `${selectedAuteur} inspired` : "Contemporary cinematic",
            composition: "Rule of thirds, leading lines",
            lighting: "Chiaroscuro with selective color grading",
            camera_work: "Slow dollies, static close-ups",
            color_grading: "Teal and orange with desaturated midtones",
          },
          auteur_influence: selectedAuteur ? {
            key: selectedAuteur,
            name: MASTER_AUTEURS.find(a => a.key === selectedAuteur)?.name || selectedAuteur,
            signature_elements: ["Visual metaphor", "Long takes", "Symmetry"],
          } : undefined,
          evidence_refs: [
            "db:vpe:analysis:unified",
            selectedAuteur ? `rag:auteur:${selectedAuteur}` : "rag:style:contemporary",
          ],
          confidence: 0.85,
          trace_id: `analysis-${Date.now()}`,
        };

        setLocalResult(analysisResult);
        setResult(analysisResult);
        setPhase("complete");

        // Update chain context
        if (chainContext) {
          // Set both VPE and AD outputs for compatibility
          chainContext.setChainData("vpe", analysisResult.logic_vector || {}, "VPE 분석 완료");
          chainContext.setChainData("ad", analysisResult.aesthetic_guidelines || {}, "AD 분석 완료");
        }

        if (!byokKey && creditCtx) {
          void creditCtx.refresh();
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Analysis failed");
        setPhase("input");
      } finally {
        setLoading(false);
        setProcessingStep(null);
      }
    });
  }, [videoFile, videoUrl, selectedAuteur, byokKey, creditCtx, creditCost, setLoading, setResult, chainContext, startTransition, labels]);

  const handleReset = useCallback(() => {
    setPhase("input");
    setVideoFile(null);
    setVideoUrl("");
    setLocalResult(null);
    setError(null);
  }, []);

  const handleExport = useCallback(() => {
    if (result) {
      exportJSON(result, `unified-analysis-${Date.now()}.json`);
    }
  }, [result, exportJSON]);

  // ========================================================================
  // Render: Input Phase
  // ========================================================================

  const renderInputPhase = () => (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="max-w-lg w-full space-y-6">
        {/* Header */}
        <div className="text-center mb-8">
          <div className={`w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center`}>
            <Film className="w-10 h-10 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-[var(--fg-0)]">{labels.title}</h2>
          <p className="text-sm text-[var(--fg-muted)] mt-2">{labels.subtitle}</p>
        </div>

        {/* DNA Context Banner */}
        {auteurContext && (
          <DNAContextBanner
            cardType="master"
            cardName={auteurContext.name}
            onDismiss={() => {
              setAuteurContext(null);
              setSelectedAuteur("");
            }}
            className="mb-4"
          />
        )}

        {/* Video Input */}
        <div className="space-y-4">
          <label className="text-xs font-bold text-[var(--fg-muted)] uppercase">
            {labels.videoInput}
          </label>

          {/* File Upload */}
          <label className="block p-6 border-2 border-dashed border-[var(--border-subtle)] rounded-xl cursor-pointer hover:border-blue-500/50 transition-colors bg-[var(--surface-1)]">
            <input
              type="file"
              accept="video/*"
              onChange={handleFileChange}
              className="hidden"
            />
            <div className="flex flex-col items-center gap-2">
              <Upload className="w-8 h-8 text-[var(--fg-muted)]" />
              <span className="text-sm text-[var(--fg-muted)]">
                {videoFile ? videoFile.name : labels.uploadVideo}
              </span>
            </div>
          </label>

          {/* URL Input */}
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-[var(--fg-subtle)]">
              {labels.orEnterUrl}
            </span>
            <input
              type="url"
              value={videoUrl}
              onChange={(e) => {
                setVideoUrl(e.target.value);
                if (e.target.value) setVideoFile(null);
              }}
              placeholder={labels.urlPlaceholder}
              className="w-full pt-6 pb-2 px-3 bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-xl text-[var(--fg-0)] placeholder:text-[var(--fg-subtle)] focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Auteur Selection - hidden in basic mode */}
        {disclosureLevel !== "basic" && (
          <div className="space-y-2">
            <label className="text-xs font-bold text-[var(--fg-muted)] uppercase">
              {labels.selectAuteur}
            </label>
            <p className="text-xs text-[var(--fg-subtle)]">{labels.auteurHint}</p>
            <div className="grid grid-cols-3 gap-2 max-h-48 overflow-y-auto">
              {MASTER_AUTEURS.slice(0, disclosureLevel === "advanced" ? 12 : 9).map((auteur) => (
                <button
                  key={auteur.key}
                  onClick={() => setSelectedAuteur(auteur.key === selectedAuteur ? "" : auteur.key)}
                  className={`p-2 rounded-lg border text-center transition-all ${
                    selectedAuteur === auteur.key
                      ? "bg-blue-500/20 border-blue-500/50"
                      : "bg-[var(--surface-1)] border-[var(--border-subtle)] hover:bg-[var(--surface-2)]"
                  }`}
                >
                  {/* Use thumbnail image instead of emoji */}
                  <div className="w-8 h-8 mx-auto rounded-full overflow-hidden bg-[var(--surface-2)]">
                    <img
                      src={auteur.thumbnail}
                      alt={auteur.name}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                  </div>
                  <p className="text-xs text-[var(--fg-muted)] mt-1 truncate">
                    {isKo ? auteur.name : auteur.nameEn}
                  </p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Start Button */}
        <button
          onClick={handleStartAnalysis}
          disabled={isPending || (!videoFile && !videoUrl.trim())}
          className="w-full py-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-medium rounded-xl transition-all disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <Sparkles className="w-5 h-5" />
          {labels.startAnalysis}
          <ArrowRight className="w-5 h-5" />
        </button>

        {error && (
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
      </div>
    </div>
  );

  // ========================================================================
  // Render: Processing Phase
  // ========================================================================

  const renderProcessingPhase = () => (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="max-w-md w-full space-y-8 text-center">
        <div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center animate-pulse">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
        </div>

        <div className="space-y-2">
          <h3 className="text-xl font-bold text-[var(--fg-0)]">{labels.analyzing}</h3>
          <p className="text-sm text-[var(--fg-muted)]">
            {processingStep === "vpe" ? labels.parsingVideo : labels.applyingAesthetic}
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex justify-center gap-4">
          <div className={`flex items-center gap-2 ${processingStep === "vpe" || processingStep === "ad" || phase === "complete" ? "text-blue-500" : "text-[var(--fg-subtle)]"}`}>
            <Video className="w-5 h-5" />
            <span className="text-sm">VPE</span>
            {(processingStep === "ad" || phase === "complete") && <CheckCircle className="w-4 h-4 text-green-500" />}
          </div>
          <div className={`flex items-center gap-2 ${processingStep === "ad" || phase === "complete" ? "text-purple-500" : "text-[var(--fg-subtle)]"}`}>
            <Palette className="w-5 h-5" />
            <span className="text-sm">AD</span>
            {phase === "complete" && <CheckCircle className="w-4 h-4 text-green-500" />}
          </div>
        </div>
      </div>
    </div>
  );

  // ========================================================================
  // Render: Complete Phase
  // ========================================================================

  const renderCompletePhase = () => (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {/* Success Header */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-green-500/10 to-blue-500/10 border border-green-500/20">
        <div className="flex items-center gap-3">
          <CheckCircle className="w-6 h-6 text-green-500" />
          <span className="font-bold text-[var(--fg-0)]">{labels.analysisComplete}</span>
        </div>
      </div>

      {/* VPE Result */}
      {result?.logic_vector && (
        <div className="p-4 rounded-xl bg-[var(--surface-1)] border border-[var(--border-subtle)] space-y-3">
          <div className="flex items-center gap-2">
            <Video className="w-5 h-5 text-blue-500" />
            <h4 className="font-medium text-[var(--fg-0)]">{labels.vpeResult}</h4>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-[var(--fg-subtle)]">Shots:</span>
              <span className="ml-2 text-[var(--fg-0)]">{result.logic_vector.shot_count}</span>
            </div>
            <div>
              <span className="text-[var(--fg-subtle)]">Style:</span>
              <span className="ml-2 text-[var(--fg-0)]">{result.logic_vector.dominant_style}</span>
            </div>
            <div>
              <span className="text-[var(--fg-subtle)]">Pacing:</span>
              <span className="ml-2 text-[var(--fg-0)]">{result.logic_vector.pacing}</span>
            </div>
          </div>
          {/* Color Palette */}
          <div className="flex gap-2">
            {result.logic_vector.color_palette.map((color, i) => (
              <div
                key={i}
                className="w-8 h-8 rounded-lg border border-white/10"
                style={{ backgroundColor: color }}
                title={color}
              />
            ))}
          </div>
          {/* Mood Keywords */}
          <div className="flex flex-wrap gap-1">
            {result.logic_vector.mood_keywords.map((keyword, i) => (
              <span
                key={i}
                className="px-2 py-0.5 text-xs bg-blue-500/10 text-blue-400 rounded-full"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* AD Result */}
      {result?.aesthetic_guidelines && (
        <div className="p-4 rounded-xl bg-[var(--surface-1)] border border-[var(--border-subtle)] space-y-3">
          <div className="flex items-center gap-2">
            <Palette className="w-5 h-5 text-purple-500" />
            <h4 className="font-medium text-[var(--fg-0)]">{labels.adResult}</h4>
          </div>
          <div className="space-y-2 text-sm">
            <p><span className="text-[var(--fg-subtle)]">Style:</span> <span className="text-[var(--fg-0)]">{result.aesthetic_guidelines.visual_style}</span></p>
            <p><span className="text-[var(--fg-subtle)]">Lighting:</span> <span className="text-[var(--fg-0)]">{result.aesthetic_guidelines.lighting}</span></p>
            <p><span className="text-[var(--fg-subtle)]">Camera:</span> <span className="text-[var(--fg-0)]">{result.aesthetic_guidelines.camera_work}</span></p>
          </div>
          {/* Auteur Influence */}
          {result.auteur_influence && (
            <div className="mt-3 p-2 rounded-lg bg-purple-500/10 border border-purple-500/20">
              <p className="text-xs text-purple-400">
                <span className="font-medium">{result.auteur_influence.name}</span> influence applied
              </p>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleExport}
          className="flex-1 py-3 bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-xl flex items-center justify-center gap-2 text-sm hover:bg-[var(--surface-2)] transition-all"
        >
          <Download className="w-4 h-4" />
          {labels.exportResult}
        </button>
        <button
          onClick={handleReset}
          className="flex-1 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-xl flex items-center justify-center gap-2 text-sm transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          {labels.newAnalysis}
        </button>
      </div>

      {/* Next Navigation */}
      <div className="mt-4">
        <DimensionPanel.NextNav currentDimension="analysis" />
      </div>
    </div>
  );

  // ========================================================================
  // Main Render
  // ========================================================================

  return (
    <>
      <DimensionPanel.Header title={labels.title} />

      <div className="flex flex-1 min-h-0">
        {/* Sidebar - only in advanced mode */}
        {disclosureLevel === "advanced" && (
          <DimensionPanel.Sidebar>
            <DimensionPanel.Select
              label={isKo ? "분석 품질" : "Analysis Quality"}
              value="balanced"
              onChange={() => {}}
              options={[
                { value: "fast", label: isKo ? "빠름" : "Fast" },
                { value: "balanced", label: isKo ? "균형" : "Balanced" },
                { value: "quality", label: isKo ? "고품질" : "High Quality" },
              ]}
            />

            {/* Credit Info */}
            <div className="mt-4 p-3 rounded-lg bg-[var(--surface-1)] border border-[var(--border-subtle)]">
              <p className="text-xs text-[var(--fg-subtle)]">
                {isKo ? "크레딧 비용" : "Credit Cost"}: <span className="text-[var(--fg-0)] font-medium">{creditCost}</span>
              </p>
              <p className="text-[10px] text-[var(--fg-subtle)] mt-1">
                VPE(50) + AD(10)
              </p>
            </div>
          </DimensionPanel.Sidebar>
        )}

        <DimensionPanel.Content>
          {phase === "input" && renderInputPhase()}
          {phase === "processing" && renderProcessingPhase()}
          {phase === "complete" && renderCompletePhase()}
        </DimensionPanel.Content>
      </div>

      <InsufficientCreditsModal
        isOpen={showCreditModal}
        onClose={() => setShowCreditModal(false)}
        requiredCredits={creditCost}
        currentBalance={creditCtx?.balance ?? 0}
        onRetry={handleStartAnalysis}
      />
    </>
  );
}

// ============================================================================
// Export
// ============================================================================

export default function UnifiedAnalysisPanel({
  disclosureLevel = "intermediate",
}: UnifiedAnalysisPanelProps = {}) {
  return (
    <DimensionPanel dimensionCode={DIMENSION_CODE}>
      <UnifiedAnalysisContent disclosureLevel={disclosureLevel} />
    </DimensionPanel>
  );
}
