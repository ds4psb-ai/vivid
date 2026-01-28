"use client";

/**
 * UnifiedChainSidebar - Adaptive Chain Data Sidebar
 *
 * Progressive Deepening UI:
 * - Summary mode (DNA Lab): Icon + label + completion check
 * - Preview mode (Story Engine): Summary + expandable preview
 * - Detailed mode (Production): Full data + metadata + edit links
 *
 * 2026 Pattern: "Progressive Disclosure"
 * - Show only what's needed at each stage
 * - Enable deeper exploration on demand
 */

import { useState } from "react";
import {
  X,
  ChevronDown,
  ChevronRight,
  Check,
  Clock,
  FileJson,
  Copy,
  Download,
  Edit,
  AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useDimensionChainOptional, type ChainData } from "@/contexts/DimensionChainContext";
import { AnimatedList, AnimatedListItem, AnimatedTagList, AnimatedTagItem } from "@/components/ui/AnimatedList";
import { STEP_LABELS, CHAIN_DATA_SOURCE_MAP, getAllStepsMap } from "./workflow-configs";
import type { SidebarMode, WorkflowConfig, UnifiedWorkflowState, WorkflowStepMetadata } from "./types";

interface UnifiedChainSidebarProps {
  /** Display mode: summary, preview, or detailed */
  mode: SidebarMode;
  /** Workflow state */
  workflow: UnifiedWorkflowState;
  /** Workflow config */
  config: WorkflowConfig;
  /** Close handler */
  onClose?: () => void;
  /** Custom class name */
  className?: string;
}

/**
 * Adaptive chain data sidebar
 */
export function UnifiedChainSidebar({
  mode,
  workflow,
  config,
  onClose,
  className,
}: UnifiedChainSidebarProps) {
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
    if (!chain) return;
    const exportData = {
      app: config.id,
      steps: chain.chainData,
      evidenceRefs: chain.accumulatedEvidenceRefs || [],
      exportedAt: new Date().toISOString(),
    };
    navigator.clipboard.writeText(JSON.stringify(exportData, null, 2));
  };

  const downloadChainData = () => {
    if (!chain) return;
    const exportData = {
      app: config.id,
      steps: chain.chainData,
      evidenceRefs: chain.accumulatedEvidenceRefs || [],
      exportedAt: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${config.id}-chain-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Collect all chain data entries (from current app and previous apps)
  const allChainEntries = chain?.chainData || {};
  const hasChainData = Object.keys(allChainEntries).length > 0;

  return (
    <div
      className={cn(
        "h-full flex flex-col bg-black/95 border-l border-white/10 backdrop-blur-xl",
        className
      )}
    >
      {/* Header */}
      <SidebarHeader
        title="체인 데이터"
        completionRate={workflow.completionPercentage}
        totalSteps={config.steps.length}
        completedSteps={workflow.completedSteps.length}
        onClose={onClose}
      />

      {/* Progress bar */}
      <div className="px-4 py-2 border-b border-white/5">
        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-500"
            style={{ width: `${workflow.completionPercentage}%` }}
          />
        </div>
      </div>

      {/* Steps list based on mode */}
      <div className="flex-1 overflow-auto">
        {/* Current app steps */}
        <div className="px-4 pt-3 pb-1">
          <span className="text-[10px] uppercase tracking-wider text-white/30">
            {config.title}
          </span>
        </div>
        <AnimatedList staggerDelay={50} className="divide-y divide-white/5">
          {workflow.steps.map((stepState) => (
            <AnimatedListItem key={stepState.step.id}>
              <ChainDataItem
                stepId={stepState.step.id}
                step={stepState.step}
                chainEntry={allChainEntries[stepState.step.id] || allChainEntries[stepState.step.outputs[0]]}
                mode={mode}
                isExpanded={expandedSteps.has(stepState.step.id)}
                isCompleted={stepState.hasData}
                onToggle={() => toggleExpanded(stepState.step.id)}
                onNavigate={() => workflow.goToStep(stepState.step.id)}
              />
            </AnimatedListItem>
          ))}
        </AnimatedList>

        {/* Required chain data from previous apps (if any) */}
        {config.requiredChainData && config.requiredChainData.length > 0 && (
          <>
            <div className="px-4 pt-4 pb-1">
              <span className="text-[10px] uppercase tracking-wider text-white/30">
                이전 단계 데이터
              </span>
            </div>
            <AnimatedList staggerDelay={50} className="divide-y divide-white/5">
              {config.requiredChainData.map((key) => {
                const source = CHAIN_DATA_SOURCE_MAP[key];
                const chainEntry = allChainEntries[key];
                const allSteps = getAllStepsMap();
                const step = allSteps[key];

                return (
                  <AnimatedListItem key={key}>
                    <ChainDataItem
                      stepId={key}
                      step={step}
                      chainEntry={chainEntry}
                      mode={mode}
                      isExpanded={expandedSteps.has(key)}
                      isCompleted={!!chainEntry}
                      isExternal
                      externalSource={source}
                      onToggle={() => toggleExpanded(key)}
                    />
                  </AnimatedListItem>
                );
              })}
            </AnimatedList>
          </>
        )}
      </div>

      {/* Evidence refs section */}
      {chain?.accumulatedEvidenceRefs && chain.accumulatedEvidenceRefs.length > 0 && (
        <div className="px-4 py-3 border-t border-white/10">
          <div className="text-xs text-white/40 mb-2">
            Evidence Refs ({chain.accumulatedEvidenceRefs.length})
          </div>
          <AnimatedTagList className="gap-1" staggerDelay={30}>
            {chain.accumulatedEvidenceRefs.slice(0, 5).map((ref, i) => (
              <AnimatedTagItem
                key={i}
                className="px-1.5 py-0.5 bg-white/5 text-white/60 text-[10px] rounded truncate max-w-[120px]"
              >
                <span title={ref}>{ref.split(":").pop()}</span>
              </AnimatedTagItem>
            ))}
            {chain.accumulatedEvidenceRefs.length > 5 && (
              <AnimatedTagItem className="px-1.5 py-0.5 bg-white/10 text-white/40 text-[10px] rounded">
                +{chain.accumulatedEvidenceRefs.length - 5} more
              </AnimatedTagItem>
            )}
          </AnimatedTagList>
        </div>
      )}

      {/* Export actions (detailed mode only) */}
      {mode === "detailed" && (
        <SidebarFooter
          onCopy={copyChainData}
          onDownload={downloadChainData}
          disabled={!hasChainData}
        />
      )}

      {/* Simple export for other modes */}
      {mode !== "detailed" && hasChainData && (
        <div className="px-4 py-3 border-t border-white/10 flex gap-2">
          <button
            onClick={copyChainData}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-xs rounded-lg bg-white/5 text-white/60 hover:bg-white/10 hover:text-white transition-colors"
          >
            <Copy className="w-3 h-3" />
            복사
          </button>
          <button
            onClick={downloadChainData}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-xs rounded-lg bg-white/5 text-white/60 hover:bg-white/10 hover:text-white transition-colors"
          >
            <Download className="w-3 h-3" />
            다운로드
          </button>
        </div>
      )}
    </div>
  );
}

/**
 * Sidebar header component
 */
function SidebarHeader({
  title,
  completionRate,
  totalSteps,
  completedSteps,
  onClose,
}: {
  title: string;
  completionRate: number;
  totalSteps: number;
  completedSteps: number;
  onClose?: () => void;
}) {
  return (
    <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
      <div>
        <h3 className="text-sm font-medium text-white">{title}</h3>
        <p className="text-xs text-white/40 mt-0.5">
          {completedSteps}/{totalSteps} 완료 ({completionRate}%)
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
  );
}

/**
 * Sidebar footer with export actions
 */
function SidebarFooter({
  onCopy,
  onDownload,
  disabled,
}: {
  onCopy: () => void;
  onDownload: () => void;
  disabled: boolean;
}) {
  return (
    <div className="px-4 py-3 border-t border-white/10 flex gap-2">
      <button
        onClick={onCopy}
        disabled={disabled}
        className={cn(
          "flex-1 flex items-center justify-center gap-2 px-3 py-2 text-xs rounded-lg transition-colors",
          disabled
            ? "bg-white/5 text-white/20 cursor-not-allowed"
            : "bg-white/5 text-white/60 hover:bg-white/10 hover:text-white"
        )}
      >
        <Copy className="w-3 h-3" />
        복사
      </button>
      <button
        onClick={onDownload}
        disabled={disabled}
        className={cn(
          "flex-1 flex items-center justify-center gap-2 px-3 py-2 text-xs rounded-lg transition-colors",
          disabled
            ? "bg-white/5 text-white/20 cursor-not-allowed"
            : "bg-white/5 text-white/60 hover:bg-white/10 hover:text-white"
        )}
      >
        <Download className="w-3 h-3" />
        다운로드
      </button>
    </div>
  );
}

/**
 * Chain data item - renders differently based on mode
 */
function ChainDataItem({
  stepId,
  step,
  chainEntry,
  mode,
  isExpanded,
  isCompleted,
  isExternal = false,
  externalSource,
  onToggle,
  onNavigate,
}: {
  stepId: string;
  step?: WorkflowStepMetadata;
  chainEntry?: ChainData;
  mode: SidebarMode;
  isExpanded: boolean;
  isCompleted: boolean;
  isExternal?: boolean;
  externalSource?: { app: string; step: string; label: string };
  onToggle?: () => void;
  onNavigate?: () => void;
}) {
  const label = step?.label || externalSource?.label || STEP_LABELS[stepId] || stepId;
  const Icon = step?.icon;

  // Summary mode: Icon + label + completion check
  if (mode === "summary") {
    return (
      <button
        onClick={isCompleted ? onToggle : onNavigate}
        className={cn(
          "w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-white/5 transition-colors border-b border-white/5",
          isExternal && "opacity-60"
        )}
      >
        <div
          className={cn(
            "w-8 h-8 rounded-full flex items-center justify-center",
            isCompleted ? "bg-emerald-500/20" : "bg-white/5"
          )}
        >
          {isCompleted ? (
            <Check className="w-4 h-4 text-emerald-400" />
          ) : Icon ? (
            <Icon className="w-4 h-4 text-white/40" />
          ) : (
            <AlertCircle className="w-4 h-4 text-white/40" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm text-white">{label}</div>
          <div className="text-xs text-white/40 truncate">
            {isCompleted ? "완료됨" : isExternal ? "이전 단계 필요" : "진행 중"}
          </div>
        </div>
        {isCompleted && (
          isExpanded ? (
            <ChevronDown className="w-4 h-4 text-white/40" />
          ) : (
            <ChevronRight className="w-4 h-4 text-white/40" />
          )
        )}
      </button>
    );
  }

  // Preview mode: Summary + collapsible preview
  if (mode === "preview") {
    return (
      <div className="border-b border-white/5">
        <button
          onClick={isCompleted ? onToggle : onNavigate}
          className={cn(
            "w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-white/5 transition-colors",
            isExternal && "opacity-60"
          )}
        >
          <div
            className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center",
              isCompleted ? "bg-emerald-500/20" : "bg-white/5"
            )}
          >
            {isCompleted ? (
              <Check className="w-4 h-4 text-emerald-400" />
            ) : Icon ? (
              <Icon className="w-4 h-4 text-white/40" />
            ) : (
              <AlertCircle className="w-4 h-4 text-white/40" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm text-white">{label}</div>
            <div className="text-xs text-white/40 truncate">
              {chainEntry?.summary || (isCompleted ? "완료됨" : "미완료")}
            </div>
          </div>
          {isCompleted && (
            isExpanded ? (
              <ChevronDown className="w-4 h-4 text-white/40" />
            ) : (
              <ChevronRight className="w-4 h-4 text-white/40" />
            )
          )}
        </button>

        {/* Expandable preview */}
        {isCompleted && isExpanded && chainEntry && (
          <div className="px-4 pb-3">
            <DataPreview data={chainEntry.output} maxLines={5} />
          </div>
        )}
      </div>
    );
  }

  // Detailed mode: Full data + metadata + edit links
  return (
    <div className="border-b border-white/5">
      <div
        className={cn(
          "px-4 py-3",
          isExternal && "opacity-60"
        )}
      >
        {/* Header row */}
        <div className="flex items-center gap-3 mb-2">
          <div
            className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
              isCompleted ? "bg-emerald-500/20" : "bg-white/5"
            )}
          >
            {isCompleted ? (
              <Check className="w-4 h-4 text-emerald-400" />
            ) : Icon ? (
              <Icon className="w-4 h-4 text-white/40" />
            ) : (
              <AlertCircle className="w-4 h-4 text-white/40" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-white">{label}</div>
            <div className="text-xs text-white/40 flex items-center gap-2">
              {chainEntry?.timestamp && (
                <>
                  <Clock className="w-3 h-3" />
                  {formatTimestamp(chainEntry.timestamp)}
                </>
              )}
              {chainEntry?.evidenceRefs && chainEntry.evidenceRefs.length > 0 && (
                <>
                  <span>•</span>
                  <span>{chainEntry.evidenceRefs.length} refs</span>
                </>
              )}
            </div>
          </div>
          {!isExternal && onNavigate && (
            <button
              onClick={onNavigate}
              className="p-1.5 text-white/40 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
              title="편집"
            >
              <Edit className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* Data viewer */}
        {chainEntry?.output && (
          <div className="mt-2">
            <DataViewer data={chainEntry.output} />
          </div>
        )}

        {/* Not completed */}
        {!isCompleted && !isExternal && (
          <button
            onClick={onNavigate}
            className="mt-2 w-full py-2 text-xs text-white/60 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
          >
            단계로 이동
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Data preview (for preview mode)
 */
function DataPreview({
  data,
  maxLines = 5,
}: {
  data: Record<string, unknown>;
  maxLines?: number;
}) {
  const jsonString = JSON.stringify(data, null, 2);
  const lines = jsonString.split("\n");
  const truncated = lines.length > maxLines;
  const displayLines = lines.slice(0, maxLines);

  return (
    <div className="p-3 bg-white/5 rounded-lg">
      <div className="flex items-center gap-2 mb-2">
        <FileJson className="w-3 h-3 text-white/40" />
        <span className="text-xs text-white/40">출력 데이터</span>
      </div>
      <pre className="text-xs text-white/60 overflow-auto max-h-32 font-mono">
        {displayLines.join("\n")}
        {truncated && "\n..."}
      </pre>
    </div>
  );
}

/**
 * Data viewer (for detailed mode)
 */
function DataViewer({ data }: { data: Record<string, unknown> }) {
  // Show key-value pairs for top-level properties
  const entries = Object.entries(data).slice(0, 10);

  return (
    <div className="space-y-1">
      {entries.map(([key, value]) => (
        <div key={key} className="flex items-start gap-2 text-xs">
          <span className="text-white/40 shrink-0">{key}:</span>
          <span className="text-white/60 truncate">
            {typeof value === "object"
              ? JSON.stringify(value).slice(0, 50) + "..."
              : String(value).slice(0, 100)}
          </span>
        </div>
      ))}
      {Object.keys(data).length > 10 && (
        <div className="text-xs text-white/30">
          +{Object.keys(data).length - 10} more properties
        </div>
      )}
    </div>
  );
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return "방금 전";
  if (diffMins < 60) return `${diffMins}분 전`;
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}시간 전`;
  return date.toLocaleDateString("ko-KR");
}
