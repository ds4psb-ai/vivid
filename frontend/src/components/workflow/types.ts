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
