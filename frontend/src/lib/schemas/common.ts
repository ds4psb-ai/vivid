/**
 * Common Schemas - Shared primitives for API contracts
 *
 * Phase -1: F2 API Contract Implementation
 */
import { z } from "zod";

// =============================================================================
// Pagination
// =============================================================================

export const PaginationRequestSchema = z.object({
  page: z.number().int().min(1).default(1),
  limit: z.number().int().min(1).max(100).default(20),
});

export const PaginationMetaSchema = z.object({
  total: z.number().int(),
  page: z.number().int(),
  limit: z.number().int(),
  totalPages: z.number().int(),
});

// =============================================================================
// API Response Wrappers
// =============================================================================

/**
 * Standard success response wrapper
 */
export function createSuccessResponseSchema<T extends z.ZodTypeAny>(dataSchema: T) {
  return z.object({
    success: z.literal(true),
    output: dataSchema,
  });
}

/**
 * Standard error response
 */
export const ErrorResponseSchema = z.object({
  success: z.literal(false),
  error: z.string(),
  detail: z.string().optional(),
  code: z.string().optional(),
});

/**
 * Combined success/error response
 */
export function createApiResponseSchema<T extends z.ZodTypeAny>(dataSchema: T) {
  return z.discriminatedUnion("success", [
    z.object({
      success: z.literal(true),
      output: dataSchema,
    }),
    z.object({
      success: z.literal(false),
      error: z.string(),
      detail: z.string().optional(),
    }),
  ]);
}

// =============================================================================
// Common Field Schemas
// =============================================================================

/**
 * UUID string validation
 */
export const UUIDSchema = z.string().uuid();

/**
 * ISO datetime string
 */
export const DateTimeSchema = z.string().datetime();

/**
 * Non-empty string with trim
 */
export const NonEmptyStringSchema = z.string().trim().min(1);

/**
 * evidence_refs array (always List[str])
 */
export const EvidenceRefsSchema = z.array(z.string()).default([]);

/**
 * Language code
 */
export const LanguageSchema = z.enum(["ko", "en"]).default("ko");

/**
 * AI Model selection
 */
export const ModelSchema = z.enum([
  "gemini-3-flash-preview",
  "gemini-3-pro-preview",
]).default("gemini-3-flash-preview");

// =============================================================================
// RAG Related Schemas
// =============================================================================

export const RAGSourceSchema = z.object({
  id: z.string(),
  content: z.string(),
  score: z.number(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

export const RAGContextSchema = z.object({
  sources: z.array(RAGSourceSchema).optional(),
  query: z.string().optional(),
  auteur_key: z.string().optional(),
});

// =============================================================================
// Dimension Common Schemas
// =============================================================================

/**
 * Style options used across dimensions
 */
export const StyleSchema = z.enum([
  "cinematic",
  "documentary",
  "commercial",
  "artistic",
  "vlog",
]).default("cinematic");

/**
 * Mood options
 */
export const MoodSchema = z.enum([
  "neutral",
  "dramatic",
  "calm",
  "energetic",
  "melancholic",
]).default("neutral");

/**
 * Duration options
 */
export const DurationSchema = z.enum([
  "5 seconds",
  "10 seconds",
  "15 seconds",
  "30 seconds",
  "60 seconds",
]).default("15 seconds");

/**
 * Aspect ratio options
 */
export const AspectRatioSchema = z.enum([
  "16:9",
  "9:16",
  "1:1",
  "4:3",
  "21:9",
]).default("16:9");

// =============================================================================
// Type Exports
// =============================================================================

export type PaginationRequest = z.infer<typeof PaginationRequestSchema>;
export type PaginationMeta = z.infer<typeof PaginationMetaSchema>;
export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;
export type RAGSource = z.infer<typeof RAGSourceSchema>;
export type RAGContext = z.infer<typeof RAGContextSchema>;
export type Style = z.infer<typeof StyleSchema>;
export type Mood = z.infer<typeof MoodSchema>;
export type Duration = z.infer<typeof DurationSchema>;
export type AspectRatio = z.infer<typeof AspectRatioSchema>;
