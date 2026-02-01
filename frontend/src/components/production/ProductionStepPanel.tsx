"use client";

/**
 * ProductionStepPanel - Panel Wrapper with Chain Data Integration
 *
 * Wraps individual panel components with:
 * - Input data injection from Story Engine
 * - Missing data indicators
 * - Completion actions (gallery/share/try another tool)
 *
 * 2026 Patterns:
 * - Cross-app data flow visualization
 * - Guide, Don't Block (show missing data but allow action)
 * - Independent step access
 */

import { AlertCircle, ExternalLink, Rocket, ArrowRight, Share2, FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import { useProductionWorkflow } from "./hooks/useProductionWorkflow";
import {
  PRODUCTION_STEPS_MAP,
  PRODUCTION_INPUT_MAP,
  getInputLabel,
  type ProductionStepId,
} from "./constants";
import { CHAIN_DATA_SOURCE_MAP } from "@/components/workflow/workflow-configs";

interface ProductionStepPanelProps {
  /** Current step ID */
  stepId: ProductionStepId;
  /** Panel component */
  children: React.ReactNode;
  /** Show input data banner */
  showInputBanner?: boolean;
  /** Show completion actions (gallery/share/try another tool) */
  showCompletionActions?: boolean;
  /** Custom class name */
  className?: string;
}

/**
 * Panel wrapper that shows input data status and provides chain integration
 */
export function ProductionStepPanel({
  stepId,
  children,
  showInputBanner = true,
  showCompletionActions = true,
  className,
}: ProductionStepPanelProps) {
  const {
    getInputDataForStep,
    getMissingInputsForStep,
    goToStep,
    goToStoryEngine,
    goToDNALab,
    goToGallery,
    chainData,
    getOtherTools,
  } = useProductionWorkflow();

  const step = PRODUCTION_STEPS_MAP[stepId];
  const inputData = getInputDataForStep(stepId);
  const missingInputs = getMissingInputsForStep(stepId);
  const hasInputs = Object.keys(inputData).length > 0;
  const hasMissingInputs = missingInputs.length > 0;
  const hasResult = !!chainData[stepId];
  const otherTools = getOtherTools(stepId);

  // Navigation handler for missing input sources
  const handleGoToSource = (key: string) => {
    const source = CHAIN_DATA_SOURCE_MAP[key];
    if (source?.app === "story-engine") {
      goToStoryEngine(source.step);
    } else if (source?.app === "dna-lab") {
      goToDNALab(source.step);
    }
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Input Data Banner */}
      {showInputBanner && (hasInputs || hasMissingInputs) && (
        <ProductionInputBanner
          stepId={stepId}
          inputData={inputData}
          missingInputs={missingInputs}
          onGoToSource={handleGoToSource}
        />
      )}

      {/* Panel Content */}
      <div className="flex-1 overflow-auto">{children}</div>

      {/* Completion Actions (when result exists) */}
      {showCompletionActions && hasResult && (
        <ProductionCompletionBar
          stepId={stepId}
          otherTools={otherTools}
          onGoToTool={(toolId) => goToStep(toolId)}
          onGoToGallery={goToGallery}
        />
      )}
    </div>
  );
}

/**
 * Input Data Banner - Shows available and missing inputs
 */
interface ProductionInputBannerProps {
  stepId: ProductionStepId;
  inputData: Record<string, Record<string, unknown>>;
  missingInputs: string[];
  onGoToSource: (key: string) => void;
}

function ProductionInputBanner({
  stepId,
  inputData,
  missingInputs,
  onGoToSource,
}: ProductionInputBannerProps) {
  const hasInputs = Object.keys(inputData).length > 0;
  const hasMissingInputs = missingInputs.length > 0;

  if (!hasInputs && !hasMissingInputs) return null;

  return (
    <div className="px-4 py-2 border-b border-white/10 bg-white/5">
      {/* Available inputs */}
      {hasInputs && (
        <div className="flex items-center flex-wrap gap-2 text-xs text-white/60 mb-1">
          <span className="text-[var(--stitch-primary)]">입력 데이터:</span>
          {Object.keys(inputData).map((inputKey) => {
            const source = CHAIN_DATA_SOURCE_MAP[inputKey];
            const isFromStoryEngine = source?.app === "story-engine";
            const isFromDNALab = source?.app === "dna-lab";

            return (
              <span
                key={inputKey}
                className={cn(
                  "px-2 py-0.5 rounded flex items-center gap-1",
                  isFromStoryEngine
                    ? "bg-purple-500/10 text-purple-400"
                    : isFromDNALab
                    ? "bg-cyan-500/10 text-cyan-400"
                    : "bg-[var(--stitch-primary)]/10 text-[var(--stitch-primary)]"
                )}
              >
                {getInputLabel(inputKey)}
                <ExternalLink className="w-2.5 h-2.5 opacity-60" />
              </span>
            );
          })}
        </div>
      )}

      {/* Missing inputs warning */}
      {hasMissingInputs && (
        <div className="flex items-center flex-wrap gap-2 text-xs">
          <AlertCircle className="w-3 h-3 text-amber-400" />
          <span className="text-amber-400">미완료:</span>

          {missingInputs.map((inputKey) => {
            const source = CHAIN_DATA_SOURCE_MAP[inputKey];
            const isFromStoryEngine = source?.app === "story-engine";

            return (
              <button
                key={inputKey}
                onClick={() => onGoToSource(inputKey)}
                className={cn(
                  "px-2 py-0.5 rounded transition-colors flex items-center gap-1",
                  isFromStoryEngine
                    ? "bg-[var(--stitch-primary)]/10 text-[var(--stitch-primary)] hover:bg-[var(--stitch-primary)]/20"
                    : "bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500/20"
                )}
              >
                {getInputLabel(inputKey)}
                <ExternalLink className="w-2.5 h-2.5" />
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

/**
 * Completion Bar - Actions after successful generation
 */
interface ProductionCompletionBarProps {
  stepId: ProductionStepId;
  otherTools: { id: ProductionStepId; label: string; icon: React.ComponentType<{ className?: string }> }[];
  onGoToTool: (toolId: ProductionStepId) => void;
  onGoToGallery: () => void;
}

function ProductionCompletionBar({
  stepId,
  otherTools,
  onGoToTool,
  onGoToGallery,
}: ProductionCompletionBarProps) {
  const step = PRODUCTION_STEPS_MAP[stepId];

  return (
    <div className="px-4 py-3 border-t border-white/10 bg-gradient-to-r from-[var(--stitch-primary)]/10 via-transparent to-[var(--stitch-primary-accent)]/10">
      <div className="flex items-center justify-between flex-wrap gap-3">
        {/* Success message */}
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[var(--stitch-primary)]/20">
            <Rocket className="w-5 h-5 text-[var(--stitch-primary)]" />
          </div>
          <div>
            <p className="text-sm font-medium text-white">{step.label} 생성 완료!</p>
            <p className="text-xs text-white/60">
              갤러리에서 확인하거나 다른 도구를 사용하세요.
            </p>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          {/* Try another tool */}
          {otherTools.length > 0 && (
            <div className="flex items-center gap-1">
              <span className="text-xs text-white/40 mr-1">다른 도구:</span>
              {otherTools.map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => onGoToTool(tool.id)}
                  className="flex items-center gap-1 px-3 py-1.5 bg-white/5 text-white/70 rounded-lg hover:bg-white/10 transition-colors text-xs"
                >
                  <tool.icon className="w-3 h-3" />
                  <span>{tool.label}</span>
                </button>
              ))}
            </div>
          )}

          {/* Divider */}
          <div className="w-px h-6 bg-white/10" />

          {/* Gallery button */}
          <button
            onClick={onGoToGallery}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--stitch-primary)]/20 text-[var(--stitch-primary)] rounded-lg hover:bg-[var(--stitch-primary)]/30 transition-colors font-medium text-sm"
          >
            <FolderOpen className="w-4 h-4" />
            <span>갤러리에서 보기</span>
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Hook to inject chain input data into panel props
 */
export function useChainInputInjection(stepId: ProductionStepId) {
  const {
    getInputDataForStep,
    getMissingInputsForStep,
    chainData,
  } = useProductionWorkflow();

  const inputData = getInputDataForStep(stepId);
  const missingInputs = getMissingInputsForStep(stepId);

  // Build injected props based on step
  const injectedProps: Record<string, unknown> = {};

  switch (stepId) {
    case "veo":
    case "kling":
      // VEO/Kling get system-prompt from Story Engine
      if (inputData["system-prompt"]) {
        injectedProps.prefillSystemPrompt = inputData["system-prompt"];
      }
      break;

    case "suno":
      // Suno gets story from Story Engine
      if (inputData.story) {
        injectedProps.prefillStory = inputData.story;
      }
      break;
  }

  return {
    inputData,
    missingInputs,
    injectedProps,
    hasAllInputs: missingInputs.length === 0,
  };
}
