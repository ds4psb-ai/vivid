"use client";

/**
 * EvidenceWrapper - DimensionPanel.Evidence compound component
 *
 * Wraps existing EvidenceDisplay component with dimension theming.
 */

import { type ComponentProps } from "react";
import EvidenceDisplay from "../EvidenceDisplay";
import { useDimensionPanel } from "./DimensionPanelContext";

type EvidenceDisplayProps = ComponentProps<typeof EvidenceDisplay>;

export interface EvidenceWrapperProps
  extends Omit<EvidenceDisplayProps, "themeColor"> {
  /** Additional className */
  className?: string;
}

export function EvidenceWrapper({
  refs,
  className = "",
  ...props
}: EvidenceWrapperProps) {
  const { token, hasResult, isLoading } = useDimensionPanel();

  // Only render when there's a result
  if (!hasResult || isLoading) return null;

  // Map dimension themeColor to EvidenceDisplay supported colors
  const themeColorMap: Record<string, EvidenceDisplayProps["themeColor"]> = {
    violet: "violet",
    cyan: "cyan",
    emerald: "emerald",
    amber: "amber",
    rose: "rose",
    fuchsia: "rose", // Fallback to rose
    indigo: "violet", // Fallback to violet
    sky: "cyan", // Fallback to cyan
    purple: "violet", // Fallback to violet
    red: "rose", // Fallback to rose
  };

  const evidenceThemeColor = themeColorMap[token.themeColor] || "amber";

  return (
    <div className={className}>
      <EvidenceDisplay
        refs={refs}
        themeColor={evidenceThemeColor}
        {...props}
      />
    </div>
  );
}

EvidenceWrapper.displayName = "DimensionPanel.Evidence";
