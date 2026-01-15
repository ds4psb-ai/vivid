"use client";

/**
 * DimensionPanel - Root Compound Component
 *
 * Provides unified panel structure for all 11 Dimension tools.
 * Uses Compound Component pattern for flexible composition.
 *
 * Usage:
 * ```tsx
 * <DimensionPanel dimensionCode="ad">
 *   <DimensionPanel.Header title="Aesthetic Director" />
 *   <DimensionPanel.Sidebar>
 *     <DimensionPanel.Textarea label="Concept" />
 *     <DimensionPanel.GenerateButton>Generate</DimensionPanel.GenerateButton>
 *   </DimensionPanel.Sidebar>
 *   <DimensionPanel.Content>
 *     <DimensionPanel.Loading />
 *     <DimensionPanel.Error />
 *     <DimensionPanel.Result>{...}</DimensionPanel.Result>
 *   </DimensionPanel.Content>
 * </DimensionPanel>
 * ```
 *
 * @see PANEL_DESIGN_UNITY_SPEC.md
 */

import { type ReactNode } from "react";
import { type DimensionCode } from "@/lib/tokens";
import { DimensionPanelProvider, useDimensionPanel } from "./DimensionPanelContext";

// Sub-components (will be attached to DimensionPanel)
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { Content } from "./Content";
import { Input } from "./Input";
import { Textarea } from "./Textarea";
import { Select } from "./Select";
import { GenerateButton } from "./GenerateButton";
import { LoadingState } from "./LoadingState";
import { ErrorState } from "./ErrorState";
import { ResultCard } from "./ResultCard";
import { EvidenceWrapper } from "./EvidenceWrapper";
import { FeedbackWrapper } from "./FeedbackWrapper";
import { NextNavWrapper } from "./NextNavWrapper";
import { FileUploadWrapper } from "./FileUploadWrapper";
import { ABComparisonWrapper } from "./ABComparisonWrapper";
import { ThreeWayComparisonWrapper } from "./ThreeWayComparisonWrapper";
import { MultiGenerateWrapper } from "./MultiGenerateWrapper";

// =============================================================================
// ROOT COMPONENT
// =============================================================================

export interface DimensionPanelProps {
  /** Dimension code for theming and context */
  dimensionCode: DimensionCode;
  /** Child components */
  children: ReactNode;
  /** Additional className for root element */
  className?: string;
}

function DimensionPanelRoot({
  dimensionCode,
  children,
  className = "",
}: DimensionPanelProps) {
  return (
    <DimensionPanelProvider dimensionCode={dimensionCode}>
      <DimensionPanelInner className={className}>
        {children}
      </DimensionPanelInner>
    </DimensionPanelProvider>
  );
}

/**
 * Inner component that has access to context
 */
function DimensionPanelInner({
  children,
  className,
}: {
  children: ReactNode;
  className: string;
}) {
  const { dimensionCode } = useDimensionPanel();

  return (
    <div
      className={`flex h-full w-full overflow-hidden relative ${className}`}
      data-dimension={dimensionCode}
    >
      {children}
    </div>
  );
}

// =============================================================================
// COMPOUND COMPONENT ASSEMBLY
// =============================================================================

/**
 * DimensionPanel with all sub-components attached
 */
export const DimensionPanel = Object.assign(DimensionPanelRoot, {
  // Layout
  Header,
  Sidebar,
  Content,

  // Input Components
  Input,
  Textarea,
  Select,
  GenerateButton,
  FileUpload: FileUploadWrapper,

  // Result Components
  Loading: LoadingState,
  Error: ErrorState,
  Result: ResultCard,
  Evidence: EvidenceWrapper,
  Feedback: FeedbackWrapper,
  NextNav: NextNavWrapper,

  // UQSL Quality Selection Components
  ABComparison: ABComparisonWrapper,
  ThreeWay: ThreeWayComparisonWrapper,
  MultiGenerate: MultiGenerateWrapper,
});

// =============================================================================
// RE-EXPORTS
// =============================================================================

export { useDimensionPanel, useDimensionPanelOptional } from "./DimensionPanelContext";
export type { DimensionPanelContextValue, DimensionPanelStyles } from "./DimensionPanelContext";
