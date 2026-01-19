"use client";

import { useEffect, useMemo, useState } from "react";
import { Coins, Info, Sparkles } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { cn } from "@/lib/utils";
import { toolsApi, type ToolDisplayInfo } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
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
  evidenceRefs?: string[];
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
  evidenceRefs = [],
  estimatedCredits,
  isPrimary = false,
  className,
}: ToolRecommendationCardProps) {
  const { language, t } = useLanguage();
  const isKo = language === "ko";
  const [expanded, setExpanded] = useState(false);
  const [open, setOpen] = useState(false);
  const [toolInfo, setToolInfo] = useState<ToolDisplayInfo | null>(null);
  const [infoLoading, setInfoLoading] = useState(false);
  const [infoError, setInfoError] = useState<string | null>(null);

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

  useEffect(() => {
    let isActive = true;

    async function loadToolInfo() {
      if (!open || toolInfo || infoLoading) return;

      setInfoLoading(true);
      setInfoError(null);

      try {
        const res = await toolsApi.getToolInfo(toolId);
        if (!res.ok || !res.data) {
          throw new Error(res.error?.message || "Failed to load tool info");
        }
        if (isActive) {
          setToolInfo(res.data);
        }
      } catch (err) {
        if (isActive) {
          setInfoError(err instanceof Error ? err.message : "Failed to load tool info");
        }
      } finally {
        if (isActive) {
          setInfoLoading(false);
        }
      }
    }

    loadToolInfo();

    return () => {
      isActive = false;
    };
  }, [open, toolInfo, infoLoading, toolId]);

  const toolDescription = toolInfo?.[isKo ? "description_ko" : "description_en"];

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

      <div className="flex items-center justify-between pt-1">
        <span className="text-[10px] text-slate-400">
          {estimatedCredits !== undefined ? `${estimatedCredits} ${t("credits")}` : " "}
        </span>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger className="text-[10px] text-violet-500 hover:underline inline-flex items-center gap-1">
            <Info className="w-3 h-3" />
            {t("viewDetails")}
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>
                {toolInfo?.[isKo ? "display_name_ko" : "display_name_en"] || displayName}
              </DialogTitle>
              <DialogDescription>
                {toolDescription || t("noToolDescription")}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
                <span className="px-2 py-1 rounded-full border border-slate-200 dark:border-slate-700">
                  {dimension}
                </span>
                <span className={`px-2 py-1 rounded-full border ${confidenceTone}`}>
                  {levelLabel}
                  {percent !== null && ` ${percent}%`}
                </span>
                {toolInfo?.base_credits !== undefined && (
                  <span className="px-2 py-1 rounded-full border border-slate-200 dark:border-slate-700">
                    {t("baseCredits")}: {toolInfo.base_credits}
                  </span>
                )}
                {estimatedCredits !== undefined && (
                  <span className="px-2 py-1 rounded-full border border-slate-200 dark:border-slate-700">
                    {t("estimatedCredits")}: {estimatedCredits}
                  </span>
                )}
              </div>

              {infoLoading && (
                <div className="text-xs text-slate-400">
                  {t("loading")}
                </div>
              )}

              {infoError && (
                <div className="text-xs text-red-500">{infoError}</div>
              )}

              {reasonCodes.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                    {t("evidenceReasonsTitle")}
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {reasonCodes.map((code) => (
                      <span key={code} className="evidence-badge text-[9px]">
                        {getReasonCodeLabel(code, language)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {evidenceRefs.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                    {t("evidenceDataTitle")}
                  </div>
                  <ul className="space-y-1 text-xs text-slate-500 dark:text-slate-400">
                    {evidenceRefs.map((ref) => (
                      <li key={ref} className="flex items-start gap-1">
                        <span className="mt-0.5">•</span>
                        <span className="break-all">{ref}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setOpen(false)}>
                {t("close")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}

export default ToolRecommendationCard;
