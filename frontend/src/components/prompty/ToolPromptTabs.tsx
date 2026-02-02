"use client";

import { useState } from "react";
import { TOOL_CONFIGS, ToolId, ParameterGuide, CommonIssue } from "@/lib/tikitaka-prompts";
import { CopyPromptButton } from "./CopyPromptButton";

interface ToolPromptTabsProps {
  prompts: Record<string, string>;
  recommendedTool?: ToolId;
  onCopy?: (toolId: string) => void;
}

/**
 * ToolPromptTabs - Tool-specific prompt tabs
 *
 * Step 5-6에서 도구별 프롬프트 표시
 * NanoBanana, MJ V7, Kling 2.6, Veo 3.1
 */
export function ToolPromptTabs({
  prompts,
  recommendedTool = "nanobanana",
  onCopy,
}: ToolPromptTabsProps) {
  const [activeTab, setActiveTab] = useState<ToolId>(recommendedTool);

  const toolIds = Object.keys(TOOL_CONFIGS) as ToolId[];
  const activeConfig = TOOL_CONFIGS[activeTab];
  const activePrompt = prompts[activeTab] || "";

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      {/* Tabs */}
      <div className="flex border-b border-border">
        {toolIds.map((toolId) => {
          const config = TOOL_CONFIGS[toolId];
          const isActive = toolId === activeTab;
          const isRecommended = toolId === recommendedTool;

          return (
            <button
              key={toolId}
              onClick={() => setActiveTab(toolId)}
              className={`
                flex-1 px-4 py-3 text-sm font-medium transition relative
                ${isActive ? "bg-card text-foreground" : "bg-muted/50 text-muted-foreground hover:text-foreground"}
              `}
            >
              <div className="flex items-center justify-center gap-2">
                <span className="font-mono text-xs opacity-60">{config.icon}</span>
                <span>{config.name}</span>
                {isRecommended && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-500/10 text-green-500">
                    Recommended
                  </span>
                )}
              </div>
              {isActive && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
              )}
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Tool Info */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center font-mono text-sm">
              {activeConfig.icon}
            </div>
            <div>
              <h4 className="font-semibold">{activeConfig.name}</h4>
              <p className="text-xs text-muted-foreground">
                Format: {activeConfig.format === "korean" ? "Korean" : "English"}
                {activeConfig.format === "english_with_params" && " + Parameters"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <a
              href={activeConfig.url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition text-sm"
            >
              Open {activeConfig.name}
            </a>
            <CopyPromptButton
              promptText={activePrompt}
              onCopy={() => onCopy?.(activeTab)}
            />
          </div>
        </div>

        {/* Example Values Warning */}
        {activePrompt && (
          <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
            <p className="text-sm text-amber-600 dark:text-amber-400">
              <span className="font-medium">주의:</span> 아래 프롬프트에는 <strong>예시 값</strong>이 포함되어 있습니다.
              본인 영상에 맞게 수정 후 사용하세요.
            </p>
          </div>
        )}

        {/* Prompt */}
        {activePrompt ? (
          <pre className="p-4 bg-muted rounded-lg text-sm overflow-x-auto whitespace-pre-wrap font-mono max-h-96">
            {activePrompt}
          </pre>
        ) : (
          <div className="p-8 bg-muted rounded-lg text-center">
            <p className="text-muted-foreground">No prompt available for {activeConfig.name}</p>
            <p className="text-sm text-muted-foreground mt-2">
              Complete Step 2 (Draft) or Step 4 (Revise) to generate tool-specific prompts.
            </p>
          </div>
        )}

        {/* Parameter Guide Section */}
        {activeConfig.parameterGuide && activeConfig.parameterGuide.length > 0 && (
          <div className="mt-4 p-4 border border-border rounded-lg">
            <h4 className="text-sm font-semibold mb-3">Parameters</h4>
            <div className="space-y-2">
              {activeConfig.parameterGuide.map((p) => (
                <div key={p.param} className="flex items-start gap-2 text-sm">
                  <code className={`px-1.5 py-0.5 rounded text-xs font-mono shrink-0 ${
                    p.impact === "critical" ? "bg-red-500/10 text-red-500" :
                    p.impact === "important" ? "bg-yellow-500/10 text-yellow-500" :
                    "bg-muted text-muted-foreground"
                  }`}>{p.param}</code>
                  <span className="text-muted-foreground">{p.description}</span>
                  <span className="text-xs text-muted-foreground/70 ml-auto shrink-0">{p.example}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Common Issues Section */}
        {activeConfig.commonIssues && activeConfig.commonIssues.length > 0 && (
          <div className="mt-4 p-4 border border-yellow-500/20 bg-yellow-500/5 rounded-lg">
            <h4 className="text-sm font-semibold mb-3 text-yellow-600 dark:text-yellow-400">Common Issues</h4>
            <div className="space-y-2">
              {activeConfig.commonIssues.map((issue, i) => (
                <div key={i} className="text-sm">
                  <span className="text-muted-foreground">{issue.problem}</span>
                  <span className="mx-2 text-muted-foreground/50">→</span>
                  <span className="text-foreground">{issue.solution}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tool-specific tips */}
        <div className="mt-4 p-3 bg-muted/50 rounded-lg">
          <ToolTips toolId={activeTab} />
        </div>
      </div>
    </div>
  );
}

function ToolTips({ toolId }: { toolId: ToolId }) {
  const tips: Record<ToolId, string[]> = {
    nanobanana: [
      "Korean prompts work best",
      "Use --no for negative prompts",
      "Supports image reference upload",
    ],
    midjourney: [
      "--ar 16:9 for widescreen",
      "--v 7 for latest version",
      "--style raw for realistic output",
      "--cw 80-100 for character weight",
    ],
    kling: [
      "Upload reference image first",
      "3-5 seconds duration recommended",
      "Subtle camera movement works best",
    ],
    veo: [
      "Photorealistic style by default",
      "4-6 seconds optimal length",
      "Describe motion explicitly",
    ],
  };

  const toolTips = tips[toolId];

  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-muted-foreground mb-2">
        {TOOL_CONFIGS[toolId].name} Tips:
      </p>
      <ul className="text-xs text-muted-foreground space-y-1">
        {toolTips.map((tip, i) => (
          <li key={i} className="flex items-start gap-2">
            <span>-</span>
            <span>{tip}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default ToolPromptTabs;
