"use client";

import { memo } from "react";
import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import {
  Activity,
  AlertTriangle,
  Ban,
  CheckCircle2,
  FileInput,
  FileOutput,
  Loader2,
  Palette,
  Settings,
  Sparkles,
  Workflow,
  Video,
} from "lucide-react";
import { motion } from "framer-motion";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { useLanguage } from "@/contexts/LanguageContext";
import { getBeatLabel, getStoryboardLabel } from "@/lib/narrative";

// Utility for cleaner classes
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export type CanvasNodeKind =
  | "input"
  | "style"
  | "customization"
  | "processing"
  | "output"
  | "capsule"
  | "asset";

// Handle types matching backend
export type HandleType = "text" | "image" | "video" | "audio" | "dna" | "metadata" | "any";
export type HandlePosition = "left" | "right" | "top" | "bottom";

export interface NodeHandle {
  id: string;
  type: HandleType;
  position: HandlePosition;
  label?: string;
  required?: boolean;
  max_connections?: number;
}

// Handle type colors
const HANDLE_COLORS: Record<HandleType, string> = {
  text: "bg-sky-400",
  image: "bg-amber-400",
  video: "bg-emerald-400",
  audio: "bg-purple-400",
  dna: "bg-rose-400",
  metadata: "bg-slate-400",
  any: "bg-white",
};

export interface CanvasNodeData extends Record<string, unknown> {
  label: string;
  subtitle?: string;
  description?: string;
  // Node category (from backend)
  category?: "input" | "generate" | "refine" | "validate" | "compose" | "output";
  // 5-State FSM: idle | loading | streaming | complete | error
  status?: "idle" | "loading" | "streaming" | "complete" | "error" | "cancelled";
  // Typed handles
  input_handles?: NodeHandle[];
  output_handles?: NodeHandle[];
  // AI model
  ai_model?: string;
  // Capsule node specific
  capsuleId?: string;
  capsuleVersion?: string;
  patternVersion?: string;
  inputContracts?: {
    required?: string[];
    optional?: string[];
    maxUpstream?: number;
    allowedTypes?: string[];
    contextMode?: "aggregate" | "sequential";
  };
  params?: Record<string, unknown>;
  evidence_refs?: string[];
  locked?: boolean;
  // DNA Compliance status
  complianceStatus?: "compliant" | "warning" | "violation";
  complianceIssueCount?: number;
  // Streaming state data
  streamingData?: {
    partialText: string;
    progress: number;
  };
  generationPreview?: {
    beat_sheet?: Array<Record<string, unknown>>;
    storyboard?: Array<Record<string, unknown>>;
  };
}

// Visual configuration for each node type
const NODE_CONFIG: Record<
  CanvasNodeKind,
  {
    icon: React.ElementType;
    gradient: string;
    glow: string;
    text: string;
    badge: string;
  }
> = {
  input: {
    icon: FileInput,
    gradient: "from-sky-400 to-blue-600",
    glow: "shadow-sky-500/20",
    text: "text-sky-100",
    badge: "bg-sky-500/20 text-sky-200 border-sky-500/30",
  },
  style: {
    icon: Palette,
    gradient: "from-amber-300 to-orange-500",
    glow: "shadow-amber-500/20",
    text: "text-amber-100",
    badge: "bg-amber-500/20 text-amber-200 border-amber-500/30",
  },
  customization: {
    icon: Settings,
    gradient: "from-slate-400 to-zinc-600",
    glow: "shadow-slate-500/20",
    text: "text-slate-100",
    badge: "bg-slate-500/20 text-slate-200 border-slate-500/30",
  },
  processing: {
    icon: Sparkles,
    gradient: "from-teal-400 to-cyan-600",
    glow: "shadow-cyan-500/30",
    text: "text-cyan-100",
    badge: "bg-cyan-500/20 text-cyan-200 border-cyan-500/30",
  },
  output: {
    icon: FileOutput,
    gradient: "from-emerald-400 to-teal-600",
    glow: "shadow-emerald-500/20",
    text: "text-emerald-100",
    badge: "bg-emerald-500/20 text-emerald-200 border-emerald-500/30",
  },
  capsule: {
    icon: Workflow,
    gradient: "from-rose-400 to-pink-600",
    glow: "shadow-rose-500/30",
    text: "text-rose-100",
    badge: "bg-rose-500/20 text-rose-200 border-rose-500/30",
  },
  asset: {
    icon: Video,
    gradient: "from-violet-400 to-fuchsia-600",
    glow: "shadow-violet-500/30",
    text: "text-violet-100",
    badge: "bg-violet-500/20 text-violet-200 border-violet-500/30",
  },
};

export const CanvasNode = memo(BaseNode);

function BaseNode({ data, type, selected }: NodeProps<Node<CanvasNodeData>>) {
  const { t } = useLanguage();
  const kind = (type as CanvasNodeKind) || "customization";
  const config = NODE_CONFIG[kind];
  const Icon = config.icon;

  const canReceive = kind !== "input";
  const canSend = kind !== "output";
  const isCapsule = kind === "capsule";
  const status = data.status ?? "idle";
  const evidenceRefs = Array.isArray(data.evidence_refs) ? data.evidence_refs : [];
  const evidenceCount = evidenceRefs.length;
  const complianceStatus = data.complianceStatus;
  const complianceIssueCount = data.complianceIssueCount || 0;

  // 5-State FSM Visual Mapping
  const statusConfig: Record<string, { class: string; label: string; icon: React.ElementType }> = {
    idle: { class: "border-white/5 bg-white/5 text-slate-400", label: t("statusReady"), icon: CheckCircle2 },
    loading: { class: "border-sky-500/30 bg-sky-500/10 text-sky-300 animate-pulse", label: t("statusLoading"), icon: Loader2 },
    streaming: { class: "border-amber-500/30 bg-amber-500/10 text-amber-300 shadow-[0_0_15px_-3px_rgba(245,158,11,0.2)]", label: t("statusStreaming"), icon: Activity },
    complete: { class: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300", label: t("statusComplete"), icon: CheckCircle2 },
    error: { class: "border-rose-500/30 bg-rose-500/10 text-rose-300", label: t("statusError"), icon: AlertTriangle },
    cancelled: { class: "border-slate-500/30 bg-slate-500/10 text-slate-400", label: t("statusCancelled"), icon: Ban },
  };
  const statusStyle = statusConfig[status] || statusConfig.idle;
  const StatusIcon = statusStyle.icon;
  const statusIconClass = cn("h-3 w-3", status === "loading" && "animate-spin");
  const generationPreview = kind === "output" ? data.generationPreview : undefined;
  const beatSheet = Array.isArray(generationPreview?.beat_sheet)
    ? generationPreview?.beat_sheet
    : [];
  const storyboard = Array.isArray(generationPreview?.storyboard)
    ? generationPreview?.storyboard
    : [];
  const hasPreview = beatSheet.length > 0 || storyboard.length > 0;

  const kindLabelMap: Record<CanvasNodeKind, string> = {
    input: t("nodeInput"),
    style: t("nodeStyle"),
    customization: t("nodeCustom"),
    processing: t("nodeProcess"),
    output: t("nodeOutput"),
    capsule: t("nodeCapsule"),
    asset: "Asset",
  };

  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      whileHover={{ scale: 1.02, y: -2 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={cn(
        "relative min-w-[260px] rounded-2xl border px-5 py-5 transition-all duration-300",
        // Glassmorphism Base
        "bg-[#0a0a0c]/60 backdrop-blur-2xl",
        // Border Logic
        selected
          ? `border-${config.gradient.split("-")[1]}-500/50 shadow-[0_0_40px_-10px_rgba(var(--${config.gradient.split("-")[1]}-500-rgb),0.3)]`
          : "border-white/5 hover:border-white/10",
        selected && "z-10"
      )}
    >
      {/* Cinematic Glow on Selection */}
      {selected && (
        <div
          className={cn(
            "absolute inset-0 -z-10 rounded-2xl opacity-10 bg-gradient-to-br",
            config.gradient
          )}
        />
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-xl shadow-lg border border-white/10",
              `bg-gradient-to-br ${config.gradient}`
            )}
          >
            <Icon className="h-5 w-5 text-white" strokeWidth={2} />
          </div>
          <div>
            <div
              className={cn(
                "text-[10px] font-bold uppercase tracking-widest opacity-70 mb-0.5",
                config.text
              )}
            >
              {kindLabelMap[kind] || kind}
            </div>
            <div className="text-base font-bold text-slate-100 leading-none tracking-tight">
              {data.label}
            </div>
          </div>
        </div>

        {/* Badges */}
        <div className="flex flex-col items-end gap-1.5">
          {/* DNA Compliance Badge */}
          {complianceStatus === "violation" && (
            <span className="inline-flex items-center gap-1 rounded-full border border-red-500/30 bg-red-500/10 px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest text-red-400 animate-pulse">
              <AlertTriangle size={10} />
              {complianceIssueCount > 0 ? `${complianceIssueCount} issues` : "DNA 위반"}
            </span>
          )}
          {complianceStatus === "warning" && (
            <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest text-amber-400">
              <AlertTriangle size={10} />
              {complianceIssueCount > 0 ? `${complianceIssueCount} warnings` : "주의"}
            </span>
          )}
          {/* Capsule Badges */}
          {isCapsule && (
            <>
              <span className="inline-flex items-center rounded-full border border-rose-500/20 bg-rose-500/5 px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest text-rose-300/80">
                {t("sealed")}
              </span>
              {evidenceCount > 0 && (
                <span className="inline-flex items-center rounded-full border border-emerald-500/20 bg-emerald-500/5 px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest text-emerald-300/80">
                  {t("evidenceRefs")} {evidenceCount}
                </span>
              )}
            </>
          )}
        </div>
      </div>

      {/* Skeleton Loading State */}
      {status === "loading" && (
        <div className="mb-4 space-y-3 px-1">
          <div className="h-3 w-3/4 rounded bg-white/10 animate-pulse" />
          <div className="space-y-2">
            <div className="h-20 rounded-xl border border-white/5 bg-white/5 animate-pulse" />
            <div className="flex gap-2">
              <div className="h-2 w-1/2 rounded bg-white/10 animate-pulse" />
              <div className="h-2 w-1/4 rounded bg-white/10 animate-pulse" />
            </div>
          </div>
        </div>
      )}

      {/* Subtitle / Description */}
      {status !== "loading" && data.subtitle && (
        <div className="mb-4 text-xs font-medium text-slate-400 leading-relaxed pl-1">
          {data.subtitle}
        </div>
      )}

      {/* Preview Content (Cards within Node) */}
      {status !== "loading" && hasPreview && (
        <div className="mb-4 overflow-hidden rounded-xl border border-white/5 bg-black/20">
          <div className="flex items-center justify-between border-b border-white/5 bg-white/5 px-3 py-1.5">
            <span className="text-[10px] font-bold uppercase tracking-widest text-emerald-400/80">
              {t("generationPreview")}
            </span>
            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
          </div>
          <div className="p-3 space-y-2">
            {beatSheet.slice(0, 1).map((beat, idx) => (
              <div key={idx} className="flex gap-2">
                <span className="shrink-0 text-[10px] font-mono text-slate-500">{`0${idx + 1}`}</span>
                <p className="text-[11px] text-slate-300 line-clamp-2">
                  {getBeatLabel(beat) ?? ""}
                </p>
              </div>
            ))}
            {storyboard.slice(0, 1).map((shot, idx) => {
              const shotData = shot as Record<string, unknown>;
              const dominant = String(shotData.dominant_color ?? "#334155");
              const shotLabel = getStoryboardLabel(shot);
              return (
                <div key={`shot-${idx}`} className="flex items-center gap-2 mt-2 pt-2 border-t border-white/5">
                  <div className="h-3 w-3 rounded-full shadow-inner" style={{ backgroundColor: dominant }} />
                  <span className="text-[10px] uppercase tracking-wide text-slate-400 truncate max-w-[150px]">
                    {shotLabel || String(shotData.composition ?? "Shot Composition")}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Footer / Status */}
      <div className="flex items-center justify-between pt-2 border-t border-white/5">
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold border transition-all duration-300",
            statusStyle.class
          )}
        >
          <StatusIcon className={statusIconClass} />
          {statusStyle.label}
        </span>
        {status === "streaming" && data.streamingData && (
          <span className="text-[10px] font-mono text-amber-400/80">
            {Math.round(data.streamingData.progress)}%
          </span>
        )}
      </div>

      {/* Streaming Text Effect */}
      {status === "streaming" && data.streamingData?.partialText && (
        <div className="mt-3 rounded-lg border border-amber-500/10 bg-amber-500/5 px-3 py-2">
          <p className="text-[11px] font-mono text-amber-200/80 leading-relaxed line-clamp-2">
            {data.streamingData.partialText}
            <motion.span
              animate={{ opacity: [0, 1, 0] }}
              transition={{ repeat: Infinity, duration: 0.8 }}
              className="inline-block w-1.5 h-3 ml-0.5 align-middle bg-amber-400"
            />
          </p>
        </div>
      )}

      {/* Handles - Multi-Handle with Typed Colors */}
      {/* Legacy fallback for nodes without typed handles */}
      {!data.input_handles?.length && canReceive && (
        <Handle
          type="target"
          position={Position.Left}
          className={cn(
            "!h-3 !w-3 !rounded-full !border-[3px] !border-[#0a0a0c] transition-transform duration-200",
            "bg-slate-500 hover:scale-125 hover:bg-white"
          )}
        />
      )}
      {!data.output_handles?.length && canSend && (
        <Handle
          type="source"
          position={Position.Right}
          className={cn(
            "!h-3 !w-3 !rounded-full !border-[3px] !border-[#0a0a0c] transition-transform duration-200",
            "bg-slate-500 hover:scale-125 hover:bg-white"
          )}
        />
      )}

      {/* Typed input handles */}
      {data.input_handles?.map((handle, idx) => {
        const positionMap: Record<string, Position> = {
          left: Position.Left,
          right: Position.Right,
          top: Position.Top,
          bottom: Position.Bottom,
        };
        const pos = positionMap[handle.position] || Position.Left;
        const isVertical = pos === Position.Top || pos === Position.Bottom;
        const offset = isVertical
          ? { left: `${30 + idx * 25}%` }
          : { top: `${30 + idx * 20}%` };

        return (
          <Handle
            key={handle.id}
            id={handle.id}
            type="target"
            position={pos}
            style={offset}
            className={cn(
              "!h-3 !w-3 !rounded-full !border-[2px] !border-[#0a0a0c] transition-all duration-200",
              HANDLE_COLORS[handle.type] || "bg-slate-500",
              "hover:scale-150 hover:!border-white",
              !handle.required && "opacity-70"
            )}
            title={handle.label || handle.type}
          />
        );
      })}

      {/* Typed output handles */}
      {data.output_handles?.map((handle, idx) => {
        const positionMap: Record<string, Position> = {
          left: Position.Left,
          right: Position.Right,
          top: Position.Top,
          bottom: Position.Bottom,
        };
        const pos = positionMap[handle.position] || Position.Right;
        const isVertical = pos === Position.Top || pos === Position.Bottom;
        const offset = isVertical
          ? { left: `${30 + idx * 25}%` }
          : { top: `${30 + idx * 20}%` };

        return (
          <Handle
            key={handle.id}
            id={handle.id}
            type="source"
            position={pos}
            style={offset}
            className={cn(
              "!h-3 !w-3 !rounded-full !border-[2px] !border-[#0a0a0c] transition-all duration-200",
              HANDLE_COLORS[handle.type] || "bg-slate-500",
              "hover:scale-150 hover:!border-white"
            )}
            title={handle.label || handle.type}
          />
        );
      })}
    </motion.div>
  );
}
