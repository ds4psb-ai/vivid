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
  Search,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "./badge";
import { Input } from "./input";
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
  /** Workflow trace items for evidence */
  workflowTrace?: EvidenceTraceItem[];
  /** Whether the evidence section is collapsible */
  isCollapsible?: boolean;
  /** Custom class name */
  className?: string;
  /** Compact mode for inline display */
  compact?: boolean;
}

export interface EvidenceTraceItem {
  evidence_id: string;
  source: string;
  ref: string;
  confidence: number | null;
  status: string | null;
  timestamp: string | null;
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

function formatEvidenceRef(ref: string): { type: string; label: string } {
  const parts = ref.split(":");
  const prefix = parts[0];
  const category = parts[1];

  if (prefix === "db" && category === "rag_docs") {
    return {
      type: "rag",
      label: `${parts.slice(2).join("/")}`,
    };
  }

  if (prefix === "db" && category === "ip_catalog") {
    return {
      type: "ip",
      label: `${parts.slice(2).join("/")}`,
    };
  }

  if (prefix === "db" && category === "capsule_runs") {
    return {
      type: "run",
      label: `${parts.slice(2).join("/")}`,
    };
  }

  if (prefix === "rag") {
    return {
      type: "rag",
      label: `${parts.slice(1).join("/")}`,
    };
  }

  if (prefix === "ip") {
    return {
      type: "ip",
      label: `${parts.slice(1).join("/")}`,
    };
  }

  if (prefix === "db") {
    return {
      type: "database",
      label: `${parts.slice(1).join("/")}`,
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
  workflowTrace = [],
  isCollapsible = true,
  className = "",
  compact = false,
}: EvidenceCardProps) {
  const { language, t } = useLanguage();
  const isKo = language === "ko";
  const [isExpanded, setIsExpanded] = useState(!isCollapsible);
  const isEvidenceOnly = variant === "evidence";
  const [traceQuery, setTraceQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [minConfidence, setMinConfidence] = useState(0);

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
      ...formatEvidenceRef(ref),
    }));
  }, [evidenceRefs]);

  const normalizedQuery = traceQuery.trim().toLowerCase();
  const statusOptions = useMemo(() => {
    const statuses = new Set<string>();
    workflowTrace.forEach((trace) => {
      if (trace.status) {
        statuses.add(trace.status.toLowerCase());
      } else {
        statuses.add("unknown");
      }
    });
    return Array.from(statuses);
  }, [workflowTrace]);

  const filteredTrace = useMemo(() => {
    let list = workflowTrace;

    if (normalizedQuery) {
      list = list.filter((trace) => {
        const haystack = [
          trace.ref,
          trace.source,
          trace.status ?? "",
          trace.confidence !== null ? String(trace.confidence) : "",
        ]
          .join(" ")
          .toLowerCase();
        return haystack.includes(normalizedQuery);
      });
    }

    if (statusFilter !== "all") {
      list = list.filter((trace) => {
        const statusValue = trace.status ? trace.status.toLowerCase() : "unknown";
        return statusValue === statusFilter;
      });
    }

    if (minConfidence > 0) {
      list = list.filter((trace) => (trace.confidence ?? 0) >= minConfidence / 100);
    }

    return list;
  }, [workflowTrace, normalizedQuery, statusFilter, minConfidence]);
  const traceVisible = useMemo(() => filteredTrace.slice(0, 6), [filteredTrace]);
  const traceHiddenCount = Math.max(filteredTrace.length - traceVisible.length, 0);

  const confidencePercent = confidence ? Math.round(confidence * 100) : null;
  const labels = useMemo(
    () => ({
      confidenceTitle: t("evidenceConfidenceTitle"),
      reasonsTitle: t("evidenceReasonsTitle"),
      evidenceTitle: t("evidenceDataTitle"),
      datasetsUsed: t("evidenceDatasetsUsed"),
      evidenceCardTitle: t("evidenceSummaryTitle"),
      evidenceSourcesTitle: t("evidenceSourcesTitle"),
      evidenceTraceTitle: t("evidenceTraceTitle"),
      evidenceTraceFilterPlaceholder: t("evidenceTraceFilterPlaceholder"),
      evidenceTraceEmpty: t("evidenceTraceEmpty"),
      evidenceTraceMinConfidence: t("evidenceTraceMinConfidence"),
      traceFilterAll: t("traceFilterAll"),
      traceFilterUnknown: t("traceFilterUnknown"),
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
                className="evidence-badge inline-flex items-center text-[11px]"
                title={code}
                data-tone={category}
              >
                {getCategoryIcon(category)}
                <span className="ml-1">{label}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Collapsible Evidence Section */}
      {(evidenceItems.length > 0 || datasetsUsed.length > 0 || workflowTrace.length > 0) && (
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
            <div className="mt-2 rounded-md border border-current/10 bg-white/60 dark:bg-slate-900/60 p-3 space-y-3 animate-in fade-in duration-200">
              {/* Evidence Sources */}
              {evidenceItems.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] uppercase tracking-[0.18em] opacity-70">
                    {labels.evidenceSourcesTitle}
                  </div>
                  <ul className="space-y-1">
                    {evidenceItems.map(({ ref, type, label }) => (
                      <li
                        key={ref}
                        className="flex items-start gap-2 text-xs opacity-80"
                      >
                        {getEvidenceIcon(type)}
                        <span className="evidence-badge text-[9px] uppercase tracking-[0.08em]" data-tone="source">
                          {getEvidenceSourceLabel(type, t as (key: string) => string)}
                        </span>
                        <span className="break-all">{label}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Workflow Trace */}
              {workflowTrace.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.18em] opacity-70">
                    <span>{labels.evidenceTraceTitle}</span>
                    <span className="text-slate-400 normal-case tracking-normal">
                      {filteredTrace.length}/{workflowTrace.length}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 rounded-md border border-current/10 bg-white/40 dark:bg-slate-900/50 px-2 py-1">
                    <Search className="w-3 h-3 text-slate-400" />
                    <Input
                      value={traceQuery}
                      onChange={(event) => setTraceQuery(event.target.value)}
                      placeholder={labels.evidenceTraceFilterPlaceholder}
                      className="border-0 bg-transparent text-[11px] focus-visible:ring-0"
                    />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => setStatusFilter("all")}
                      className={cn(
                        "text-[10px] px-2 py-0.5 rounded-full border",
                        statusFilter === "all"
                          ? "bg-violet-500/10 border-violet-400 text-violet-500"
                          : "border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400"
                      )}
                    >
                      {labels.traceFilterAll}
                    </button>
                    {statusOptions.map((status) => (
                      <button
                        key={status}
                        type="button"
                        onClick={() => setStatusFilter(status)}
                        className={cn(
                          "text-[10px] px-2 py-0.5 rounded-full border uppercase",
                          statusFilter === status
                            ? "bg-violet-500/10 border-violet-400 text-violet-500"
                            : "border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400"
                        )}
                      >
                        {getStatusLabel(status, t as (key: string) => string, labels.traceFilterUnknown)}
                      </button>
                    ))}
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-slate-500 dark:text-slate-400">
                    <span>{labels.evidenceTraceMinConfidence}</span>
                    <input
                      type="range"
                      min={0}
                      max={100}
                      value={minConfidence}
                      onChange={(event) => setMinConfidence(Number(event.target.value))}
                      className="flex-1 accent-violet-500"
                    />
                    <span className="tabular-nums">{minConfidence}%</span>
                  </div>
                  {filteredTrace.length === 0 ? (
                    <div className="text-[11px] text-slate-400">
                      {labels.evidenceTraceEmpty}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {traceVisible.map((trace) => (
                        <div
                          key={trace.evidence_id}
                          className="flex items-center justify-between rounded-md border border-current/10 px-3 py-2 text-[11px]"
                        >
                          <div className="flex flex-col gap-0.5">
                            <span className="font-mono text-slate-600 dark:text-slate-300">
                              {trace.ref}
                            </span>
                            <span className="text-[10px] text-slate-400">
                              {trace.source}
                              {trace.timestamp ? ` · ${new Date(trace.timestamp).toLocaleString()}` : ""}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 text-[10px] text-slate-500 dark:text-slate-400">
                            {trace.confidence !== null && (
                              <span>{Math.round(trace.confidence * 100)}%</span>
                            )}
                          {trace.status && (
                            <span
                              className="status-badge"
                              data-tone={getStatusTone(trace.status)}
                            >
                              {getStatusLabel(
                                trace.status.toLowerCase(),
                                t,
                                labels.traceFilterUnknown
                              )}
                            </span>
                          )}
                          </div>
                        </div>
                      ))}
                      {traceHiddenCount > 0 && (
                        <div className="text-[10px] text-slate-400">
                          +{traceHiddenCount} {t("moreLabel")}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Datasets Used */}
              {datasetsUsed.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] uppercase tracking-[0.18em] opacity-70">
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
    case "run":
      return <Database className="w-3 h-3 shrink-0 mt-0.5" />;
    case "rag":
      return <FileText className="w-3 h-3 shrink-0 mt-0.5" />;
    case "ip":
      return <Sparkles className="w-3 h-3 shrink-0 mt-0.5" />;
    default:
      return <FileText className="w-3 h-3 shrink-0 mt-0.5" />;
  }
}

function getStatusLabel(
  status: string,
  t: (key: string) => string,
  unknownLabel: string
) {
  switch (status) {
    case "completed":
      return t("statusCompleted");
    case "failed":
      return t("statusFailed");
    case "running":
      return t("statusRunning");
    case "pending":
      return t("statusPending");
    case "cancelled":
      return t("statusCancelled");
    case "unknown":
      return unknownLabel;
    default:
      return status.toUpperCase();
  }
}

function getStatusTone(status: string) {
  switch (status.toLowerCase()) {
    case "completed":
      return "success";
    case "failed":
      return "error";
    case "running":
      return "info";
    case "pending":
      return "warning";
    case "cancelled":
      return "muted";
    default:
      return "muted";
  }
}

function getEvidenceSourceLabel(type: string, t: (key: string) => string) {
  switch (type) {
    case "rag":
      return t("evidenceSourceRag");
    case "ip":
      return t("evidenceSourceIp");
    case "run":
      return t("evidenceSourceRun");
    case "database":
      return t("evidenceSourceDb");
    default:
      return t("evidenceSourceOther");
  }
}

// =============================================================================
// Exports
// =============================================================================

export default EvidenceCard;
