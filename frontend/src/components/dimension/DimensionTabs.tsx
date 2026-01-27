"use client";

/**
 * DimensionTabs - In-page Navigation for Dimension Tools
 *
 * Provides tab-based navigation within dimension pages to switch
 * between related tools in the same workflow stage.
 *
 * Usage:
 * ```tsx
 * <DimensionTabs currentApp="reference-decoder" />
 * ```
 */

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  DIMENSION_ITEMS,
  getDimensionIcon,
  type DimensionItemData,
  type DimensionStage,
} from "@/lib/dimension-data";

// =============================================================================
// TYPES
// =============================================================================

interface DimensionTabsProps {
  /** Current app ID (e.g., "reference-decoder") */
  currentApp?: string;
  /** Override stage filter */
  stage?: DimensionStage;
  /** Custom className */
  className?: string;
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Get related tools based on current app's stage
 */
function getRelatedTools(currentApp: string): DimensionItemData[] {
  const current = DIMENSION_ITEMS.find((item) => item.id === currentApp);
  if (!current) return [];

  return DIMENSION_ITEMS.filter(
    (item) => item.stage === current.stage && item.id !== currentApp
  ).sort((a, b) => a.stageOrder - b.stageOrder);
}

/**
 * Get all tools for a specific stage
 */
function getToolsByStage(stage: DimensionStage): DimensionItemData[] {
  return DIMENSION_ITEMS.filter((item) => item.stage === stage).sort(
    (a, b) => a.stageOrder - b.stageOrder
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function DimensionTabs({
  currentApp,
  stage,
  className = "",
}: DimensionTabsProps) {
  const pathname = usePathname();

  // Determine which tools to show
  const tools = stage
    ? getToolsByStage(stage)
    : currentApp
    ? [
        DIMENSION_ITEMS.find((item) => item.id === currentApp),
        ...getRelatedTools(currentApp),
      ].filter(Boolean) as DimensionItemData[]
    : [];

  // If no tools to show, return null
  if (tools.length === 0) return null;

  // Determine active tab from pathname
  const activeHref = tools.find((tool) => pathname === tool.href)?.href;

  return (
    <div
      className={`
        flex items-center gap-1 p-1
        bg-[var(--surface-2)] dark:bg-white/[0.03]
        border border-[var(--glass-border)]
        rounded-xl overflow-x-auto
        ${className}
      `}
      role="tablist"
      aria-label="관련 도구"
    >
      {tools.map((tool) => {
        const Icon = getDimensionIcon(tool.iconName);
        const isActive = pathname === tool.href || activeHref === tool.href;

        return (
          <Link
            key={tool.id}
            href={tool.href}
            role="tab"
            aria-selected={isActive}
            className={`
              flex items-center gap-2 px-3 py-2 rounded-lg
              text-sm font-medium whitespace-nowrap
              transition-all duration-200
              ${
                isActive
                  ? "bg-[var(--surface-1)] dark:bg-white/10 text-[var(--fg-0)] dark:text-white shadow-sm"
                  : "text-[var(--fg-muted)] hover:text-[var(--fg-0)] dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5"
              }
            `}
          >
            <Icon className="w-4 h-4" />
            <span>{tool.titleKo}</span>
            {tool.isNew && (
              <span className="px-1 py-0.5 text-[9px] font-bold uppercase tracking-wider bg-[var(--color-brand-primary)]/20 text-[var(--color-brand-primary)] rounded">
                NEW
              </span>
            )}
          </Link>
        );
      })}
    </div>
  );
}

// =============================================================================
// STAGE TABS VARIANT
// =============================================================================

interface DimensionStageTabsProps {
  /** Current stage */
  currentStage: DimensionStage;
  /** Custom className */
  className?: string;
}

/**
 * Alternative variant that shows stage-based tabs
 */
export function DimensionStageTabs({
  currentStage,
  className = "",
}: DimensionStageTabsProps) {
  const stages: { key: DimensionStage; label: string; color: string }[] = [
    { key: "planning", label: "기획", color: "emerald" },
    { key: "pre_production", label: "사전 제작", color: "violet" },
    { key: "production", label: "제작", color: "amber" },
    { key: "finishing", label: "완성", color: "cyan" },
    { key: "extended", label: "확장", color: "fuchsia" },
  ];

  return (
    <div
      className={`
        flex items-center gap-2 overflow-x-auto pb-2
        ${className}
      `}
      role="tablist"
      aria-label="워크플로우 단계"
    >
      {stages.map((stage) => {
        const isActive = currentStage === stage.key;
        const firstTool = DIMENSION_ITEMS.find(
          (item) => item.stage === stage.key
        );

        return (
          <Link
            key={stage.key}
            href={firstTool?.href || "/dimension"}
            role="tab"
            aria-selected={isActive}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-full
              text-sm font-medium whitespace-nowrap
              border transition-all duration-200
              ${
                isActive
                  ? `bg-${stage.color}-500/20 text-${stage.color}-500 border-${stage.color}-500/30`
                  : "bg-transparent text-[var(--fg-muted)] border-[var(--glass-border)] hover:text-[var(--fg-0)] dark:hover:text-white hover:border-[var(--border-strong)]"
              }
            `}
          >
            <span>{stage.label}</span>
          </Link>
        );
      })}
    </div>
  );
}

export default DimensionTabs;
