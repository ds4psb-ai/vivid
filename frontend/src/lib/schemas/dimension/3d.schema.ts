/**
 * 3D Visual Realizer Schema
 *
 * API: POST /api/dimension/3d/generate
 */
import { z } from "zod";
import { EvidenceRefsSchema, ModelSchema, AspectRatioSchema } from "../common";

// =============================================================================
// Request Schema
// =============================================================================

export const VisualStyleSchema = z.enum([
  "photorealistic",
  "cinematic",
  "anime",
  "illustration",
  "3d-render",
  "oil-painting",
  "watercolor",
  "digital-art",
]).default("photorealistic");

export const Generate3DRequestSchema = z.object({
  description: z.string()
    .trim()
    .min(1, "이미지 설명을 입력해주세요")
    .max(2000, "이미지 설명은 2000자 이하로 입력해주세요"),
  style: VisualStyleSchema,
  aspect_ratio: AspectRatioSchema,
  model: ModelSchema,
});

// =============================================================================
// Response Schema
// =============================================================================

export const ImageParametersSchema = z.object({
  style: z.string().optional(),
  aspect_ratio: z.string().optional(),
  quality: z.string().optional(),
});

export const ImagePromptResultSchema = z.object({
  prompt: z.string(),
  negative_prompt: z.string().optional(),
  parameters: ImageParametersSchema.optional(),
  evidence_refs: EvidenceRefsSchema.optional(),
  confidence: z.number().optional(),
});

export const Generate3DResponseSchema = z.discriminatedUnion("success", [
  z.object({
    success: z.literal(true),
    output: ImagePromptResultSchema,
  }),
  z.object({
    success: z.literal(false),
    error: z.string(),
  }),
]);

// =============================================================================
// Type Exports
// =============================================================================

export type Generate3DRequest = z.infer<typeof Generate3DRequestSchema>;
export type Generate3DResponse = z.infer<typeof Generate3DResponseSchema>;
export type ImagePromptResult = z.infer<typeof ImagePromptResultSchema>;
export type ImageParameters = z.infer<typeof ImageParametersSchema>;
export type VisualStyle = z.infer<typeof VisualStyleSchema>;
