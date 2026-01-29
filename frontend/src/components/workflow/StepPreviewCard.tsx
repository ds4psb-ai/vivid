"use client";

/**
 * StepPreviewCard - Progressive Disclosure Step Card
 *
 * Phase 4: Workflow UX Innovation
 *
 * Features:
 * - Status-based color/icon system (completed, active, pending, error, skipped)
 * - Input source badges with origin coloring (internal, dna-lab, story-engine, production)
 * - Output data JSON preview with truncation
 * - Three display modes: collapsed, compact, expanded
 * - Action bar: Copy JSON, Edit, Navigate
 *
 * 2026 Pattern: "Progressive Disclosure"
 * - Show only what's needed at each interaction level
 * - Enable deeper exploration on demand
 */

import { useState } from "react";
import {
  Check,
  Loader2,
  Clock,
  AlertCircle,
  SkipForward,
  ChevronDown,
  ChevronRight,
  Copy,
  Edit,
  ExternalLink,
  FileJson,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type {
  WorkflowStepMetadata,
  StepState,
  StepStatus,
  ChainDataEntry,
  MegaAppId,
} from "./types";

// =============================================================================
// Types
// =============================================================================

/** Input source origin */
export type InputSourceOrigin = "internal" | "dna-lab" | "story-engine" | "production";

/** Input source info */
export interface InputSourceInfo {
  /** Data key name */
  dataKey: string;
  /** Origin app/source */
  source: InputSourceOrigin;
  /** Whether data is available */
  available: boolean;
  /** Optional display label */
  label?: string;
}

/** Display mode for progressive disclosure */
export type StepPreviewMode = "collapsed" | "compact" | "expanded";

export interface StepPreviewCardProps {
  // Step metadata
  /** Step configuration */
  step: WorkflowStepMetadata;
  /** Current step state */
  stepState: StepState;

  // Chain data
  /** Chain entry data (if available) */
  chainEntry?: ChainDataEntry;
  /** Input sources with availability */
  inputSources?: InputSourceInfo[];

  // Mode
  /** Display mode */
  mode?: StepPreviewMode;
  /** Start expanded in collapsed mode */
  defaultExpanded?: boolean;

  // Events
  /** Click handler for navigation */
  onClick?: () => void;
  /** Edit handler */
  onEdit?: () => void;
  /** Copy handler */
  onCopy?: () => void;

  // Style
  /** Custom class name */
  className?: string;
}

// =============================================================================
// Config
// =============================================================================

/** Status visual configuration */
const STATUS_CONFIG: Record<
  StepStatus,
  {
    bg: string;
    text: string;
    icon: typeof Check;
    label: string;
    labelEn: string;
  }
> = {
  completed: {
    bg: "bg-emerald-500/20",
    text: "text-emerald-400",
    icon: Check,
    label: "완료",
    labelEn: "Completed",
  },
  active: {
    bg: "bg-blue-500/20",
    text: "text-blue-400",
    icon: Loader2,
    label: "진행 중",
    labelEn: "Active",
  },
  pending: {
    bg: "bg-slate-500/20",
    text: "text-slate-400",
    icon: Clock,
    label: "대기",
    labelEn: "Pending",
  },
  error: {
    bg: "bg-red-500/20",
    text: "text-red-400",
    icon: AlertCircle,
    label: "오류",
    labelEn: "Error",
  },
  skipped: {
    bg: "bg-slate-500/10",
    text: "text-slate-300",
    icon: SkipForward,
    label: "건너뜀",
    labelEn: "Skipped",
  },
};

/** Input source visual configuration */
const SOURCE_CONFIG: Record<
  InputSourceOrigin,
  {
    bg: string;
    text: string;
    label: string;
    labelEn: string;
  }
> = {
  internal: {
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    label: "내부",
    labelEn: "Internal",
  },
  "dna-lab": {
    bg: "bg-cyan-500/10",
    text: "text-cyan-400",
    label: "DNA Lab",
    labelEn: "DNA Lab",
  },
  "story-engine": {
    bg: "bg-purple-500/10",
    text: "text-purple-400",
    label: "Story Engine",
    labelEn: "Story Engine",
  },
  production: {
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    label: "Production",
    labelEn: "Production",
  },
};

// =============================================================================
// Sub-Components
// =============================================================================

/**
 * Status badge with icon and color
 */
function StepStatusBadge({
  status,
  className,
}: {
  status: StepStatus;
  className?: string;
}) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;
  const isAnimated = status === "active";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium",
        config.bg,
        config.text,
        className
      )}
    >
      <Icon
        className={cn("w-3 h-3", isAnimated && "animate-spin")}
      />
      {config.label}
    </span>
  );
}

/**
 * Input source badge showing origin and availability
 */
function InputSourceBadge({
  dataKey,
  source,
  available,
  label,
  className,
}: InputSourceInfo & { className?: string }) {
  const config = SOURCE_CONFIG[source];
  const isExternal = source !== "internal";

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs",
        config.bg,
        className
      )}
    >
      {available ? (
        <Check className="w-3 h-3 text-emerald-400" />
      ) : (
        <AlertCircle className="w-3 h-3 text-amber-400" />
      )}
      <span className={cn(config.text, !available && "opacity-60")}>
        {label || dataKey}
      </span>
      {isExternal && (
        <span className="text-white/30 text-[10px]">({config.label})</span>
      )}
      {isExternal && available && (
        <ExternalLink className={cn("w-2.5 h-2.5", config.text, "opacity-60")} />
      )}
    </div>
  );
}

/**
 * Output data JSON preview with truncation
 */
function OutputDataPreview({
  data,
  maxLines = 5,
  className,
}: {
  data: Record<string, unknown>;
  maxLines?: number;
  className?: string;
}) {
  const json = JSON.stringify(data, null, 2);
  const lines = json.split("\n");
  const truncated = lines.length > maxLines;
  const displayLines = lines.slice(0, maxLines);
  const propertyCount = Object.keys(data).length;

  return (
    <div className={cn("rounded-lg overflow-hidden", className)}>
      <div className="flex items-center gap-2 px-3 py-2 bg-white/5 border-b border-white/5">
        <FileJson className="w-3 h-3 text-white/40" />
        <span className="text-xs text-white/40">출력 데이터</span>
        <span className="text-[10px] text-white/30 ml-auto">
          {propertyCount} properties
        </span>
      </div>
      <pre className="p-3 text-xs text-white/60 font-mono bg-black/20 overflow-x-auto">
        {displayLines.join("\n")}
        {truncated && (
          <span className="text-white/30">
            {"\n"}... +{lines.length - maxLines} more lines
          </span>
        )}
      </pre>
    </div>
  );
}

/**
 * Inline output summary (for compact view)
 */
function OutputSummary({
  data,
  summary,
  className,
}: {
  data?: Record<string, unknown>;
  summary?: string;
  className?: string;
}) {
  if (summary) {
    return (
      <p className={cn("text-xs text-white/60 line-clamp-2", className)}>
        {summary}
      </p>
    );
  }

  if (!data) return null;

  const keys = Object.keys(data);
  const preview = keys.slice(0, 3).join(", ");
  const remaining = keys.length - 3;

  return (
    <p className={cn("text-xs text-white/40 font-mono", className)}>
      {`{ ${preview}${remaining > 0 ? `, +${remaining}` : ""} }`}
    </p>
  );
}

/**
 * Action bar with copy, edit, navigate
 */
function ActionBar({
  onCopy,
  onEdit,
  onNavigate,
  hasCopyData,
  className,
}: {
  onCopy?: () => void;
  onEdit?: () => void;
  onNavigate?: () => void;
  hasCopyData: boolean;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!onCopy) return;
    onCopy();
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div
      className={cn(
        "flex items-center gap-2 pt-3 border-t border-white/5",
        className
      )}
    >
      {hasCopyData && (
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-white/5 text-white/60 hover:bg-white/10 hover:text-white transition-colors"
        >
          <Copy className="w-3 h-3" />
          {copied ? "복사됨" : "JSON 복사"}
        </button>
      )}
      {onEdit && (
        <button
          onClick={onEdit}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-white/5 text-white/60 hover:bg-white/10 hover:text-white transition-colors"
        >
          <Edit className="w-3 h-3" />
          편집
        </button>
      )}
      {onNavigate && (
        <button
          onClick={onNavigate}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-white/5 text-white/60 hover:bg-white/10 hover:text-white transition-colors ml-auto"
        >
          이동
          <ExternalLink className="w-3 h-3" />
        </button>
      )}
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

/**
 * StepPreviewCard - Progressive Disclosure Step Card
 *
 * Three modes:
 * - collapsed: Status header only, click to expand
 * - compact: Status + input sources + output summary
 * - expanded: Full detail with JSON preview and actions
 */
export function StepPreviewCard({
  step,
  stepState,
  chainEntry,
  inputSources = [],
  mode = "compact",
  defaultExpanded = false,
  onClick,
  onEdit,
  onCopy,
  className,
}: StepPreviewCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const status = stepState.status;
  const statusConfig = STATUS_CONFIG[status];
  const Icon = step.icon;
  const hasOutput = !!chainEntry?.output;
  const hasInputSources = inputSources.length > 0;

  // Effective mode - collapsed can expand
  const effectiveMode = mode === "collapsed" && isExpanded ? "compact" : mode;

  // Copy handler
  const handleCopy = () => {
    if (chainEntry?.output) {
      navigator.clipboard.writeText(JSON.stringify(chainEntry.output, null, 2));
    }
    onCopy?.();
  };

  // Toggle expansion for collapsed mode
  const handleHeaderClick = () => {
    if (mode === "collapsed") {
      setIsExpanded(!isExpanded);
    }
    onClick?.();
  };

  return (
    <div
      className={cn(
        "rounded-xl border transition-all duration-200",
        "bg-black/40 backdrop-blur-sm",
        status === "active" && "border-blue-500/30 ring-1 ring-blue-500/20",
        status === "completed" && "border-emerald-500/20",
        status === "error" && "border-red-500/30",
        status === "pending" && "border-white/10",
        status === "skipped" && "border-white/5 opacity-60",
        className
      )}
    >
      {/* Status Header - Always visible */}
      <button
        onClick={handleHeaderClick}
        className={cn(
          "w-full flex items-center gap-3 p-4 text-left transition-colors",
          mode === "collapsed" && "hover:bg-white/5 cursor-pointer",
          mode !== "collapsed" && onClick && "hover:bg-white/5 cursor-pointer"
        )}
      >
        {/* Step Icon */}
        <div
          className={cn(
            "w-10 h-10 rounded-full flex items-center justify-center shrink-0",
            statusConfig.bg
          )}
        >
          <Icon className={cn("w-5 h-5", statusConfig.text)} />
        </div>

        {/* Label & Description */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-medium text-white truncate">
              {step.label}
            </h3>
            <StepStatusBadge status={status} />
          </div>
          {effectiveMode !== "collapsed" && (
            <p className="text-xs text-white/50 mt-0.5 line-clamp-1">
              {step.description}
            </p>
          )}
        </div>

        {/* Expand indicator for collapsed mode */}
        {mode === "collapsed" && (
          isExpanded ? (
            <ChevronDown className="w-4 h-4 text-white/40 shrink-0" />
          ) : (
            <ChevronRight className="w-4 h-4 text-white/40 shrink-0" />
          )
        )}
      </button>

      {/* Input Section - Compact & Expanded */}
      {(effectiveMode === "compact" || effectiveMode === "expanded") &&
        hasInputSources && (
          <div className="px-4 pb-3 border-t border-white/5 pt-3">
            <div className="text-[10px] uppercase tracking-wider text-white/30 mb-2">
              입력 데이터
            </div>
            <div className="flex flex-wrap gap-1.5">
              {inputSources.map((source) => (
                <InputSourceBadge key={source.dataKey} {...source} />
              ))}
            </div>
          </div>
        )}

      {/* Output Preview - Compact (summary) */}
      {effectiveMode === "compact" && hasOutput && (
        <div className="px-4 pb-4">
          <OutputSummary
            data={chainEntry?.output}
            summary={chainEntry?.summary}
          />
        </div>
      )}

      {/* Output Preview - Expanded (full JSON) */}
      {effectiveMode === "expanded" && hasOutput && (
        <div className="px-4 pb-4">
          <OutputDataPreview data={chainEntry!.output} maxLines={8} />
        </div>
      )}

      {/* Action Bar - Expanded only */}
      {effectiveMode === "expanded" && (
        <div className="px-4 pb-4">
          <ActionBar
            onCopy={hasOutput ? handleCopy : undefined}
            onEdit={onEdit}
            onNavigate={onClick}
            hasCopyData={hasOutput}
          />
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Exports
// =============================================================================

export default StepPreviewCard;

export { StepStatusBadge, InputSourceBadge, OutputDataPreview };
