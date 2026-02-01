/**
 * Production Workflow Constants
 *
 * Step definitions, themes, and input mapping for the Production workflow.
 * Receives system-prompt from Story Engine and produces media outputs.
 *
 * 2026 Patterns:
 * - Independent step access (VEO, Kling, Suno are independent)
 * - Optional steps (all can be skipped)
 * - Cross-app chain data flow (Story Engine → Production)
 */

import { Video, Film, Music2, type LucideIcon } from "lucide-react";

/**
 * Step IDs for Production workflow
 */
export type ProductionStepId = "veo" | "kling" | "suno";

/**
 * Step configuration for Production workflow
 */
export interface ProductionStep {
  /** Unique step identifier */
  id: ProductionStepId;
  /** Korean label */
  label: string;
  /** English label */
  labelEn: string;
  /** Lucide icon component */
  icon: LucideIcon;
  /** Short description */
  description: string;
  /** Output data key (for chain data) */
  outputKey: string;
  /** Dimension route key mapping (for panel component reference) */
  dimensionKey: string;
  /** Whether this step is optional (all Production steps are optional) */
  optional: boolean;
  /** Media type produced by this step */
  mediaType: "video" | "audio";
}

/**
 * Production workflow steps
 * Access is independent - any step can be used without completing others
 */
export const PRODUCTION_STEPS: ProductionStep[] = [
  {
    id: "veo",
    label: "VEO 3.1",
    labelEn: "VEO 3.1",
    icon: Video,
    description: "Google VEO 비디오 생성",
    outputKey: "veo",
    dimensionKey: "veo",
    optional: true,
    mediaType: "video",
  },
  {
    id: "kling",
    label: "Kling 2.6",
    labelEn: "Kling 2.6",
    icon: Film,
    description: "고품질 시네마틱 비디오",
    outputKey: "kling",
    dimensionKey: "kling",
    optional: true,
    mediaType: "video",
  },
  {
    id: "suno",
    label: "Suno AI",
    labelEn: "Suno AI",
    icon: Music2,
    description: "AI 음악 생성",
    outputKey: "suno",
    dimensionKey: "suno",
    optional: true,
    mediaType: "audio",
  },
];

/**
 * Step ID to Step lookup
 */
export const PRODUCTION_STEPS_MAP: Record<ProductionStepId, ProductionStep> =
  PRODUCTION_STEPS.reduce(
    (acc, step) => ({ ...acc, [step.id]: step }),
    {} as Record<ProductionStepId, ProductionStep>
  );

/**
 * Input dependency map for Production
 * Defines which data keys provide input to each step
 *
 * Note: "system-prompt" and "story" come from Story Engine (cross-app dependency)
 * - VEO/Kling use system-prompt for video generation
 * - Suno uses story for music generation (different source!)
 */
export const PRODUCTION_INPUT_MAP: Record<ProductionStepId, string[]> = {
  veo: ["system-prompt"],
  kling: ["system-prompt"],
  suno: ["story"],
};

/**
 * Step status for workflow progress
 */
export type StepStatus = "pending" | "active" | "completed" | "skipped";

/**
 * Chain data output structure for each step
 */
export interface ProductionChainOutput {
  veo?: {
    videoUrl: string;
    thumbnailUrl?: string;
    duration?: number;
    metadata?: Record<string, unknown>;
    generationTimestamp: number;
  };
  kling?: {
    videoUrl: string;
    thumbnailUrl?: string;
    duration?: number;
    metadata?: Record<string, unknown>;
    generationTimestamp: number;
  };
  suno?: {
    audioUrl: string;
    title?: string;
    duration?: number;
    lyrics?: string;
    metadata?: Record<string, unknown>;
    generationTimestamp: number;
  };
}

/**
 * Theme configuration for Production
 * V7 Design: Unified Neon Red theme
 */
export const PRODUCTION_THEME = {
  hue: 0, // Neon Red (V7 unified theme)
  primaryColor: "oklch(0.62 0.28 20)",
  glowColor: "oklch(0.62 0.28 20 / 0.3)",
  gradientFrom: "from-[var(--stitch-primary)]/20",
  gradientTo: "to-[var(--stitch-primary-accent)]/20",
};

/**
 * Step theme colors (for visual distinction)
 * V7 Design: Unified Neon Red theme with subtle variations
 */
export const PRODUCTION_STEP_THEMES: Record<ProductionStepId, { hue: number; color: string }> = {
  veo: { hue: 0, color: "oklch(0.62 0.28 20)" }, // Neon Red
  kling: { hue: 5, color: "oklch(0.60 0.26 15)" }, // Neon Red variant
  suno: { hue: 10, color: "oklch(0.58 0.24 10)" }, // Neon Red variant
};

/**
 * URL parameter name for step navigation
 */
export const PRODUCTION_STEP_PARAM = "step";

/**
 * Default step when no parameter provided
 */
export const PRODUCTION_DEFAULT_STEP: ProductionStepId = "veo";

/**
 * Get step by ID with type safety
 */
export function getStepById(id: string): ProductionStep | undefined {
  return PRODUCTION_STEPS_MAP[id as ProductionStepId];
}

/**
 * Get step index in workflow
 */
export function getStepIndex(id: ProductionStepId): number {
  return PRODUCTION_STEPS.findIndex((step) => step.id === id);
}

/**
 * Get next step in workflow (sequential)
 */
export function getNextStep(id: ProductionStepId): ProductionStep | undefined {
  const index = getStepIndex(id);
  return index < PRODUCTION_STEPS.length - 1 ? PRODUCTION_STEPS[index + 1] : undefined;
}

/**
 * Get previous step in workflow (sequential)
 */
export function getPreviousStep(id: ProductionStepId): ProductionStep | undefined {
  const index = getStepIndex(id);
  return index > 0 ? PRODUCTION_STEPS[index - 1] : undefined;
}

/**
 * Check if step has all required input data
 */
export function hasRequiredInputs(
  stepId: ProductionStepId,
  chainData: Record<string, unknown>
): boolean {
  const requiredInputs = PRODUCTION_INPUT_MAP[stepId];
  return requiredInputs.every((inputKey) => !!chainData[inputKey]);
}

/**
 * Get missing inputs for a step
 */
export function getMissingInputs(
  stepId: ProductionStepId,
  chainData: Record<string, unknown>
): string[] {
  const requiredInputs = PRODUCTION_INPUT_MAP[stepId];
  return requiredInputs.filter((inputKey) => !chainData[inputKey]);
}

/**
 * Check if a step produces video output
 */
export function isVideoStep(stepId: ProductionStepId): boolean {
  const step = PRODUCTION_STEPS_MAP[stepId];
  return step?.mediaType === "video";
}

/**
 * Check if a step produces audio output
 */
export function isAudioStep(stepId: ProductionStepId): boolean {
  const step = PRODUCTION_STEPS_MAP[stepId];
  return step?.mediaType === "audio";
}

/**
 * Labels for external data sources (from Story Engine)
 */
export const EXTERNAL_INPUT_LABELS: Record<string, string> = {
  "system-prompt": "시스템 프롬프트 (Story Engine)",
  story: "스토리 (Story Engine)",
  prompt: "프롬프트 (Story Engine)",
  vpe: "영상 분석 (DNA Lab)",
  ad: "미학 적용 (DNA Lab)",
};

/**
 * Get display label for an input key
 */
export function getInputLabel(inputKey: string): string {
  // Check external inputs first
  if (EXTERNAL_INPUT_LABELS[inputKey]) {
    return EXTERNAL_INPUT_LABELS[inputKey];
  }
  // Check Production steps
  const step = PRODUCTION_STEPS_MAP[inputKey as ProductionStepId];
  return step?.label || inputKey;
}

/**
 * Get other production tools (for completion bar "try another tool")
 */
export function getOtherProductionTools(currentStepId: ProductionStepId): ProductionStep[] {
  return PRODUCTION_STEPS.filter((step) => step.id !== currentStepId);
}

/**
 * Get video production tools
 */
export function getVideoTools(): ProductionStep[] {
  return PRODUCTION_STEPS.filter((step) => step.mediaType === "video");
}

/**
 * Get audio production tools
 */
export function getAudioTools(): ProductionStep[] {
  return PRODUCTION_STEPS.filter((step) => step.mediaType === "audio");
}
