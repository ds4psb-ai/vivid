"use client";

/**
 * SystemPromptPanel - System Prompt Generator Panel
 *
 * Converts Logic Vector + Story Structure to platform-specific System Prompts.
 * Supports VEO 3.1, Kling 2.6, Sora 2 Pro, Runway Gen-3.
 *
 * Part of Mega App Panel Integration (Phase 2)
 * Enhanced with 4-D DNA Architecture Chain Integration
 */

import { useState, useCallback, useEffect } from "react";
import { FileCode } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BaseMegaAppPanel } from "@/components/mega-app/panels";
import { useDimensionChainOptional, type ChainData } from "@/contexts/DimensionChainContext";
import ChainDataInput from "./ChainDataInput";
import { useChainDataInjection } from "@/hooks/useChainDataInjection";

const DIMENSION_KEY = "system-prompt";

export default function SystemPromptPanel() {
  const chainCtx = useDimensionChainOptional();
  const {
    logicVector,
    rawInputData,
    evidenceRefs,
    hasUpstreamData,
  } = useChainDataInjection(DIMENSION_KEY);

  const [logicVectorJson, setLogicVectorJson] = useState("");
  const [storyStructure, setStoryStructure] = useState("");
  const [targetPlatform, setTargetPlatform] = useState("veo");
  const [isLoading, setIsLoading] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState<string | null>(null);

  // Set current dimension on mount
  useEffect(() => {
    if (chainCtx) chainCtx.setCurrentDimension(DIMENSION_KEY);
  }, [chainCtx]);

  // Auto-inject logicVector from upstream (reference-decoder)
  useEffect(() => {
    if (logicVector && !logicVectorJson) {
      setLogicVectorJson(JSON.stringify(logicVector, null, 2));
    }
  }, [logicVector, logicVectorJson]);

  // Handle applying chain data from ChainDataInput
  const handleApplyChainData = useCallback((data: Record<string, ChainData>) => {
    // From reference-decoder: get logicVector
    const refOutput = data["reference-decoder"]?.output;
    if (refOutput?.logic_vector || refOutput?.logicVector) {
      setLogicVectorJson(JSON.stringify(refOutput.logic_vector || refOutput.logicVector, null, 2));
    }

    // From story-architect: get story structure
    const storyOutput = data["story-architect"]?.output;
    if (storyOutput) {
      const structure = {
        hook: storyOutput.logline,
        build: storyOutput.synopsis,
        climax: (storyOutput.structure as Array<{ description: string }> | undefined)?.[
          ((storyOutput.structure as Array<unknown> | undefined)?.length ?? 1) - 1
        ]?.description,
      };
      setStoryStructure(JSON.stringify(structure, null, 2));
    }

    // From prompt-alchemy: use generated prompt hints
    const promptOutput = data["prompt-alchemy"]?.output;
    if (promptOutput?.prompt && !storyStructure) {
      // Use prompt as story hook
      setStoryStructure(JSON.stringify({ hook: promptOutput.prompt }, null, 2));
    }
  }, [storyStructure]);

  const handleGenerate = async () => {
    if (!logicVectorJson) return;

    setIsLoading(true);
    try {
      let parsedLogicVector;
      try {
        parsedLogicVector = JSON.parse(logicVectorJson);
      } catch {
        alert("Logic Vector JSON 형식이 올바르지 않습니다.");
        setIsLoading(false);
        return;
      }

      const response = await fetch("/api/story-engine/system-prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          logic_vector: parsedLogicVector,
          story_structure: storyStructure ? JSON.parse(storyStructure) : undefined,
          target_platform: targetPlatform,
        }),
      });
      const data = await response.json();
      if (data.success) {
        setSystemPrompt(data.system_prompt);

        // Store in chain context for downstream dimensions (veo, kling)
        if (chainCtx) {
          chainCtx.setChainData(
            DIMENSION_KEY,
            {
              systemPrompt: data.system_prompt,
              targetPlatform,
              logicVector: parsedLogicVector,
            },
            `${targetPlatform.toUpperCase()} System Prompt 생성`,
            data.evidence_refs || evidenceRefs
          );
        }
      }
    } catch (error) {
      console.error("System prompt generation failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <BaseMegaAppPanel
      title="System Prompt Generator"
      icon={FileCode}
      description="DNA Lab에서 추출한 Logic Vector를 VEO, Kling, Sora 등의 플랫폼에서 사용할 수 있는 System Prompt로 변환합니다."
      nextStep={{
        app: "production",
        tab: "veo",
        label: "VEO로 영상 생성하기",
      }}
    >
      {/* Chain Data Input */}
      <ChainDataInput
        currentDimension={DIMENSION_KEY}
        onApplyData={handleApplyChainData}
        themeColor="emerald"
      />

      {/* Upstream Data Banner */}
      {hasUpstreamData && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 mb-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-medium text-emerald-400">
              DNA Lab 데이터 감지됨 - 자동 적용 가능
            </span>
          </div>
          {"reference-decoder" in rawInputData && (
            <p className="text-xs text-white/50 mt-1 ml-4">
              Reference Decoder에서 Logic Vector 자동 주입됨
            </p>
          )}
        </div>
      )}

      {/* Logic Vector Input */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-white/80">
          Logic Vector (JSON)
          <span className="text-white/40 ml-2">DNA Lab에서 자동 주입</span>
        </label>
        <textarea
          placeholder={`{
  "auteur_id": "bong",
  "camera_grammar": { "dolly": 0.35, "handheld": 0.15 },
  "lighting_physics": { "key_light": "low_key" },
  ...
}`}
          value={logicVectorJson}
          onChange={(e) => setLogicVectorJson(e.target.value)}
          className="w-full h-40 px-3 py-2 border rounded-md bg-white/5 border-white/10 text-white placeholder:text-white/30 font-mono text-sm"
        />
      </div>

      {/* Story Structure Input */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-white/80">
          Story Structure (선택, JSON)
        </label>
        <textarea
          placeholder={`{
  "hook": "A mysterious figure enters",
  "build": "Tension rises",
  "climax": "The revelation"
}`}
          value={storyStructure}
          onChange={(e) => setStoryStructure(e.target.value)}
          className="w-full h-24 px-3 py-2 border rounded-md bg-white/5 border-white/10 text-white placeholder:text-white/30 font-mono text-sm"
        />
      </div>

      {/* Target Platform Selector */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-white/80">대상 플랫폼</label>
        <select
          value={targetPlatform}
          onChange={(e) => setTargetPlatform(e.target.value)}
          className="w-full px-3 py-2 border rounded-md bg-white/5 border-white/10 text-white"
        >
          <option value="veo">VEO 3.1</option>
          <option value="kling">Kling 2.6</option>
          <option value="sora">Sora 2 Pro</option>
          <option value="runway">Runway Gen-3</option>
        </select>
      </div>

      {/* Generate Button */}
      <button
        onClick={handleGenerate}
        disabled={!logicVectorJson || isLoading}
        className="w-full px-4 py-2 bg-white/10 text-white rounded-md hover:bg-white/20 disabled:opacity-50 transition-colors"
      >
        {isLoading ? "생성 중..." : "System Prompt 생성"}
      </button>

      {/* Result Display */}
      {systemPrompt && (
        <Card className="mt-6 bg-black/30 border-white/10">
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-white">
              생성된 System Prompt
              <button
                onClick={() => navigator.clipboard.writeText(systemPrompt)}
                className="text-sm px-3 py-1 bg-white/10 rounded-md hover:bg-white/20 transition-colors"
              >
                복사
              </button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="p-4 bg-black/30 rounded-md overflow-auto text-sm whitespace-pre-wrap text-white/80">
              {systemPrompt}
            </pre>
          </CardContent>
        </Card>
      )}
    </BaseMegaAppPanel>
  );
}
