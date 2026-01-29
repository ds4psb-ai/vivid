/**
 * Unified Workflow Components
 *
 * Adaptive Layout Engine for all Mega Apps.
 * Single set of components, multiple behaviors based on configuration.
 *
 * Usage:
 * ```tsx
 * import { UnifiedWorkflowShell } from "@/components/workflow";
 *
 * export default function DNALabPage() {
 *   return (
 *     <UnifiedWorkflowShell appId="dna-lab">
 *       {(currentStepId) => <StepPanel stepId={currentStepId} />}
 *     </UnifiedWorkflowShell>
 *   );
 * }
 * ```
 */

// Legacy export (keep for backward compatibility)
export { WorkflowStepNav } from "./WorkflowStepNav";
export type { WorkflowStepNavProps } from "./WorkflowStepNav";

// Main shell component
export { UnifiedWorkflowShell } from "./UnifiedWorkflowShell";

// Progress/Stepper
export {
  UnifiedWorkflowProgress,
  UnifiedWorkflowProgressCompact,
} from "./UnifiedWorkflowProgress";

// Step navigation
export { UnifiedStepNav, UnifiedStepNavCompact } from "./UnifiedStepNav";

// Chain sidebar
export { UnifiedChainSidebar } from "./UnifiedChainSidebar";

// Missing data UI
export { MissingDataBanner, MissingDataIndicator } from "./MissingDataBanner";

// Execution Timer
export {
  StepExecutionTimer,
  InlineTimer,
  WorkflowTimingSummary,
  formatDuration,
  formatDurationPrecise,
} from "./StepExecutionTimer";

// Sync Status
export { SyncStatusIndicator, InlineSyncStatus } from "./SyncStatusIndicator";

// Hooks
export { useUnifiedWorkflow } from "./hooks/useUnifiedWorkflow";
export {
  useRequiredChainData,
  useOptionalChainData,
} from "./hooks/useRequiredChainData";
export {
  useWorkflowObservability,
  WorkflowObservabilityProvider,
  useWorkflowObservabilityContext,
  useWorkflowObservabilityOptional,
} from "./hooks/useWorkflowObservability";
export {
  useChainDataWithOptimism,
} from "./hooks/useChainDataWithOptimism";
export {
  useIPChainData,
} from "./hooks/useIPChainData";

// Configs & Utilities
export {
  WORKFLOW_CONFIGS,
  DNA_LAB_STEPS,
  STORY_ENGINE_STEPS,
  PRODUCTION_STEPS,
  CHAIN_DATA_SOURCE_MAP,
  STEP_LABELS,
  getWorkflowConfig,
  getStepMetadata,
  getStepIndex,
  getNextStep,
  getPreviousStep,
  hasRequiredInputs,
  getMissingInputs,
  getAllStepsMap,
} from "./workflow-configs";

// Types
export type {
  MegaAppId,
  SidebarMode,
  StepStatus,
  WorkflowStepMetadata,
  SidebarConfig,
  WorkflowFeatures,
  WorkflowConfig,
  StepState,
  UnifiedWorkflowState,
  ChainDataEntry,
  UnifiedWorkflowShellProps,
  ChainDataSource,
  // Phase 2: Suggested Defaults
  SuggestedDefault,
  ConfidenceLevel,
} from "./types";

// Helper functions
export {
  getConfidenceLevel,
  getConfidenceColorConfig,
} from "./types";

// Observability types
export type {
  StepMetrics,
  WorkflowMetrics,
  WorkflowObservabilityResult,
} from "./hooks/useWorkflowObservability";

// Optimistic state types
export type {
  OptimisticOptions,
  OptimisticSyncStatus,
  ChainDataWithOptimismResult,
} from "./hooks/useChainDataWithOptimism";

// IP Chain Data types (Phase 3)
export type {
  SyntheticIPDetail,
  IPWorldbuilding,
  SyntheticPreset,
  UseIPChainDataOptions,
  UseIPChainDataResult,
  VPEDefaults,
  ADDefaults,
  MirrorDefaults,
  StoryDefaults,
} from "./hooks/types";
