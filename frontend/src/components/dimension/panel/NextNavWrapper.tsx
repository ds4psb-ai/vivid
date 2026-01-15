"use client";

/**
 * NextNavWrapper - DimensionPanel.NextNav compound component
 *
 * Wraps existing NextDimensionNav component with dimension theming.
 */

import { type ComponentProps } from "react";
import NextDimensionNav from "../NextDimensionNav";
import { useDimensionPanel } from "./DimensionPanelContext";

type NextDimensionNavProps = ComponentProps<typeof NextDimensionNav>;

export interface NextNavWrapperProps
  extends Omit<NextDimensionNavProps, "currentDimension" | "themeColor" | "show"> {
  /** Override current dimension (uses context if not provided) */
  currentDimension?: string;
  /** Show navigation (default: true when result exists) */
  show?: boolean;
  /** Additional className */
  className?: string;
}

// Map dimension code to route key
const DIMENSION_ROUTE_MAP: Record<string, string> = {
  "1d": "prompt-alchemy",
  "2d": "sound-crafter",
  "3d": "visual-realizer",
  "4d": "video-maker",
  ad: "aesthetic-director",
  ai: "reference-decoder",
  qc: "quality-director",
  veo: "veo",
  story: "story-architect",
  mirror: "abyss-mirror",
};

export function NextNavWrapper({
  currentDimension: propCurrentDimension,
  show = true,
  className = "",
  ...props
}: NextNavWrapperProps) {
  const { dimensionCode, token, hasResult, isLoading } = useDimensionPanel();

  // Only render when there's a result and show is true
  if (!show || !hasResult || isLoading) return null;

  // Convert dimension code to route key
  const currentDimension =
    propCurrentDimension || DIMENSION_ROUTE_MAP[dimensionCode] || dimensionCode;

  // Map dimension themeColor to NextDimensionNav supported colors
  // NextDimensionNav uses ThemeColor type from DimensionPanelLayout
  const themeColorMap: Record<string, NextDimensionNavProps["themeColor"]> = {
    violet: "violet",
    cyan: "cyan",
    emerald: "emerald",
    amber: "amber",
    rose: "rose",
    fuchsia: "fuchsia",
    indigo: "indigo",
    sky: "sky",
    purple: "violet", // Fallback
    red: "rose", // Fallback
  };

  const navThemeColor = themeColorMap[token.themeColor] || "amber";

  return (
    <div className={`mt-6 ${className}`}>
      <NextDimensionNav
        currentDimension={currentDimension}
        show={show}
        themeColor={navThemeColor}
        {...props}
      />
    </div>
  );
}

NextNavWrapper.displayName = "DimensionPanel.NextNav";
