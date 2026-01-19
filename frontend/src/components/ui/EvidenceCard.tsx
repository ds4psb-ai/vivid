"use client";

/**
 * EvidenceCard - Display tool recommendation evidence and reason codes
 *
 * IP-First Coordination Phase 2.5
 *
 * Features:
 * - Confidence level indicator (HIGH/MEDIUM/LOW)
 * - Reason codes with i18n labels
 * - Collapsible evidence references
 * - Visual styling based on confidence
 */

import { useState, useMemo } from "react";
import {
  ChevronDown,
  ChevronUp,
  Target,
  FileText,
  Database,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "./badge";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  getReasonCodeLabel,
  getConfidenceLabel,
  type ConfidenceLevel as ReasonConfidenceLevel,
} from "@/lib/reason-codes";

// =============================================================================
// Types
// =============================================================================

export type ConfidenceLevel = ReasonConfidenceLevel;

export interface EvidenceCardProps {
  /** Visual variant */
  variant?: "recommendation" | "evidence";
  /** Optional title override */
  title?: string;
  /** Confidence level from recommendation */
  confidenceLevel: ConfidenceLevel;
  /** Raw confidence score (0-1) */
  confidence?: number;
  /** Reason codes explaining the recommendation */
  reasonCodes: string[];
  /** Evidence references (e.g., "db:ip_catalog:goblin") */
  evidenceRefs: string[];
  /** Human-readable summary */
  reasonSummary: string;
  /** Datasets used for the recommendation */
  datasetsUsed?: string[];
  /** Whether the evidence section is collapsible */
  isCollapsible?: boolean;
  /** Custom class name */
  className?: string;
  /** Compact mode for inline display */
  compact?: boolean;
}

// =============================================================================
// Helpers
// =============================================================================

function parseReasonCode(code: string): { category: string; value: string } {
  const [category, ...rest] = code.split(":");
  return { category, value: rest.join(":") };
}

function getConfidenceColor(level: ConfidenceLevel): string {
  switch (level) {
    case "high":
      return "text-emerald-700 bg-emerald-50 border-emerald-200 dark:text-emerald-300 dark:bg-emerald-500/10 dark:border-emerald-500/30";
    case "medium":
      return "text-amber-700 bg-amber-50 border-amber-200 dark:text-amber-300 dark:bg-amber-500/10 dark:border-amber-500/30";
    case "low":
      return "text-slate-600 bg-slate-50 border-slate-200 dark:text-slate-300 dark:bg-slate-800/60 dark:border-slate-700";
  }
}

function formatEvidenceRef(
  ref: string,
  isKo: boolean
): { type: string; label: string } {
  const parts = ref.split(":");
  const prefix = parts[0];
  const category = parts[1];

  if (prefix === "db" && category === "rag_docs") {
    return {
      type: "rag",
      label: `${isKo ? "RAG" : "RAG"} · ${parts.slice(2).join("/")}`,
    };
  }

  if (prefix === "db" && category === "ip_catalog") {
    return {
      type: "ip",
      label: `${isKo ? "IP" : "IP"} · ${parts.slice(2).join("/")}`,
    };
  }

  if (prefix === "db" && category === "capsule_runs") {
    return {
      type: "database",
      label: `${isKo ? "실행" : "Run"} · ${parts.slice(2).join("/")}`,
    };
  }

  if (prefix === "rag") {
    return {
      type: "rag",
      label: `${isKo ? "RAG" : "RAG"} · ${parts.slice(1).join("/")}`,
    };
  }

  if (prefix === "ip") {
    return {
      type: "ip",
      label: `${isKo ? "IP" : "IP"} · ${parts.slice(1).join("/")}`,
    };
  }

  if (prefix === "db") {
    return {
      type: "database",
      label: `${isKo ? "DB" : "DB"} · ${parts.slice(1).join("/")}`,
    };
  }

  return {
    type: "other",
    label: ref,
  };
}

// =============================================================================
// Component
// =============================================================================

export function EvidenceCard({
  variant = "recommendation",
  title,
  confidenceLevel,
  confidence,
  reasonCodes,
  evidenceRefs,
  reasonSummary,
  datasetsUsed = [],
  isCollapsible = true,
  className = "",
  compact = false,
}: EvidenceCardProps) {
  const { language, t } = useLanguage();
  const isKo = language === "ko";
  const [isExpanded, setIsExpanded] = useState(!isCollapsible);
  const isEvidenceOnly = variant === "evidence";

  // Parse reason codes into display format
  const reasonLabels = useMemo(() => {
    return reasonCodes.map((code) => ({
      code,
      label: getReasonCodeLabel(code, isKo ? "ko" : "en"),
      category: parseReasonCode(code).category,
    }));
  }, [reasonCodes, isKo]);

  // Parse evidence refs
  const evidenceItems = useMemo(() => {
    return evidenceRefs.map((ref) => ({
      ref,
      ...formatEvidenceRef(ref, isKo),
    }));
  }, [evidenceRefs, isKo]);

  const confidencePercent = confidence ? Math.round(confidence * 100) : null;
  const labels = useMemo(
    () => ({
      confidenceTitle: t("evidenceConfidenceTitle"),
      reasonsTitle: t("evidenceReasonsTitle"),
      evidenceTitle: t("evidenceDataTitle"),
      datasetsUsed: t("evidenceDatasetsUsed"),
      evidenceCardTitle: t("evidenceSummaryTitle"),
    }),
    [t, language]
  );

  // Compact mode for inline display
  if (compact) {
    return (
      <div
        className={cn(
          "inline-flex items-center gap-2 px-2 py-1 rounded-md text-xs",
          getConfidenceColor(confidenceLevel),
          className
        )}
      >
        <Target className="w-3 h-3" />
        <span className="font-medium">
            {getConfidenceLabel(confidenceLevel, isKo ? "ko" : "en")}
          {confidencePercent && ` (${confidencePercent}%)`}
        </span>
        {reasonCodes.length > 0 && (
          <span className="text-xs opacity-75">
            {reasonLabels.slice(0, 2).map((r) => r.label).join(", ")}
          </span>
        )}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "rounded-lg border p-4 space-y-3",
        isEvidenceOnly
          ? "text-slate-700 bg-slate-50 border-slate-200 dark:text-slate-200 dark:bg-slate-900/40 dark:border-slate-700"
          : getConfidenceColor(confidenceLevel),
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isEvidenceOnly ? (
            <Database className="w-4 h-4" />
          ) : (
            <Target className="w-4 h-4" />
          )}
          <span className="font-medium text-sm">
            {title ||
              (isEvidenceOnly
                ? labels.evidenceCardTitle
                : labels.confidenceTitle)}
          </span>
          {!isEvidenceOnly && (
            <Badge
              variant={confidenceLevel === "high" ? "default" : "secondary"}
              className="ml-1"
            >
          {getConfidenceLabel(confidenceLevel, isKo ? "ko" : "en")}
              {confidencePercent && ` (${confidencePercent}%)`}
            </Badge>
          )}
        </div>
      </div>

      {/* Reason Summary */}
      {reasonSummary && (
        <p className="text-sm opacity-90">{reasonSummary}</p>
      )}

      {/* Reason Codes */}
      {!isEvidenceOnly && reasonLabels.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs font-medium opacity-75">
            <Sparkles className="w-3 h-3" />
            <span>{labels.reasonsTitle}</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {reasonLabels.map(({ code, label, category }) => (
              <span
                key={code}
                className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-white/50 border border-current/20"
                title={code}
              >
                {getCategoryIcon(category)}
                <span className="ml-1">{label}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Collapsible Evidence Section */}
      {(evidenceItems.length > 0 || datasetsUsed.length > 0) && (
        <div className="pt-2 border-t border-current/10">
          {isCollapsible ? (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-1 text-xs font-medium opacity-75 hover:opacity-100 transition-opacity w-full"
            >
              <Database className="w-3 h-3" />
              <span>{labels.evidenceTitle}</span>
              {isExpanded ? (
                <ChevronUp className="w-3 h-3 ml-auto" />
              ) : (
                <ChevronDown className="w-3 h-3 ml-auto" />
              )}
            </button>
          ) : (
            <div className="flex items-center gap-1 text-xs font-medium opacity-75">
              <Database className="w-3 h-3" />
              <span>{labels.evidenceTitle}</span>
            </div>
          )}

          {isExpanded && (
            <div className="mt-2 space-y-2 animate-in fade-in duration-200">
              {/* Evidence Refs */}
              {evidenceItems.length > 0 && (
                <ul className="space-y-1">
                  {evidenceItems.map(({ ref, type, label }) => (
                    <li
                      key={ref}
                      className="flex items-start gap-1.5 text-xs opacity-80"
                    >
                      {getEvidenceIcon(type)}
                      <span className="break-all">{label}</span>
                    </li>
                  ))}
                </ul>
              )}

              {/* Datasets Used */}
              {datasetsUsed.length > 0 && (
                <div className="pt-2">
                  <div className="text-[10px] uppercase tracking-[0.18em] opacity-70 mb-1">
                    {labels.datasetsUsed}
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {datasetsUsed.map((dataset) => (
                      <span
                        key={dataset}
                        className="px-1.5 py-0.5 rounded text-xs bg-white/30"
                      >
                        {dataset}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Helper Components
// =============================================================================

function getCategoryIcon(category: string) {
  switch (category) {
    case "auteur":
      return <span className="text-purple-500">*</span>;
    case "genre":
      return <span className="text-blue-500">*</span>;
    case "dimension":
      return <span className="text-green-500">*</span>;
    case "shot":
      return <span className="text-orange-500">*</span>;
    default:
      return null;
  }
}

function getEvidenceIcon(type: string) {
  switch (type) {
    case "database":
      return <Database className="w-3 h-3 shrink-0 mt-0.5" />;
    case "rag":
      return <FileText className="w-3 h-3 shrink-0 mt-0.5" />;
    case "ip":
      return <Sparkles className="w-3 h-3 shrink-0 mt-0.5" />;
    default:
      return <FileText className="w-3 h-3 shrink-0 mt-0.5" />;
  }
}

// =============================================================================
// Exports
// =============================================================================

export default EvidenceCard;
