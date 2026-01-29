/**
 * DNA Lab Components
 *
 * Integrated workflow experience for DNA Lab mega app.
 * Replaces tab-based MegaAppShell with step-based workflow.
 */

// Main shell
export { DNALabWorkflowShell } from "./DNALabWorkflowShell";

// Onboarding
export { DNALabOnboarding } from "./DNALabOnboarding";

// Progress/Stepper
export {
  DNALabWorkflowProgress,
  DNALabWorkflowProgressCompact,
} from "./DNALabWorkflowProgress";

// Step components
export { DNALabStepPanel, useChainInputInjection } from "./DNALabStepPanel";
export { DNALabChainSummary } from "./DNALabChainSummary";
export { DNALabStepNav, DNALabStepNavCompact, DNALabRunPipelineButton } from "./DNALabStepNav";

// Hook
export { useDNALabWorkflow, type StepState, type DNALabWorkflowState } from "./hooks/useDNALabWorkflow";

// Constants & Types
export {
  DNA_LAB_STEPS,
  DNA_LAB_STEPS_MAP,
  DNA_LAB_INPUT_MAP,
  DNA_LAB_OUTPUT_MAP,
  DNA_LAB_THEME,
  DNA_LAB_STEP_THEMES,
  DNA_LAB_STEP_PARAM,
  DNA_LAB_DEFAULT_STEP,
  getStepById,
  getStepIndex,
  getNextStep,
  getPreviousStep,
  hasRequiredInputs,
  getMissingInputs,
  type DNALabStepId,
  type DNALabStep,
  type StepStatus,
  type DNALabChainOutput,
} from "./constants";
