/**
 * 1D Prompt Generator Schema
 *
 * API: POST /api/dimension/1d/generate
 */
import { z } from "zod";
import { EvidenceRefsSchema, LanguageSchema, ModelSchema, StyleSchema, MoodSchema, DurationSchema } from "../common";

// =============================================================================
// Request Schema
// =============================================================================

export const Generate1DRequestSchema = z.object({
  topic: z.string()
    .trim()
    .min(1, "주제를 입력해주세요")
    .max(500, "주제는 500자 이하로 입력해주세요"),
  style: StyleSchema,
  mood: MoodSchema,
  duration: DurationSchema,
  language: LanguageSchema,
  model: ModelSchema,
  use_rag: z.boolean().default(true),
  auteur_key: z.string().optional(),
});

// =============================================================================
// Response Schema
// =============================================================================

export const StyleDetailsSchema = z.object({
  cinematography: z.string().optional(),
  lighting: z.string().optional(),
  color_grade: z.string().optional(),
});

export const TechnicalDetailsSchema = z.object({
  aspect_ratio: z.string().optional(),
  duration: z.string().optional(),
  fps: z.string().optional(),
});

export const PromptResultSchema = z.object({
  prompt: z.string(),
  negative_prompt: z.string().optional(),
  style: StyleDetailsSchema.optional(),
  technical: TechnicalDetailsSchema.optional(),
  evidence_refs: EvidenceRefsSchema.optional(),
  confidence: z.number().optional(),
});

export const Generate1DResponseSchema = z.discriminatedUnion("success", [
  z.object({
    success: z.literal(true),
    output: PromptResultSchema,
  }),
  z.object({
    success: z.literal(false),
    error: z.string(),
  }),
]);

// =============================================================================
// Type Exports
// =============================================================================

export type Generate1DRequest = z.infer<typeof Generate1DRequestSchema>;
export type Generate1DResponse = z.infer<typeof Generate1DResponseSchema>;
export type PromptResult = z.infer<typeof PromptResultSchema>;
export type StyleDetails = z.infer<typeof StyleDetailsSchema>;
export type TechnicalDetails = z.infer<typeof TechnicalDetailsSchema>;
