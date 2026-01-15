/**
 * 2D Storyboard Schema
 *
 * API: POST /api/dimension/2d/create
 */
import { z } from "zod";
import { LanguageSchema, ModelSchema } from "../common";

// =============================================================================
// Request Schema
// =============================================================================

export const Create2DRequestSchema = z.object({
  concept: z.string()
    .trim()
    .min(1, "스토리 컨셉을 입력해주세요")
    .max(3000, "스토리 컨셉은 3000자 이하로 입력해주세요"),
  scene_count: z.number().int().min(1).max(30).default(5),
  language: LanguageSchema,
  model: ModelSchema,
  style: z.string().default("Cinematic"),
});

// =============================================================================
// Response Schema
// =============================================================================

export const StoryboardSceneSchema = z.object({
  scene_number: z.number().int(),
  description: z.string(),
  camera: z.string(),
  duration: z.string(),
  notes: z.string().optional(),
  visual_prompt: z.string().optional(),
  shot_type: z.string().optional(),
  camera_movement: z.string().optional(),
  audio_cues: z.string().optional(),
  camera_angle: z.string().optional(),
  midjourney_prompt: z.string().optional(),
});

export const StoryboardResultSchema = z.object({
  scenes: z.array(StoryboardSceneSchema),
});

export const Create2DResponseSchema = z.discriminatedUnion("success", [
  z.object({
    success: z.literal(true),
    output: StoryboardResultSchema,
  }),
  z.object({
    success: z.literal(false),
    error: z.string(),
  }),
]);

// =============================================================================
// Type Exports
// =============================================================================

export type Create2DRequest = z.infer<typeof Create2DRequestSchema>;
export type Create2DResponse = z.infer<typeof Create2DResponseSchema>;
export type StoryboardResult = z.infer<typeof StoryboardResultSchema>;
export type StoryboardScene = z.infer<typeof StoryboardSceneSchema>;
