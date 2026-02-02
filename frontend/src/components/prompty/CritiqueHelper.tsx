"use client";

import { useState, useCallback } from "react";
import {
  generateCritiquePrompt,
  copyToClipboard,
  IMAGE_CRITIQUE_DIMENSIONS,
  VIDEO_CRITIQUE_DIMENSIONS,
  type CritiqueContext,
} from "@/lib/critique-prompt-generator";
import {
  parseCritiqueResult,
  calculateWeightedScore,
  getVerdictFromScore,
  type ParsedCritiqueResult,
} from "@/lib/critique-result-parser";
import { api } from "@/lib/api";

interface CritiqueHelperProps {
  projectId: string;
  scenes: Array<{
    id: string;
    name: string;
    isAnchor: boolean;
    imagePath?: string;
  }>;
  anchorImagePath?: string;
  onCritiqueSaved?: () => void;
}

export function CritiqueHelper({
  projectId,
  scenes,
  anchorImagePath,
  onCritiqueSaved,
}: CritiqueHelperProps) {
  const [selectedScene, setSelectedScene] = useState<string>(
    scenes[0]?.id || ""
  );
  const [critiqueType, setCritiqueType] = useState<"image" | "video">("image");
  const [generatedPrompt, setGeneratedPrompt] = useState<string>("");
  const [aiOutput, setAiOutput] = useState<string>("");
  const [parsedResult, setParsedResult] = useState<ParsedCritiqueResult | null>(
    null
  );
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const [step, setStep] = useState<1 | 2 | 3>(1);

  const currentScene = scenes.find((s) => s.id === selectedScene);

  // Step 1: Generate prompt
  const handleGeneratePrompt = useCallback(() => {
    if (!currentScene) return;

    const context: CritiqueContext = {
      sceneId: currentScene.id,
      sceneName: currentScene.name,
      isAnchor: currentScene.isAnchor,
      imagePath: currentScene.imagePath,
      anchorImagePath: currentScene.isAnchor ? undefined : anchorImagePath,
      critiqueType,
    };

    const prompt = generateCritiquePrompt(context);
    setGeneratedPrompt(prompt);
    setStep(2);
  }, [currentScene, anchorImagePath, critiqueType]);

  // Copy prompt to clipboard
  const handleCopyPrompt = async () => {
    const success = await copyToClipboard(generatedPrompt);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Step 2: Parse AI output
  const handleParseOutput = useCallback(() => {
    const result = parseCritiqueResult(aiOutput);
    if (result) {
      // Recalculate score if needed
      if (Object.keys(result.scores).length > 0) {
        result.totalScore = calculateWeightedScore(result.scores, critiqueType);
        result.verdict = getVerdictFromScore(result.totalScore);
      }
      result.sceneId = selectedScene;
      result.critiqueType = critiqueType;
      setParsedResult(result);
      setStep(3);
    }
  }, [aiOutput, selectedScene, critiqueType]);

  // Step 3: Save to database
  const handleSave = async () => {
    if (!parsedResult) return;
    setSaving(true);

    try {
      await api.submitPromptyCritique(projectId, {
        stage: critiqueType,
        step_id: parsedResult.sceneId,
        score: parsedResult.totalScore,
        verdict: parsedResult.verdict,
        issues: parsedResult.issues,
        suggestions: parsedResult.suggestions,
        scores_detail: parsedResult.scores as Record<string, number>,
      });
      onCritiqueSaved?.();
      // Reset for next critique
      setAiOutput("");
      setParsedResult(null);
      setGeneratedPrompt("");
      setStep(1);
    } catch (error) {
      console.error("Failed to save critique:", error);
    } finally {
      setSaving(false);
    }
  };

  const dimensions =
    critiqueType === "image"
      ? IMAGE_CRITIQUE_DIMENSIONS
      : VIDEO_CRITIQUE_DIMENSIONS;

  return (
    <div className="space-y-6">
      {/* Scene & Type Selection */}
      <div className="flex gap-4 flex-wrap">
        <div className="flex-1 min-w-[200px]">
          <label className="block text-sm font-medium mb-1">Scene</label>
          <select
            value={selectedScene}
            onChange={(e) => setSelectedScene(e.target.value)}
            className="w-full px-3 py-2 bg-background border border-border rounded-lg"
          >
            {scenes.map((scene) => (
              <option key={scene.id} value={scene.id}>
                {scene.isAnchor ? "⭐ " : ""}
                {scene.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex-1 min-w-[200px]">
          <label className="block text-sm font-medium mb-1">Type</label>
          <div className="flex gap-2">
            <button
              onClick={() => setCritiqueType("image")}
              className={`flex-1 px-4 py-2 rounded-lg border transition ${
                critiqueType === "image"
                  ? "bg-primary text-primary-foreground border-primary"
                  : "border-border hover:bg-accent"
              }`}
            >
              🖼️ Image
            </button>
            <button
              onClick={() => setCritiqueType("video")}
              className={`flex-1 px-4 py-2 rounded-lg border transition ${
                critiqueType === "video"
                  ? "bg-primary text-primary-foreground border-primary"
                  : "border-border hover:bg-accent"
              }`}
            >
              🎬 Video
            </button>
          </div>
        </div>
      </div>

      {/* Step Indicator */}
      <div className="flex items-center gap-2 text-sm">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center font-medium ${
                step >= s
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              {s}
            </div>
            {s < 3 && (
              <div
                className={`w-8 h-0.5 ${
                  step > s ? "bg-primary" : "bg-muted"
                }`}
              />
            )}
          </div>
        ))}
        <span className="ml-2 text-muted-foreground">
          {step === 1 && "프롬프트 생성"}
          {step === 2 && "AI 결과 붙여넣기"}
          {step === 3 && "결과 확인 & 저장"}
        </span>
      </div>

      {/* Step 1: Generate Prompt */}
      {step === 1 && (
        <div className="space-y-4">
          <div className="p-4 border border-border rounded-lg bg-card">
            <h3 className="font-medium mb-2">5D 평가 기준</h3>
            <ul className="text-sm space-y-1 text-muted-foreground">
              {dimensions.map((d) => (
                <li key={d.id}>
                  • <strong>{d.nameKo}</strong> ({d.weight}%): {d.description}
                </li>
              ))}
            </ul>
          </div>
          <button
            onClick={handleGeneratePrompt}
            disabled={!currentScene}
            className="w-full py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 transition"
          >
            프롬프트 생성하기
          </button>
        </div>
      )}

      {/* Step 2: Copy & Paste */}
      {step === 2 && (
        <div className="space-y-4">
          {/* Generated Prompt */}
          <div className="relative">
            <label className="block text-sm font-medium mb-1">
              1. 이 프롬프트를 복사하여 Gemini/Claude에 붙여넣기
            </label>
            <textarea
              value={generatedPrompt}
              readOnly
              rows={8}
              className="w-full px-3 py-2 bg-muted border border-border rounded-lg font-mono text-sm resize-none"
            />
            <button
              onClick={handleCopyPrompt}
              className="absolute top-8 right-2 px-3 py-1 bg-primary text-primary-foreground text-sm rounded hover:bg-primary/90 transition"
            >
              {copied ? "✅ Copied!" : "📋 Copy"}
            </button>
          </div>

          {/* AI Output */}
          <div>
            <label className="block text-sm font-medium mb-1">
              2. AI 응답을 여기에 붙여넣기
            </label>
            <textarea
              value={aiOutput}
              onChange={(e) => setAiOutput(e.target.value)}
              rows={8}
              placeholder="Gemini/Claude의 응답을 여기에 붙여넣으세요..."
              className="w-full px-3 py-2 bg-background border border-border rounded-lg font-mono text-sm resize-none"
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setStep(1)}
              className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition"
            >
              ← 이전
            </button>
            <button
              onClick={handleParseOutput}
              disabled={!aiOutput.trim()}
              className="flex-1 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 transition"
            >
              결과 파싱하기
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Review & Save */}
      {step === 3 && parsedResult && (
        <div className="space-y-4">
          {/* Score Summary */}
          <div className="p-4 border border-border rounded-lg bg-card">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="font-medium">{currentScene?.name}</h3>
                <span className="text-sm text-muted-foreground">
                  {critiqueType === "image" ? "🖼️ Image" : "🎬 Video"} Critique
                </span>
              </div>
              <div className="text-right">
                <div
                  className={`text-3xl font-bold ${
                    parsedResult.verdict === "PASS"
                      ? "text-green-500"
                      : parsedResult.verdict === "REVISE"
                      ? "text-yellow-500"
                      : "text-red-500"
                  }`}
                >
                  {parsedResult.totalScore}
                </div>
                <span
                  className={`text-sm font-medium ${
                    parsedResult.verdict === "PASS"
                      ? "text-green-500"
                      : parsedResult.verdict === "REVISE"
                      ? "text-yellow-500"
                      : "text-red-500"
                  }`}
                >
                  {parsedResult.verdict}
                </span>
              </div>
            </div>

            {/* Individual Scores */}
            <div className="space-y-2">
              {dimensions.map((dim) => {
                const score =
                  parsedResult.scores[
                    dim.id as keyof typeof parsedResult.scores
                  ];
                return (
                  <div key={dim.id} className="flex items-center gap-2 text-sm">
                    <span className="w-32 text-muted-foreground">
                      {dim.nameKo}
                    </span>
                    <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all ${
                          score !== undefined && score >= 85
                            ? "bg-green-500"
                            : score !== undefined && score >= 60
                            ? "bg-yellow-500"
                            : "bg-red-500"
                        }`}
                        style={{ width: `${score ?? 0}%` }}
                      />
                    </div>
                    <span className="w-10 text-right">
                      {score !== undefined ? score : "-"}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Issues & Suggestions */}
          {(parsedResult.issues.length > 0 ||
            parsedResult.suggestions.length > 0) && (
            <div className="p-4 border border-border rounded-lg bg-card space-y-3">
              {parsedResult.issues.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-red-400 mb-1">
                    문제점
                  </h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    {parsedResult.issues.map((issue, i) => (
                      <li key={i}>• {issue}</li>
                    ))}
                  </ul>
                </div>
              )}
              {parsedResult.suggestions.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-blue-400 mb-1">
                    개선 제안
                  </h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    {parsedResult.suggestions.map((sug, i) => (
                      <li key={i}>→ {sug}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={() => setStep(2)}
              className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition"
            >
              ← 수정
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex-1 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 transition"
            >
              {saving ? "저장 중..." : "💾 저장하기"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default CritiqueHelper;
