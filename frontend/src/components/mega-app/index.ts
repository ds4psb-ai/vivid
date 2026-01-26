/**
 * MegaApp Shell - Unified layout components for mega apps
 *
 * Usage:
 * ```tsx
 * import { MegaAppShell, type MegaAppTab } from "@/components/mega-app";
 *
 * const TABS: MegaAppTab[] = [
 *   { value: "vpe", label: "비디오 파싱", ... },
 * ];
 *
 * export default function DNALabPage() {
 *   return (
 *     <MegaAppShell
 *       appId="dna-lab"
 *       title="DNA Lab"
 *       ...
 *     >
 *       {(activeTab) => <Content tab={activeTab} />}
 *     </MegaAppShell>
 *   );
 * }
 * ```
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
