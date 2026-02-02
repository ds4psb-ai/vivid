"use client";

import { useState } from "react";
import { TOOL_CONFIGS, ToolId } from "@/lib/tikitaka-prompts";
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
