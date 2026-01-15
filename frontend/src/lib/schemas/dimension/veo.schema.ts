/**
 * VEO Video Generation Schema
 *
 * API: POST /api/dimension/veo/generate/stream
 */
import { z } from "zod";
import { AspectRatioSchema, DurationSchema, ModelSchema } from "../common";

// =============================================================================
// Request Schema
// =============================================================================

export const VeoStyleSchema = z.enum([
  "cinematic",
  "documentary",
  "commercial",
  "artistic",
  "vlog",
  "animation",
]).default("cinematic");

export const GenerateVeoRequestSchema = z.object({
  prompt: z.string()
    .trim()
    .min(1, "프롬프트를 입력해주세요")
    .max(2000, "프롬프트는 2000자 이하로 입력해주세요"),
  negative_prompt: z.string()
    .trim()
    .max(500, "네거티브 프롬프트는 500자 이하로 입력해주세요")
    .optional(),
  style: VeoStyleSchema,
  duration: DurationSchema,
  aspect_ratio: AspectRatioSchema,
  model: ModelSchema,
  seed: z.number().int().optional(),
  reference_image_url: z.string().url().optional(),
});

// =============================================================================
// Response Schema
// =============================================================================

export const VeoVideoResultSchema = z.object({
  video_url: z.string().url(),
  thumbnail_url: z.string().url().optional(),
  duration_seconds: z.number(),
  resolution: z.string().optional(),
  seed_used: z.number().int().optional(),
  generation_time_ms: z.number().optional(),
});

export const GenerateVeoResponseSchema = z.discriminatedUnion("success", [
  z.object({
    success: z.literal(true),
    output: VeoVideoResultSchema,
  }),
  z.object({
    success: z.literal(false),
    error: z.string(),
  }),
]);

// =============================================================================
// SSE Progress Events (for streaming)
// =============================================================================

export const VeoProgressEventSchema = z.object({
  type: z.literal("progress"),
  percent: z.number().min(0).max(100),
  message: z.string(),
  stage: z.enum(["starting", "processing", "finalizing", "complete", "error"]).optional(),
});

export const VeoCompleteEventSchema = z.object({
  type: z.literal("complete"),
  data: VeoVideoResultSchema,
});

export const VeoErrorEventSchema = z.object({
  type: z.literal("error"),
  error: z.string(),
});

export const VeoSSEEventSchema = z.discriminatedUnion("type", [
  VeoProgressEventSchema,
  VeoCompleteEventSchema,
  VeoErrorEventSchema,
]);

// =============================================================================
// Type Exports
// =============================================================================

export type GenerateVeoRequest = z.infer<typeof GenerateVeoRequestSchema>;
export type GenerateVeoResponse = z.infer<typeof GenerateVeoResponseSchema>;
export type VeoVideoResult = z.infer<typeof VeoVideoResultSchema>;
export type VeoStyle = z.infer<typeof VeoStyleSchema>;
export type VeoProgressEvent = z.infer<typeof VeoProgressEventSchema>;
export type VeoCompleteEvent = z.infer<typeof VeoCompleteEventSchema>;
export type VeoErrorEvent = z.infer<typeof VeoErrorEventSchema>;
export type VeoSSEEvent = z.infer<typeof VeoSSEEventSchema>;
