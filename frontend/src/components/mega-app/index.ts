/**
 * @deprecated MegaApp Shell components are deprecated.
 *
 * Use the new `@/components/workflow` components instead:
 * - `UnifiedWorkflowShell` replaces `MegaAppShell`
 * - `UnifiedWorkflowProgress` replaces `MegaAppTabs`
 * - `UnifiedStepNav` for step-based navigation
 * - `UnifiedChainSidebar` for chain data display
 *
 * Migration example:
 * ```tsx
 * // Before
 * import { MegaAppShell, type MegaAppTab } from "@/components/mega-app";
 * <MegaAppShell appId="dna-lab" tabs={TABS}>{children}</MegaAppShell>
 *
 * // After
 * import { UnifiedWorkflowShell } from "@/components/workflow";
 * <UnifiedWorkflowShell appId="dna-lab">{children}</UnifiedWorkflowShell>
 * ```
 *
 * Note: `MegaAppHeader`, `MegaAppAurora`, and `WorkflowProgress` are still
 * actively used by the new workflow system and are NOT deprecated.
 *
 * ---
 *
 * MegaApp Shell - Unified layout components for mega apps (Legacy)
 */

// Main component
export { MegaAppShell } from "./MegaAppShell";

// Sub-components (for custom composition)
export { MegaAppHeader } from "./MegaAppHeader";
export { MegaAppTabs } from "./MegaAppTabs";
export { WorkflowProgress } from "./WorkflowProgress";
export { MegaAppAurora } from "./MegaAppAurora";

// Hooks
export { useMegaAppTab } from "./hooks/useMegaAppTab";

// Constants
export { MEGA_APP_THEMES, WORKFLOW_STEPS, getTheme, getWorkflowStepIndex } from "./constants";

// Types
export type {
  MegaAppId,
  MegaAppTab,
  MegaAppTheme,
  MegaAppShellProps,
  MegaAppHeaderProps,
  MegaAppTabsProps,
  WorkflowProgressProps,
  MegaAppAuroraProps,
  WorkflowStep,
} from "./types";
