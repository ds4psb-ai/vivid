/**
 * 4D Reference Decoder Schema
 *
 * API: POST /api/dimension/4d/analyze
 */
import { z } from "zod";
import { EvidenceRefsSchema, LanguageSchema, ModelSchema } from "../common";

// =============================================================================
// Request Schema
// =============================================================================

export const AnalysisDepthSchema = z.enum([
  "quick",
  "standard",
  "deep",
]).default("standard");

export const Analyze4DRequestSchema = z.object({
  reference_url: z.string()
    .trim()
    .min(1, "레퍼런스 URL을 입력해주세요")
    .url("유효한 URL을 입력해주세요")
    .optional(),
  reference_text: z.string()
    .trim()
    .max(5000, "레퍼런스 텍스트는 5000자 이하로 입력해주세요")
    .optional(),
  analysis_depth: AnalysisDepthSchema,
  language: LanguageSchema,
  model: ModelSchema,
  use_rag: z.boolean().default(true),
  auteur_key: z.string().optional(),
}).refine(
  (data) => data.reference_url || data.reference_text,
  { message: "URL 또는 텍스트 중 하나를 입력해주세요" }
);

// =============================================================================
// Response Schema
// =============================================================================

export const VisualElementSchema = z.object({
  element: z.string(),
  description: z.string(),
  technique: z.string().optional(),
});

export const NarrativeElementSchema = z.object({
  element: z.string(),
  description: z.string(),
  function: z.string().optional(),
});

export const TechnicalElementSchema = z.object({
  aspect: z.string(),
  value: z.string(),
  notes: z.string().optional(),
});

export const ReferenceAnalysisSchema = z.object({
  title: z.string(),
  summary: z.string(),
  visual_elements: z.array(VisualElementSchema).optional(),
  narrative_elements: z.array(NarrativeElementSchema).optional(),
  technical_elements: z.array(TechnicalElementSchema).optional(),
  style_tags: z.array(z.string()).optional(),
  mood: z.string().optional(),
  recommendations: z.array(z.string()).optional(),
  evidence_refs: EvidenceRefsSchema.optional(),
  confidence: z.number().optional(),
});

export const Analyze4DResponseSchema = z.discriminatedUnion("success", [
  z.object({
    success: z.literal(true),
    output: ReferenceAnalysisSchema,
  }),
  z.object({
    success: z.literal(false),
    error: z.string(),
  }),
]);

// =============================================================================
// Type Exports
// =============================================================================

export type Analyze4DRequest = z.infer<typeof Analyze4DRequestSchema>;
export type Analyze4DResponse = z.infer<typeof Analyze4DResponseSchema>;
export type ReferenceAnalysis = z.infer<typeof ReferenceAnalysisSchema>;
export type VisualElement = z.infer<typeof VisualElementSchema>;
export type NarrativeElement = z.infer<typeof NarrativeElementSchema>;
export type TechnicalElement = z.infer<typeof TechnicalElementSchema>;
export type AnalysisDepth = z.infer<typeof AnalysisDepthSchema>;
