import { SceneSnapshot } from "@/types/agent";
import { asRecord, getText } from "@/lib/agentUtils";

const buildSceneSnapshot = (
  output: Record<string, unknown>,
  meta?: { status?: string; source?: string; updatedAt?: string }
): SceneSnapshot | null => {
  const sceneId = getText(output.scene_id);
  if (!sceneId) return null;
  return {
    sceneId,
    title: getText(output.title),
    summary: getText(output.summary),
    style: asRecord(output.style) ?? undefined,
    updatedAt: getText(output.updated_at) || getText(output.created_at) || meta?.updatedAt,
    status: meta?.status,
    source: meta?.source,
  };
};

export const extractScenesFromToolPayload = (
  toolName: string,
  payload: Record<string, unknown>,
): SceneSnapshot[] => {
  const output = asRecord(payload.output) || {};
  const status = getText(payload.status);
  const updatedAt = getText(payload.updated_at);
  const source = toolName || "tool";

  if (toolName === "split_scene") {
    const created = Array.isArray(output.created) ? output.created : [];
    return created
      .map((item) => buildSceneSnapshot(asRecord(item) || {}, { status, source, updatedAt }))
      .filter((scene): scene is SceneSnapshot => Boolean(scene));
  }

  const scene = buildSceneSnapshot(output, { status, source, updatedAt });
  return scene ? [scene] : [];
};
