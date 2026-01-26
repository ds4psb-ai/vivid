"use client";

/**
 * SystemPromptPanel - System Prompt Generator Panel
 *
 * Converts Logic Vector + Story Structure to platform-specific System Prompts.
 * Supports VEO 3.1, Kling 2.6, Sora 2 Pro, Runway Gen-3.
 *
 * Part of Mega App Panel Integration (Phase 2)
 */

import { useState } from "react";
import { FileCode } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BaseMegaAppPanel } from "@/components/mega-app/panels";

export default function SystemPromptPanel() {
  const [logicVectorJson, setLogicVectorJson] = useState("");
  const [storyStructure, setStoryStructure] = useState("");
  const [targetPlatform, setTargetPlatform] = useState("veo");
  const [isLoading, setIsLoading] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!logicVectorJson) return;

    setIsLoading(true);
    try {
      let logicVector;
      try {
        logicVector = JSON.parse(logicVectorJson);
      } catch {
        alert("Logic Vector JSON 형식이 올바르지 않습니다.");
        setIsLoading(false);
        return;
      }

      const response = await fetch("/api/story-engine/system-prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          logic_vector: logicVector,
          story_structure: storyStructure ? JSON.parse(storyStructure) : undefined,
          target_platform: targetPlatform,
        }),
      });
      const data = await response.json();
      if (data.success) {
        setSystemPrompt(data.system_prompt);
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
      {/* Logic Vector Input */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-white/80">
          Logic Vector (JSON)
          <span className="text-white/40 ml-2">DNA Lab에서 복사</span>
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
