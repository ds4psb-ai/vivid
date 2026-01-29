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
 *
 * Phase 2 Enhancement:
 * - suggestedDefaults: AI-inferred values with confidence scores
 * - Individual apply/dismiss per suggestion
 * - Confidence badges matching EvidenceCard patterns
 */

import { useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  Sparkles,
  ExternalLink,
  Check,
  X,
  ChevronDown,
  ChevronUp,
  FileText,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { CHAIN_DATA_SOURCE_MAP, STEP_LABELS } from "./workflow-configs";
import type { MegaAppId, SuggestedDefault, ConfidenceLevel } from "./types";
import { getConfidenceColorConfig } from "./types";

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

  // Phase 2: Suggested Defaults
  /** AI-inferred default values for missing keys */
  suggestedDefaults?: Record<string, SuggestedDefault>;
  /** Handler to apply a suggestion */
  onApplySuggestion?: (key: string, value: unknown) => void;
  /** Handler to dismiss a suggestion */
  onDismissSuggestion?: (key: string) => void;
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
  // Phase 2: Suggested Defaults
  suggestedDefaults,
  onApplySuggestion,
  onDismissSuggestion,
}: MissingDataBannerProps) {
  // Track which suggestions have been dismissed locally
  const [dismissedKeys, setDismissedKeys] = useState<Set<string>>(new Set());

  if (missingKeys.length === 0) return null;

  const isWarning = variant === "warning";

  // Filter out dismissed suggestions
  const activeSuggestions = suggestedDefaults
    ? Object.entries(suggestedDefaults).filter(
        ([key]) => !dismissedKeys.has(key)
      )
    : [];

  const hasSuggestions = activeSuggestions.length > 0;

  // Handle dismiss with local state + callback
  const handleDismiss = (key: string) => {
    setDismissedKeys((prev) => new Set([...prev, key]));
    onDismissSuggestion?.(key);
  };

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
            {hasSuggestions
              ? "이전 단계의 데이터가 필요합니다"
              : "필요한 데이터가 없습니다"}
          </h3>
          <p className="text-sm text-white/60">
            {message ||
              (hasSuggestions
                ? `AI가 ${activeSuggestions.length}개의 값을 추론했습니다. 적용하거나 직접 설정할 수 있습니다.`
                : `이 기능을 사용하려면 ${missingKeys.length}개의 이전 단계를 완료해야 합니다.`)}
          </p>
        </div>
      </div>

      {/* Missing items list with suggestions */}
      <div className="space-y-3 mb-4">
        {missingKeys.map((key) => {
          const source = CHAIN_DATA_SOURCE_MAP[key];
          const label = source?.label || STEP_LABELS[key] || key;
          const appLabel = getAppLabel(source?.app);
          const suggestion =
            suggestedDefaults?.[key] && !dismissedKeys.has(key)
              ? suggestedDefaults[key]
              : null;

          if (suggestion) {
            // Render suggestion item with apply/dismiss options
            return (
              <SuggestionItem
                key={key}
                dataKey={key}
                label={label}
                appLabel={appLabel}
                stepLabel={source?.step}
                suggestion={suggestion}
                onApply={(value) => onApplySuggestion?.(key, value)}
                onDismiss={() => handleDismiss(key)}
                onGoToSource={() => onGoToSource(key)}
                isWarning={isWarning}
              />
            );
          }

          // Render basic missing item (no suggestion available)
          return (
            <div
              key={key}
              className={cn(
                "rounded-lg border p-4",
                isWarning
                  ? "bg-amber-500/5 border-amber-500/10"
                  : "bg-blue-500/5 border-blue-500/10"
              )}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-white font-medium">{label}</div>
                  {source && (
                    <div className="text-xs text-white/40 flex items-center gap-1 mt-0.5">
                      <span>{appLabel}</span>
                      <span>•</span>
                      <span>{source.step}</span>
                    </div>
                  )}
                  <div className="text-xs text-white/50 mt-2 flex items-center gap-1">
                    <X className="w-3 h-3" />
                    추론 불가 - 원본 데이터 필요
                  </div>
                </div>
                <button
                  onClick={() => onGoToSource(key)}
                  className={cn(
                    "flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
                    isWarning
                      ? "bg-amber-500/20 text-amber-200 hover:bg-amber-500/30"
                      : "bg-blue-500/20 text-blue-200 hover:bg-blue-500/30"
                  )}
                >
                  이동
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
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
            전체 AI 추론하기
          </button>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// SuggestionItem Component
// =============================================================================

interface SuggestionItemProps {
  dataKey: string;
  label: string;
  appLabel: string;
  stepLabel?: string;
  suggestion: SuggestedDefault;
  onApply: (value: unknown) => void;
  onDismiss: () => void;
  onGoToSource: () => void;
  isWarning: boolean;
}

function SuggestionItem({
  dataKey,
  label,
  appLabel,
  stepLabel,
  suggestion,
  onApply,
  onDismiss,
  onGoToSource,
  isWarning,
}: SuggestionItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const colorConfig = getConfidenceColorConfig(suggestion.confidenceLevel);

  // Format value preview (truncate if too long)
  const valuePreview = formatValuePreview(suggestion.value, 100);

  return (
    <div
      className={cn(
        "rounded-lg border p-4",
        colorConfig.bg,
        colorConfig.border
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm text-white font-medium">{label}</span>
            <ConfidenceBadge
              level={suggestion.confidenceLevel}
              confidence={suggestion.confidence}
            />
          </div>
          {(appLabel || stepLabel) && (
            <div className="text-xs text-white/40 flex items-center gap-1">
              {appLabel && <span>{appLabel}</span>}
              {appLabel && stepLabel && <span>•</span>}
              {stepLabel && <span>{stepLabel}</span>}
            </div>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Sparkles className={cn("w-4 h-4", colorConfig.text)} />
          <span className={cn("text-xs", colorConfig.text)}>AI 추론 가능</span>
        </div>
      </div>

      {/* Summary */}
      {suggestion.summary && (
        <p className="text-xs text-white/60 mb-3">{suggestion.summary}</p>
      )}

      {/* Value Preview */}
      <div className="mb-3">
        <div className="text-xs text-white/40 mb-1">추론값:</div>
        <div className="bg-black/20 rounded-lg p-2 text-xs text-white/80 font-mono overflow-x-auto">
          {valuePreview}
        </div>
      </div>

      {/* Evidence Sources (Collapsible) */}
      {suggestion.evidenceSources && suggestion.evidenceSources.length > 0 && (
        <div className="mb-3">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 text-xs text-white/50 hover:text-white/70 transition-colors"
          >
            {isExpanded ? (
              <ChevronUp className="w-3 h-3" />
            ) : (
              <ChevronDown className="w-3 h-3" />
            )}
            <span>출처 ({suggestion.evidenceSources.length}개)</span>
          </button>
          {isExpanded && (
            <div className="mt-2 space-y-1 ml-4">
              {suggestion.evidenceSources.map((source, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 text-xs text-white/50"
                >
                  <FileText className="w-3 h-3" />
                  <span className="font-mono">{source}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => onApply(suggestion.value)}
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
            "bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30"
          )}
        >
          <Check className="w-3 h-3" />
          적용하기
        </button>
        <button
          onClick={onDismiss}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white/50 hover:text-white/70 hover:bg-white/5 transition-colors"
        >
          <X className="w-3 h-3" />
          무시
        </button>
        <button
          onClick={onGoToSource}
          className={cn(
            "flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium ml-auto transition-colors",
            isWarning
              ? "text-amber-300/70 hover:text-amber-300 hover:bg-amber-500/10"
              : "text-blue-300/70 hover:text-blue-300 hover:bg-blue-500/10"
          )}
        >
          직접 설정
          <ArrowRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}

// =============================================================================
// ConfidenceBadge Component
// =============================================================================

interface ConfidenceBadgeProps {
  level: ConfidenceLevel;
  confidence: number;
  compact?: boolean;
}

function ConfidenceBadge({
  level,
  confidence,
  compact = false,
}: ConfidenceBadgeProps) {
  const config = getConfidenceColorConfig(level);

  if (compact) {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium",
          config.bg,
          config.text
        )}
      >
        {confidence}%
      </span>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium",
        config.bg,
        config.text
      )}
    >
      <span>{config.label}</span>
      <span className="opacity-70">({confidence}%)</span>
    </span>
  );
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Format value for preview display
 */
function formatValuePreview(value: unknown, maxLength: number): string {
  if (value === null || value === undefined) {
    return "null";
  }

  if (typeof value === "string") {
    return value.length > maxLength
      ? value.slice(0, maxLength) + "..."
      : value;
  }

  try {
    const json = JSON.stringify(value, null, 2);
    return json.length > maxLength ? json.slice(0, maxLength) + "..." : json;
  } catch {
    return String(value);
  }
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
