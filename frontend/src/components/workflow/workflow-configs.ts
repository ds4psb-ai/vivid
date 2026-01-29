/**
 * Workflow Configurations
 *
 * Adaptive Layout Engine configurations for each Mega App.
 * One Shell component uses these configs to behave differently per app.
 */

import {
  Dna,
  Video,
  Palette,
  Brain,
  CheckCircle,
  BookOpen,
  Layers,
  Wand2,
  FileCode,
  Clapperboard,
  Film,
  Music2,
} from "lucide-react";
import type { WorkflowConfig, WorkflowStepMetadata, MegaAppId, ChainDataSource } from "./types";

/**
 * Responsive Layout Configuration
 *
 * Centralized config for breakpoints and sidebar widths.
 * Q2 리팩토링 시 AdaptiveLayout + Compound Components로 전환 예정.
 *
 * Breakpoints (Tailwind default):
 * - sm: 640px
 * - md: 768px
 * - lg: 1024px
 * - xl: 1280px
 */
export const RESPONSIVE_CONFIG = {
  sidebar: {
    mobile: {
      width: "w-[85vw]",
      maxWidth: "max-w-80",
    },
    tablet: {
      width: "w-72", // 288px
      padding: "pr-72",
    },
    desktop: {
      width: "w-80", // 320px
      padding: "pr-80",
    },
  },
  breakpoints: {
    /** Mobile: < 768px (show FAB + Sheet drawer) */
    showMobileFab: "md:hidden",
    /** Tablet+: >= 768px (show fixed sidebar) */
    showFixedSidebar: "hidden md:block",
    /** Toggle button: >= 768px */
    showToggleButton: "hidden md:flex",
  },
  viewport: {
    /** Dynamic viewport height for iOS Safari */
    height: "h-[100dvh]",
    /** Fallback for browsers without dvh support */
    heightFallback: "h-screen",
  },
} as const;

/**
 * DNA Lab workflow steps
 */
export const DNA_LAB_STEPS: WorkflowStepMetadata[] = [
  {
    id: "vpe",
    label: "영상 분석",
    labelEn: "Video Parsing",
    icon: Video,
    description: "Logic Vector 추출",
    inputs: [],
    outputs: ["vpe"],
    canInfer: false,
    color: "oklch(0.7 0.15 200)", // Blue
    panelComponent: "VPEPanel",
  },
  {
    id: "ad",
    label: "미학 적용",
    labelEn: "Aesthetic Director",
    icon: Palette,
    description: "거장 스타일 적용",
    inputs: ["vpe"],
    outputs: ["ad"],
    canInfer: true,
    color: "oklch(0.7 0.15 45)", // Amber
    panelComponent: "AestheticDirectorPanel",
  },
  {
    id: "mirror",
    label: "창작 DNA",
    labelEn: "Abyss Mirror",
    icon: Brain,
    description: "페르소나 DNA 분석",
    inputs: ["vpe", "ad"],
    outputs: ["mirror"],
    canInfer: true,
    color: "oklch(0.7 0.15 280)", // Purple
    panelComponent: "AbyssMirrorPanel",
  },
  {
    id: "qc",
    label: "품질 검증",
    labelEn: "Quality Director",
    icon: CheckCircle,
    description: "최종 품질 검수",
    inputs: ["vpe", "ad", "mirror"],
    outputs: ["qc"],
    canInfer: false,
    color: "oklch(0.7 0.15 148)", // Green
    panelComponent: "QualityDirectorPanel",
  },
];

/**
 * Story Engine workflow steps
 */
export const STORY_ENGINE_STEPS: WorkflowStepMetadata[] = [
  {
    id: "story",
    label: "스토리 설계",
    labelEn: "Story Architect",
    icon: Layers,
    description: "내러티브 구조 설계",
    inputs: ["vpe", "ad"],
    outputs: ["story"],
    canInfer: false,
    color: "oklch(0.7 0.15 270)", // Purple
    panelComponent: "StoryArchitectPanel",
  },
  {
    id: "prompt",
    label: "프롬프트 연금술",
    labelEn: "Prompt Alchemy",
    icon: Wand2,
    description: "AI 프롬프트 생성",
    inputs: ["vpe", "ad", "story"],
    outputs: ["prompt"],
    canInfer: true,
    color: "oklch(0.7 0.15 320)", // Pink
    panelComponent: "PromptGeneratorPanel",
  },
  {
    id: "system-prompt",
    label: "시스템 프롬프트",
    labelEn: "System Prompt",
    icon: FileCode,
    description: "최종 시스템 프롬프트",
    inputs: ["story", "prompt"],
    outputs: ["system-prompt"],
    canInfer: false,
    color: "oklch(0.7 0.15 190)", // Cyan
    panelComponent: "SystemPromptPanel",
  },
];

/**
 * Production workflow steps
 */
export const PRODUCTION_STEPS: WorkflowStepMetadata[] = [
  {
    id: "veo",
    label: "VEO 3.1",
    labelEn: "VEO 3.1",
    icon: Video,
    description: "Google VEO 비디오 생성",
    inputs: ["system-prompt"],
    outputs: ["veo"],
    optional: true,
    canInfer: false,
    color: "oklch(0.7 0.15 148)", // Green
    panelComponent: "VeoVideoPanel",
  },
  {
    id: "kling",
    label: "Kling 2.6",
    labelEn: "Kling 2.6",
    icon: Film,
    description: "고품질 시네마틱 비디오",
    inputs: ["system-prompt"],
    outputs: ["kling"],
    optional: true,
    canInfer: false,
    color: "oklch(0.7 0.15 30)", // Orange
    panelComponent: "KlingPanel",
  },
  {
    id: "suno",
    label: "Suno AI",
    labelEn: "Suno AI",
    icon: Music2,
    description: "AI 음악 생성",
    inputs: ["story"],
    outputs: ["suno"],
    optional: true,
    canInfer: false,
    color: "oklch(0.7 0.15 0)", // Red
    panelComponent: "SunoPanel",
  },
];

/**
 * Workflow configurations for each Mega App
 */
export const WORKFLOW_CONFIGS: Record<MegaAppId, WorkflowConfig> = {
  "dna-lab": {
    id: "dna-lab",
    title: "DNA Lab",
    subtitle: "통합 워크플로우",
    icon: Dna,
    steps: DNA_LAB_STEPS,
    sidebar: {
      mode: "summary",
      collapsible: true,
      defaultCollapsed: true,
    },
    features: {
      aiInference: true,
      pipeline: true,
      showTimer: true,
    },
    stepParamName: "step",
    defaultStep: "vpe",
  },
  "story-engine": {
    id: "story-engine",
    title: "Story Engine",
    subtitle: "스토리 구성 및 System Prompt 생성",
    icon: BookOpen,
    steps: STORY_ENGINE_STEPS,
    sidebar: {
      mode: "preview",
      collapsible: true,
      defaultCollapsed: false,
    },
    features: {
      aiInference: false,
      pipeline: false,
    },
    requiredChainData: ["vpe", "ad"],
    stepParamName: "step",
    defaultStep: "story",
  },
  production: {
    id: "production",
    title: "Production Bridge",
    subtitle: "통합 미디어 생성 플랫폼",
    icon: Clapperboard,
    steps: PRODUCTION_STEPS,
    sidebar: {
      mode: "detailed",
      collapsible: false,
      defaultCollapsed: false,
    },
    features: {
      aiInference: false,
      pipeline: false,
      showTimer: true,
    },
    requiredChainData: ["vpe", "ad", "story", "prompt", "system-prompt"],
    stepParamName: "step",
    defaultStep: "veo",
  },
};

/**
 * Chain data source mapping
 * Maps each chain data key to its source app and step
 */
export const CHAIN_DATA_SOURCE_MAP: Record<string, ChainDataSource> = {
  // DNA Lab outputs
  vpe: { app: "dna-lab", step: "vpe", label: "영상 분석" },
  ad: { app: "dna-lab", step: "ad", label: "미학 적용" },
  mirror: { app: "dna-lab", step: "mirror", label: "창작 DNA" },
  qc: { app: "dna-lab", step: "qc", label: "품질 검증" },

  // Story Engine outputs
  story: { app: "story-engine", step: "story", label: "스토리 설계" },
  prompt: { app: "story-engine", step: "prompt", label: "프롬프트" },
  "system-prompt": { app: "story-engine", step: "system-prompt", label: "시스템 프롬프트" },

  // Production outputs
  veo: { app: "production", step: "veo", label: "VEO 3.1" },
  kling: { app: "production", step: "kling", label: "Kling 2.6" },
  suno: { app: "production", step: "suno", label: "Suno AI" },
};

/**
 * Step labels for display
 */
export const STEP_LABELS: Record<string, string> = Object.fromEntries(
  [
    ...DNA_LAB_STEPS,
    ...STORY_ENGINE_STEPS,
    ...PRODUCTION_STEPS,
  ].map((step) => [step.id, step.label])
);

/**
 * Get workflow config by app ID
 */
export function getWorkflowConfig(appId: MegaAppId): WorkflowConfig {
  return WORKFLOW_CONFIGS[appId];
}

/**
 * Get step metadata by ID within a config
 */
export function getStepMetadata(
  config: WorkflowConfig,
  stepId: string
): WorkflowStepMetadata | undefined {
  return config.steps.find((s) => s.id === stepId);
}

/**
 * Get step index within a config
 */
export function getStepIndex(config: WorkflowConfig, stepId: string): number {
  return config.steps.findIndex((s) => s.id === stepId);
}

/**
 * Get next step in workflow
 */
export function getNextStep(
  config: WorkflowConfig,
  currentStepId: string
): WorkflowStepMetadata | undefined {
  const index = getStepIndex(config, currentStepId);
  return index < config.steps.length - 1 ? config.steps[index + 1] : undefined;
}

/**
 * Get previous step in workflow
 */
export function getPreviousStep(
  config: WorkflowConfig,
  currentStepId: string
): WorkflowStepMetadata | undefined {
  const index = getStepIndex(config, currentStepId);
  return index > 0 ? config.steps[index - 1] : undefined;
}

/**
 * Check if step has all required inputs
 */
export function hasRequiredInputs(
  step: WorkflowStepMetadata,
  chainData: Record<string, unknown>
): boolean {
  return step.inputs.every((inputKey) => !!chainData[inputKey]);
}

/**
 * Get missing inputs for a step
 */
export function getMissingInputs(
  step: WorkflowStepMetadata,
  chainData: Record<string, unknown>
): string[] {
  return step.inputs.filter((inputKey) => !chainData[inputKey]);
}

/**
 * Get all steps map by ID across all apps
 */
export function getAllStepsMap(): Record<string, WorkflowStepMetadata> {
  const map: Record<string, WorkflowStepMetadata> = {};
  for (const config of Object.values(WORKFLOW_CONFIGS)) {
    for (const step of config.steps) {
      map[step.id] = step;
    }
  }
  return map;
}
