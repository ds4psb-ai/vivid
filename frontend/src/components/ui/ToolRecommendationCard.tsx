"use client";

import { useEffect, useMemo, useState } from "react";
import { Coins, Info, Sparkles, ThumbsDown, ThumbsUp } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { cn } from "@/lib/utils";
import { toolsApi, type ToolDisplayInfo, type ToolEvidenceResponse } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
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
  ipId?: string;
  summary?: string;
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
  ipId,
  summary,
  className,
}: ToolRecommendationCardProps) {
  const { language, t } = useLanguage();
  const router = useRouter();
  const isKo = language === "ko";
  const [expanded, setExpanded] = useState(false);
  const [open, setOpen] = useState(false);
  const [toolInfo, setToolInfo] = useState<ToolDisplayInfo | null>(null);
  const [infoLoading, setInfoLoading] = useState(false);
  const [infoError, setInfoError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [toolEvidence, setToolEvidence] = useState<ToolEvidenceResponse | null>(null);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [evidenceError, setEvidenceError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);
  const [feedbackNote, setFeedbackNote] = useState(false);

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
        tone: code.split(":")[0],
      })),
    [visibleReasons, language]
  );

  const confidenceTone =
    level === "high"
      ? "text-emerald-500 bg-emerald-500/10 border-emerald-500/30"
      : level === "medium"
      ? "text-amber-500 bg-amber-500/10 border-amber-500/30"
      : "text-slate-400 bg-slate-500/10 border-slate-500/30";

  const confidenceBarTone =
    level === "high"
      ? "bg-emerald-500/70"
      : level === "medium"
      ? "bg-amber-500/70"
      : "bg-slate-400/70";

  const dimensionKey = dimension?.toLowerCase();
  const dimensionBadgeClass = dimensionKey
    ? `bg-dimension-${dimensionKey}/20 text-dimension-${dimensionKey}`
    : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300";
  const dimensionBorderClass = dimensionKey
    ? `border-dimension-${dimensionKey}/50`
    : "border-slate-200 dark:border-slate-700";

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

  useEffect(() => {
    let isActive = true;

    async function loadEvidence() {
      if (!open || toolEvidence || evidenceLoading) return;

      setEvidenceLoading(true);
      setEvidenceError(null);

      try {
        const res = await toolsApi.getToolEvidence(toolId, ipId);
        if (!res.ok || !res.data) {
          throw new Error(res.error?.message || "Failed to load evidence");
        }
        if (isActive) {
          setToolEvidence(res.data);
        }
      } catch (err) {
        if (isActive) {
          setEvidenceError(err instanceof Error ? err.message : "Failed to load evidence");
        }
      } finally {
        if (isActive) {
          setEvidenceLoading(false);
        }
      }
    }

    loadEvidence();

    return () => {
      isActive = false;
    };
  }, [open, toolEvidence, evidenceLoading, toolId, ipId]);

  const toolDescription = toolInfo?.[isKo ? "description_ko" : "description_en"];
  const toolIcon = toolInfo?.icon || "✨";
  const resolvedReasonCodes =
    toolEvidence?.reason_codes && toolEvidence.reason_codes.length > 0
      ? toolEvidence.reason_codes
      : reasonCodes;
  const resolvedEvidenceRefs =
    toolEvidence?.evidence_refs && toolEvidence.evidence_refs.length > 0
      ? toolEvidence.evidence_refs
      : evidenceRefs;
  const resolvedDatasets = toolEvidence?.datasets_used || [];
  const summaryText = summary?.trim()
    || (resolvedReasonCodes.length > 0
      ? `${t("recommendationHintPrefix")} ${resolvedReasonCodes
          .slice(0, 2)
          .map((code) => getReasonCodeLabel(code, language))
          .join(", ")}`
      : "");

  const handleCopyToolId = async () => {
    try {
      await navigator.clipboard?.writeText(toolId);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.warn("Failed to copy tool id", err);
    }
  };

  const handleFeedback = (value: "up" | "down") => {
    setFeedback((prev) => (prev === value ? null : value));
    setFeedbackNote(true);
    setTimeout(() => setFeedbackNote(false), 1500);
  };

  return (
    <div
      className={cn(
        "rounded-xl border border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/40 p-3 space-y-2 border-l-4",
        dimensionBorderClass,
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
            <span className={cn("text-[10px] px-1.5 py-0.5 rounded-full", dimensionBadgeClass)}>
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

      {percent !== null && (
        <div className="space-y-1">
          <div className="h-1 w-full rounded-full bg-slate-200/70 dark:bg-slate-800 overflow-hidden">
            <div
              className={cn("h-full rounded-full", confidenceBarTone)}
              style={{ width: `${percent}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-[10px] text-slate-400">
            <span>{t("evidenceConfidenceTitle")}</span>
            <span>{percent}%</span>
          </div>
          <div className="text-[10px] text-slate-400">
            {t("confidenceDisclaimer")}
          </div>
        </div>
      )}

      {chips.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {chips.map((chip) => (
            <span key={chip.code} className="evidence-badge text-[9px]" data-tone={chip.tone}>
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

      {summaryText && (
        <div className="text-[11px] text-slate-600 dark:text-slate-300 bg-slate-50/80 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-700 rounded-md px-2 py-1">
          {summaryText}
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
                <span className="inline-flex items-center gap-2">
                  <span className="text-lg">{toolIcon}</span>
                  <span>
                    {toolInfo?.[isKo ? "display_name_ko" : "display_name_en"] || displayName}
                  </span>
                </span>
              </DialogTitle>
              <DialogDescription>
                {toolDescription || t("noToolDescription")}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              <div className="text-xs text-slate-500 dark:text-slate-400">
                <span className="uppercase tracking-[0.18em] text-[10px] mr-2">
                  {t("toolIdLabel")}
                </span>
                <span className="font-mono">{toolId}</span>
              </div>
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

              {resolvedReasonCodes.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                    {t("evidenceReasonsTitle")}
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {resolvedReasonCodes.map((code) => (
                      <span key={code} className="evidence-badge text-[9px]" data-tone={code.split(":")[0]}>
                        {getReasonCodeLabel(code, language)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {(resolvedEvidenceRefs.length > 0 || resolvedDatasets.length > 0) && (
                <div className="space-y-2">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                    {t("evidenceDataTitle")}
                  </div>
                  {resolvedEvidenceRefs.length > 0 && (
                    <ul className="space-y-1 text-xs text-slate-500 dark:text-slate-400">
                      {resolvedEvidenceRefs.map((ref) => (
                        <li key={ref} className="flex items-start gap-1">
                          <span className="mt-0.5">•</span>
                          <span className="break-all">{ref}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  {resolvedDatasets.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {resolvedDatasets.map((dataset) => (
                        <span key={dataset} className="evidence-badge text-[9px]" data-tone="dataset">
                          {dataset}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {evidenceLoading && (
                <div className="text-xs text-slate-400">{t("loading")}</div>
              )}

              {evidenceError && (
                <div className="text-xs text-red-500">{t("toolEvidenceLoadFailed")}</div>
              )}

              {!evidenceLoading &&
                !evidenceError &&
                resolvedEvidenceRefs.length === 0 &&
                resolvedDatasets.length === 0 && (
                  <div className="text-xs text-slate-400">{t("noEvidenceRefs")}</div>
                )}
            </div>

            <DialogFooter>
              <Button variant="ghost" onClick={handleCopyToolId}>
                {copied ? t("copied") : t("copyToolId")}
              </Button>
              <Button variant="secondary" onClick={() => router.push("/tools")}>
                {t("openToolsCatalog")}
              </Button>
              <Button variant="outline" onClick={() => setOpen(false)}>
                {t("close")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex items-center justify-between text-[10px] text-slate-400">
        <span>{t("recommendationFeedbackLabel")}</span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => handleFeedback("up")}
            className={cn(
              "inline-flex items-center gap-1 px-2 py-0.5 rounded-full border",
              feedback === "up"
                ? "border-emerald-400 text-emerald-500 bg-emerald-500/10"
                : "border-slate-200 dark:border-slate-700 text-slate-400"
            )}
          >
            <ThumbsUp className="w-3 h-3" />
            {t("feedbackHelpful")}
          </button>
          <button
            type="button"
            onClick={() => handleFeedback("down")}
            className={cn(
              "inline-flex items-center gap-1 px-2 py-0.5 rounded-full border",
              feedback === "down"
                ? "border-rose-400 text-rose-500 bg-rose-500/10"
                : "border-slate-200 dark:border-slate-700 text-slate-400"
            )}
          >
            <ThumbsDown className="w-3 h-3" />
            {t("feedbackNotHelpful")}
          </button>
        </div>
      </div>

      {feedbackNote && (
        <div className="text-[10px] text-emerald-500">
          {t("feedbackThanks")}
        </div>
      )}
    </div>
  );
}

export default ToolRecommendationCard;
