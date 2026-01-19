"use client";

/**
 * Content - DimensionPanel.Content compound component
 *
 * Main content area for results, loading states, and errors.
 * Automatically shows loading overlay when isLoading is true.
 */

import { type ReactNode } from "react";
import { useDimensionPanel } from "./DimensionPanelContext";

export interface ContentProps {
  /** Child components (Result, Loading, Error, etc.) */
  children: ReactNode;
  /** Additional className */
  className?: string;
  /** Padding (default: p-8) */
  padding?: string;
}

export function Content({
  children,
  className = "",
  padding = "p-8",
}: ContentProps) {
  const { isLoading, hasError } = useDimensionPanel();

  return (
    <div
      className={`flex-1 flex flex-col min-w-0 bg-transparent relative z-10 ${className}`}
    >
      <div
        className={`flex-1 overflow-y-auto ${padding} relative scroll-smooth custom-scrollbar`}
      >
        {children}

        {/* Loading/Error Overlay */}
        {(isLoading || hasError) && (
          <div
            className="absolute inset-0 bg-slate-900/40 dark:bg-[#0F0F1A]/40 backdrop-blur-md flex items-center justify-center z-50 animate-in fade-in duration-300"
            role="status"
            aria-live="polite"
          >
            {/* Overlay content is handled by LoadingState and ErrorState components */}
          </div>
        )}
      </div>
    </div>
  );
}

Content.displayName = "DimensionPanel.Content";
