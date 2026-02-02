"use client";

import { useState, useCallback, useMemo } from "react";
import {
  CRITIQUE_DIMENSIONS,
  VERDICT_THRESHOLDS,
  getVerdict,
  calculateItemScore,
  generateCritiqueMarkdown,
  generateImprovedPrompt,
  type CritiqueItemResult,
} from "@/lib/tikitaka-prompts";
import { copyToClipboard } from "@/lib/critique-prompt-generator";
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
  originalPrompt?: string; // 현재 프롬프트 (개선 프롬프트 생성용)
}

export function CritiqueHelper({
  projectId,
  scenes,
  anchorImagePath,
  onCritiqueSaved,
  originalPrompt = "",
}: CritiqueHelperProps) {
  const [selectedScene, setSelectedScene] = useState<string>(
    scenes[0]?.id || ""
  );
  const [critiqueType, setCritiqueType] = useState<"image" | "video">("image");

  // 5D×23 체크리스트 상태: {dimension_id: {item_id: boolean}}
  const [checkedItems, setCheckedItems] = useState<
    Record<string, Record<string, boolean>>
  >({});

  // 아코디언 열림 상태
  const [expandedDimensions, setExpandedDimensions] = useState<
    Record<string, boolean>
  >({});

  const [saving, setSaving] = useState(false);
  const [markdownCopied, setMarkdownCopied] = useState(false);

  const currentScene = scenes.find((s) => s.id === selectedScene);

  // 점수 및 결과 계산
  const { score, passedItems, failedItems } = useMemo(() => {
    return calculateItemScore(checkedItems);
  }, [checkedItems]);

  const verdict = useMemo(() => getVerdict(score), [score]);

  // 개선 프롬프트 생성 (규칙 기반)
  const improvedPrompt = useMemo(() => {
    if (failedItems.length === 0 || !originalPrompt) return undefined;
    return generateImprovedPrompt(originalPrompt, failedItems);
  }, [originalPrompt, failedItems]);

  // Markdown 출력 생성
  const markdownOutput = useMemo(() => {
    if (!currentScene) return "";
    return generateCritiqueMarkdown(
      currentScene.name,
      score,
      verdict,
      passedItems,
      failedItems,
      improvedPrompt
    );
  }, [currentScene, score, verdict, passedItems, failedItems, improvedPrompt]);

  // 아이템 체크/해제
  const handleItemToggle = useCallback(
    (dimensionId: string, itemId: string) => {
      setCheckedItems((prev) => {
        const dimItems = prev[dimensionId] || {};
        return {
          ...prev,
          [dimensionId]: {
            ...dimItems,
            [itemId]: !dimItems[itemId],
          },
        };
      });
    },
    []
  );

  // 차원 전체 체크/해제
  const handleDimensionToggleAll = useCallback(
    (dimensionId: string, items: { id: string }[]) => {
      setCheckedItems((prev) => {
        const dimItems = prev[dimensionId] || {};
        const allChecked = items.every((item) => dimItems[item.id] === true);

        const newDimItems: Record<string, boolean> = {};
        for (const item of items) {
          newDimItems[item.id] = !allChecked;
        }

        return {
          ...prev,
          [dimensionId]: newDimItems,
        };
      });
    },
    []
  );

  // 아코디언 토글
  const toggleDimension = useCallback((dimensionId: string) => {
    setExpandedDimensions((prev) => ({
      ...prev,
      [dimensionId]: !prev[dimensionId],
    }));
  }, []);

  // Markdown 복사
  const handleCopyMarkdown = async () => {
    const success = await copyToClipboard(markdownOutput);
    if (success) {
      setMarkdownCopied(true);
      setTimeout(() => setMarkdownCopied(false), 2000);
    }
  };

  // 저장
  const handleSave = async () => {
    if (!currentScene) return;
    setSaving(true);

    try {
      // 차원별 점수 계산 (기존 API 호환용)
      const dimensionScores: Record<string, number> = {};
      for (const dim of CRITIQUE_DIMENSIONS) {
        const dimChecks = checkedItems[dim.id] || {};
        let dimEarned = 0;
        let dimTotal = 0;
        for (const item of dim.items) {
          dimTotal += item.weight;
          if (dimChecks[item.id]) {
            dimEarned += item.weight;
          }
        }
        dimensionScores[dim.id] = dimTotal > 0 ? Math.round((dimEarned / dimTotal) * 100) : 0;
      }

      await api.submitPromptyCritique(projectId, {
        stage: critiqueType,
        step_id: currentScene.id,
        score: score,
        verdict: verdict,
        issues: failedItems.map((f) => `[${f.dimensionName}] ${f.label}`),
        suggestions: failedItems.map((f) => f.suggestion),
        scores_detail: dimensionScores,
      });
      onCritiqueSaved?.();

      // Reset for next critique
      setCheckedItems({});
    } catch (error) {
      console.error("Failed to save critique:", error);
    } finally {
      setSaving(false);
    }
  };

  // 전체 리셋
  const handleReset = useCallback(() => {
    setCheckedItems({});
    setExpandedDimensions({});
  }, []);

  // 전체 체크 (모두 통과)
  const handleCheckAll = useCallback(() => {
    const allChecked: Record<string, Record<string, boolean>> = {};
    for (const dim of CRITIQUE_DIMENSIONS) {
      allChecked[dim.id] = {};
      for (const item of dim.items) {
        allChecked[dim.id][item.id] = true;
      }
    }
    setCheckedItems(allChecked);
  }, []);

  // 체크된 항목 수 계산
  const getCheckedCount = (dimensionId: string): { checked: number; total: number } => {
    const dim = CRITIQUE_DIMENSIONS.find((d) => d.id === dimensionId);
    if (!dim) return { checked: 0, total: 0 };

    const dimChecks = checkedItems[dimensionId] || {};
    const checked = dim.items.filter((item) => dimChecks[item.id] === true).length;
    return { checked, total: dim.items.length };
  };

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
              Image
            </button>
            <button
              onClick={() => setCritiqueType("video")}
              className={`flex-1 px-4 py-2 rounded-lg border transition ${
                critiqueType === "video"
                  ? "bg-primary text-primary-foreground border-primary"
                  : "border-border hover:bg-accent"
              }`}
            >
              Video
            </button>
          </div>
        </div>
      </div>

      {/* Score Display */}
      <div className="p-4 border border-border rounded-lg bg-card">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="font-medium">{currentScene?.name || "Select Scene"}</h3>
            <div className="text-xs text-muted-foreground mt-1">
              PASS: {VERDICT_THRESHOLDS.PASS}+ | REVISE: {VERDICT_THRESHOLDS.REVISE_MIN}-{VERDICT_THRESHOLDS.PASS - 1} | REJECT: &lt;{VERDICT_THRESHOLDS.REVISE_MIN}
            </div>
          </div>
          <div className="text-right">
            <div
              className={`text-3xl font-bold ${
                verdict === "PASS"
                  ? "text-green-500"
                  : verdict === "REVISE"
                  ? "text-yellow-500"
                  : "text-red-500"
              }`}
            >
              {score}
            </div>
            <span
              className={`text-sm font-medium ${
                verdict === "PASS"
                  ? "text-green-500"
                  : verdict === "REVISE"
                  ? "text-yellow-500"
                  : "text-red-500"
              }`}
            >
              {verdict}
            </span>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex gap-2 text-xs">
          <button
            onClick={handleCheckAll}
            className="px-2 py-1 bg-green-500/10 text-green-500 rounded hover:bg-green-500/20 transition"
          >
            All Pass
          </button>
          <button
            onClick={handleReset}
            className="px-2 py-1 bg-red-500/10 text-red-500 rounded hover:bg-red-500/20 transition"
          >
            Reset
          </button>
        </div>
      </div>

      {/* 5D Accordion Checklist */}
      <div className="space-y-2">
        {CRITIQUE_DIMENSIONS.map((dimension) => {
          const isExpanded = expandedDimensions[dimension.id] ?? false;
          const { checked, total } = getCheckedCount(dimension.id);
          const isFullyChecked = checked === total;
          const isPartiallyChecked = checked > 0 && checked < total;

          return (
            <div
              key={dimension.id}
              className="border border-border rounded-lg overflow-hidden"
            >
              {/* Accordion Header */}
              <button
                onClick={() => toggleDimension(dimension.id)}
                className={`w-full px-4 py-3 flex items-center justify-between text-left transition ${
                  isFullyChecked
                    ? "bg-green-500/10"
                    : isPartiallyChecked
                    ? "bg-yellow-500/10"
                    : "bg-card hover:bg-accent"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`w-6 h-6 rounded flex items-center justify-center text-xs font-bold ${
                      isFullyChecked
                        ? "bg-green-500 text-white"
                        : isPartiallyChecked
                        ? "bg-yellow-500 text-white"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {checked}
                  </span>
                  <span className="font-medium">
                    {dimension.nameKo}
                    {dimension.id === "consistency" && " ⭐"}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    ({dimension.weight}%)
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">
                    {checked}/{total}
                  </span>
                  <span
                    className={`transition-transform ${
                      isExpanded ? "rotate-180" : ""
                    }`}
                  >
                    ▼
                  </span>
                </div>
              </button>

              {/* Accordion Content */}
              {isExpanded && (
                <div className="px-4 py-2 space-y-1 bg-background">
                  {/* Toggle All Button */}
                  <button
                    onClick={() =>
                      handleDimensionToggleAll(dimension.id, dimension.items)
                    }
                    className="text-xs text-muted-foreground hover:text-foreground mb-2"
                  >
                    {isFullyChecked ? "Uncheck All" : "Check All"}
                  </button>

                  {dimension.items.map((item) => {
                    const isChecked =
                      checkedItems[dimension.id]?.[item.id] === true;

                    return (
                      <div
                        key={item.id}
                        className={`flex items-start gap-2 p-2 rounded transition cursor-pointer ${
                          isChecked
                            ? "bg-green-500/10"
                            : "hover:bg-accent"
                        }`}
                        onClick={() =>
                          handleItemToggle(dimension.id, item.id)
                        }
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() =>
                            handleItemToggle(dimension.id, item.id)
                          }
                          className="mt-1"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-sm">
                              {item.label}
                            </span>
                            <span
                              className={`text-xs px-1 rounded ${
                                isChecked
                                  ? "bg-green-500/20 text-green-500"
                                  : "bg-muted text-muted-foreground"
                              }`}
                            >
                              {isChecked ? "+" : ""}{item.weight}pt
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {item.description}
                          </p>
                          {!isChecked && (
                            <p className="text-xs text-orange-400 mt-1">
                              → {item.suggestion}
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Markdown Output */}
      {(passedItems.length > 0 || failedItems.length > 0) && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium">
              Markdown 출력 (복사용)
            </label>
            <button
              onClick={handleCopyMarkdown}
              className="px-3 py-1 bg-primary text-primary-foreground text-sm rounded hover:bg-primary/90 transition"
            >
              {markdownCopied ? "Copied!" : "Copy"}
            </button>
          </div>
          <textarea
            value={markdownOutput}
            readOnly
            rows={12}
            className="w-full px-3 py-2 bg-muted border border-border rounded-lg font-mono text-xs resize-none"
          />
        </div>
      )}

      {/* Save Button */}
      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={saving || score === 0}
          className="flex-1 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 transition"
        >
          {saving ? "Saving..." : "Save Critique"}
        </button>
      </div>
    </div>
  );
}

export default CritiqueHelper;
