"use client";

/**
 * WorkflowBreadcrumb - Navigation breadcrumb for workflow context
 *
 * Features:
 * - Shows navigation hierarchy (Studio > App > Step)
 * - Clickable links for navigation
 * - Current item highlighted
 * - Accessible (aria-label, semantic nav)
 *
 * 2026 UX Pattern: Always know where you are
 */

import Link from "next/link";
import { ChevronRight, Home, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

// =============================================================================
// Types
// =============================================================================

export interface BreadcrumbItem {
  /** Display label */
  label: string;
  /** Navigation href (optional - no link if not provided) */
  href?: string;
  /** Optional icon */
  icon?: LucideIcon;
}

export interface WorkflowBreadcrumbProps {
  /** Breadcrumb items */
  items: BreadcrumbItem[];
  /** Additional className */
  className?: string;
  /** Size variant */
  size?: "sm" | "md";
}

// =============================================================================
// Component
// =============================================================================

/**
 * Workflow breadcrumb navigation
 *
 * @example
 * ```tsx
 * <WorkflowBreadcrumb
 *   items={[
 *     { label: "Studio", href: "/", icon: Home },
 *     { label: "DNA Lab", href: "/dna-lab" },
 *     { label: "Creative DNA" }
 *   ]}
 * />
 * ```
 */
export function WorkflowBreadcrumb({
  items,
  className,
  size = "sm",
}: WorkflowBreadcrumbProps) {
  if (items.length === 0) return null;

  const textSize = size === "sm" ? "text-xs" : "text-sm";
  const iconSize = size === "sm" ? "w-3 h-3" : "w-4 h-4";

  return (
    <nav aria-label="Breadcrumb" className={cn("px-4 py-2", className)}>
      <ol className={cn("flex items-center gap-1.5 flex-wrap", textSize)}>
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          const Icon = item.icon;

          return (
            <li key={index} className="flex items-center gap-1.5">
              {/* Separator (not for first item) */}
              {index > 0 && (
                <ChevronRight
                  className={cn(iconSize, "text-white/30")}
                  aria-hidden="true"
                />
              )}

              {/* Breadcrumb item */}
              {item.href && !isLast ? (
                <Link
                  href={item.href}
                  className={cn(
                    "inline-flex items-center gap-1 text-white/60 hover:text-white transition-colors",
                    "rounded px-1 py-0.5 -mx-1 hover:bg-white/5"
                  )}
                >
                  {Icon && <Icon className={iconSize} />}
                  <span>{item.label}</span>
                </Link>
              ) : (
                <span
                  className={cn(
                    "inline-flex items-center gap-1",
                    isLast ? "text-white font-medium" : "text-white/60"
                  )}
                  aria-current={isLast ? "page" : undefined}
                >
                  {Icon && <Icon className={iconSize} />}
                  <span>{item.label}</span>
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

// =============================================================================
// Workflow-specific Breadcrumb Builder
// =============================================================================

export interface WorkflowBreadcrumbConfig {
  /** App ID (e.g., "dna-lab") */
  appId: string;
  /** App title */
  appTitle: string;
  /** Current step label */
  currentStepLabel: string;
  /** Whether to show home link */
  showHome?: boolean;
}

/**
 * Build breadcrumb items for workflow context
 *
 * @example
 * ```tsx
 * const items = buildWorkflowBreadcrumb({
 *   appId: "dna-lab",
 *   appTitle: "DNA Lab",
 *   currentStepLabel: "Creative DNA",
 * });
 * ```
 */
export function buildWorkflowBreadcrumb({
  appId,
  appTitle,
  currentStepLabel,
  showHome = true,
}: WorkflowBreadcrumbConfig): BreadcrumbItem[] {
  const items: BreadcrumbItem[] = [];

  if (showHome) {
    items.push({
      label: "Studio",
      href: "/",
      icon: Home,
    });
  }

  items.push({
    label: appTitle,
    href: `/${appId}`,
  });

  items.push({
    label: currentStepLabel,
  });

  return items;
}
