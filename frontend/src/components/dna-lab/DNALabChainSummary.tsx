"use client";

/**
 * DNALabChainSummary - Chain Data Sidebar
 *
 * Shows accumulated data from workflow steps:
 * - Step completion status
 * - Output data previews
 * - Evidence refs
 * - Export/share options
 *
 * Collapsible sidebar for desktop view.
 */

import { X, ChevronDown, ChevronRight, Check, Clock, FileJson, Copy, Download } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { useDNALabWorkflow } from "./hooks/useDNALabWorkflow";
import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";
import { DNA_LAB_STEPS, DNA_LAB_STEPS_MAP, type DNALabStepId } from "./constants";

interface DNALabChainSummaryProps {
  /** Close handler */
  onClose?: () => void;
  /** Custom class name */
  className?: string;
}

/**
 * Chain data summary sidebar
 */
export function DNALabChainSummary({ onClose, className }: DNALabChainSummaryProps) {
  const { chainData, completedSteps, completionPercentage, goToStep } = useDNALabWorkflow();
  const chain = useDimensionChainOptional();
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());

  const toggleExpanded = (stepId: string) => {
    setExpandedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(stepId)) {
        next.delete(stepId);
      } else {
        next.add(stepId);
      }
      return next;
    });
  };

  const copyChainData = () => {
    const exportData = {
      steps: chainData,
      evidenceRefs: chain?.accumulatedEvidenceRefs || [],
      exportedAt: new Date().toISOString(),
    };
    navigator.clipboard.writeText(JSON.stringify(exportData, null, 2));
  };

  const downloadChainData = () => {
    const exportData = {
      steps: chainData,
      evidenceRefs: chain?.accumulatedEvidenceRefs || [],
      exportedAt: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `dna-lab-chain-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div
      className={cn(
        "h-full flex flex-col bg-stitch-surface border-l border-white/10 backdrop-blur-xl",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
        <div>
          <h3 className="text-sm font-medium text-white">체인 데이터</h3>
          <p className="text-xs text-white/40 mt-0.5">
            {completedSteps.length}/{DNA_LAB_STEPS.length} 완료 ({completionPercentage}%)
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1.5 text-white/40 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Progress bar */}
      <div className="px-4 py-2 border-b border-white/5">
        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-500"
            style={{ width: `${completionPercentage}%` }}
          />
        </div>
      </div>

      {/* Steps list */}
      <div className="flex-1 overflow-auto">
        {DNA_LAB_STEPS.map((step) => {
          const stepData = chainData[step.id];
          const isCompleted = !!stepData;
          const isExpanded = expandedSteps.has(step.id);
          const Icon = step.icon;

          return (
            <div key={step.id} className="border-b border-white/5">
              {/* Step header */}
              <button
                onClick={() => (isCompleted ? toggleExpanded(step.id) : goToStep(step.id))}
                className={cn(
                  "w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-white/5 transition-colors",
                  isExpanded && "bg-white/5"
                )}
              >
                {/* Status indicator */}
                <div
                  className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center",
                    isCompleted ? "bg-emerald-500/20" : "bg-white/5"
                  )}
                >
                  {isCompleted ? (
                    <Check className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <Icon className="w-4 h-4 text-white/40" />
                  )}
                </div>

                {/* Step info */}
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-white">{step.label}</div>
                  <div className="text-xs text-white/40 truncate">
                    {isCompleted ? "완료됨" : step.description}
                  </div>
                </div>

                {/* Expand/navigate indicator */}
                {isCompleted ? (
                  isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-white/40" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-white/40" />
                  )
                ) : (
                  <span className="text-xs text-white/40">이동</span>
                )}
              </button>

              {/* Expanded data preview */}
              {isCompleted && isExpanded && (
                <div className="px-4 pb-3">
                  <div className="p-3 bg-white/5 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <FileJson className="w-3 h-3 text-white/40" />
                      <span className="text-xs text-white/40">출력 데이터</span>
                    </div>
                    <pre className="text-xs text-white/60 overflow-auto max-h-32 font-mono">
                      {JSON.stringify(stepData, null, 2).slice(0, 500)}
                      {JSON.stringify(stepData).length > 500 && "..."}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Evidence refs section */}
      {chain?.accumulatedEvidenceRefs && chain.accumulatedEvidenceRefs.length > 0 && (
        <div className="px-4 py-3 border-t border-white/10">
          <div className="text-xs text-white/40 mb-2">
            Evidence Refs ({chain.accumulatedEvidenceRefs.length})
          </div>
          <div className="flex flex-wrap gap-1">
            {chain.accumulatedEvidenceRefs.slice(0, 5).map((ref, i) => (
              <span
                key={i}
                className="px-1.5 py-0.5 bg-white/5 text-white/60 text-[10px] rounded truncate max-w-[120px]"
                title={ref}
              >
                {ref.split(":").pop()}
              </span>
            ))}
            {chain.accumulatedEvidenceRefs.length > 5 && (
              <span className="px-1.5 py-0.5 bg-white/10 text-white/40 text-[10px] rounded">
                +{chain.accumulatedEvidenceRefs.length - 5} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Export actions */}
      <div className="px-4 py-3 border-t border-white/10 flex gap-2">
        <button
          onClick={copyChainData}
          disabled={completedSteps.length === 0}
          className={cn(
            "flex-1 flex items-center justify-center gap-2 px-3 py-2 text-xs rounded-lg transition-colors",
            completedSteps.length > 0
              ? "bg-white/5 text-white/60 hover:bg-white/10 hover:text-white"
              : "bg-white/5 text-white/20 cursor-not-allowed"
          )}
        >
          <Copy className="w-3 h-3" />
          복사
        </button>
        <button
          onClick={downloadChainData}
          disabled={completedSteps.length === 0}
          className={cn(
            "flex-1 flex items-center justify-center gap-2 px-3 py-2 text-xs rounded-lg transition-colors",
            completedSteps.length > 0
              ? "bg-white/5 text-white/60 hover:bg-white/10 hover:text-white"
              : "bg-white/5 text-white/20 cursor-not-allowed"
          )}
        >
          <Download className="w-3 h-3" />
          다운로드
        </button>
      </div>
    </div>
  );
}
