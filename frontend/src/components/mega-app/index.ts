/**
 * MegaApp UI Components
 *
 * Active components used by the workflow system:
 * - `MegaAppHeader` - Header with app branding
 * - `MegaAppAurora` - Background gradient effect
 * - `WorkflowProgress` - Step progress indicator
 *
 * For full workflow shells, use `@/components/workflow`:
 * - `UnifiedWorkflowShell` for complete app shells
 */

// Active components (used by workflow system)
export { MegaAppHeader } from "./MegaAppHeader";
export { WorkflowProgress } from "./WorkflowProgress";
export { MegaAppAurora } from "./MegaAppAurora";

// Constants
export { MEGA_APP_THEMES, WORKFLOW_STEPS, getTheme, getWorkflowStepIndex } from "./constants";

// Types
export type {
  MegaAppId,
  MegaAppTab,
  MegaAppTheme,
  MegaAppHeaderProps,
  WorkflowProgressProps,
  MegaAppAuroraProps,
  WorkflowStep,
} from "./types";
