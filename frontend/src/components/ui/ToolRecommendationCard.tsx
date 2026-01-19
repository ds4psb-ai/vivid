"use client";

import { useMemo, useState } from "react";
import { Coins, Sparkles } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { cn } from "@/lib/utils";
import {
  getReasonCodeLabel,
  getConfidenceLabel,
  scoreToConfidenceLevel,
  type ConfidenceLevel,
} from "@/lib/reason-codes";

interface ToolRecommendationCardProps {
  toolId: string;
  displayName: string;
  dimension: string;
  confidence?: number;
  confidenceLevel?: ConfidenceLevel;
  reasonCodes?: string[];
  estimatedCredits?: number;
  isPrimary?: boolean;
  className?: string;
}

export function ToolRecommendationCard({
  toolId,
  displayName,
  dimension,
  confidence,
  confidenceLevel,
  reasonCodes = [],
  estimatedCredits,
  isPrimary = false,
  className,
}: ToolRecommendationCardProps) {
  const { language, t } = useLanguage();
  const isKo = language === "ko";
  const [expanded, setExpanded] = useState(false);

  const level =
    confidenceLevel ?? scoreToConfidenceLevel(confidence ?? 0);
  const levelLabel = getConfidenceLabel(level, language);
  const percent = confidence ? Math.round(confidence * 100) : null;

  const visibleReasons = expanded ? reasonCodes : reasonCodes.slice(0, 2);
  const hiddenCount = Math.max(reasonCodes.length - visibleReasons.length, 0);

  const chips = useMemo(
    () =>
      visibleReasons.map((code) => ({
        code,
        label: getReasonCodeLabel(code, language),
      })),
    [visibleReasons, language]
  );

  const confidenceTone =
    level === "high"
      ? "text-emerald-500 bg-emerald-500/10 border-emerald-500/30"
      : level === "medium"
      ? "text-amber-500 bg-amber-500/10 border-amber-500/30"
      : "text-slate-400 bg-slate-500/10 border-slate-500/30";

  return (
    <div
      className={cn(
        "rounded-xl border border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/40 p-3 space-y-2",
        isPrimary && "ring-1 ring-violet-400/30",
        className
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-slate-900 dark:text-white">
              {displayName}
            </span>
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-300">
              {dimension}
            </span>
            {isPrimary && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-violet-500/10 text-violet-500 border border-violet-500/30">
                {t("recommendationTopBadge")}
              </span>
            )}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400">
            {toolId}
          </div>
        </div>

        <div className="flex flex-col items-end gap-1">
          <span className={`text-[10px] px-1.5 py-0.5 rounded-full border ${confidenceTone}`}>
            {levelLabel}
            {percent !== null && ` ${percent}%`}
          </span>
          {typeof estimatedCredits === "number" && (
            <span className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1">
              <Coins className="w-3 h-3" />
              {estimatedCredits} {t("credits")}
            </span>
          )}
        </div>
      </div>

      {chips.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {chips.map((chip) => (
            <span key={chip.code} className="evidence-badge text-[9px]">
              {chip.label}
            </span>
          ))}
          {hiddenCount > 0 && (
            <button
              type="button"
              onClick={() => setExpanded((prev) => !prev)}
              className="text-[9px] text-slate-500 dark:text-slate-400"
            >
              {expanded
                ? t("collapseLabel")
                : isKo
                ? `+${hiddenCount} ${t("moreLabel")}`
                : `+${hiddenCount} ${t("moreLabel")}`}
            </button>
          )}
        </div>
      )}

      {reasonCodes.length === 0 && (
        <div className="text-[10px] text-slate-400 flex items-center gap-1">
          <Sparkles className="w-3 h-3" />
          {t("noReasonCodes")}
        </div>
      )}
    </div>
  );
}

export default ToolRecommendationCard;
