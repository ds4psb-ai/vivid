/**
 * Unified Workflow Types
 *
 * Shared types for the adaptive workflow system across all Mega Apps.
 * Supports DNA Lab, Story Engine, and Production with unified semantics.
 */

import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

/**
 * Mega App Identifiers
 */
export type MegaAppId = "dna-lab" | "story-engine" | "production";

/**
 * Sidebar display modes for progressive deepening UI
 */
export type SidebarMode = "summary" | "preview" | "detailed";

/**
 * Step execution status
 */
export type StepStatus = "pending" | "active" | "completed" | "skipped" | "error";

/**
 * Workflow step metadata
 */
export interface WorkflowStepMetadata {
  /** Unique step identifier */
  id: string;
  /** Korean label */
  label: string;
  /** English label */
  labelEn: string;
  /** Lucide icon component */
  icon: LucideIcon;
  /** Short description */
  description: string;

  // Data flow
  /** Required chain data keys from previous steps */
  inputs: string[];
  /** Chain data keys this step produces */
  outputs: string[];

  // Features
  /** Can AI infer missing inputs? */
  canInfer?: boolean;
  /** Can this step be skipped? */
  optional?: boolean;

  // UI
  /** Theme color (oklch hue) */
  color: string;
  /** Panel component name for dynamic loading */
  panelComponent: string;
}

/**
 * Sidebar configuration
 */
export interface SidebarConfig {
  /** Display mode: summary (DNA), preview (Story), detailed (Production) */
  mode: SidebarMode;
  /** Can sidebar be collapsed? */
  collapsible: boolean;
  /** Default collapsed state */
  defaultCollapsed?: boolean;
}

/**
 * Feature flags for workflow
 */
export interface WorkflowFeatures {
  /** AI inference for missing data */
  aiInference: boolean;
  /** Unified pipeline execution */
  pipeline: boolean;
  /** Show step execution timer */
  showTimer?: boolean;
  /** Auto-advance to next step on completion */
  autoAdvance?: boolean;
}

/**
 * Workflow configuration for each Mega App
 */
export interface WorkflowConfig {
  /** Unique app identifier */
  id: MegaAppId;
  /** App display title */
  title: string;
  /** App subtitle */
  subtitle: string;
  /** Header icon */
  icon: LucideIcon;
  /** Workflow steps */
  steps: WorkflowStepMetadata[];
  /** Sidebar configuration */
  sidebar: SidebarConfig;
  /** Feature flags */
  features: WorkflowFeatures;
  /** Required chain data from previous apps */
  requiredChainData?: string[];
  /** URL parameter name for step navigation */
  stepParamName?: string;
  /** Default step when no parameter */
  defaultStep?: string;
}

/**
 * Step state with completion and data info
 */
export interface StepState {
  step: WorkflowStepMetadata;
  status: StepStatus;
  hasData: boolean;
  missingInputs: string[];
  canInfer: boolean;
}

/**
 * Workflow state returned by useUnifiedWorkflow
 */
export interface UnifiedWorkflowState {
  // Config
  config: WorkflowConfig;

  // Current state
  currentStep: WorkflowStepMetadata;
  currentStepId: string;
  currentStepIndex: number;

  // All steps state
  steps: StepState[];
  completedSteps: string[];
  completionPercentage: number;

  // Navigation
  canGoNext: boolean;
  canGoPrevious: boolean;
  nextStep: WorkflowStepMetadata | undefined;
  previousStep: WorkflowStepMetadata | undefined;

  // Actions
  goToStep: (stepId: string) => void;
  goToNext: () => void;
  goToPrevious: () => void;
  markStepComplete: (stepId: string, data: Record<string, unknown>) => void;

  // Data
  getStepData: (stepId: string) => Record<string, unknown> | undefined;
  getInputDataForStep: (stepId: string) => Record<string, Record<string, unknown>>;
  chainData: Record<string, Record<string, unknown>>;

  // AI Inference
  canInferForStep: (stepId: string) => boolean;
  getMissingInputsForStep: (stepId: string) => string[];
}

/**
 * Chain data stored for each dimension/step
 */
export interface ChainDataEntry {
  /** Step/dimension key */
  key: string;
  /** Output data */
  output: Record<string, unknown>;
  /** Timestamp of generation */
  timestamp: number;
  /** Summary text for display */
  summary?: string;
  /** Evidence references */
  evidenceRefs?: string[];
}

/**
 * Props for UnifiedWorkflowShell
 */
export interface UnifiedWorkflowShellProps {
  /** App identifier */
  appId: MegaAppId;
  /** Children render function receives current step ID */
  children: (currentStepId: string) => ReactNode;
  /** Show aurora background */
  showAurora?: boolean;
  /** Show global workflow progress */
  showWorkflowProgress?: boolean;
  /** Show chain summary sidebar */
  showChainSummary?: boolean;
  /** Header right slot */
  headerRight?: ReactNode;
}

/**
 * Chain data source mapping - which app/step produces each data key
 */
export interface ChainDataSource {
  app: MegaAppId;
  step: string;
  label: string;
}

// =============================================================================
// AI Suggested Defaults (Phase 2: MissingDataBanner 확장)
// =============================================================================

/**
 * AI-inferred default value for missing chain data
 * Used by MissingDataBanner to propose values instead of blocking
 */
export interface SuggestedDefault {
  /** Inferred value (can be any JSON-serializable data) */
  value: unknown;
  /** Confidence score 0-100 */
  confidence: number;
  /** Confidence level category */
  confidenceLevel: "high" | "medium" | "low";
  /** Evidence sources (evidence_refs format, e.g., "db:rag_docs:4D:kang:001") */
  evidenceSources?: string[];
  /** Human-readable summary of inference reasoning */
  summary?: string;
}

/**
 * Confidence level type (shared with EvidenceCard)
 */
export type ConfidenceLevel = "high" | "medium" | "low";

/**
 * Get confidence level from numeric score
 * - high: >= 85%
 * - medium: 50-84%
 * - low: < 50%
 */
export function getConfidenceLevel(confidence: number): ConfidenceLevel {
  if (confidence >= 85) return "high";
  if (confidence >= 50) return "medium";
  return "low";
}

/**
 * Get color configuration for confidence level
 * Matches EvidenceCard/RAGSuggestionCard patterns
 */
export function getConfidenceColorConfig(level: ConfidenceLevel) {
  switch (level) {
    case "high":
      return {
        bg: "bg-emerald-500/10",
        text: "text-emerald-400",
        border: "border-emerald-500/20",
        label: "높음",
        labelEn: "High",
      };
    case "medium":
      return {
        bg: "bg-amber-500/10",
        text: "text-amber-400",
        border: "border-amber-500/20",
        label: "보통",
        labelEn: "Medium",
      };
    case "low":
      return {
        bg: "bg-slate-500/10",
        text: "text-slate-400",
        border: "border-slate-500/20",
        label: "낮음",
        labelEn: "Low",
      };
  }
}
