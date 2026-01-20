"use client";

/**
 * NextNavWrapper - DimensionPanel.NextNav compound component
 *
 * Wraps existing NextDimensionNav component with dimension theming.
 * When in workflow mode (URL has ip/step/workflow params), shows WorkflowStepNav instead.
 */

import { type ComponentProps, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import NextDimensionNav from "../NextDimensionNav";
import { useDimensionPanel } from "./DimensionPanelContext";
import { WorkflowStepNav } from "@/components/workflow";
import { parseWorkflowUrlParams } from "@/lib/workflow-state";

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

// Inner component that uses useSearchParams (needs Suspense boundary)
function NextNavInner({
  currentDimension,
  show,
  className,
  navThemeColor,
  isLoading,
  result,
  props,
}: {
  currentDimension: string;
  show: boolean;
  className: string;
  navThemeColor: NextDimensionNavProps["themeColor"];
  isLoading: boolean;
  result: unknown;
  props: Omit<NextNavWrapperProps, "currentDimension" | "show" | "className">;
}) {
  const searchParams = useSearchParams();

  // Parse workflow URL params
  const workflowParams = useMemo(
    () => parseWorkflowUrlParams(searchParams),
    [searchParams]
  );

  // Check if we're in workflow mode
  const isWorkflowMode = !!(
    workflowParams.ipSlug &&
    workflowParams.step &&
    workflowParams.workflowKey
  );

  // In workflow mode, show WorkflowStepNav instead of NextDimensionNav
  if (isWorkflowMode) {
    // Extract result summary from result data for workflow state persistence
    const resultSummary = (() => {
      if (!result) return undefined;
      const r = result as Record<string, unknown>;
      // Try common result fields in priority order
      return (r.style_prompt || r.description || r.recreation_prompt || "Complete") as string;
    })();

    return (
      <div className={`mt-6 ${className}`}>
        <WorkflowStepNav
          currentApp={currentDimension}
          disabled={isLoading}
          resultData={result as Record<string, unknown>}
          resultSummary={resultSummary?.slice(0, 100)}
        />
      </div>
    );
  }

  // Default: show NextDimensionNav
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

export function NextNavWrapper({
  currentDimension: propCurrentDimension,
  show = true,
  className = "",
  ...props
}: NextNavWrapperProps) {
  const { dimensionCode, token, hasResult, isLoading, result } = useDimensionPanel();

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

  // Wrap with Suspense for useSearchParams
  return (
    <Suspense
      fallback={
        <div className={`mt-6 ${className}`}>
          <NextDimensionNav
            currentDimension={currentDimension}
            show={show}
            themeColor={navThemeColor}
            {...props}
          />
        </div>
      }
    >
      <NextNavInner
        currentDimension={currentDimension}
        show={show}
        className={className}
        navThemeColor={navThemeColor}
        isLoading={isLoading}
        result={result}
        props={props}
      />
    </Suspense>
  );
}

NextNavWrapper.displayName = "DimensionPanel.NextNav";
