/**
 * Local Project Schema - Zod validation for localStorage projects
 *
 * Used for storing projects locally before login sync.
 * Schema versioning enables safe migrations.
 */
import { z } from "zod";

// Schema version for migration
export const SCHEMA_VERSION = 1;

export const LocalProjectSchema = z.object({
  local_id: z.string().uuid(),
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
  template_id: z.string().uuid().optional(),
  state: z.record(z.string(), z.unknown()).default({}),
  current_stage: z
    .enum(["analysis", "image", "video", "assembly"])
    .default("analysis"),
  current_step: z.string().default("step1"),
  progress_percent: z.number().min(0).max(100).default(0),
  status: z.enum(["active", "paused", "completed"]).default("active"),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
  synced: z.boolean().default(false),
  server_id: z.string().uuid().optional(),
});

export const LocalStorageSchema = z.object({
  version: z.number().default(SCHEMA_VERSION),
  projects: z.array(LocalProjectSchema),
});

export type LocalProject = z.infer<typeof LocalProjectSchema>;
export type LocalStorageData = z.infer<typeof LocalStorageSchema>;
