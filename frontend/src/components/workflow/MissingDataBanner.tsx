"use client";

/**
 * MissingDataBanner - UI for missing chain data notification
 *
 * Shows when a component requires chain data that hasn't been generated yet.
 * Provides navigation to the source step.
 *
 * 2026 Pattern: "Guide, Don't Block"
 * - Show what's missing clearly
 * - Provide direct action to resolve
 * - Don't block all functionality
 */

import { AlertTriangle, ArrowRight, Sparkles, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import { CHAIN_DATA_SOURCE_MAP, STEP_LABELS } from "./workflow-configs";
import type { MegaAppId } from "./types";

interface MissingDataBannerProps {
  /** Keys of missing data */
  missingKeys: string[];
  /** Handler to navigate to source */
  onGoToSource: (key: string) => void;
  /** Optional custom message */
  message?: string;
  /** Variant: warning (default) or info */
  variant?: "warning" | "info";
  /** Show AI inference option */
  showInferenceOption?: boolean;
  /** Handler for AI inference */
  onInfer?: () => void;
  /** Additional class name */
  className?: string;
}

/**
 * Banner component showing missing required data
 */
export function MissingDataBanner({
  missingKeys,
  onGoToSource,
  message,
  variant = "warning",
  showInferenceOption = false,
  onInfer,
  className,
}: MissingDataBannerProps) {
  if (missingKeys.length === 0) return null;

  const isWarning = variant === "warning";

  return (
    <div
      className={cn(
        "rounded-xl border p-6",
        isWarning
          ? "bg-amber-500/5 border-amber-500/20"
          : "bg-blue-500/5 border-blue-500/20",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start gap-3 mb-4">
        <div
          className={cn(
            "p-2 rounded-lg",
            isWarning ? "bg-amber-500/10" : "bg-blue-500/10"
          )}
        >
          <AlertTriangle
            className={cn(
              "w-5 h-5",
              isWarning ? "text-amber-400" : "text-blue-400"
            )}
          />
        </div>
        <div className="flex-1">
          <h3
            className={cn(
              "font-medium mb-1",
              isWarning ? "text-amber-200" : "text-blue-200"
            )}
          >
            필요한 데이터가 없습니다
          </h3>
          <p className="text-sm text-white/60">
            {message ||
              `이 기능을 사용하려면 ${missingKeys.length}개의 이전 단계를 완료해야 합니다.`}
          </p>
        </div>
      </div>

      {/* Missing items list */}
      <div className="space-y-2 mb-4">
        {missingKeys.map((key) => {
          const source = CHAIN_DATA_SOURCE_MAP[key];
          const label = source?.label || STEP_LABELS[key] || key;
          const appLabel = getAppLabel(source?.app);

          return (
            <button
              key={key}
              onClick={() => onGoToSource(key)}
              className={cn(
                "w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors",
                isWarning
                  ? "bg-amber-500/10 hover:bg-amber-500/20"
                  : "bg-blue-500/10 hover:bg-blue-500/20"
              )}
            >
              <div className="flex-1">
                <div className="text-sm text-white">{label}</div>
                {source && (
                  <div className="text-xs text-white/40 flex items-center gap-1">
                    <span>{appLabel}</span>
                    <span>•</span>
                    <span>{source.step}</span>
                  </div>
                )}
              </div>
              <ArrowRight className="w-4 h-4 text-white/40" />
            </button>
          );
        })}
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-2">
        {/* Primary action: Go to first missing */}
        <button
          onClick={() => onGoToSource(missingKeys[0])}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
            isWarning
              ? "bg-amber-500/20 text-amber-200 hover:bg-amber-500/30"
              : "bg-blue-500/20 text-blue-200 hover:bg-blue-500/30"
          )}
        >
          <ExternalLink className="w-4 h-4" />
          {missingKeys.length === 1
            ? "단계로 이동"
            : `첫 번째 단계로 이동 (${missingKeys.length}개 필요)`}
        </button>

        {/* AI Inference option */}
        {showInferenceOption && onInfer && (
          <button
            onClick={onInfer}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-purple-500/20 text-purple-200 hover:bg-purple-500/30 transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            AI로 추론하기
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Compact version for inline use
 */
export function MissingDataIndicator({
  missingKeys,
  onGoToSource,
  className,
}: {
  missingKeys: string[];
  onGoToSource: (key: string) => void;
  className?: string;
}) {
  if (missingKeys.length === 0) return null;

  return (
    <div
      className={cn(
        "flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-400 text-xs",
        className
      )}
    >
      <AlertTriangle className="w-3 h-3" />
      <span>{missingKeys.length}개 데이터 필요</span>
      <button
        onClick={() => onGoToSource(missingKeys[0])}
        className="underline hover:no-underline"
      >
        이동
      </button>
    </div>
  );
}

/**
 * Helper: Get app display label
 */
function getAppLabel(app: MegaAppId | undefined): string {
  switch (app) {
    case "dna-lab":
      return "DNA Lab";
    case "story-engine":
      return "Story Engine";
    case "production":
      return "Production";
    default:
      return "";
  }
}
