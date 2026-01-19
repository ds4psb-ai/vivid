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

// =============================================================================
// Types
// =============================================================================

export type ConfidenceLevel = "high" | "medium" | "low";

export interface EvidenceCardProps {
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
// Reason Code Labels (i18n ready)
// =============================================================================

const REASON_CODE_LABELS: Record<string, Record<string, string>> = {
  genre: {
    romance: "Romance Genre",
    horror: "Horror Genre",
    action: "Action Genre",
    drama: "Drama Genre",
    comedy: "Comedy Genre",
    thriller: "Thriller Genre",
    fantasy: "Fantasy Genre",
    "sci-fi": "Sci-Fi Genre",
  },
  auteur: {
    bong: "Bong Joon-ho Style",
    nolan: "Christopher Nolan Style",
    kubrick: "Stanley Kubrick Style",
    tarantino: "Quentin Tarantino Style",
    ghibli: "Studio Ghibli Style",
    villeneuve: "Denis Villeneuve Style",
  },
  dimension: {
    "1D": "1D Prompt",
    "2D": "2D Storyboard",
    "3D": "3D Visual",
    "4D": "4D Reference",
    AD: "Aesthetic Director",
    QC: "Quality Check",
    VEO: "Video Generation",
    STORY: "Story Architect",
    SOUND: "Sound Crafter",
  },
  shot: {
    closeup: "Close-up Shot",
    wide: "Wide Shot",
    establishing: "Establishing Shot",
    pov: "POV Shot",
    tracking: "Tracking Shot",
    aerial: "Aerial Shot",
    action: "Action Scene",
    dialogue: "Dialogue Scene",
    montage: "Montage",
  },
  context: {
    worldbuilding: "Worldbuilding Context",
    character: "Character Focus",
    setting: "Setting Focus",
    theme: "Theme Match",
    workflow_preset: "Workflow Match",
  },
  history: {
    frequently_used: "Frequently Used",
    recently_used: "Recently Used",
    workflow_pattern: "Workflow Pattern",
  },
};

// =============================================================================
// Helpers
// =============================================================================

function parseReasonCode(code: string): { category: string; value: string } {
  const [category, ...rest] = code.split(":");
  return { category, value: rest.join(":") };
}

function getReasonLabel(code: string): string {
  const { category, value } = parseReasonCode(code);
  return REASON_CODE_LABELS[category]?.[value] || code;
}

function getConfidenceColor(level: ConfidenceLevel): string {
  switch (level) {
    case "high":
      return "text-green-600 bg-green-50 border-green-200";
    case "medium":
      return "text-yellow-600 bg-yellow-50 border-yellow-200";
    case "low":
      return "text-gray-600 bg-gray-50 border-gray-200";
  }
}

function getConfidenceLabel(level: ConfidenceLevel): string {
  switch (level) {
    case "high":
      return "HIGH";
    case "medium":
      return "MEDIUM";
    case "low":
      return "LOW";
  }
}

function formatEvidenceRef(ref: string): { type: string; label: string } {
  const parts = ref.split(":");
  const prefix = parts[0];

  switch (prefix) {
    case "db":
      return {
        type: "database",
        label: parts.slice(1).join("/"),
      };
    case "rag":
      return {
        type: "rag",
        label: `RAG: ${parts.slice(1).join("/")}`,
      };
    case "ip":
      return {
        type: "ip",
        label: `IP: ${parts.slice(1).join("/")}`,
      };
    default:
      return {
        type: "other",
        label: ref,
      };
  }
}

// =============================================================================
// Component
// =============================================================================

export function EvidenceCard({
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
  const [isExpanded, setIsExpanded] = useState(!isCollapsible);

  // Parse reason codes into display format
  const reasonLabels = useMemo(() => {
    return reasonCodes.map((code) => ({
      code,
      label: getReasonLabel(code),
      category: parseReasonCode(code).category,
    }));
  }, [reasonCodes]);

  // Parse evidence refs
  const evidenceItems = useMemo(() => {
    return evidenceRefs.map((ref) => ({
      ref,
      ...formatEvidenceRef(ref),
    }));
  }, [evidenceRefs]);

  const confidencePercent = confidence ? Math.round(confidence * 100) : null;

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
          {getConfidenceLabel(confidenceLevel)}
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
        getConfidenceColor(confidenceLevel),
        className
      )}
    >
      {/* Header: Confidence */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4" />
          <span className="font-medium text-sm">Recommendation Confidence:</span>
          <Badge
            variant={confidenceLevel === "high" ? "default" : "secondary"}
            className="ml-1"
          >
            {getConfidenceLabel(confidenceLevel)}
            {confidencePercent && ` (${confidencePercent}%)`}
          </Badge>
        </div>
      </div>

      {/* Reason Summary */}
      {reasonSummary && (
        <p className="text-sm opacity-90">{reasonSummary}</p>
      )}

      {/* Reason Codes */}
      {reasonLabels.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs font-medium opacity-75">
            <Sparkles className="w-3 h-3" />
            <span>Recommendation Reasons:</span>
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
              <span>Evidence Data</span>
              {isExpanded ? (
                <ChevronUp className="w-3 h-3 ml-auto" />
              ) : (
                <ChevronDown className="w-3 h-3 ml-auto" />
              )}
            </button>
          ) : (
            <div className="flex items-center gap-1 text-xs font-medium opacity-75">
              <Database className="w-3 h-3" />
              <span>Evidence Data</span>
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
                <div className="flex flex-wrap gap-1 pt-1">
                  {datasetsUsed.map((dataset) => (
                    <span
                      key={dataset}
                      className="px-1.5 py-0.5 rounded text-xs bg-white/30"
                    >
                      {dataset}
                    </span>
                  ))}
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
