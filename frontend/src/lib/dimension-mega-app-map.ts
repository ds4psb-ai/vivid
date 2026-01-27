/**
 * Dimension to MegaApp Mapping
 *
 * Maps individual dimension apps to their parent MegaApp for
 * intelligent workflow routing and context sharing.
 *
 * MegaApp Structure:
 * - DNA Lab: Analysis & extraction (VPE, AD, Mirror, QC)
 * - Story Engine: Narrative & prompt creation (Story, Prompt, System Prompt)
 * - Production: Media generation (VEO, Kling, Suno, Imagen)
 */

export type MegaAppId = "dna-lab" | "story-engine" | "production";

/**
 * Dimension key to MegaApp mapping
 */
export const DIMENSION_TO_MEGA_APP = {
  // DNA Lab - Analysis & Extraction
  "reference-decoder": "dna-lab",
  "aesthetic-director": "dna-lab",
  "abyss-mirror": "dna-lab",
  "quality-director": "dna-lab",

  // Story Engine - Narrative & Prompts
  "story-architect": "story-engine",
  "prompt-alchemy": "story-engine",
  "system-prompt": "story-engine",

  // Production Bridge - Media Generation
  "video-maker": "production",
  "visual-realizer": "production",
  "sound-crafter": "production",
  "kling": "production",
  "suno": "production",
  "veo": "production",
} as const;

export type DimensionKey = keyof typeof DIMENSION_TO_MEGA_APP;

/**
 * MegaApp to dimensions mapping (reverse lookup)
 */
export const MEGA_APP_DIMENSIONS: Record<MegaAppId, readonly DimensionKey[]> = {
  "dna-lab": [
    "reference-decoder",
    "aesthetic-director",
    "abyss-mirror",
    "quality-director",
  ],
  "story-engine": ["story-architect", "prompt-alchemy", "system-prompt"],
  production: [
    "video-maker",
    "visual-realizer",
    "sound-crafter",
    "kling",
    "suno",
    "veo",
  ],
} as const;

/**
 * MegaApp metadata for UI display
 */
export const MEGA_APP_INFO: Record<
  MegaAppId,
  {
    name: string;
    nameKr: string;
    description: string;
    route: string;
    primaryColor: string;
  }
> = {
  "dna-lab": {
    name: "DNA Lab",
    nameKr: "DNA 연구소",
    description: "Auteur DNA analysis and extraction",
    route: "/dna-lab",
    primaryColor: "#8B5CF6", // violet
  },
  "story-engine": {
    name: "Story Engine",
    nameKr: "스토리 엔진",
    description: "Narrative composition and system prompt generation",
    route: "/story-engine",
    primaryColor: "#3B82F6", // blue
  },
  production: {
    name: "Production Bridge",
    nameKr: "프로덕션 브릿지",
    description: "Unified media generation platform",
    route: "/production",
    primaryColor: "#F59E0B", // amber
  },
} as const;

/**
 * Get MegaApp for a dimension
 */
export function getMegaAppForDimension(
  dimensionKey: string
): MegaAppId | null {
  return (
    DIMENSION_TO_MEGA_APP[dimensionKey as keyof typeof DIMENSION_TO_MEGA_APP] ||
    null
  );
}

/**
 * Get all dimensions for a MegaApp
 */
export function getDimensionsForMegaApp(
  megaAppId: MegaAppId
): readonly DimensionKey[] {
  return MEGA_APP_DIMENSIONS[megaAppId] || [];
}

/**
 * Check if a dimension belongs to a MegaApp
 */
export function isDimensionInMegaApp(
  dimensionKey: string,
  megaAppId: MegaAppId
): boolean {
  const dimensions = MEGA_APP_DIMENSIONS[megaAppId];
  return dimensions.includes(dimensionKey as DimensionKey);
}

/**
 * Workflow order: DNA Lab -> Story Engine -> Production
 */
export const MEGA_APP_WORKFLOW_ORDER: readonly MegaAppId[] = [
  "dna-lab",
  "story-engine",
  "production",
] as const;

/**
 * Get next MegaApp in workflow
 */
export function getNextMegaApp(currentMegaApp: MegaAppId): MegaAppId | null {
  const currentIndex = MEGA_APP_WORKFLOW_ORDER.indexOf(currentMegaApp);
  if (currentIndex === -1 || currentIndex === MEGA_APP_WORKFLOW_ORDER.length - 1) {
    return null;
  }
  return MEGA_APP_WORKFLOW_ORDER[currentIndex + 1];
}

/**
 * Get previous MegaApp in workflow
 */
export function getPreviousMegaApp(currentMegaApp: MegaAppId): MegaAppId | null {
  const currentIndex = MEGA_APP_WORKFLOW_ORDER.indexOf(currentMegaApp);
  if (currentIndex <= 0) {
    return null;
  }
  return MEGA_APP_WORKFLOW_ORDER[currentIndex - 1];
}
