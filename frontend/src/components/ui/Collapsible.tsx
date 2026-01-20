"use client";

import React, { useState, useId, ReactNode } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface CollapsibleProps {
  /** Header content (text or ReactNode) */
  header: ReactNode;
  /** Collapsible body content */
  children: ReactNode;
  /** Optional icon to display before header */
  icon?: ReactNode;
  /** Initial expanded state (default: false) */
  defaultExpanded?: boolean;
  /** Container className */
  className?: string;
  /** Header button className */
  headerClassName?: string;
}

/**
 * Collapsible component with CSS Grid animation
 *
 * Features:
 * - ARIA accessibility (aria-expanded, aria-controls)
 * - Keyboard navigation (Enter/Space)
 * - CSS Grid trick for smooth height animation
 * - Motion tokens from tokens.motion.css
 * - Reduced motion support (auto via tokens)
 *
 * @example
 * <Collapsible header="세계관" icon={<Globe />} defaultExpanded={false}>
 *   <p>Content here...</p>
 * </Collapsible>
 */
export function Collapsible({
  header,
  children,
  icon,
  defaultExpanded = false,
  className,
  headerClassName,
}: CollapsibleProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const id = useId();
  const contentId = `collapsible-content-${id}`;
  const headerId = `collapsible-header-${id}`;

  return (
    <div className={cn("rounded-xl border border-slate-200 dark:border-slate-700", className)}>
      {/* Header Button */}
      <button
        id={headerId}
        type="button"
        aria-expanded={isExpanded}
        aria-controls={contentId}
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "w-full flex items-center justify-between gap-3 p-4",
          "text-left font-bold text-slate-900 dark:text-white",
          "hover:bg-slate-50 dark:hover:bg-slate-800/50",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 focus-visible:ring-offset-2",
          "rounded-xl transition-colors",
          // Add duration token inline since Tailwind doesn't know custom properties
          "[transition-duration:var(--duration-fast)]",
          headerClassName
        )}
      >
        <span className="flex items-center gap-2 text-lg">
          {icon}
          {header}
        </span>
        <ChevronDown
          className={cn(
            "w-5 h-5 text-slate-500 dark:text-slate-400 flex-shrink-0",
            // Chevron rotation with motion token
            "transition-transform [transition-duration:var(--duration-moderate)] [transition-timing-function:var(--ease-smooth)]",
            isExpanded && "rotate-180"
          )}
          aria-hidden="true"
        />
      </button>

      {/* Content Region - CSS Grid Animation Trick */}
      <div
        id={contentId}
        role="region"
        aria-labelledby={headerId}
        className={cn(
          "grid overflow-hidden",
          // CSS Grid trick: 0fr → 1fr for smooth height animation
          "transition-[grid-template-rows] [transition-duration:var(--duration-moderate)] [transition-timing-function:var(--ease-smooth)]",
          isExpanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
        )}
      >
        <div className="min-h-0">
          <div className="px-4 pb-4">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
