"use client";

/**
 * AIProgressIndicator - Transparent AI progress display
 *
 * Shows users what the AI is doing during generation:
 * - Stage-based progress (analyzing, generating, refining, finalizing)
 * - Progress bar visualization
 * - Explanatory text for trust building
 *
 * 2026 UX Pattern: AI Co-pilot Trust through transparency
 */

import { Brain, Sparkles, Wand2, CheckCircle, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/utils";

export type AIStage = "analyzing" | "generating" | "refining" | "finalizing" | "complete";

const AI_STAGES: Array<{
  id: AIStage;
  label: string;
  description: string;
  icon: typeof Brain;
}> = [
  {
    id: "analyzing",
    label: "입력 분석 중...",
    description: "입력 내용을 이해하고 있습니다",
    icon: Brain,
  },
  {
    id: "generating",
    label: "AI 생성 중...",
    description: "창의적인 결과물을 생성하고 있습니다",
    icon: Sparkles,
  },
  {
    id: "refining",
    label: "결과 다듬는 중...",
    description: "품질을 높이기 위해 결과를 개선하고 있습니다",
    icon: Wand2,
  },
  {
    id: "finalizing",
    label: "최종 처리 중...",
    description: "결과물을 준비하고 있습니다",
    icon: CheckCircle,
  },
];

export interface AIProgressIndicatorProps {
  /** Current stage of AI processing */
  stage: AIStage;
  /** Optional progress percentage (0-100) */
  progress?: number;
  /** Estimated time remaining (optional) */
  estimatedSeconds?: number;
  /** Custom message to display */
  message?: string;
  /** Show detailed stage steps */
  showSteps?: boolean;
  /** Compact mode for inline use */
  compact?: boolean;
  /** Additional className */
  className?: string;
}

/**
 * AIProgressIndicator - Transparent AI progress display
 *
 * @example
 * ```tsx
 * <AIProgressIndicator
 *   stage="generating"
 *   progress={45}
 *   showSteps
 * />
 * ```
 */
export function AIProgressIndicator({
  stage,
  progress,
  estimatedSeconds,
  message,
  showSteps = true,
  compact = false,
  className,
}: AIProgressIndicatorProps) {
  const prefersReducedMotion = useReducedMotion();
  const currentStageIndex = AI_STAGES.findIndex((s) => s.id === stage);
  const currentStage = AI_STAGES[currentStageIndex] || AI_STAGES[0];
  const StageIcon = currentStage.icon;

  if (compact) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <Loader2
          className={cn(
            "w-4 h-4 text-[var(--fg-subtle)]",
            !prefersReducedMotion && "animate-spin"
          )}
        />
        <span className="text-sm text-[var(--fg-muted)]">
          {message || currentStage.label}
        </span>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "p-4 bg-white/5 rounded-xl border border-white/10 space-y-4",
        className
      )}
    >
      {/* Header with icon and message */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <StageIcon className="w-5 h-5 text-[var(--fg-subtle)]" />
          {!prefersReducedMotion && stage !== "complete" && (
            <motion.div
              className="absolute -inset-1 rounded-full bg-white/10"
              animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          )}
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-[var(--fg-0)]">
            {message || currentStage.label}
          </p>
          <p className="text-xs text-[var(--fg-muted)]">
            {currentStage.description}
          </p>
        </div>
        {estimatedSeconds !== undefined && estimatedSeconds > 0 && (
          <span className="text-xs text-[var(--fg-muted)]">
            ~{estimatedSeconds}초
          </span>
        )}
      </div>

      {/* Progress bar */}
      {progress !== undefined && (
        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          />
        </div>
      )}

      {/* Stage steps */}
      {showSteps && (
        <div className="flex gap-1">
          {AI_STAGES.map((s, i) => (
            <div
              key={s.id}
              className={cn(
                "h-1 flex-1 rounded-full transition-colors duration-300",
                i <= currentStageIndex ? "bg-emerald-500" : "bg-white/10"
              )}
            />
          ))}
        </div>
      )}

      {/* Trust message */}
      <p className="text-xs text-[var(--fg-muted)]">
        AI가 최적의 결과를 생성하고 있습니다. 잠시만 기다려주세요.
      </p>
    </div>
  );
}

/**
 * Inline AI status badge
 */
export function AIStatusBadge({
  stage,
  className,
}: {
  stage: AIStage;
  className?: string;
}) {
  const prefersReducedMotion = useReducedMotion();
  const currentStage = AI_STAGES.find((s) => s.id === stage) || AI_STAGES[0];
  const StageIcon = currentStage.icon;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-1 bg-white/5 rounded-full text-xs",
        className
      )}
    >
      <StageIcon
        className={cn(
          "w-3 h-3 text-emerald-400",
          stage !== "complete" && !prefersReducedMotion && "animate-pulse"
        )}
      />
      <span className="text-[var(--fg-muted)]">{currentStage.label}</span>
    </div>
  );
}
