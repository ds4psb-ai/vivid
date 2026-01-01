import type { Edge, Node } from "@xyflow/react";
import type { WorkflowPlanResponse } from "@/lib/api";
import type { CanvasNodeData } from "@/components/canvas/CustomNodes";
import { getText } from "@/lib/agentUtils";

export type CanvasSyncEvent =
  | { type: "workflow_plan"; payload: CanvasWorkflowPayload }
  | { type: "canvas_snapshot"; payload: CanvasSnapshot }
  | { type: "canvas_settings"; payload: CanvasSettingsPayload };

export interface CanvasWorkflowPayload {
  source: "studio" | "canvas";
  sessionId?: string | null;
  plan: WorkflowPlanResponse;
}

export interface CanvasNodeSnapshot {
  id: string;
  type: string;
  label?: string;
  summary?: string;
  capsuleId?: string;
  status?: string;
  category?: string;
  aiModel?: string;
}

export interface CanvasEdgeSnapshot {
  id: string;
  source: string;
  target: string;
}

export interface CanvasSnapshot {
  source: "canvas";
  canvasId?: string | null;
  title?: string | null;
  updatedAt: string;
  nodes: CanvasNodeSnapshot[];
  edges: CanvasEdgeSnapshot[];
}

export interface CanvasSettingsPayload {
  source: "studio" | "canvas";
  canvasId?: string | null;
  autoApplyChatWorkflow: boolean;
}

const extractNodeSummary = (data: CanvasNodeData): string | undefined => {
  return (
    getText(data.description) ||
    getText(data.summary) ||
    getText(data.content) ||
    getText(data.subtitle)
  );
};

export const buildCanvasSnapshot = (
  nodes: Node<CanvasNodeData>[],
  edges: Edge[],
  meta?: { canvasId?: string | null; title?: string | null },
): CanvasSnapshot => {
  const sortedNodes = [...nodes].sort((a, b) => a.id.localeCompare(b.id));
  const sortedEdges = [...edges].sort((a, b) => a.id.localeCompare(b.id));
  return {
    source: "canvas",
    canvasId: meta?.canvasId ?? null,
    title: meta?.title ?? null,
    updatedAt: new Date().toISOString(),
    nodes: sortedNodes.map((node) => ({
      id: node.id,
      type: node.type || "unknown",
      label: getText(node.data.label),
      summary: extractNodeSummary(node.data),
      capsuleId: getText(node.data.capsuleId),
      status: getText(node.data.status),
      category: getText(node.data.category),
      aiModel: getText(node.data.ai_model),
    })),
    edges: sortedEdges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
    })),
  };
};

export const createCanvasSyncChannel = (): BroadcastChannel | null => {
  if (typeof window === "undefined") return null;
  if (!("BroadcastChannel" in window)) return null;
  return new BroadcastChannel("vivid-canvas-sync");
};

const AUTO_APPLY_STORAGE_PREFIX = "vivid.canvas.autoApplyChatWorkflow";

export const resolveAutoApplyStorageKey = (canvasId?: string | null): string => {
  return `${AUTO_APPLY_STORAGE_PREFIX}.${canvasId ?? "new"}`;
};

export const readAutoApplySetting = (canvasId?: string | null): boolean => {
  if (typeof window === "undefined") return false;
  const key = resolveAutoApplyStorageKey(canvasId);
  return window.localStorage.getItem(key) === "true";
};

export const writeAutoApplySetting = (canvasId: string | null | undefined, value: boolean): void => {
  if (typeof window === "undefined") return;
  const key = resolveAutoApplyStorageKey(canvasId);
  window.localStorage.setItem(key, String(value));
};
