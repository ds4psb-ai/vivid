/**
 * Design Tokens - TypeScript Definitions
 *
 * W3C DTCG 2025.10 aligned token system for Crebit/Vivid.
 * SSoT for dimension colors, semantic colors, and theme utilities.
 *
 * @see globals.css @theme block for CSS variable definitions
 * @see https://www.designtokens.org/TR/2025.10/format/ - W3C DTCG Spec
 */

// =============================================================================
// DIMENSION TOKEN TYPES
// =============================================================================

/**
 * Dimension code keys (1D-4D + special dimensions)
 */
export type DimensionCode =
  | "1d"
  | "2d"
  | "3d"
  | "4d"
  | "ad"
  | "ai"
  | "qc"
  | "veo"
  | "story"
  | "mirror";

/**
 * Theme color type (for Tailwind class mapping)
 */
export type ThemeColor =
  | "violet"
  | "cyan"
  | "emerald"
  | "amber"
  | "rose"
  | "indigo"
  | "red"
  | "sky"
  | "fuchsia"
  | "purple";

/**
 * Semantic color type for status indicators
 */
export type SemanticColor = "success" | "warning" | "error" | "info";

// =============================================================================
// DIMENSION TOKEN DEFINITIONS
// =============================================================================

export interface DimensionToken {
  /** Dimension code (e.g., "1d", "ad") */
  code: DimensionCode;
  /** CSS variable name (e.g., "--color-dimension-1d") */
  cssVar: string;
  /** Tailwind class prefix (e.g., "dimension-1d") */
  tailwindKey: string;
  /** Associated Tailwind color (fallback) */
  themeColor: ThemeColor;
  /** Human-readable label */
  label: string;
  /** Korean label */
  labelKo: string;
  /** Description */
  description: string;
}

/**
 * Dimension tokens registry - SSoT for all dimension color mappings
 */
export const DIMENSION_TOKENS: Record<DimensionCode, DimensionToken> = {
  "1d": {
    code: "1d",
    cssVar: "--color-dimension-1d",
    tailwindKey: "dimension-1d",
    themeColor: "violet",
    label: "1D Prompt",
    labelKo: "1차원 프롬프트",
    description: "Text prompt generation and refinement",
  },
  "2d": {
    code: "2d",
    cssVar: "--color-dimension-2d",
    tailwindKey: "dimension-2d",
    themeColor: "cyan",
    label: "2D Sound",
    labelKo: "2차원 사운드",
    description: "Audio and sound design",
  },
  "3d": {
    code: "3d",
    cssVar: "--color-dimension-3d",
    tailwindKey: "dimension-3d",
    themeColor: "emerald",
    label: "3D Visual",
    labelKo: "3차원 비주얼",
    description: "Image generation and visual composition",
  },
  "4d": {
    code: "4d",
    cssVar: "--color-dimension-4d",
    tailwindKey: "dimension-4d",
    themeColor: "amber",
    label: "4D Video",
    labelKo: "4차원 비디오",
    description: "Video generation and temporal composition",
  },
  ad: {
    code: "ad",
    cssVar: "--color-dimension-ad",
    tailwindKey: "dimension-ad",
    themeColor: "rose",
    label: "Aesthetic Director",
    labelKo: "미학 디렉터",
    description: "Aesthetic style guidance and direction",
  },
  ai: {
    code: "ai",
    cssVar: "--color-dimension-ai",
    tailwindKey: "dimension-ai",
    themeColor: "indigo",
    label: "AI Insight",
    labelKo: "AI 인사이트",
    description: "AI-powered analysis and insights",
  },
  qc: {
    code: "qc",
    cssVar: "--color-dimension-qc",
    tailwindKey: "dimension-qc",
    themeColor: "red",
    label: "Quality Control",
    labelKo: "퀄리티 체크",
    description: "Quality assessment and validation",
  },
  veo: {
    code: "veo",
    cssVar: "--color-dimension-veo",
    tailwindKey: "dimension-veo",
    themeColor: "sky",
    label: "Veo Video",
    labelKo: "Veo 비디오",
    description: "Google Veo video generation",
  },
  story: {
    code: "story",
    cssVar: "--color-dimension-story",
    tailwindKey: "dimension-story",
    themeColor: "fuchsia",
    label: "Story Architect",
    labelKo: "스토리 아키텍트",
    description: "Narrative structure and story development",
  },
  mirror: {
    code: "mirror",
    cssVar: "--color-dimension-mirror",
    tailwindKey: "dimension-mirror",
    themeColor: "purple",
    label: "Abyss Mirror",
    labelKo: "심연의 거울",
    description: "Self-reflection and creative exploration",
  },
};

// =============================================================================
// SEMANTIC TOKEN DEFINITIONS
// =============================================================================

export interface SemanticToken {
  /** Token key */
  key: SemanticColor;
  /** CSS variable name */
  cssVar: string;
  /** Tailwind utility class */
  tailwindKey: string;
  /** Description */
  description: string;
}

export const SEMANTIC_TOKENS: Record<SemanticColor, SemanticToken> = {
  success: {
    key: "success",
    cssVar: "--color-success",
    tailwindKey: "success",
    description: "Positive actions and confirmations",
  },
  warning: {
    key: "warning",
    cssVar: "--color-warning",
    tailwindKey: "warning",
    description: "Caution and attention needed",
  },
  error: {
    key: "error",
    cssVar: "--color-error",
    tailwindKey: "error",
    description: "Errors and destructive actions",
  },
  info: {
    key: "info",
    cssVar: "--color-info",
    tailwindKey: "info",
    description: "Informational messages",
  },
};

// =============================================================================
// SPACING TOKENS
// =============================================================================

export type SpacingKey = "panel" | "card" | "button" | "input" | "gap";

export const SPACING_TOKENS: Record<SpacingKey, { cssVar: string; value: string }> = {
  panel: { cssVar: "--spacing-panel", value: "1.5rem" },
  card: { cssVar: "--spacing-card", value: "1rem" },
  button: { cssVar: "--spacing-button", value: "0.75rem" },
  input: { cssVar: "--spacing-input", value: "0.625rem" },
  gap: { cssVar: "--spacing-gap", value: "0.5rem" },
};

// =============================================================================
// BORDER RADIUS TOKENS
// =============================================================================

export type RadiusKey = "sm" | "md" | "lg" | "xl" | "2xl" | "full";

export const RADIUS_TOKENS: Record<RadiusKey, { cssVar: string; value: string }> = {
  sm: { cssVar: "--radius-sm", value: "0.375rem" },
  md: { cssVar: "--radius-md", value: "0.5rem" },
  lg: { cssVar: "--radius-lg", value: "0.75rem" },
  xl: { cssVar: "--radius-xl", value: "1rem" },
  "2xl": { cssVar: "--radius-2xl", value: "1.5rem" },
  full: { cssVar: "--radius-full", value: "9999px" },
};

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Get dimension token by code
 */
export function getDimensionToken(code: DimensionCode): DimensionToken {
  return DIMENSION_TOKENS[code];
}

/**
 * Get dimension CSS variable value
 */
export function getDimensionCssVar(code: DimensionCode): string {
  return `var(${DIMENSION_TOKENS[code].cssVar})`;
}

/**
 * Get Tailwind class for dimension background
 */
export function getDimensionBgClass(code: DimensionCode): string {
  return `bg-${DIMENSION_TOKENS[code].tailwindKey}`;
}

/**
 * Get Tailwind class for dimension text
 */
export function getDimensionTextClass(code: DimensionCode): string {
  return `text-${DIMENSION_TOKENS[code].tailwindKey}`;
}

/**
 * Get Tailwind class for dimension border
 */
export function getDimensionBorderClass(code: DimensionCode): string {
  return `border-${DIMENSION_TOKENS[code].tailwindKey}`;
}

/**
 * Convert route key to dimension code
 * @example "prompt-alchemy" → "1d"
 */
export function routeKeyToDimensionCode(routeKey: string): DimensionCode | null {
  const mapping: Record<string, DimensionCode> = {
    "prompt-alchemy": "1d",
    "sound-crafter": "2d",
    "visual-realizer": "3d",
    "video-maker": "4d",
    "aesthetic-director": "ad",
    "reference-decoder": "ai",
    "quality-director": "qc",
    "veo": "veo",
    "story-architect": "story",
    "abyss-mirror": "mirror",
  };
  return mapping[routeKey] ?? null;
}

/**
 * Get all dimension codes
 */
export function getAllDimensionCodes(): DimensionCode[] {
  return Object.keys(DIMENSION_TOKENS) as DimensionCode[];
}

/**
 * Check if a string is a valid dimension code
 */
export function isDimensionCode(value: string): value is DimensionCode {
  return value in DIMENSION_TOKENS;
}

// =============================================================================
// THEME COLOR UTILITIES (Legacy compatibility with dimension-theme.ts)
// =============================================================================

/**
 * Theme color classes for Tailwind (backward compatible)
 */
export interface ThemeColorClasses {
  bg: string;
  bgSubtle: string;
  border: string;
  text: string;
  button: string;
  buttonActive: string;
  glow: string;
}

/**
 * Get theme color classes for a dimension
 * Generates Tailwind classes using the new design token system
 */
export function getDimensionThemeClasses(code: DimensionCode): ThemeColorClasses {
  const token = DIMENSION_TOKENS[code];
  const key = token.tailwindKey;

  return {
    bg: `bg-${key}`,
    bgSubtle: `bg-${key}/10`,
    border: `border-${key}/20`,
    text: `text-${key}`,
    button: `bg-${key}/20 hover:bg-${key}/30 text-${key}`,
    buttonActive: `bg-${key} text-black dark:text-white`,
    glow: `shadow-[0_0_20px] shadow-${key}/30`,
  };
}

// =============================================================================
// PANEL DESIGN UNITY UTILITIES (2026)
// =============================================================================

/**
 * Gradient definitions for dimension generate buttons
 * Uses Tailwind gradient classes with dimension-specific colors
 */
const DIMENSION_GRADIENTS: Record<DimensionCode, string> = {
  "1d": "bg-gradient-to-r from-violet-500 to-purple-600",
  "2d": "bg-gradient-to-r from-cyan-500 to-teal-600",
  "3d": "bg-gradient-to-r from-emerald-500 to-green-600",
  "4d": "bg-gradient-to-r from-amber-500 to-orange-600",
  "ad": "bg-gradient-to-r from-rose-500 to-pink-600",
  "ai": "bg-gradient-to-r from-indigo-500 to-blue-600",
  "qc": "bg-gradient-to-r from-red-500 to-rose-600",
  "veo": "bg-gradient-to-r from-sky-500 to-blue-600",
  "story": "bg-gradient-to-r from-fuchsia-500 to-purple-600",
  "mirror": "bg-gradient-to-r from-purple-500 to-violet-600",
};

/**
 * Get gradient classes for dimension buttons
 * @example getDimensionGradient("ad") => "bg-gradient-to-r from-rose-500 to-pink-600"
 */
export function getDimensionGradient(code: DimensionCode): string {
  return DIMENSION_GRADIENTS[code];
}

/**
 * Glow shadow sizes
 */
type GlowSize = "sm" | "md" | "lg";

/**
 * Get glow shadow classes by size
 * @example getDimensionGlow("ad", "lg") => "shadow-[0_0_30px] shadow-dimension-ad/40"
 */
export function getDimensionGlow(code: DimensionCode, size: GlowSize = "md"): string {
  const key = DIMENSION_TOKENS[code].tailwindKey;
  const sizes: Record<GlowSize, string> = {
    sm: `shadow-[0_0_10px] shadow-${key}/20`,
    md: `shadow-[0_0_20px] shadow-${key}/30`,
    lg: `shadow-[0_0_30px] shadow-${key}/40`,
  };
  return sizes[size];
}

/**
 * Get glassmorphism panel classes
 * Includes backdrop-blur and dimension-colored border
 * @example getDimensionGlassStyle("ad") => "bg-black/40 backdrop-blur-xl border border-dimension-ad/20 rounded-2xl"
 */
export function getDimensionGlassStyle(code: DimensionCode): string {
  const key = DIMENSION_TOKENS[code].tailwindKey;
  return `bg-black/40 backdrop-blur-xl border border-${key}/20 rounded-2xl`;
}

/**
 * Get unified input field classes with dimension focus ring
 * @example getDimensionInputStyle("ad") => "bg-white/5 border border-white/10 ... focus:border-dimension-ad/50 ..."
 */
export function getDimensionInputStyle(code: DimensionCode): string {
  const key = DIMENSION_TOKENS[code].tailwindKey;
  return [
    "bg-white/5 border border-white/10 rounded-lg px-4 py-3",
    "text-white placeholder:text-white/40",
    `focus:border-${key}/50 focus:ring-1 focus:ring-${key}/30`,
    "focus:outline-none transition-colors duration-200",
  ].join(" ");
}

/**
 * Get generate button classes with gradient and glow
 * @example getDimensionButtonStyle("ad") => full button classes with gradient + glow
 */
export function getDimensionButtonStyle(code: DimensionCode): string {
  return [
    "relative overflow-hidden px-6 py-3 rounded-xl font-semibold text-white",
    "transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed",
    getDimensionGradient(code),
    getDimensionGlow(code, "lg"),
    "hover:scale-[1.02]",
  ].join(" ");
}

/**
 * Get result card classes (glassmorphism with dimension accent)
 */
export function getDimensionResultStyle(code: DimensionCode): string {
  const key = DIMENSION_TOKENS[code].tailwindKey;
  return `bg-black/40 backdrop-blur-xl border border-${key}/20 rounded-2xl p-6 space-y-4`;
}

/**
 * Get skeleton loading classes
 */
export function getSkeletonStyle(): string {
  return "animate-pulse bg-white/10 rounded-lg";
}

/**
 * Get error alert classes
 */
export function getErrorStyle(): string {
  return "bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-red-400";
}

// =============================================================================
// EXPORTS
// =============================================================================

export {
  DIMENSION_TOKENS as dimensionTokens,
  SEMANTIC_TOKENS as semanticTokens,
  SPACING_TOKENS as spacingTokens,
  RADIUS_TOKENS as radiusTokens,
};
