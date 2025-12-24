"use client";

import { memo } from "react";
import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import {
  FileInput,
  FileOutput,
  Lock,
  Palette,
  Settings,
  Sparkles,
  Workflow,
} from "lucide-react";
import { motion } from "framer-motion";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { useLanguage } from "@/contexts/LanguageContext";

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
  | "capsule";

export interface CanvasNodeData extends Record<string, unknown> {
  label: string;
  subtitle?: string;
  // Optional: override icon or add explicit status
  status?: "idle" | "running" | "error" | "success";
  // Capsule node specific
  capsuleId?: string;
  capsuleVersion?: string;
  params?: Record<string, unknown>;
  locked?: boolean;
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
    gradient: "from-fuchsia-400 to-purple-600",
    glow: "shadow-purple-500/30",
    text: "text-purple-100",
    badge: "bg-purple-500/20 text-purple-200 border-purple-500/30",
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
};

function BaseNode({ data, type, selected }: NodeProps<Node<CanvasNodeData>>) {
  const { t } = useLanguage();
  const kind = (type as CanvasNodeKind) || "customization";
  const config = NODE_CONFIG[kind];
  const Icon = config.icon;

  const canReceive = kind !== "input";
  const canSend = kind !== "output";
  const isCapsule = kind === "capsule";
  const isLocked = isCapsule && Boolean(data.locked);
  const status = data.status ?? "idle";
  const statusClass =
    status === "running"
      ? "bg-amber-500/20 text-amber-200 border-amber-500/30"
      : status === "success"
        ? "bg-emerald-500/20 text-emerald-200 border-emerald-500/30"
        : status === "error"
          ? "bg-rose-500/20 text-rose-200 border-rose-500/30"
          : config.badge;
  const generationPreview = kind === "output" ? data.generationPreview : undefined;
  const beatSheet = Array.isArray(generationPreview?.beat_sheet)
    ? generationPreview?.beat_sheet
    : [];
  const storyboard = Array.isArray(generationPreview?.storyboard)
    ? generationPreview?.storyboard
    : [];
  const hasPreview = beatSheet.length > 0 || storyboard.length > 0;

  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      whileHover={{ scale: 1.02, y: -2 }}
      transition={{ duration: 0.2 }}
      className={cn(
        "relative min-w-[240px] rounded-2xl border bg-slate-950/80 px-4 py-4 backdrop-blur-xl transition-all duration-300",
        selected
          ? `border-transparent ring-2 ring-offset-2 ring-offset-slate-950 ring-${config.gradient.split("-")[1]}-400`
          : "border-slate-800",
        config.glow,
        selected && "shadow-2xl"
      )}
    >
      {/* Gradient border effect via pseudo-element container if desired, or simple border for MVP */}
      {selected && (
        <div
          className={cn(
            "absolute inset-0 -z-10 rounded-2xl opacity-20 bg-gradient-to-br",
            config.gradient
          )}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br shadow-inner",
              config.gradient
            )}
          >
            <Icon className="h-4 w-4 text-white" strokeWidth={2.5} />
          </div>
          <div>
            <div
              className={cn(
                "text-xs font-bold uppercase tracking-wider opacity-60",
                config.text
              )}
            >
              {kind}
            </div>
            <div className="text-sm font-bold text-slate-100 leading-tight">
              {data.label}
            </div>
          </div>
        </div>
        {isCapsule && (
          <div className="flex items-center gap-1 text-[10px] uppercase tracking-widest">
            <span className="rounded-full border border-rose-400/30 bg-rose-500/10 px-2 py-0.5 text-rose-200">
              Sealed
            </span>
            {isLocked && (
              <span className="flex items-center gap-1 rounded-full border border-slate-400/30 bg-slate-500/10 px-2 py-0.5 text-slate-200">
                <Lock className="h-3 w-3" />
                Locked
              </span>
            )}
          </div>
        )}
      </div>

      {/* Body / Content */}
      {data.subtitle && (
        <div className="mb-2 rounded-md bg-slate-900/50 px-3 py-2 text-xs font-medium text-slate-400">
          {data.subtitle}
        </div>
      )}

      {hasPreview && (
        <div className="mb-3 rounded-md border border-emerald-500/20 bg-emerald-500/5 px-3 py-2 text-xs text-slate-200">
          <div className="text-[10px] uppercase tracking-widest text-emerald-300">
            {t("generationPreview")}
          </div>
          {beatSheet.length > 0 && (
            <div className="mt-2 space-y-1">
              {beatSheet.slice(0, 2).map((beat, idx) => (
                <div key={idx} className="text-[11px] text-slate-300">
                  {String((beat as Record<string, unknown>).beat ?? `Beat ${idx + 1}`)}:{" "}
                  {String((beat as Record<string, unknown>).note ?? "")}
                </div>
              ))}
            </div>
          )}
          {storyboard.length > 0 && (
            <div className="mt-2 space-y-1">
              {storyboard.slice(0, 2).map((shot, idx) => {
                const shotData = shot as Record<string, unknown>;
                const dominant = String(shotData.dominant_color ?? "#334155");
                const accent = String(shotData.accent_color ?? "#64748b");
                return (
                  <div key={idx} className="flex items-center gap-2 text-[11px] text-slate-300">
                    <span className="text-slate-400">Shot {String(shotData.shot ?? idx + 1)}</span>
                    <span className="h-2 w-2 rounded-full" style={{ backgroundColor: dominant }} />
                    <span className="h-2 w-2 rounded-full" style={{ backgroundColor: accent }} />
                    <span className="truncate">{String(shotData.composition ?? "composition")}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Status indicator if needed */}
      <div className="flex items-center justify-between mt-2">
        <span className={cn("px-2 py-0.5 rounded text-[10px] font-medium border", statusClass)}>
          {status === "running" ? t("running") : status === "success" ? "DONE" : status === "error" ? t("error") : "ACTIVE"}
        </span>
        {/* Could add processing spinners here */}
      </div>

      {/* Handles with improved styling */}
      {canReceive && (
        <Handle
          type="target"
          position={Position.Left}
          className={cn(
            "!h-4 !w-2 !rounded-full !border-2 !border-slate-950 transition-colors",
            "bg-slate-400 hover:bg-white"
          )}
        />
      )}
      {canSend && (
        <Handle
          type="source"
          position={Position.Right}
          className={cn(
            "!h-4 !w-2 !rounded-full !border-2 !border-slate-950 transition-colors",
            "bg-slate-400 hover:bg-white"
          )}
        />
      )}
    </motion.div>
  );
}

export const CanvasNode = memo(BaseNode);
