import type { MegaAppId, MegaAppTheme, WorkflowStep } from "./types";

/**
 * Mega App Themes
 * Oklch hue values for consistent theming
 */
export const MEGA_APP_THEMES: Record<MegaAppId, MegaAppTheme> = {
  "dna-lab": {
    id: "dna-lab",
    hue: 148,
    cssVar: "--color-mega-app-dna-lab",
    glowColor: "oklch(0.64 0.18 148 / 0.3)",
  },
  "story-engine": {
    id: "story-engine",
    hue: 45,
    cssVar: "--color-mega-app-story-engine",
    glowColor: "oklch(0.64 0.18 45 / 0.3)",
  },
  production: {
    id: "production",
    hue: 228,
    cssVar: "--color-mega-app-production",
    glowColor: "oklch(0.64 0.18 228 / 0.3)",
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
