/**
 * useChainDataInjection - Auto-inject chain data from upstream dimensions
 *
 * Automatically retrieves and injects relevant data from the DimensionChain
 * based on the current dimension's input dependencies.
 *
 * Features:
 * - Auto-loads LogicVector from upstream dimensions (VPE, Reference Decoder)
 * - Injects AestheticGuidelines when available
 * - Provides PersonaDNA context from Mirror
 * - Accumulates evidence_refs across workflow
 *
 * @example
 * ```tsx
 * function StoryArchitectPanel() {
 *   const {
 *     logicVector,
 *     aestheticGuidelines,
 *     personaDNA,
 *     evidenceRefs,
 *     isReady,
 *   } = useChainDataInjection("story-architect");
 *
 *   if (!isReady) return <LoadingSpinner />;
 *
 *   // Use injected data for story generation
 * }
 * ```
 */

import { useMemo, useEffect, useState } from "react";
import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";

/** LogicVector structure (from VPE) */
export interface LogicVector {
  auteur_id?: string;
  cadence?: {
    tempo?: string;
    rhythm_pattern?: string[];
  };
  composition?: {
    primary_strategy?: string;
    symmetry_score?: number;
    depth_layers?: number;
  };
  camera_grammar?: {
    static?: number;
    dolly?: number;
    handheld?: number;
    tracking?: number;
  };
  lighting_physics?: {
    key_light?: string;
    color_temp_range?: number[];
  };
  color_science?: {
    palette?: string[];
    saturation_profile?: string;
  };
  confidence?: number;
  analysis_timestamp?: string;
}

/** Aesthetic Guidelines structure (from AD) */
export interface AestheticGuidelines {
  visual_style?: string;
  color_palette?: string[];
  mood_keywords?: string[];
  reference_directors?: string[];
  composition_notes?: string;
  lighting_approach?: string;
}

/** PersonaDNA structure (from Mirror/Abyss) */
export interface PersonaDNA {
  persona_type?: string;
  creative_tendencies?: string[];
  visual_preferences?: string[];
  narrative_style?: string;
  emotional_range?: string[];
  // Big Five (OCEAN) - Phase 2
  openness?: number;
  conscientiousness?: number;
  extraversion?: number;
  agreeableness?: number;
  neuroticism?: number;
}

/** Injection result */
export interface ChainDataInjection {
  /** Extracted LogicVector from upstream */
  logicVector: LogicVector | null;
  /** Aesthetic guidelines from AD */
  aestheticGuidelines: AestheticGuidelines | null;
  /** Persona DNA from Mirror */
  personaDNA: PersonaDNA | null;
  /** Accumulated evidence refs */
  evidenceRefs: string[];
  /** All upstream data is loaded and ready */
  isReady: boolean;
  /** Has any upstream data available */
  hasUpstreamData: boolean;
  /** Raw input data from upstream dimensions */
  rawInputData: Record<string, unknown>;
  /** Sync current session to storage */
  syncToSession: (ipSlug: string) => void;
  /** Load session from storage */
  loadFromSession: (ipSlug: string) => boolean;
}

/** Input map: which dimensions provide input to which */
const INPUT_MAP: Record<string, string[]> = {
  // Story Engine dimensions
  "story-architect": ["reference-decoder", "aesthetic-director"],
  "prompt-alchemy": ["story-architect", "reference-decoder"],
  "system-prompt": ["story-architect", "prompt-alchemy", "reference-decoder"],

  // Production dimensions
  "video-maker": ["system-prompt", "prompt-alchemy", "story-architect"],
  "visual-realizer": ["prompt-alchemy", "system-prompt"],
  "sound-crafter": ["story-architect", "system-prompt"],
  veo: ["system-prompt", "prompt-alchemy"],
  kling: ["system-prompt", "prompt-alchemy"],
  suno: ["story-architect", "sound-crafter"],

  // DNA Lab dimensions (mostly independent or feed others)
  "reference-decoder": [],
  "aesthetic-director": ["reference-decoder"],
  "abyss-mirror": [],
  "quality-director": ["video-maker", "visual-realizer"],
};

/**
 * Extract LogicVector from chain data
 */
function extractLogicVector(
  inputData: Record<string, { output: Record<string, unknown> }>
): LogicVector | null {
  // Check reference-decoder first
  const refDecoder = inputData["reference-decoder"]?.output;
  if (refDecoder?.logic_vector || refDecoder?.logicVector) {
    return (refDecoder.logic_vector || refDecoder.logicVector) as LogicVector;
  }

  // Check for direct logic_vector in any output
  for (const [, data] of Object.entries(inputData)) {
    if (data.output?.logic_vector) {
      return data.output.logic_vector as LogicVector;
    }
    if (data.output?.logicVector) {
      return data.output.logicVector as LogicVector;
    }
  }

  return null;
}

/**
 * Extract AestheticGuidelines from chain data
 */
function extractAestheticGuidelines(
  inputData: Record<string, { output: Record<string, unknown> }>
): AestheticGuidelines | null {
  const ad = inputData["aesthetic-director"]?.output;
  if (ad?.aesthetic_guidelines || ad?.aestheticGuidelines) {
    return (ad.aesthetic_guidelines ||
      ad.aestheticGuidelines) as AestheticGuidelines;
  }

  // Check for nested output structure
  if (ad?.output) {
    const nested = ad.output as Record<string, unknown>;
    if (nested.visual_style || nested.color_palette) {
      return nested as AestheticGuidelines;
    }
  }

  // Direct properties check
  if (ad?.visual_style || ad?.color_palette) {
    return ad as unknown as AestheticGuidelines;
  }

  return null;
}

/**
 * Extract PersonaDNA from chain data
 */
function extractPersonaDNA(
  inputData: Record<string, { output: Record<string, unknown> }>
): PersonaDNA | null {
  const mirror = inputData["abyss-mirror"]?.output;
  if (mirror?.persona_dna || mirror?.personaDNA) {
    return (mirror.persona_dna || mirror.personaDNA) as PersonaDNA;
  }

  // Check for direct persona properties
  if (mirror?.persona_type || mirror?.creative_tendencies) {
    return mirror as unknown as PersonaDNA;
  }

  return null;
}

/**
 * Collect all evidence refs from input data
 */
function collectEvidenceRefs(
  inputData: Record<string, { output: Record<string, unknown>; evidenceRefs?: string[] }>
): string[] {
  const refs = new Set<string>();

  for (const [, data] of Object.entries(inputData)) {
    // Check evidenceRefs at data level
    if (data.evidenceRefs) {
      data.evidenceRefs.forEach((ref) => refs.add(ref));
    }

    // Check evidence_refs in output
    const outputRefs = data.output?.evidence_refs || data.output?.evidenceRefs;
    if (Array.isArray(outputRefs)) {
      outputRefs.forEach((ref) => {
        if (typeof ref === "string") refs.add(ref);
      });
    }
  }

  return Array.from(refs);
}

/**
 * Hook for automatic chain data injection
 *
 * @param dimensionKey - Current dimension key
 * @returns Injected chain data and utilities
 */
export function useChainDataInjection(
  dimensionKey: string
): ChainDataInjection {
  const chain = useDimensionChainOptional();
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize on mount
  useEffect(() => {
    setIsInitialized(true);
  }, []);

  // Get input dimensions for current dimension
  const inputDimensions = useMemo(
    () => INPUT_MAP[dimensionKey] || [],
    [dimensionKey]
  );

  // Get raw input data from chain
  const rawInputData = useMemo(() => {
    if (!chain) return {};
    return chain.getInputData(dimensionKey);
  }, [chain, dimensionKey]);

  // Extract structured data
  const logicVector = useMemo(
    () => extractLogicVector(rawInputData as Record<string, { output: Record<string, unknown> }>),
    [rawInputData]
  );

  const aestheticGuidelines = useMemo(
    () => extractAestheticGuidelines(rawInputData as Record<string, { output: Record<string, unknown> }>),
    [rawInputData]
  );

  const personaDNA = useMemo(
    () => extractPersonaDNA(rawInputData as Record<string, { output: Record<string, unknown> }>),
    [rawInputData]
  );

  // Collect evidence refs
  const localEvidenceRefs = useMemo(
    () => collectEvidenceRefs(rawInputData as Record<string, { output: Record<string, unknown>; evidenceRefs?: string[] }>),
    [rawInputData]
  );

  // Combine with accumulated refs from context
  const evidenceRefs = useMemo(() => {
    if (!chain) return localEvidenceRefs;
    const combined = new Set([
      ...chain.accumulatedEvidenceRefs,
      ...localEvidenceRefs,
    ]);
    return Array.from(combined);
  }, [chain, localEvidenceRefs]);

  // Check readiness
  const hasUpstreamData = Object.keys(rawInputData).length > 0;
  const isReady = isInitialized && (inputDimensions.length === 0 || hasUpstreamData);

  // Session sync functions
  const syncToSession = chain?.syncToSession || (() => {});
  const loadFromSession = chain?.loadFromSession || (() => false);

  return {
    logicVector,
    aestheticGuidelines,
    personaDNA,
    evidenceRefs,
    isReady,
    hasUpstreamData,
    rawInputData,
    syncToSession,
    loadFromSession,
  };
}

/**
 * Hook to check if upstream data is available without extracting
 */
export function useHasUpstreamData(dimensionKey: string): boolean {
  const chain = useDimensionChainOptional();

  return useMemo(() => {
    if (!chain) return false;
    const inputData = chain.getInputData(dimensionKey);
    return Object.keys(inputData).length > 0;
  }, [chain, dimensionKey]);
}

export default useChainDataInjection;
