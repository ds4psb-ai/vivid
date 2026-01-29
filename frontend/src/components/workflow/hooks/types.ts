/**
 * Workflow Hooks Types
 *
 * Type definitions for workflow hooks including IP integration.
 * Used by useIPChainData and related hooks.
 */

import type { SuggestedDefault } from "../types";

// =============================================================================
// IP Data Types (from demo-ip-overrides.ts)
// =============================================================================

/**
 * Synthetic IP Detail - IP 데이터 구조
 * Based on backend IPCatalog response and demo-ip-overrides.ts
 */
export interface SyntheticIPDetail {
  id: string;
  slug: string;
  name_ko: string;
  name_en: string;
  description_ko: string | null;
  description_en: string | null;
  thumbnail_url: string | null;
  banner_url: string | null;
  preview_video_url: string | null;
  genre: string[];
  tags: string[];
  worldbuilding: IPWorldbuilding;
  license_status: "allowed" | "restricted" | "prohibited";
  preset_count: number;
  generation_count: number;
  presets: SyntheticPreset[];
}

/**
 * IP Worldbuilding data structure
 * Contains thematic elements, visual style, characters, etc.
 */
export interface IPWorldbuilding {
  /** Thematic elements for VPE initialization */
  thematic_elements?: {
    core?: string;
    motifs?: string[];
    themes?: string[];
  };
  /** Visual style for AD initialization */
  visual_style?: {
    colors?: string[];
    lighting?: string;
    mood?: string;
    cinematography?: string;
  };
  /** Character definitions for Mirror initialization */
  characters?: Array<{
    name: string;
    role?: string;
    traits?: string[];
    backstory?: string;
  }>;
  /** Story setting for Story Engine */
  setting?: string;
  logline?: string;
  mood?: string;
  /** Additional arbitrary worldbuilding data */
  [key: string]: unknown;
}

/**
 * IP Preset definition
 */
export interface SyntheticPreset {
  id: string;
  name_ko: string;
  name_en?: string;
  description_ko?: string | null;
  description_en?: string | null;
  thumbnail_url?: string | null;
  preset_type: string;
  estimated_credits: number;
  estimated_duration_seconds?: number;
  is_featured?: boolean;
}

// =============================================================================
// useIPChainData Hook Types
// =============================================================================

/**
 * Options for useIPChainData hook
 */
export interface UseIPChainDataOptions {
  /** IP slug from URL parameter (?ip=xxx) */
  ipSlug: string | null;
  /** Required chain data keys to track */
  requiredKeys?: string[];
  /** Auto-fetch IP data from backend/demo */
  autoFetchIP?: boolean;
  /** Auto-restore chain data from session */
  autoRestoreSession?: boolean;
}

/**
 * Result returned by useIPChainData hook
 */
export interface UseIPChainDataResult<T extends Record<string, unknown> = Record<string, unknown>> {
  // IP State
  /** Current IP slug */
  ipSlug: string | null;
  /** Fetched IP data */
  ipData: SyntheticIPDetail | null;
  /** IP data loading state */
  ipLoading: boolean;
  /** IP fetch error */
  ipError: Error | null;

  // Chain Data (from useRequiredChainData)
  /** Complete chain data (null if any required key missing) */
  chainData: T | null;
  /** Whether any required data is missing */
  hasMissingData: boolean;
  /** Keys that are missing */
  missingKeys: string[];
  /** Partial data (even when some keys missing) */
  partialData: Partial<T>;

  // IP-based Defaults (Phase 2 MissingDataBanner integration)
  /** Suggested defaults extracted from IP worldbuilding */
  ipDefaults: Record<string, SuggestedDefault>;

  // Actions
  /** Initialize chain data from IP (restore session + fetch IP) */
  initializeFromIP: () => Promise<void>;
  /** Save current chain data to session storage */
  saveToIP: () => void;
  /** Restore chain data from session storage */
  restoreFromIP: () => boolean;
  /** Apply a suggested default to chain data */
  applySuggestion: (key: string, value: unknown) => void;
  /** Navigate to source step for a missing key */
  goToSource: (key: string) => void;

  // Evidence Accumulation (DimensionChainContext integration)
  /** All accumulated evidence refs */
  evidenceRefs: string[];
  /** Add a new evidence ref */
  addEvidenceRef: (ref: string) => void;

  // Session Status
  /** Whether session was successfully restored */
  sessionRestored: boolean;
  /** Whether IP has existing session data */
  hasExistingSession: boolean;
}

// =============================================================================
// IP Defaults Extraction Types
// =============================================================================

/**
 * VPE (Video Prompt Engineering) default values
 */
export interface VPEDefaults {
  thematicCore?: string;
  visualMotifs?: string[];
  themes?: string[];
}

/**
 * AD (Aesthetic Director) default values
 */
export interface ADDefaults {
  colorPalette?: string[];
  lightingStyle?: string;
  mood?: string;
  cinematographyStyle?: string;
}

/**
 * Mirror (Abyss Mirror) default values
 */
export interface MirrorDefaults {
  characters?: Array<{
    name: string;
    role?: string;
    traits?: string[];
  }>;
}

/**
 * Story Engine default values
 */
export interface StoryDefaults {
  setting?: string;
  logline?: string;
  mood?: string;
}
