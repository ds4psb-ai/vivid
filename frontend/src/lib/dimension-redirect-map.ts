/**
 * Dimension Route to MegaApp Redirect Mapping
 *
 * Maps legacy /dimension/* routes to unified MegaApp routes.
 * Used for:
 * 1. Server-side redirects in individual dimension pages
 * 2. DimensionGrid link generation
 *
 * Migration (2026.01):
 * All dimension apps are now consolidated into 3 MegaApps:
 * - DNA Lab: Analysis & Extraction
 * - Story Engine: Narrative & Prompts
 * - Production: Media Generation
 */

export interface DimensionRedirect {
  /** Target MegaApp route */
  megaApp: "/dna-lab" | "/story-engine" | "/production";
  /** Step parameter for the MegaApp */
  step: string;
  /** Full redirect URL */
  url: string;
}

/**
 * Dimension route key to MegaApp redirect mapping
 */
export const DIMENSION_REDIRECT_MAP: Record<string, DimensionRedirect> = {
  // DNA Lab - Analysis & Extraction
  "reference-decoder": {
    megaApp: "/dna-lab",
    step: "vpe",
    url: "/dna-lab?step=vpe",
  },
  aesthetic: {
    megaApp: "/dna-lab",
    step: "ad",
    url: "/dna-lab?step=ad",
  },
  abyss: {
    megaApp: "/dna-lab",
    step: "mirror",
    url: "/dna-lab?step=mirror",
  },
  "quality-check": {
    megaApp: "/dna-lab",
    step: "qc",
    url: "/dna-lab?step=qc",
  },

  // Story Engine - Narrative & Prompts
  "story-architect": {
    megaApp: "/story-engine",
    step: "story",
    url: "/story-engine?step=story",
  },
  prompt: {
    megaApp: "/story-engine",
    step: "prompt",
    url: "/story-engine?step=prompt",
  },
  "prompt-translator": {
    megaApp: "/story-engine",
    step: "system-prompt",
    url: "/story-engine?step=system-prompt",
  },

  // Production - Media Generation
  "video-maker": {
    megaApp: "/production",
    step: "veo",
    url: "/production?step=veo",
  },
  "visual-realizer": {
    megaApp: "/production",
    step: "veo",
    url: "/production?step=veo",
  },
  kling: {
    megaApp: "/production",
    step: "kling",
    url: "/production?step=kling",
  },
  suno: {
    megaApp: "/production",
    step: "suno",
    url: "/production?step=suno",
  },
  "sound-crafter": {
    megaApp: "/production",
    step: "suno",
    url: "/production?step=suno",
  },

  // Legacy/Unmapped - redirect to closest MegaApp
  storyboard: {
    megaApp: "/story-engine",
    step: "story",
    url: "/story-engine?step=story",
  },
  "creative-editor": {
    megaApp: "/production",
    step: "veo",
    url: "/production?step=veo",
  },
  "character-consistency": {
    megaApp: "/dna-lab",
    step: "mirror",
    url: "/dna-lab?step=mirror",
  },
};

/**
 * Get redirect URL for a dimension route
 */
export function getDimensionRedirectUrl(dimensionKey: string): string | null {
  const redirect = DIMENSION_REDIRECT_MAP[dimensionKey];
  return redirect?.url ?? null;
}

/**
 * Get redirect info for a dimension route
 */
export function getDimensionRedirect(
  dimensionKey: string
): DimensionRedirect | null {
  return DIMENSION_REDIRECT_MAP[dimensionKey] ?? null;
}
