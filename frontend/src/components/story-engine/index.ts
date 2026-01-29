/**
 * Story Engine Components
 *
 * Integrated workflow experience for Story Engine mega app.
 * Builds upon DNA Lab outputs and produces system prompts for Production.
 *
 * Workflow: DNA Lab (VPE + AD) → Story → Prompt → System Prompt → Production
 */

// Step panel wrapper
export { StoryEngineStepPanel, useChainInputInjection } from "./StoryEngineStepPanel";

// Hook
export {
  useStoryEngineWorkflow,
  useIsFinalStep,
  type StoryEngineStepState,
  type StoryEngineWorkflowState,
} from "./hooks/useStoryEngineWorkflow";

// Constants & Types
export {
  STORY_ENGINE_STEPS,
  STORY_ENGINE_STEPS_MAP,
  STORY_ENGINE_INPUT_MAP,
  STORY_ENGINE_OUTPUT_MAP,
  STORY_ENGINE_THEME,
  STORY_ENGINE_STEP_THEMES,
  STORY_ENGINE_STEP_PARAM,
  STORY_ENGINE_DEFAULT_STEP,
  EXTERNAL_INPUT_LABELS,
  getStepById,
  getStepIndex,
  getNextStep,
  getPreviousStep,
  hasRequiredInputs,
  getMissingInputs,
  isFinalStep,
  getInputLabel,
  type StoryEngineStepId,
  type StoryEngineStep,
  type StepStatus,
  type StoryEngineChainOutput,
} from "./constants";
