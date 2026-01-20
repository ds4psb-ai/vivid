"use client";

/**
 * Content - DimensionPanel.Content compound component
 *
 * Main content area for results, loading states, and errors.
 * Automatically shows loading overlay when isLoading is true.
 */

import { type ReactNode, Children, isValidElement } from "react";
import { useDimensionPanel } from "./DimensionPanelContext";
import { LoadingState } from "./LoadingState";
import { ErrorState } from "./ErrorState";

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
  const { isLoading, hasError, error } = useDimensionPanel();

  // Separate LoadingState and ErrorState from other children
  const childArray = Children.toArray(children);
  const loadingChild = childArray.find(
    (child) => isValidElement(child) && child.type === LoadingState
  );
  const errorChild = childArray.find(
    (child) => isValidElement(child) && child.type === ErrorState
  );
  const otherChildren = childArray.filter(
    (child) =>
      !isValidElement(child) ||
      (child.type !== LoadingState && child.type !== ErrorState)
  );

  return (
    <div
      className={`flex-1 flex flex-col min-w-0 bg-transparent relative z-10 ${className}`}
    >
      <div
        className={`flex-1 overflow-y-auto ${padding} relative scroll-smooth custom-scrollbar`}
      >
        {/* Other children (Result, etc.) - these get blurred during loading */}
        {otherChildren}

        {/* Loading/Error Overlay - content is INSIDE so it's not blurred */}
        {(isLoading || hasError) && (
          <div
            className="absolute inset-0 bg-[var(--bg-overlay)] backdrop-blur-sm flex items-center justify-center z-50"
            style={{ animation: 'var(--animation-fade-in)' }}
            role="status"
            aria-live="polite"
          >
            {/* LoadingState and ErrorState are rendered INSIDE the overlay */}
            <div className="bg-[var(--glass-bg-strong)] backdrop-blur-xl rounded-2xl p-8 shadow-[var(--glass-shadow)] border border-[var(--glass-border)] max-w-md mx-4">
              {isLoading && loadingChild}
              {hasError && (errorChild || <ErrorState error={error || undefined} />)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

Content.displayName = "DimensionPanel.Content";
