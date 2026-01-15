/**
 * Quality Director & Creative Editor Schemas
 *
 * APIs:
 * - POST /api/dimension/quality/check
 * - POST /api/dimension/quality/editor
 */
import { z } from "zod";
import { ModelSchema, EvidenceRefsSchema } from "../common";

// =============================================================================
// Quality Check Request Schema
// =============================================================================

export const ContentTypeSchema = z.enum([
  "prompt",
  "script",
  "storyboard",
  "general",
]).default("prompt");

export const QualityCheckRequestSchema = z.object({
  content: z.string()
    .trim()
    .min(1, "검사할 콘텐츠를 입력해주세요")
    .max(10000, "콘텐츠는 10000자 이하로 입력해주세요"),
  content_type: ContentTypeSchema,
  model: ModelSchema,
  strict_mode: z.boolean().default(false),
});

// =============================================================================
// Quality Check Response Schema
// =============================================================================

export const QualityIssueSchema = z.object({
  severity: z.enum(["error", "warning", "suggestion"]),
  category: z.string(),
  message: z.string(),
  location: z.string().optional(),
  fix_suggestion: z.string().optional(),
});

export const QualityScoreSchema = z.object({
  overall: z.number().min(0).max(100),
  clarity: z.number().min(0).max(100).optional(),
  specificity: z.number().min(0).max(100).optional(),
  creativity: z.number().min(0).max(100).optional(),
  technical: z.number().min(0).max(100).optional(),
});

export const QualityCheckResultSchema = z.object({
  score: QualityScoreSchema,
  issues: z.array(QualityIssueSchema),
  summary: z.string(),
  recommendations: z.array(z.string()).optional(),
});

export const QualityCheckResponseSchema = z.discriminatedUnion("success", [
  z.object({
    success: z.literal(true),
    output: QualityCheckResultSchema,
  }),
  z.object({
    success: z.literal(false),
    error: z.string(),
  }),
]);

// =============================================================================
// Creative Editor Request Schema
// =============================================================================

export const EditorPersonaSchema = z.enum([
  "Senior Editor",
  "Ruthless Critic",
  "Commercial Producer",
  "Artistic Director",
]).default("Senior Editor");

export const CreativeEditorRequestSchema = z.object({
  content: z.string()
    .trim()
    .min(1, "검토할 콘텐츠를 입력해주세요")
    .max(10000, "콘텐츠는 10000자 이하로 입력해주세요"),
  context: z.string().default("General Creative Content"),
  persona: EditorPersonaSchema,
  model: ModelSchema,
  use_rag: z.boolean().default(true),
});

// =============================================================================
// Creative Editor Response Schema
// =============================================================================

export const EditorialCritiqueSchema = z.object({
  narrative_score: z.number().min(0).max(100),
  visual_score: z.number().min(0).max(100),
  pacing_score: z.number().min(0).max(100),
  key_issues: z.array(z.string()),
});

export const ChangeSchema = z.object({
  type: z.string(),
  description: z.string(),
});

export const CreativeEditorResultSchema = z.object({
  critique: EditorialCritiqueSchema,
  original_content: z.string(),
  improved_content: z.string(),
  changes_made: z.array(ChangeSchema),
  evidence_refs: EvidenceRefsSchema.optional(),
});

export const CreativeEditorResponseSchema = z.discriminatedUnion("success", [
  z.object({
    success: z.literal(true),
    output: CreativeEditorResultSchema,
  }),
  z.object({
    success: z.literal(false),
    error: z.string(),
  }),
]);

// =============================================================================
// Type Exports
// =============================================================================

// Quality Check
export type QualityCheckRequest = z.infer<typeof QualityCheckRequestSchema>;
export type QualityCheckResponse = z.infer<typeof QualityCheckResponseSchema>;
export type QualityCheckResult = z.infer<typeof QualityCheckResultSchema>;
export type QualityScore = z.infer<typeof QualityScoreSchema>;
export type QualityIssue = z.infer<typeof QualityIssueSchema>;
export type ContentType = z.infer<typeof ContentTypeSchema>;

// Creative Editor
export type CreativeEditorRequest = z.infer<typeof CreativeEditorRequestSchema>;
export type CreativeEditorResponse = z.infer<typeof CreativeEditorResponseSchema>;
export type CreativeEditorResult = z.infer<typeof CreativeEditorResultSchema>;
export type EditorialCritique = z.infer<typeof EditorialCritiqueSchema>;
export type Change = z.infer<typeof ChangeSchema>;
export type EditorPersona = z.infer<typeof EditorPersonaSchema>;
