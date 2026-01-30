"use client";

/**
 * UnifiedPromptPanel - Merged Prompt + System Prompt Generator
 *
 * Phase 1-3: Story Engine Step Simplification
 * Combines Prompt Alchemy and System Prompt generation into a single step.
 *
 * Features:
 * - Generates both AI video prompt and System Prompt
 * - Platform-specific optimization (VEO, Kling, Sora)
 * - Chain data flow integration (Story → Prompt/SystemPrompt → Production)
 * - React 19 useTransition for non-blocking UI
 *
 * @see docs/PANEL_DESIGN_UNITY_SPEC.md
 */

import { useState, useCallback, useEffect, useTransition } from "react";
import { Wand2, FileCode, Settings2, ChevronDown } from "lucide-react";
import { BaseMegaAppPanel } from "@/components/mega-app/panels";
import {
  useDimensionChainOptional,
  type ChainData,
} from "@/contexts/DimensionChainContext";
import ChainDataInput from "./ChainDataInput";
import { useChainDataInjection } from "@/hooks/useChainDataInjection";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// =============================================================================
// CONSTANTS
// =============================================================================

const DIMENSION_KEY = "prompt-generator"; // Chain context key

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

// Platform options (from prompt.py)
const PLATFORMS = [
  { value: "veo_31", label: "VEO 3.1", description: "대화/나레이션 중심 영상 (추천)" },
  { value: "kling_26", label: "Kling 2.6", description: "고화질 실사 + 립싱크" },
  { value: "sora_max_2pro", label: "Sora Max 2 Pro", description: "애니메이션 + 물리 시뮬레이션" },
];

const STYLES = [
  { value: "cinematic", label: "시네마틱" },
  { value: "documentary", label: "다큐멘터리" },
  { value: "commercial", label: "광고/커머셜" },
  { value: "artistic", label: "아트/실험" },
  { value: "vlog", label: "브이로그" },
];

const DURATIONS = [
  { value: 8, label: "8초 (기본)" },
  { value: 15, label: "15초" },
  { value: 30, label: "30초" },
  { value: 60, label: "60초" },
  { value: 120, label: "120초 (최대)" },
];

// =============================================================================
// TYPES
// =============================================================================

/** Disclosure level for progressive UI complexity */
type DisclosureLevel = "basic" | "intermediate" | "advanced";

interface UnifiedPromptPanelProps {
  disclosureLevel?: DisclosureLevel;
}

interface PromptResult {
  prompt: string;
  systemPrompt: string;
  platform: string;
  negative_prompt?: string;
  quality_scores?: Record<string, number>;
  evidence_refs?: string[];
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function UnifiedPromptPanel({
  disclosureLevel = "intermediate",
}: UnifiedPromptPanelProps = {}) {
  const chainCtx = useDimensionChainOptional();
  const {
    logicVector,
    hasUpstreamData,
    rawInputData,
    evidenceRefs,
  } = useChainDataInjection(DIMENSION_KEY);

  // Form state
  const [sceneDescription, setSceneDescription] = useState("");
  const [targetPlatform, setTargetPlatform] = useState("veo_31");
  const [style, setStyle] = useState("cinematic");
  const [duration, setDuration] = useState(15);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [auteurKey, setAuteurKey] = useState<string | undefined>();

  // Result state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PromptResult | null>(null);

  // React 19: useTransition for non-blocking UI
  const [isPending, startTransition] = useTransition();

  // Set current dimension on mount
  useEffect(() => {
    if (chainCtx) chainCtx.setCurrentDimension(DIMENSION_KEY);
  }, [chainCtx]);

  // Auto-inject data from upstream (Story Architect)
  useEffect(() => {
    // From story-architect: get logline/synopsis as scene description
    const storyOutput = rawInputData["story-architect"] as {
      output?: { logline?: string; synopsis?: string };
    } | undefined;

    if (!sceneDescription) {
      if (storyOutput?.output?.synopsis) {
        setSceneDescription(storyOutput.output.synopsis);
      } else if (storyOutput?.output?.logline) {
        setSceneDescription(storyOutput.output.logline);
      }
    }

    // From aesthetic-director: get auteur key
    const adOutput = rawInputData["aesthetic-director"] as {
      output?: { auteur_key?: string };
    } | undefined;
    if (adOutput?.output?.auteur_key) {
      setAuteurKey(adOutput.output.auteur_key);
    }
  }, [rawInputData, sceneDescription]);

  // Handle chain data from ChainDataInput
  const handleApplyChainData = useCallback((data: Record<string, ChainData>) => {
    // From story-architect
    const storyOutput = data["story-architect"]?.output;
    if (storyOutput && !sceneDescription) {
      const synopsis = storyOutput.synopsis as string | undefined;
      const logline = storyOutput.logline as string | undefined;
      if (synopsis) {
        setSceneDescription(synopsis);
      } else if (logline) {
        setSceneDescription(logline);
      }
    }

    // From aesthetic-director
    const adOutput = data["aesthetic-director"]?.output;
    if (adOutput?.auteur_key) {
      setAuteurKey(adOutput.auteur_key as string);
    }
  }, [sceneDescription]);

  // Generate both prompt and system-prompt
  const handleGenerate = async () => {
    if (!sceneDescription.trim()) {
      setError("씬 설명을 입력해주세요");
      return;
    }

    if (sceneDescription.length < 10) {
      setError("씬 설명은 10자 이상 입력해주세요");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Call the prompt translate API
      const response = await fetch(`${API_BASE}/api/dimension/prompt/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scene_description: sceneDescription,
          target_platform: targetPlatform,
          style,
          auteur_key: auteurKey,
          duration,
          language: "ko",
          model: "gemini-3-flash-preview",
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        const output = data.output;

        // Build result with both prompt and system-prompt
        const promptResult: PromptResult = {
          prompt: output.optimized_prompt || output.prompt || sceneDescription,
          systemPrompt: buildSystemPrompt(output, targetPlatform),
          platform: targetPlatform,
          negative_prompt: output.negative_prompt,
          quality_scores: output.quality_scores,
          evidence_refs: output.evidence_refs,
        };

        startTransition(() => {
          setResult(promptResult);
        });

        // Store in chain context for Production
        if (chainCtx) {
          // Store prompt data
          chainCtx.setChainData(
            "prompt",
            {
              generatedPrompt: promptResult.prompt,
              targetPlatform,
              style,
              duration,
              auteurKey,
            },
            `${PLATFORMS.find(p => p.value === targetPlatform)?.label} 프롬프트 생성`,
            promptResult.evidence_refs || evidenceRefs
          );

          // Store system-prompt data (for backward compatibility)
          chainCtx.setChainData(
            "system-prompt",
            {
              systemPrompt: promptResult.systemPrompt,
              platform: targetPlatform.includes("veo") ? "veo" : targetPlatform.includes("kling") ? "kling" : "both",
              logicVector,
            },
            `${PLATFORMS.find(p => p.value === targetPlatform)?.label} System Prompt`,
            promptResult.evidence_refs || evidenceRefs
          );
        }
      } else {
        throw new Error(data.error || "생성에 실패했습니다");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "알 수 없는 오류");
    } finally {
      setIsLoading(false);
    }
  };

  // Build system prompt from API output
  const buildSystemPrompt = (
    output: Record<string, unknown>,
    platform: string
  ): string => {
    const prompt = output.optimized_prompt || output.prompt || "";
    const platformInfo = PLATFORMS.find(p => p.value === platform);

    return `# System Prompt for ${platformInfo?.label || platform}

## Scene Description
${prompt}

## Technical Parameters
- Platform: ${platformInfo?.label}
- Style: ${style}
- Duration: ${duration} seconds
${auteurKey ? `- Auteur Style: ${auteurKey}` : ""}

## Generation Notes
${output.suggestions ? (output.suggestions as string[]).join("\n- ") : "Use default platform settings."}
`;
  };

  const combinedLoading = isLoading || isPending;

  return (
    <BaseMegaAppPanel
      title="프롬프트 생성"
      icon={Wand2}
      description="Story → Prompt + System Prompt 통합 생성. Production으로 바로 연결됩니다."
      nextStep={{
        app: "production",
        tab: "veo",
        label: "VEO로 영상 생성하기",
      }}
    >
      {/* Chain Data Input - hidden in basic mode */}
      {disclosureLevel !== "basic" && (
        <ChainDataInput
          currentDimension={DIMENSION_KEY}
          onApplyData={handleApplyChainData}
          themeColor="fuchsia"
        />
      )}

      {/* Upstream Data Banner - hidden in basic mode */}
      {disclosureLevel !== "basic" && hasUpstreamData && (
        <div className="p-3 rounded-xl bg-fuchsia-500/10 border border-fuchsia-500/20 mb-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-fuchsia-500 animate-pulse" />
            <span className="text-xs font-medium text-fuchsia-400">
              Story Engine 데이터 감지됨 - 자동 적용됨
            </span>
          </div>
        </div>
      )}

      {/* Scene Description Input */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-white/80">
          씬 설명 (Scene Description)
          <span className="text-white/40 ml-2">10자 이상</span>
        </label>
        <textarea
          placeholder="영상의 장면을 자세히 설명해주세요. Story Architect에서 자동 주입됩니다.

예: 밤하늘 아래 두 연인이 걷고 있다. 달빛이 그들의 얼굴을 비추고, 주변에는 벚꽃이 흩날린다. 카메라는 천천히 돌리 인하며 두 사람을 클로즈업한다."
          value={sceneDescription}
          onChange={(e) => setSceneDescription(e.target.value)}
          className="w-full h-32 px-3 py-2 border rounded-md bg-white/5 border-white/10 text-white placeholder:text-white/30 text-sm resize-none"
          disabled={combinedLoading}
        />
        <div className="flex justify-end">
          <span className="text-xs text-white/40">{sceneDescription.length}/3000</span>
        </div>
      </div>

      {/* Platform Selector - hidden in basic mode */}
      {disclosureLevel !== "basic" && (
        <div className="space-y-2">
          <label className="text-sm font-medium text-white/80">대상 플랫폼</label>
          <div className="grid grid-cols-1 gap-2">
            {PLATFORMS.map((platform) => (
              <button
                key={platform.value}
                onClick={() => setTargetPlatform(platform.value)}
                disabled={combinedLoading}
                className={`p-3 rounded-lg border text-left transition-all ${
                  targetPlatform === platform.value
                    ? "bg-fuchsia-500/20 border-fuchsia-500/50 text-white"
                    : "bg-white/5 border-white/10 text-white/70 hover:bg-white/10"
                }`}
              >
                <div className="font-medium text-sm">{platform.label}</div>
                <div className="text-xs text-white/50">{platform.description}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Advanced Options Toggle - only in intermediate/advanced mode */}
      {disclosureLevel !== "basic" && (
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10 text-white/70 hover:bg-white/10 transition-all"
        >
          <div className="flex items-center gap-2">
            <Settings2 className="w-4 h-4" />
            <span className="text-sm">고급 옵션</span>
          </div>
          <ChevronDown
            className={`w-4 h-4 transition-transform ${showAdvanced ? "rotate-180" : ""}`}
          />
        </button>
      )}

      {/* Advanced Options - auto-show in advanced mode, toggleable in intermediate */}
      {(showAdvanced || disclosureLevel === "advanced") && disclosureLevel !== "basic" && (
        <div className="space-y-4 p-4 rounded-lg bg-white/5 border border-white/10">
          {/* Style & Duration */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <label className="text-xs font-medium text-white/60">스타일</label>
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                disabled={combinedLoading}
                className="w-full px-3 py-2 rounded-md bg-white/5 border border-white/10 text-white text-sm"
              >
                {STYLES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-white/60">영상 길이</label>
              <select
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                disabled={combinedLoading}
                className="w-full px-3 py-2 rounded-md bg-white/5 border border-white/10 text-white text-sm"
              >
                {DURATIONS.map((d) => (
                  <option key={d.value} value={d.value}>
                    {d.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Auteur Key */}
          {auteurKey && (
            <div className="p-2 rounded-md bg-fuchsia-500/10 border border-fuchsia-500/20">
              <span className="text-xs text-fuchsia-400">
                거장 스타일: <strong>{auteurKey}</strong> (DNA Lab에서 자동 적용)
              </span>
            </div>
          )}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Generate Button */}
      <button
        onClick={handleGenerate}
        disabled={!sceneDescription.trim() || sceneDescription.length < 10 || combinedLoading}
        className="w-full px-4 py-3 bg-gradient-to-r from-fuchsia-500 to-pink-500 text-white rounded-lg font-medium hover:from-fuchsia-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
      >
        {combinedLoading ? (
          <>
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            생성 중...
          </>
        ) : (
          <>
            <Wand2 className="w-4 h-4" />
            Prompt + System Prompt 생성
          </>
        )}
      </button>

      {/* Results */}
      {result && (
        <div className="space-y-4 mt-6">
          {/* Generated Prompt */}
          <Card className="bg-black/30 border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center justify-between text-white text-sm">
                <div className="flex items-center gap-2">
                  <Wand2 className="w-4 h-4 text-fuchsia-400" />
                  생성된 프롬프트
                </div>
                <button
                  onClick={() => navigator.clipboard.writeText(result.prompt)}
                  className="text-xs px-3 py-1 bg-white/10 rounded-md hover:bg-white/20 transition-colors"
                >
                  복사
                </button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="p-3 bg-black/30 rounded-md overflow-auto text-sm whitespace-pre-wrap text-white/80 max-h-48">
                {result.prompt}
              </pre>
            </CardContent>
          </Card>

          {/* System Prompt */}
          <Card className="bg-black/30 border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center justify-between text-white text-sm">
                <div className="flex items-center gap-2">
                  <FileCode className="w-4 h-4 text-cyan-400" />
                  System Prompt ({PLATFORMS.find(p => p.value === result.platform)?.label})
                </div>
                <button
                  onClick={() => navigator.clipboard.writeText(result.systemPrompt)}
                  className="text-xs px-3 py-1 bg-white/10 rounded-md hover:bg-white/20 transition-colors"
                >
                  복사
                </button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="p-3 bg-black/30 rounded-md overflow-auto text-sm whitespace-pre-wrap text-white/80 max-h-48">
                {result.systemPrompt}
              </pre>
            </CardContent>
          </Card>

          {/* Evidence Refs */}
          {result.evidence_refs && result.evidence_refs.length > 0 && (
            <div className="p-3 rounded-lg bg-white/5 border border-white/10">
              <div className="text-xs font-medium text-white/60 mb-2">Evidence References</div>
              <div className="flex flex-wrap gap-1">
                {result.evidence_refs.map((ref, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 bg-white/10 rounded text-xs text-white/70 font-mono"
                  >
                    {ref}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </BaseMegaAppPanel>
  );
}
