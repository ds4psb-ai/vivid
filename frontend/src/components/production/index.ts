/**
 * Production Components
 *
 * Integrated workflow experience for Production mega app.
 * Receives system-prompt from Story Engine and produces media outputs.
 *
 * Workflow: DNA Lab → Story Engine → Production (VEO/Kling/Suno)
 */

// Step panel wrapper
export { ProductionStepPanel, useChainInputInjection } from "./ProductionStepPanel";

// Hook
export {
  useProductionWorkflow,
  type ProductionStepState,
  type ProductionWorkflowState,
  type CompletedOutput,
} from "./hooks/useProductionWorkflow";

// Constants & Types
export {
  PRODUCTION_STEPS,
  PRODUCTION_STEPS_MAP,
  PRODUCTION_INPUT_MAP,
  PRODUCTION_THEME,
  PRODUCTION_STEP_THEMES,
  PRODUCTION_STEP_PARAM,
  PRODUCTION_DEFAULT_STEP,
  EXTERNAL_INPUT_LABELS,
  getStepById,
  getStepIndex,
  getNextStep,
  getPreviousStep,
  hasRequiredInputs,
  getMissingInputs,
  isVideoStep,
  isAudioStep,
  getInputLabel,
  getOtherProductionTools,
  getVideoTools,
  getAudioTools,
  type ProductionStepId,
  type ProductionStep,
  type StepStatus,
  type ProductionChainOutput,
} from "./constants";
