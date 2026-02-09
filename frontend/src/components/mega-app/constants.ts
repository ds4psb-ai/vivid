import type { MegaAppId, MegaAppTheme, WorkflowStep } from "./types";

/**
 * Mega App Themes
 * Oklch hue values for consistent theming
 */
/**
 * V7 Design System: Unified Warm Amber Theme
 *
 * All mega-apps use the same warm amber theme for visual consistency.
 * - hue: 65 (amber)
 * - oklch glow: 0.62 0.18 65 for soft cinematic emphasis
 */
export const MEGA_APP_THEMES: Record<MegaAppId, MegaAppTheme> = {
  "dna-lab": {
    id: "dna-lab",
    hue: 65,
    cssVar: "--color-mega-app-dna-lab",
    glowColor: "oklch(0.62 0.18 65 / 0.3)",
  },
  "story-engine": {
    id: "story-engine",
    hue: 65,
    cssVar: "--color-mega-app-story-engine",
    glowColor: "oklch(0.62 0.18 65 / 0.3)",
  },
  production: {
    id: "production",
    hue: 65,
    cssVar: "--color-mega-app-production",
    glowColor: "oklch(0.62 0.18 65 / 0.3)",
  },
};

/**
 * Workflow Steps
 * DNA Lab → Story Engine → Production
 */
export const WORKFLOW_STEPS: WorkflowStep[] = [
  {
    id: "dna-lab",
    label: "DNA Lab",
    labelEn: "DNA Lab",
    href: "/dna-lab",
    description: "거장 DNA 분석",
  },
  {
    id: "story-engine",
    label: "Story Engine",
    labelEn: "Story Engine",
    href: "/story-engine",
    description: "스토리 구성",
  },
  {
    id: "production",
    label: "Production",
    labelEn: "Production",
    href: "/production",
    description: "미디어 생성",
  },
];

/**
 * Get theme by app ID
 */
export function getTheme(appId: MegaAppId): MegaAppTheme {
  return MEGA_APP_THEMES[appId];
}

/**
 * Get current step index in workflow
 */
export function getWorkflowStepIndex(appId: MegaAppId): number {
  return WORKFLOW_STEPS.findIndex((step) => step.id === appId);
}
