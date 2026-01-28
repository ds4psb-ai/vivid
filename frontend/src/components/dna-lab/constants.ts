/**
 * DNA Lab Workflow Constants
 *
 * Step definitions, themes, and input mapping for the integrated workflow.
 * Supports 2026 trends:
 * - Non-sequential access (any step accessible)
 * - AI inference when data missing
 * - Parallel preview capability
 */

import { Video, Palette, Brain, CheckCircle, type LucideIcon } from "lucide-react";

/**
 * Step IDs for DNA Lab workflow
 */
export type DNALabStepId = "vpe" | "ad" | "mirror" | "qc";

/**
 * Step configuration for DNA Lab workflow
 */
export interface DNALabStep {
  /** Unique step identifier */
  id: DNALabStepId;
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
  /** Dimension route key mapping */
  dimensionKey: string;
  /** Whether this step can auto-infer missing input data */
  canInferInput?: boolean;
}

/**
 * DNA Lab workflow steps
 * Order represents logical flow, but access is non-sequential
 */
export const DNA_LAB_STEPS: DNALabStep[] = [
  {
    id: "vpe",
    label: "영상 분석",
    labelEn: "Video Parsing",
    icon: Video,
    description: "Logic Vector 추출",
    outputKey: "logicVector",
    dimensionKey: "vpe",
    canInferInput: false, // Entry point, needs user input
  },
  {
    id: "ad",
    label: "미학 적용",
    labelEn: "Aesthetic Director",
    icon: Palette,
    description: "거장 스타일 적용",
    outputKey: "aestheticGuidelines",
    dimensionKey: "aesthetic-director",
    canInferInput: true, // Can work with auteur hint alone
  },
  {
    id: "mirror",
    label: "창작 DNA",
    labelEn: "Abyss Mirror",
    icon: Brain,
    description: "페르소나 DNA 분석",
    outputKey: "personaDNA",
    dimensionKey: "abyss-mirror",
    canInferInput: true, // Independent, can work without input
  },
  {
    id: "qc",
    label: "품질 검증",
    labelEn: "Quality Director",
    icon: CheckCircle,
    description: "최종 품질 검수",
    outputKey: "qualityReport",
    dimensionKey: "quality-director",
    canInferInput: false, // Needs content to verify
  },
];

/**
 * Step ID to Step lookup
 */
export const DNA_LAB_STEPS_MAP: Record<DNALabStepId, DNALabStep> = DNA_LAB_STEPS.reduce(
  (acc, step) => ({ ...acc, [step.id]: step }),
  {} as Record<DNALabStepId, DNALabStep>
);

/**
 * Input dependency map for DNA Lab
 * Defines which steps provide input to other steps
 *
 * 2026 Enhancement: Non-sequential access
 * - Steps can be accessed directly without completing dependencies
 * - Missing data triggers AI inference suggestions
 */
export const DNA_LAB_INPUT_MAP: Record<DNALabStepId, DNALabStepId[]> = {
  vpe: [], // Entry point
  ad: ["vpe"], // Uses Logic Vector from VPE
  mirror: ["vpe", "ad"], // Uses Logic Vector + Aesthetic Guidelines
  qc: ["vpe", "ad", "mirror"], // Uses all previous outputs
};

/**
 * Output dependency map (reverse of input)
 * Which steps consume this step's output
 */
export const DNA_LAB_OUTPUT_MAP: Record<DNALabStepId, DNALabStepId[]> = {
  vpe: ["ad", "mirror", "qc"], // VPE output flows to all
  ad: ["mirror", "qc"], // AD output flows to Mirror and QC
  mirror: ["qc"], // Mirror output flows to QC
  qc: [], // Final step, no downstream
};

/**
 * Step status for workflow progress
 */
export type StepStatus = "pending" | "active" | "completed" | "skipped";

/**
 * Chain data output structure for each step
 */
export interface DNALabChainOutput {
  vpe?: {
    logicVector: Record<string, unknown>;
    videoUrl?: string;
    analysisTimestamp: number;
  };
  ad?: {
    aestheticGuidelines: Record<string, unknown>;
    auteurKey?: string;
    moodboard?: unknown[];
  };
  mirror?: {
    personaDNA: Record<string, unknown>;
    genomeAnalysis?: unknown;
  };
  qc?: {
    qualityReport: Record<string, unknown>;
    scores?: Record<string, number>;
    passed?: boolean;
  };
}

/**
 * Theme configuration for DNA Lab
 */
export const DNA_LAB_THEME = {
  hue: 148, // Cyan/Teal (matches mega-app theme)
  primaryColor: "oklch(0.64 0.18 148)",
  glowColor: "oklch(0.64 0.18 148 / 0.3)",
  gradientFrom: "from-emerald-500/20",
  gradientTo: "to-cyan-500/20",
};

/**
 * Step theme colors (for visual distinction)
 */
export const DNA_LAB_STEP_THEMES: Record<DNALabStepId, { hue: number; color: string }> = {
  vpe: { hue: 200, color: "oklch(0.7 0.15 200)" }, // Blue
  ad: { hue: 45, color: "oklch(0.7 0.15 45)" }, // Amber
  mirror: { hue: 280, color: "oklch(0.7 0.15 280)" }, // Purple
  qc: { hue: 148, color: "oklch(0.7 0.15 148)" }, // Green
};

/**
 * URL parameter name for step navigation
 */
export const DNA_LAB_STEP_PARAM = "step";

/**
 * Default step when no parameter provided
 */
export const DNA_LAB_DEFAULT_STEP: DNALabStepId = "vpe";

/**
 * Get step by ID with type safety
 */
export function getStepById(id: string): DNALabStep | undefined {
  return DNA_LAB_STEPS_MAP[id as DNALabStepId];
}

/**
 * Get step index in workflow
 */
export function getStepIndex(id: DNALabStepId): number {
  return DNA_LAB_STEPS.findIndex((step) => step.id === id);
}

/**
 * Get next step in workflow (sequential)
 */
export function getNextStep(id: DNALabStepId): DNALabStep | undefined {
  const index = getStepIndex(id);
  return index < DNA_LAB_STEPS.length - 1 ? DNA_LAB_STEPS[index + 1] : undefined;
}

/**
 * Get previous step in workflow (sequential)
 */
export function getPreviousStep(id: DNALabStepId): DNALabStep | undefined {
  const index = getStepIndex(id);
  return index > 0 ? DNA_LAB_STEPS[index - 1] : undefined;
}

/**
 * Check if step has all required input data
 */
export function hasRequiredInputs(
  stepId: DNALabStepId,
  chainData: Record<string, unknown>
): boolean {
  const requiredInputs = DNA_LAB_INPUT_MAP[stepId];
  return requiredInputs.every((inputId) => !!chainData[inputId]);
}

/**
 * Get missing inputs for a step
 */
export function getMissingInputs(
  stepId: DNALabStepId,
  chainData: Record<string, unknown>
): DNALabStepId[] {
  const requiredInputs = DNA_LAB_INPUT_MAP[stepId];
  return requiredInputs.filter((inputId) => !chainData[inputId]);
}
