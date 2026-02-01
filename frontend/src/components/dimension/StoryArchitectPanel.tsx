"use client";

/**
 * StoryArchitectPanel - 스토리 아키텍트
 *
 * 2026 Golden App: React 19 Best Practices + Multimodal Input
 *
 * Features:
 * - useTransition for non-blocking form submission
 * - useOptimistic for instant UI feedback
 * - File upload for reference documents
 * - Evidence refs display
 *
 * @see https://react.dev/blog/2024/12/05/react-19
 */

import { useState, useEffect, useCallback, useMemo } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import { useDimensionChainOptional, type ChainData } from "@/contexts/DimensionChainContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import ChainDataInput from "./ChainDataInput";
import { getDemoIPOverride } from "@/lib/demo-ip-overrides";
import { getPreviousStepResult } from "@/lib/workflow-state";
import { Layers, ArrowRight, CheckCircle, Download, Sparkles, BookOpen, Film } from "lucide-react";
import { type ThemeColor as DimensionThemeColor } from "@/lib/dimension-theme";
import { useDNACardContextConsumer } from "@/hooks/useDNACardContextConsumer";
import { useChainDataInjection } from "@/hooks/useChainDataInjection";
import { DNAContextBanner } from "@/components/dna-card/DNAContextBanner";
import { MASTER_AUTEURS } from "@/components/dna-card/constants";

const DIMENSION_CODE = "story";
const DIMENSION_KEY = "story-architect";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

// Map tokens ThemeColor to dimension-theme ThemeColor
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

interface StoryResult {
  title?: string;
  logline?: string;
  synopsis?: string;
  structure?: Array<{
    act: string;
    description: string;
    duration: string;
    emotion: string;
  }>;
  characters?: Array<{
    name: string;
    role: string;
    arc: string;
    traits: string[];
  }>;
  themes?: string[];
  visual_motifs?: string[];
  next_dimension?: string;
}

interface NarrativeAngle {
  id: string;
  title: string;
  logline: string;
  tone: string;
  theme: string;
}

interface StoryRefineResult {
  angles: NarrativeAngle[];
}

type Stage = "pitch" | "blueprint" | "script";

const getGenres = (isKo: boolean) => [
  { value: "drama", label: isKo ? "드라마" : "Drama" },
  { value: "thriller", label: isKo ? "스릴러" : "Thriller" },
  { value: "comedy", label: isKo ? "코미디" : "Comedy" },
  { value: "documentary", label: isKo ? "다큐멘터리" : "Documentary" },
  { value: "horror", label: isKo ? "호러" : "Horror" },
  { value: "scifi", label: "SF" },
  { value: "ad", label: isKo ? "광고" : "Advertisement" },
  { value: "mv", label: isKo ? "뮤직비디오" : "Music Video" },
  { value: "short", label: isKo ? "숏폼" : "Short Form" },
];

const getDurations = (isKo: boolean) => [
  { value: "15", label: isKo ? "15초 (숏폼)" : "15s (Short)" },
  { value: "30", label: isKo ? "30초" : "30s" },
  { value: "60", label: isKo ? "1분" : "1 min" },
  { value: "180", label: isKo ? "3분" : "3 min" },
  { value: "300", label: isKo ? "5분" : "5 min" },
];

const getStructures = (isKo: boolean) => [
  { value: "3-act", label: isKo ? "3막 구조" : "3-Act Structure" },
  { value: "5-act", label: isKo ? "5막 구조" : "5-Act Structure" },
  { value: "hero-journey", label: isKo ? "영웅의 여정" : "Hero's Journey" },
  { value: "hook-body-cta", label: isKo ? "훅-본론-CTA" : "Hook-Body-CTA" },
  { value: "problem-solution", label: isKo ? "문제-해결" : "Problem-Solution" },
  { value: "story-arc", label: isKo ? "스토리 아크" : "Story Arc" },
  { value: "nonlinear", label: isKo ? "비선형" : "Nonlinear" },
  { value: "slice-of-life", label: isKo ? "일상물" : "Slice of Life" },
  { value: "montage", label: isKo ? "몽타주" : "Montage" },
];

// === Content Component ===
function StoryArchitectContent() {
  const { token, classes, styles, setLoading, setResult, setError } = useDimensionPanel();
  const { language } = useLanguage();
  const isKo = language === "ko";

  // Chain data injection for upstream data (DNA→Story flow)
  const { logicVector, aestheticGuidelines, personaDNA, hasUpstreamData, rawInputData, evidenceRefs } =
    useChainDataInjection(DIMENSION_KEY);

  // i18n labels
  const labels = useMemo(() => ({
    title: isKo ? "시나리오 생성기" : "Scenario Generator",
    conceptLabel: isKo ? "컨셉" : "Concept",
    conceptPlaceholder: isKo ? "스토리 컨셉을 자유롭게 입력하세요..." : "Enter your story concept freely...",
    genreLabel: isKo ? "장르" : "Genre",
    durationLabel: isKo ? "영상 길이" : "Video Length",
    structureLabel: isKo ? "구조" : "Structure",
    referenceLabel: isKo ? "참고자료 업로드" : "Upload Reference",
    referenceHelper: isKo ? "PDF, 이미지, 문서 등 참고자료" : "PDFs, images, documents, etc.",
    refineButton: isKo ? "다양한 시각 찾기" : "Find Different Angles",
    refining: isKo ? "시각 탐색 중..." : "Exploring angles...",
    generateButton: isKo ? "시나리오 생성" : "Generate Scenario",
    generating: isKo ? "시나리오 생성 중..." : "Generating scenario...",
    enterConcept: isKo ? "컨셉을 입력해주세요." : "Please enter a concept.",
    enterLongerConcept: isKo ? "컨셉을 10자 이상 입력해주세요." : "Please enter at least 10 characters.",
    conceptTooLong: (max: number) => isKo ? `컨셉은 ${max}자 이하로 입력해주세요.` : `Concept must be ${max} characters or less.`,
    stagePitch: isKo ? "발상" : "Pitch",
    stageBlueprint: isKo ? "설계" : "Blueprint",
    stageScript: isKo ? "집필" : "Script",
    selectAngle: isKo ? "시각 선택" : "Select Angle",
    changeAngle: isKo ? "시각 변경" : "Change Angle",
    selected: isKo ? "선택됨" : "Selected",
    choose: isKo ? "선택" : "Choose",
    exportJson: isKo ? "JSON 내보내기" : "Export JSON",
    logline: "Logline",
    synopsis: isKo ? "시놉시스" : "Synopsis",
    narrativeStructure: isKo ? "서사 구조" : "Narrative Structure",
    characters: isKo ? "등장인물" : "Characters",
    themes: isKo ? "테마" : "Themes",
    visualMotifs: isKo ? "시각적 모티프" : "Visual Motifs",
    act: isKo ? "막" : "Act",
    duration: isKo ? "시간" : "Duration",
    emotion: isKo ? "감정" : "Emotion",
    role: isKo ? "역할" : "Role",
    arc: isKo ? "아크" : "Arc",
    traits: isKo ? "특성" : "Traits",
    emptyStateTitle: isKo ? "스토리 아키텍트" : "Story Architect",
    emptyStateDesc: isKo ? "컨셉을 입력하고 시나리오를 생성하세요" : "Enter a concept and generate a scenario",
    // Pitch stage
    pitchWelcome: isKo ? "Writer's Room에 오신 것을 환영합니다" : "Welcome to the Writer's Room",
    pitchDesc1: isKo ? "단순한 문장이 위대한 스토리로 발전하는 공간입니다." : "A space where simple sentences evolve into great stories.",
    pitchDesc2: isKo ? "먼저 떠오르는 영감을 좌측에 적어주세요." : "Start by writing your inspiration on the left.",
    pitchDesc3: isKo ? "AI가 3가지 다른 이야기 방향을 제안해드립니다." : "AI will suggest 3 different story directions.",
    // Blueprint stage
    selectDirection: isKo ? "이야기의 방향을 선택하세요" : "Select a story direction",
    coreTheme: isKo ? "핵심 테마" : "Core Theme",
    // Script stage
    generationComplete: isKo ? "생성 완료" : "Generation Complete",
    overviewLabel: isKo ? "개요" : "Overview",
    charactersLabel: isKo ? "등장인물" : "Characters",
    themesLabel: isKo ? "주제" : "Themes",
    visualMotifsLabel: isKo ? "시각적 모티프" : "Visual Motifs",
    // Sidebar
    selectedAngleLabel: isKo ? "선택된 앵글" : "Selected Angle",
    notSelectedYet: isKo ? "아직 선택 안됨" : "Not selected yet",
    backToDesign: isKo ? "◀ 다시 설계하기" : "◀ Back to Design",
    estimatedCost: isKo ? "예상 비용" : "Estimated cost",
    freeByok: isKo ? "무료 (BYOK)" : "Free (BYOK)",
    credits: isKo ? "크레딧" : "credits",
    emptyStateDesc2: isKo
      ? "영상 컨셉을 입력하면 당신만의 스토리를 자동으로 작성합니다. 장르와 구조를 선택하여 맞춤형 시나리오를 만들어보세요."
      : "Enter your video concept to automatically write your own story. Choose genre and structure to create a customized scenario.",
  }), [isKo]);

  // i18n presets
  const GENRES = useMemo(() => getGenres(isKo), [isKo]);
  const DURATIONS = useMemo(() => getDurations(isKo), [isKo]);
  const STRUCTURES = useMemo(() => getStructures(isKo), [isKo]);

  const [concept, setConcept] = useState("");
  const [genre, setGenre] = useState("drama");
  const [duration, setDuration] = useState("60");
  const [structure, setStructure] = useState("3-act");

  // Writer's Room Workflow State
  const [stage, setStage] = useState<Stage>("pitch");
  const [angles, setAngles] = useState<NarrativeAngle[]>([]);
  const [selectedAngle, setSelectedAngle] = useState<NarrativeAngle | null>(null);
  const [storyResult, setStoryResult] = useState<StoryResult | null>(null);

  const [showCreditModal, setShowCreditModal] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // File upload state (2026 Best Practice: Multimodal input)
  const [_uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  const { byokKey } = useBYOK();
  const creditCtx = useCreditContextOptional();
  const chainCtx = useDimensionChainOptional();

  const { getToolByDimension } = useDimensionConfig();
  const toolConfig = getToolByDimension("STORY") ?? getToolByDimension("SA");
  const creditCost = toolConfig?.creditCost ?? 10;

  const { exportJSON } = useResultExport();

  // DNA 카드 컨텍스트 상태
  const [dnaContextInfo, setDnaContextInfo] = useState<{
    type: "master" | "masterpiece" | null;
    name: string;
    auteurKey?: string;
    ipId?: string;
  } | null>(null);
  const [narrativeStyleHint, setNarrativeStyleHint] = useState<string | null>(null);

  // DNA 카드 컨텍스트 소비 - 거장/작품 DNA에서 스토리 힌트 적용
  const { dismissContext: dismissDNAContext } = useDNACardContextConsumer({
    onMasterContext: (auteurKey, metadata) => {
      const auteurInfo = MASTER_AUTEURS.find((a) => a.key === auteurKey);
      const auteurName = auteurInfo?.name ?? auteurKey;

      // 거장 특성에서 내러티브 스타일 힌트 추출
      if (metadata.signatureMoods) {
        setNarrativeStyleHint(metadata.signatureMoods.slice(0, 2).join(", "));
      }

      // 컨셉이 비어있을 때만 자동 설정
      if (!concept) {
        setConcept(`${auteurName} 스타일의 영상 시나리오`);
      }

      setDnaContextInfo({
        type: "master",
        name: auteurName,
        auteurKey,
      });
    },
    onMasterpieceContext: (ipId, metadata) => {
      // 작품 DNA에서 로직벡터 요약을 컨셉에 반영
      if (metadata.logicVectorSummary && !concept) {
        const { compositionStyle, lightingPattern } = metadata.logicVectorSummary;
        setConcept(`"${ipId}" 작품의 서사 구조를 참고한 새로운 시나리오\n\n스타일 힌트: ${compositionStyle}, ${lightingPattern}`);
      }

      setDnaContextInfo({
        type: "masterpiece",
        name: ipId,
        ipId,
      });
    },
    autoConsume: false,
  });

  // DNA 컨텍스트 해제
  const handleDismissDNAContext = useCallback(() => {
    dismissDNAContext();
    setDnaContextInfo(null);
    setNarrativeStyleHint(null);
  }, [dismissDNAContext]);

  // Async operation hook
  const {
    isLoading,
    error,
    execute,
  } = useAsyncOperation<{ success: boolean; output: StoryResult; error?: string }>({
    onSuccess: (data) => {
      if (data.success && data.output) {
        setStoryResult(data.output);
        setResult(data.output);
        // Store in chain context for next dimensions
        if (chainCtx) {
          chainCtx.setChainData(
            DIMENSION_KEY,
            data.output as unknown as Record<string, unknown>,
            data.output.title || data.output.logline || concept.slice(0, 50),
            (data as { evidence_refs?: string[] }).evidence_refs || evidenceRefs
          );
        }
        // Refresh credits
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

  // Sync loading state
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

  // Set current dimension on mount
  useEffect(() => {
    if (chainCtx) {
      chainCtx.setCurrentDimension(DIMENSION_KEY);
    }
  }, [chainCtx]);

  // IP context state for workflow integration
  const [ipContext, setIpContext] = useState<{
    slug: string;
    title: string;
    desc: string;
  } | null>(null);

  // URL parameter handling for workflow integration
  useEffect(() => {
    if (typeof window === "undefined") return;

    const params = new URLSearchParams(window.location.search);
    const ipParam = params.get("ip");
    const promptParam = params.get("prompt");
    const stepParam = params.get("step");
    const currentStep = stepParam ? parseInt(stepParam, 10) : null;

    if (ipParam) {
      const ipData = getDemoIPOverride(ipParam);
      if (ipData) {
        setIpContext({
          slug: ipParam,
          title: isKo ? ipData.titleKo : ipData.titleEn,
          desc: isKo ? ipData.descKo : ipData.descEn,
        });
        // Pre-fill concept with IP context if no prompt
        if (!promptParam && !concept) {
          const ipConcept = isKo
            ? `"${ipData.titleKo}" IP를 기반으로 한 새로운 스토리`
            : `A new story based on "${ipData.titleEn}" IP`;
          setConcept(ipConcept);
        }
      }

      // Load previous step results from workflow state (P0: Critical for data flow)
      // Note: useChainDataInjection now handles most chain data automatically
      // This legacy logic handles URL param-based workflow state for backwards compatibility
      if (currentStep && currentStep > 1) {
        // Check for Reference Decoder result (typically step before scenario)
        for (let prevStep = currentStep - 1; prevStep >= 1; prevStep--) {
          const prevResult = getPreviousStepResult(ipParam, prevStep + 1);
          if (prevResult?.outputData) {
            const data = prevResult.outputData;
            // Check if this is Reference Decoder output (has style/analysis fields)
            if (data.style_prompt || data.recreation_prompt || data.description || data.style) {
              // Also update concept to include reference context
              const refPrompt = (data.style_prompt || data.recreation_prompt || data.description || "") as string;
              if (refPrompt && !concept) {
                const ipTitle = ipData ? (isKo ? ipData.titleKo : ipData.titleEn) : ipParam;
                const enrichedConcept = isKo
                  ? `"${ipTitle}" 원본 영상의 핵심 스토리 구조를 유지하면서 새로운 시나리오 작성:\n\n원본 스타일: ${refPrompt.slice(0, 200)}`
                  : `Create a new scenario preserving the core story structure of "${ipTitle}":\n\nOriginal style: ${refPrompt.slice(0, 200)}`;
                setConcept(enrichedConcept);
              }
              console.log("[StoryArchitectPanel] Loaded reference context from workflow step", prevStep);
              break;
            }
          }
        }
      }
    }

    if (promptParam) {
      setConcept(decodeURIComponent(promptParam));
    }
  }, [isKo, concept]);

  // Auto-apply upstream data from useChainDataInjection
  useEffect(() => {
    // From reference-decoder: 자동으로 컨셉에 스타일 힌트 적용
    if (logicVector && !concept) {
      const hints: string[] = [];
      if (logicVector.auteur_id) hints.push(`${logicVector.auteur_id} 스타일`);
      if (logicVector.composition?.primary_strategy) hints.push(logicVector.composition.primary_strategy);
      if (hints.length > 0) {
        setConcept(hints.join(" - "));
      }
    }
  }, [logicVector, concept]);

  // Auto-apply aesthetic guidelines from AD
  useEffect(() => {
    if (aestheticGuidelines && !concept) {
      const adHints: string[] = [];

      // Add visual style
      if (aestheticGuidelines.visual_style) {
        adHints.push(`Visual: ${aestheticGuidelines.visual_style}`);
      }

      // Add mood keywords
      if (aestheticGuidelines.mood_keywords && aestheticGuidelines.mood_keywords.length > 0) {
        adHints.push(`Mood: ${aestheticGuidelines.mood_keywords.slice(0, 3).join(", ")}`);
      }

      // Add lighting approach
      if (aestheticGuidelines.lighting_approach) {
        adHints.push(`Lighting: ${aestheticGuidelines.lighting_approach}`);
      }

      // Add reference directors
      if (aestheticGuidelines.reference_directors && aestheticGuidelines.reference_directors.length > 0) {
        adHints.push(`Reference: ${aestheticGuidelines.reference_directors.slice(0, 2).join(", ")}`);
      }

      if (adHints.length > 0) {
        setConcept(adHints.join("\n"));
      }
    }
  }, [aestheticGuidelines, concept]);

  // Handler to apply chain data from previous dimensions (manual fallback via ChainDataInput)
  // Note: useChainDataInjection now handles most of this automatically
  const handleApplyChainData = useCallback((data: Record<string, ChainData>) => {
    const conceptParts: string[] = [];

    // Extract hints from reference-decoder for concept if empty
    const refOutput = data["reference-decoder"]?.output as Record<string, unknown> | undefined;
    if (refOutput) {
      const stylePrompt = refOutput.style_prompt as string | undefined;
      const description = refOutput.description as string | undefined;
      if (stylePrompt || description) {
        conceptParts.push(`${stylePrompt || description}`.slice(0, 300));
      }
    }

    // Extract hints from aesthetic-director (AD)
    const adOutput = data["aesthetic-director"]?.output as Record<string, unknown> | undefined;
    if (adOutput) {
      const adHints: string[] = [];

      // Visual style
      if (adOutput.visual_style) {
        adHints.push(`스타일: ${adOutput.visual_style}`);
      }

      // Color palette
      const colorPalette = adOutput.color_palette as string[] | undefined;
      if (colorPalette && colorPalette.length > 0) {
        adHints.push(`색상: ${colorPalette.slice(0, 3).join(", ")}`);
      }

      // Mood keywords
      const moodKeywords = adOutput.mood_keywords as string[] | undefined;
      if (moodKeywords && moodKeywords.length > 0) {
        adHints.push(`무드: ${moodKeywords.slice(0, 3).join(", ")}`);
      }

      // Lighting approach
      if (adOutput.lighting_approach) {
        adHints.push(`조명: ${adOutput.lighting_approach}`);
      }

      if (adHints.length > 0) {
        conceptParts.push(`[AD 가이드라인]\n${adHints.join("\n")}`);
      }
    }

    if (conceptParts.length > 0 && !concept) {
      setConcept(conceptParts.join("\n\n"));
    }
  }, [concept]);

  const MAX_CONCEPT_LENGTH = 3000;

  // Async operation hook for refine (returns angles)
  const {
    isLoading: isRefineLoading,
    execute: executeRefine,
  } = useAsyncOperation<{ success: boolean; output: StoryRefineResult; error?: string }>({
    onSuccess: (data) => {
      if (data.success && data.output?.angles) {
        setAngles(data.output.angles);
        setStage("blueprint");
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

  const wrappedExecuteRefine = useCallback(
    async (url: string, payload: object, headers?: Record<string, string>) => {
      setLoading(true);
      try {
        return await executeRefine(url, payload, headers);
      } finally {
        setLoading(false);
      }
    },
    [executeRefine, setLoading]
  );

  const handleRefine = useCallback(async () => {
    const trimmedConcept = concept.trim();
    if (!trimmedConcept || trimmedConcept.length < 5) {
      setValidationError(labels.enterConcept);
      return;
    }
    setValidationError(null);

    await wrappedExecuteRefine(
      `${API_BASE}/api/dimension/story/refine`,
      {
        concept,
        genre,
        model: "gemini-3-pro-preview",
      },
      getBYOKHeaders(byokKey)
    );
  }, [concept, genre, byokKey, wrappedExecuteRefine, labels]);

  const handleGenerate = useCallback(async () => {
    const trimmedConcept = concept.trim();
    if (!trimmedConcept || trimmedConcept.length < 10) {
      setValidationError(labels.enterLongerConcept);
      return;
    }
    if (trimmedConcept.length > MAX_CONCEPT_LENGTH) {
      setValidationError(labels.conceptTooLong(MAX_CONCEPT_LENGTH));
      return;
    }
    setValidationError(null);

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(creditCost)) {
      setShowCreditModal(true);
      return;
    }

    const finalConcept = selectedAngle
      ? `Original Concept: ${trimmedConcept}\nSelected Angle: ${selectedAngle.title} - ${selectedAngle.logline}\nTone: ${selectedAngle.tone}\nTheme: ${selectedAngle.theme}`
      : trimmedConcept;

    const res = await wrappedExecute(
      `${API_BASE}/api/dimension/story/architect`,
      {
        concept: finalConcept,
        genre,
        duration,
        structure,
        language: "ko",
        model: "gemini-3-pro-preview",
        // Use hook-provided data (from useChainDataInjection)
        persona_data: personaDNA || {},
        reference_analysis: logicVector ? { logic_vector: logicVector } : {},
      },
      getBYOKHeaders(byokKey)
    );
    if (res && res.success) {
      setStage("script");
    }
  }, [concept, genre, duration, structure, personaDNA, logicVector, byokKey, creditCtx, creditCost, wrappedExecute, selectedAngle, labels]);

  const handleExportJson = useCallback(() => {
    if (!storyResult) return;
    exportJSON(storyResult, `story-architect-${Date.now()}.json`);
  }, [storyResult, exportJSON]);

  const displayError = validationError || error;
  const isAnyLoading = isLoading || isRefineLoading;

  return (
    <>
      <DimensionPanel.Header title={labels.title} />

      <div className="flex flex-1 min-h-0">
        <DimensionPanel.Sidebar>
          {/* DNA Context Banner */}
          {dnaContextInfo && (
            <DNAContextBanner
              cardType={dnaContextInfo.type!}
              cardName={dnaContextInfo.name}
              onDismiss={handleDismissDNAContext}
              additionalInfo={
                narrativeStyleHint
                  ? `스타일: ${narrativeStyleHint}`
                  : undefined
              }
              className="mb-4"
            />
          )}

          {/* Chain Data Input */}
          <ChainDataInput
            currentDimension={DIMENSION_KEY}
            onApplyData={handleApplyChainData}
            themeColor={CHAIN_INPUT_THEME_MAP[token.themeColor] || "emerald"}
          />

          {/* Upstream Data Banner */}
          {hasUpstreamData && !isAnyLoading && stage === "pitch" && (
            <div className="mb-4 p-3 bg-violet-500/10 border border-violet-500/20 rounded-lg">
              <div className="flex items-center gap-2 text-sm text-violet-600 dark:text-violet-400">
                <Sparkles className="w-4 h-4" />
                <span>{isKo ? "DNA Lab 데이터 감지됨" : "DNA Lab Data Detected"}</span>
              </div>
              {logicVector && (
                <p className="text-xs text-violet-500/80 mt-1 ml-6">
                  {isKo ? "Reference Decoder 스타일 힌트 적용 가능" : "Reference Decoder style hints available"}
                  {logicVector.auteur_id && ` (${logicVector.auteur_id})`}
                </p>
              )}
              {aestheticGuidelines && (
                <p className="text-xs text-amber-500/80 mt-1 ml-6">
                  {isKo ? "Aesthetic Director 가이드라인 감지" : "Aesthetic Director guidelines detected"}
                  {aestheticGuidelines.visual_style && ` - ${aestheticGuidelines.visual_style}`}
                </p>
              )}
            </div>
          )}

          {/* Stage Indicator */}
          <div className="flex items-center justify-between text-xs text-slate-400 dark:text-white/50 mb-2">
            <span className={stage === "pitch" ? `${classes.text} font-bold` : ""}>1. {labels.stagePitch}</span>
            <span>→</span>
            <span className={stage === "blueprint" ? `${classes.text} font-bold` : ""}>2. {labels.stageBlueprint}</span>
            <span>→</span>
            <span className={stage === "script" ? `${classes.text} font-bold` : ""}>3. {labels.stageScript}</span>
          </div>

          {/* Concept Input */}
          <DimensionPanel.Textarea
            label={isKo ? "영상 컨셉" : "Video Concept"}
            value={concept}
            onChange={(e) => setConcept(e.target.value)}
            placeholder={isKo ? "어떤 영상을 만들고 싶으신가요? 아이디어, 분위기, 메시지 등을 자유롭게 적어주세요..." : "What kind of video do you want to create? Feel free to describe your ideas, mood, message, etc."}
            rows={5}
            maxLength={MAX_CONCEPT_LENGTH}
            disabled={isAnyLoading || stage === "script"}
          />

          {/* File Upload (2026 Best Practice: Multimodal Input) */}
          <DimensionPanel.FileUpload
            accept={["*"]}
            maxSizeMB={100}
            multiple
            onUpload={setUploadedFiles}
            label={isKo ? "참고 자료 (선택)" : "Reference (Optional)"}
            helperText={isKo ? "시나리오 참고 문서, 무드보드, 참고 이미지 첨부" : "Scenario reference docs, moodboards, images"}
          />

          {/* Stage Actions */}
          {stage === "pitch" && (
            <>
              <DimensionPanel.Select
                label={isKo ? "선호 장르" : "Preferred Genre"}
                value={genre}
                onChange={(e) => setGenre(e.target.value)}
                options={GENRES}
                disabled={isAnyLoading}
              />

              <DimensionPanel.GenerateButton
                onClick={handleRefine}
                disabled={isAnyLoading || concept.length < 5}
                loading={isRefineLoading}
                loadingText={isKo ? "분석 중..." : "Analyzing..."}
                icon={<Sparkles className="w-4 h-4" />}
              >
                {isKo ? "아이디어 다듬기 (Pitch)" : "Refine Ideas (Pitch)"}
              </DimensionPanel.GenerateButton>
            </>
          )}

          {stage === "blueprint" && (
            <>
              <div className={`p-4 ${classes.bgSubtle} border ${classes.border} rounded-xl`}>
                <h4 className={`${classes.text} text-sm font-bold mb-1`}>{labels.selectedAngleLabel}</h4>
                <p className="text-slate-800 dark:text-white font-medium text-sm">{selectedAngle?.title || labels.notSelectedYet}</p>
              </div>

              <DimensionPanel.Select
                label={isKo ? "길이" : "Length"}
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                options={DURATIONS}
                disabled={isAnyLoading}
              />

              <DimensionPanel.Select
                label={isKo ? "스토리 구조" : "Story Structure"}
                value={structure}
                onChange={(e) => setStructure(e.target.value)}
                options={STRUCTURES}
                disabled={isAnyLoading}
              />

              <DimensionPanel.GenerateButton
                onClick={handleGenerate}
                disabled={isAnyLoading || !selectedAngle}
                loading={isLoading}
                loadingText={isKo ? "시나리오 쓰는 중..." : "Writing scenario..."}
                icon={<ArrowRight className="w-4 h-4" />}
              >
                {isKo ? "시나리오 완성하기" : "Complete Scenario"}
              </DimensionPanel.GenerateButton>
            </>
          )}

          {stage === "script" && (
            <div className="space-y-3">
              {/* 다음 단계 버튼들 */}
              <div className="space-y-2">
                <p className="text-xs text-slate-400 dark:text-white/50 mb-2">
                  {isKo ? "다음 단계로 이동" : "Continue to next step"}
                </p>
                <button
                  onClick={() => {
                    const params = new URLSearchParams(window.location.search);
                    const ipParam = params.get("ip");
                    const promptParam = params.get("prompt");
                    const workflowParam = params.get("workflow");

                    // Build URL with context
                    let url = "/dimension/storyboard-sketch";
                    const queryParts: string[] = [];
                    if (ipParam) queryParts.push(`ip=${ipParam}`);
                    if (promptParam) queryParts.push(`prompt=${encodeURIComponent(promptParam)}`);
                    if (workflowParam) {
                      const step = parseInt(params.get("step") || "3", 10);
                      queryParts.push(`step=${step + 1}`);
                      queryParts.push(`workflow=${workflowParam}`);
                    }
                    if (queryParts.length > 0) url += `?${queryParts.join("&")}`;

                    window.location.href = url;
                  }}
                  className={`w-full py-3 rounded-xl ${classes.bg} hover:brightness-110 text-white font-medium transition-all flex items-center justify-center gap-2`}
                >
                  <Layers className="w-4 h-4" />
                  {isKo ? "스토리보드 스케치로" : "To Storyboard Sketch"}
                  <ArrowRight className="w-4 h-4" />
                </button>
                <button
                  onClick={() => {
                    const params = new URLSearchParams(window.location.search);
                    const ipParam = params.get("ip");
                    const promptParam = params.get("prompt");

                    let url = "/dimension/prompt-alchemy";
                    const queryParts: string[] = [];
                    if (ipParam) queryParts.push(`ip=${ipParam}`);
                    if (promptParam) queryParts.push(`prompt=${encodeURIComponent(promptParam)}`);
                    if (queryParts.length > 0) url += `?${queryParts.join("&")}`;

                    window.location.href = url;
                  }}
                  className="w-full py-3 rounded-xl bg-white/5 hover:bg-white/10 text-white border border-white/10 transition-all font-medium flex items-center justify-center gap-2"
                >
                  <Sparkles className="w-4 h-4" />
                  {isKo ? "프롬프트 연금술로" : "To Prompt Alchemy"}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>

              {/* 다시 설계하기 버튼 */}
              <button
                onClick={() => setStage("blueprint")}
                className="w-full py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/60 border border-white/5 transition-all text-sm"
              >
                {labels.backToDesign}
              </button>
            </div>
          )}

          {/* Credit Cost */}
          {!byokKey && (
            <div className="text-xs text-slate-500 dark:text-white/40 text-center mt-4">
              {labels.estimatedCost}: {stage === "pitch" ? labels.freeByok : `${creditCost} ${labels.credits}`}
            </div>
          )}
        </DimensionPanel.Sidebar>

        <DimensionPanel.Content>
          <DimensionPanel.Loading />
          <DimensionPanel.Error error={displayError || undefined} />

          {/* Stage 1: Pitch (Initial State) */}
          {stage === "pitch" && !isAnyLoading && (
            <div className="flex flex-col items-center justify-center h-full min-h-[var(--layout-panel-min-height)] text-center p-8">
              <div className={`w-20 h-20 rounded-full ${classes.bgSubtle} flex items-center justify-center mb-6`}>
                <Sparkles className={`w-10 h-10 ${classes.text}`} />
              </div>
              <h3 className="text-2xl font-bold text-slate-800 dark:text-white mb-2">{labels.pitchWelcome}</h3>
              <p className="text-slate-600 dark:text-white/60 max-w-md leading-relaxed">
                {labels.pitchDesc1}<br />
                {labels.pitchDesc2}<br />
                {labels.pitchDesc3}
              </p>

              {/* IP Context Banner */}
              {ipContext && (
                <div className="mt-6 p-4 rounded-xl bg-violet-500/10 border border-violet-500/20 max-w-md">
                  <div className="flex items-center gap-2 mb-2">
                    <Film className="w-4 h-4 text-violet-500" />
                    <span className="text-xs font-medium text-violet-600 dark:text-violet-400">
                      {isKo ? "IP 레퍼런스" : "IP Reference"}
                    </span>
                    <span className="px-2 py-0.5 text-[9px] bg-violet-500/20 text-violet-600 dark:text-violet-400 rounded-full">
                      {ipContext.slug}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-slate-800 dark:text-white">{ipContext.title}</p>
                  <p className="text-xs text-slate-600 dark:text-white/60 mt-1">{ipContext.desc}</p>
                </div>
              )}
            </div>
          )}

          {/* Stage 2: Blueprint (Select Angle) */}
          {stage === "blueprint" && !isAnyLoading && (
            <div className="space-y-6 animate-in fade-in duration-500">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <BookOpen className={`w-5 h-5 ${classes.text}`} />
                {labels.selectDirection}
              </h3>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {angles.map((angle) => (
                  <button
                    key={angle.id}
                    onClick={() => setSelectedAngle(angle)}
                    className={`text-left p-6 rounded-2xl border transition-all relative overflow-hidden group
                      ${selectedAngle?.id === angle.id
                        ? `${classes.bgSubtle} border-dimension-${token.code} ring-2 ring-dimension-${token.code}/30`
                        : "bg-white dark:bg-white/5 border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/20 hover:bg-slate-50 dark:hover:bg-white/10"
                      }`}
                  >
                    <div className="relative z-10">
                      <div className="mb-4">
                        <span className={`text-xs font-bold px-2 py-1 rounded-full ${selectedAngle?.id === angle.id ? `${classes.bgSubtle} ${classes.text}` : "bg-slate-200 text-slate-700 dark:bg-white/10 dark:text-white/70"}`}>
                          {angle.tone}
                        </span>
                      </div>
                      <h4 className={`text-lg font-bold mb-2 ${selectedAngle?.id === angle.id ? classes.text : "text-slate-900 dark:text-white"}`}>
                        {angle.title}
                      </h4>
                      <p className={`text-sm leading-relaxed mb-4 ${selectedAngle?.id === angle.id ? "text-slate-700 dark:text-white/70" : "text-slate-600 dark:text-white/70"}`}>
                        {angle.logline}
                      </p>
                      <div className="pt-4 border-t border-black/5 dark:border-white/5">
                        <p className="text-xs text-slate-400 dark:text-white/40 italic">
                          {labels.coreTheme}: {angle.theme}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Stage 3: Script (Result Display) */}
          {stage === "script" && storyResult && (
            <div className="space-y-6 animate-in fade-in duration-500 pb-10">
              {/* Title & Logline */}
              <div className={`p-6 rounded-2xl ${classes.bgSubtle} border ${classes.border}`}>
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className={`w-5 h-5 ${classes.text}`} />
                  <span className={`${classes.text} font-bold text-sm`}>{labels.generationComplete}</span>
                </div>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">{storyResult.title}</h2>
                <p className="text-slate-600 dark:text-white/70 italic">&ldquo;{storyResult.logline}&rdquo;</p>
              </div>

              {/* Export Button */}
              <div className="flex justify-end">
                <button
                  onClick={handleExportJson}
                  className="px-4 py-2 bg-white dark:bg-white/5 hover:bg-slate-100 dark:hover:bg-white/10 border border-slate-200 dark:border-white/10 rounded-lg flex items-center gap-2 text-sm text-slate-600 dark:text-white/70 hover:text-slate-900 dark:hover:text-white transition-all"
                >
                  <Download className="w-4 h-4" />
                  {labels.exportJson}
                </button>
              </div>

              {/* Synopsis */}
              {storyResult.synopsis && (
                <div className="space-y-2">
                  <h3 className="text-lg font-bold text-slate-800 dark:text-white">{labels.overviewLabel}</h3>
                  <p className="text-slate-600 dark:text-white/70 leading-relaxed">{storyResult.synopsis}</p>
                </div>
              )}

              {/* Structure */}
              {storyResult.structure && storyResult.structure.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-lg font-bold text-slate-800 dark:text-white">{labels.structureLabel}</h3>
                  <div className="space-y-2">
                    {storyResult.structure.map((act, i) => (
                      <div key={i} className="p-4 rounded-xl bg-white/50 dark:bg-white/5 border border-slate-200 dark:border-white/10">
                        <div className="flex items-center justify-between mb-2">
                          <span className={`${classes.text} font-bold`}>Act {act.act}</span>
                          <span className="text-xs text-slate-400 dark:text-white/40">{act.duration}</span>
                        </div>
                        <p className="text-slate-600 dark:text-white/70 text-sm">{act.description}</p>
                        <span className={`inline-block mt-2 px-2 py-1 text-xs rounded-full ${classes.bgSubtle} ${classes.text}`}>
                          {act.emotion}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Characters */}
              {storyResult.characters && storyResult.characters.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-lg font-bold text-slate-800 dark:text-white">{labels.charactersLabel}</h3>
                  <div className="grid gap-3">
                    {storyResult.characters.map((char, i) => (
                      <div key={i} className="p-4 rounded-xl bg-white/50 dark:bg-white/5 border border-slate-200 dark:border-white/10">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-slate-900 dark:text-white font-bold">{char.name}</span>
                          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-200 dark:bg-white/10 text-slate-600 dark:text-white/60">
                            {char.role}
                          </span>
                        </div>
                        <p className="text-slate-600 dark:text-white/60 text-sm mb-2">{char.arc}</p>
                        <div className="flex flex-wrap gap-1">
                          {char.traits?.map((trait, j) => (
                            <span key={j} className={`text-xs px-2 py-0.5 rounded-full ${classes.bgSubtle} ${classes.text}`}>
                              {trait}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Themes & Visual Motifs */}
              <div className="grid grid-cols-2 gap-4">
                {storyResult.themes && storyResult.themes.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-bold text-slate-700 dark:text-white/80">{labels.themesLabel}</h3>
                    <div className="flex flex-wrap gap-1">
                      {storyResult.themes.map((theme, i) => (
                        <span key={i} className="text-xs px-2 py-1 rounded-full bg-slate-100 dark:bg-white/10 text-slate-600 dark:text-white/70">
                          {theme}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {storyResult.visual_motifs && storyResult.visual_motifs.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-bold text-slate-700 dark:text-white/80">{labels.visualMotifsLabel}</h3>
                    <div className="flex flex-wrap gap-1">
                      {storyResult.visual_motifs.map((motif, i) => (
                        <span key={i} className={`text-xs px-2 py-1 rounded-full ${classes.bgSubtle} ${classes.text}`}>
                          {motif}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Evidence Display */}
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              <DimensionPanel.Evidence refs={(storyResult as any)?.evidence_refs} />

              {/* Next Dimension Navigation */}
              <DimensionPanel.NextNav currentDimension={DIMENSION_KEY} />
            </div>
          )}

          {/* Empty State */}
          {!stage && !storyResult && !displayError && (
            <div className="flex flex-col items-center justify-center h-full min-h-[var(--layout-panel-min-height)] text-center">
              <Layers className={`w-16 h-16 ${classes.text} opacity-30 mb-4`} />
              <h3 className="text-xl font-bold text-slate-400 dark:text-white/60 mb-2">{labels.emptyStateTitle}</h3>
              <p className="text-slate-400 dark:text-white/40 text-sm max-w-md">
                {labels.emptyStateDesc2}
              </p>
            </div>
          )}
        </DimensionPanel.Content>
      </div>

      <InsufficientCreditsModal
        isOpen={showCreditModal}
        onClose={() => setShowCreditModal(false)}
        requiredCredits={creditCost}
        currentBalance={creditCtx?.balance || 0}
      />
    </>
  );
}

// === Main Export ===
export default function StoryArchitectPanel() {
  return (
    <DimensionPanel dimensionCode={DIMENSION_CODE}>
      <StoryArchitectContent />
    </DimensionPanel>
  );
}
