import { dimensionIdToCode, type DimensionCode } from "@/lib/tokens";

export type DimensionType =
  | "1D"
  | "2D"
  | "3D"
  | "4D"
  | "AD"
  | "AI"
  | "QC"
  | "VEO"
  | "STORY"
  | "STORYBOARD"
  | "SOUND"
  | "SUNO"
  | "KLING"
  | "CHARACTER"
  | "PROMPT"
  | "MIRROR"
  | "JSON_GEN"
  | "NANOBANANA"
  // Legacy / alias codes
  | "SA"
  | "SC"
  | "CE"
  | "REF"
  | "VIS";

export type WorkflowDimension =
  | "1D"
  | "2D"
  | "3D"
  | "4D"
  | "QC"
  | "AD"
  | "AI"
  | "VEO"
  | "STORY"
  | "SOUND";

export const WORKFLOW_DIMENSION_CODES = new Set<DimensionCode>([
  "1d",
  "2d",
  "3d",
  "4d",
  "qc",
  "ad",
  "ai",
  "veo",
  "story",
  "sound",
  "storyboard",
]);

export function normalizeWorkflowDimension(value: string): WorkflowDimension | null {
  if (!value) return null;
  if (value === "SA") return "STORY";
  if (value === "SC") return "SOUND";

  const code = dimensionIdToCode(value);
  if (!code) return null;

  switch (code) {
    case "1d":
      return "1D";
    case "2d":
      return "2D";
    case "3d":
      return "3D";
    case "4d":
      return "4D";
    case "qc":
      return "QC";
    case "ad":
      return "AD";
    case "ai":
      return "AI";
    case "veo":
      return "VEO";
    case "story":
      return "STORY";
    case "sound":
      return "SOUND";
    case "storyboard":
      return "2D";
    default:
      return null;
  }
}
