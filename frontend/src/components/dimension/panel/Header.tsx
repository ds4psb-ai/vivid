"use client";

/**
 * Header - DimensionPanel.Header compound component
 *
 * Displays panel title with dimension color, credit cost badge, and optional actions.
 */

import { type ReactNode } from "react";
import Link from "next/link";
import { HelpCircle } from "lucide-react";
import { useDimensionPanel } from "./DimensionPanelContext";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useBYOK } from "@/hooks/useBYOK";

export interface HeaderProps {
  /** Panel title */
  title: string;
  /** Korean title (optional) */
  titleKo?: string;
  /** Credit cost to display */
  creditCost?: number;
  /** Help content for modal (if provided, shows help button) */
  helpContent?: ReactNode;
  /** Click handler for help button */
  onHelpClick?: () => void;
  /** Additional actions slot */
  actions?: ReactNode;
  /** Show back button (default: true) */
  showBackButton?: boolean;
  /** Back URL (default: /dimension) */
  backUrl?: string;
}

export function Header({
  title,
  titleKo,
  creditCost,
  helpContent,
  onHelpClick,
  actions,
  showBackButton = true,
  backUrl = "/dimension",
}: HeaderProps) {
  const { classes, token } = useDimensionPanel();
  const creditCtx = useCreditContextOptional();
  const { isBYOKEnabled } = useBYOK();

  return (
    <div
      className={`h-16 flex items-center justify-between px-6 border-b border-slate-200 dark:border-white/10 flex-shrink-0 bg-transparent relative`}
    >
      {/* Left: Back button + Title */}
      <div className="flex items-center gap-3">
        {showBackButton && (
          <Link
            href={backUrl}
            className="p-2 rounded-lg text-slate-500 dark:text-white/50 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/5 transition-colors"
            title="Back to Dimension"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
          </Link>
        )}

        <div className="flex flex-col">
          <h1
            className={`text-lg font-bold tracking-tight text-slate-900 dark:text-white/90`}
          >
            {title}
          </h1>
          {titleKo && (
            <span className="text-xs text-slate-500 dark:text-white/40">
              {titleKo}
            </span>
          )}
        </div>

        {/* Help Button */}
        {(helpContent || onHelpClick) && (
          <button
            onClick={onHelpClick}
            className="p-1.5 rounded-lg text-slate-400 dark:text-white/30 hover:text-slate-600 dark:hover:text-white/60 hover:bg-slate-100 dark:hover:bg-white/5 transition-colors"
            title="Help"
          >
            <HelpCircle className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Right: Actions + Credit Display */}
      <div className="flex items-center gap-3">
        {/* Custom actions */}
        {actions}

        {/* Credit Cost Badge */}
        {creditCost !== undefined && !isBYOKEnabled && (
          <div
            className={`px-3 py-1 rounded-full text-xs font-medium ${classes.bgSubtle} ${classes.text} border ${classes.border}`}
          >
            {creditCost} 크레딧
          </div>
        )}

        {/* Credit Balance */}
        {creditCtx && !isBYOKEnabled && (
          <Link
            href="/credits"
            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-200 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/10 transition-all group"
            title="크레딧 충전하기"
          >
            <svg
              className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            <span className="text-xs font-bold text-slate-700 dark:text-white/80 group-hover:text-slate-900 dark:group-hover:text-white font-mono">
              {creditCtx.isLoading ? "..." : creditCtx.balance.toLocaleString()}
            </span>
          </Link>
        )}

        {/* BYOK Active Badge */}
        {isBYOKEnabled && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-violet-100 dark:bg-violet-500/10 border border-violet-200 dark:border-violet-500/20 shadow-sm dark:shadow-[0_0_10px_rgba(139,92,246,0.2)]">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-violet-500" />
            </span>
            <span className="text-[10px] font-bold text-violet-600 dark:text-violet-400 tracking-wider">
              BYOK
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

Header.displayName = "DimensionPanel.Header";
