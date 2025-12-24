import type { Edge, Node } from "@xyflow/react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";
const USER_ID = process.env.NEXT_PUBLIC_USER_ID || "";

interface ApiError {
  detail?: string;
}

export interface CanvasGraph {
  nodes: Node[];
  edges: Edge[];
}

export interface Canvas {
  id: string;
  title: string;
  graph_data: CanvasGraph;
  is_public: boolean;
  version: number;
  owner_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CanvasCreate {
  title: string;
  graph_data: CanvasGraph;
  is_public?: boolean;
  owner_id?: string | null;
}

export interface Template {
  id: string;
  slug: string;
  title: string;
  description: string;
  tags: string[];
  graph_data: CanvasGraph;
  is_public: boolean;
  creator_id?: string | null;
  version?: number;
  preview_video_url?: string;
}

export interface TemplateVersion {
  id: string;
  template_id: string;
  version: number;
  graph_data: CanvasGraph;
  notes?: string | null;
  creator_id?: string | null;
  created_at: string;
}

export interface CapsuleSpec {
  id: string;
  capsule_key: string;
  version: string;
  display_name: string;
  description: string;
  spec: Record<string, unknown>;
  is_active: boolean;
}

export interface CapsuleRun {
  run_id: string;
  status: string;
  summary: Record<string, unknown>;
  evidence_refs: string[];
  version: string;
  cached?: boolean;
}

export interface CapsuleRunHistoryItem {
  run_id: string;
  status: string;
  summary: Record<string, unknown>;
  evidence_refs: string[];
  version: string;
  created_at: string;
}

export interface CapsuleRunRequest {
  canvas_id?: string;
  node_id?: string;
  capsule_id: string;
  capsule_version: string;
  inputs: Record<string, unknown>;
  params: Record<string, unknown>;
  async_mode?: boolean;
}

export interface CapsuleRunStatus {
  run_id: string;
  capsule_id: string;
  status: string;
  summary: Record<string, unknown>;
  evidence_refs: string[];
  version: string;
  created_at: string;
  updated_at: string;
}

export interface ScenePreview {
  scene_number: number;
  composition: string;
  dominant_color: string;
  accent_color: string;
  pacing_note: string;
  duration_hint: string;
}

export interface StoryboardPreview {
  run_id: string;
  capsule_id: string;
  scenes: ScenePreview[];
  palette: string[];
  style_vector: number[];
  evidence_refs: string[];
}

export interface GenerationRun {
  id: string;
  canvas_id: string;
  spec: Record<string, unknown>;
  status: string;
  outputs: Record<string, unknown>;
  owner_id?: string | null;
  created_at: string;
  updated_at: string;
}

class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(USER_ID ? { "X-User-Id": USER_ID } : {}),
        ...(options.headers || {}),
      },
    });

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Request failed");
    }

    return response.json();
  }

  async listCanvases(): Promise<Canvas[]> {
    return this.request<Canvas[]>("/api/v1/canvases/");
  }

  async createCanvas(data: CanvasCreate): Promise<Canvas> {
    return this.request<Canvas>("/api/v1/canvases/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async loadCanvas(id: string): Promise<Canvas> {
    return this.request<Canvas>(`/api/v1/canvases/${id}`);
  }

  async updateCanvas(id: string, data: Partial<CanvasCreate>): Promise<Canvas> {
    return this.request<Canvas>(`/api/v1/canvases/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async listTemplates(includePrivate: boolean = true): Promise<Template[]> {
    const params = includePrivate ? "?public_only=false" : "";
    return this.request<Template[]>(`/api/v1/templates/${params}`);
  }

  async getTemplate(id: string): Promise<Template> {
    return this.request<Template>(`/api/v1/templates/${id}`);
  }

  async updateTemplate(id: string, data: Partial<Template> & { notes?: string }): Promise<Template> {
    return this.request<Template>(`/api/v1/templates/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async listTemplateVersions(id: string): Promise<TemplateVersion[]> {
    return this.request<TemplateVersion[]>(`/api/v1/templates/${id}/versions`);
  }

  async createCanvasFromTemplate(templateId: string, title?: string, ownerId?: string): Promise<Canvas> {
    return this.request<Canvas>("/api/v1/canvases/from-template", {
      method: "POST",
      body: JSON.stringify({ template_id: templateId, title, owner_id: ownerId }),
    });
  }

  async getCapsuleSpec(capsuleKey: string, version?: string): Promise<CapsuleSpec> {
    const params = version ? `?version=${encodeURIComponent(version)}` : "";
    return this.request<CapsuleSpec>(`/api/v1/capsules/${capsuleKey}${params}`);
  }

  async runCapsule(payload: CapsuleRunRequest): Promise<CapsuleRun> {
    return this.request<CapsuleRun>("/api/v1/capsules/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async listCapsuleRuns(capsuleKey: string, limit: number = 5): Promise<CapsuleRunHistoryItem[]> {
    return this.request<CapsuleRunHistoryItem[]>(
      `/api/v1/capsules/${capsuleKey}/runs?limit=${limit}`
    );
  }

  async getCapsuleRun(runId: string): Promise<CapsuleRunStatus> {
    return this.request<CapsuleRunStatus>(`/api/v1/capsules/run/${runId}`);
  }

  async computeSpec(nodes: Node[], edges: Edge[]): Promise<{ spec: Record<string, unknown>; generated: boolean }> {
    return this.request("/api/v1/spec/compute", {
      method: "POST",
      body: JSON.stringify({ nodes, edges }),
    });
  }

  async optimizeParams(
    nodes: Node[],
    edges: Edge[],
    targetProfile: string = "balanced"
  ): Promise<{
    recommendations: Array<{
      params: Record<string, unknown>;
      fitness_score: number;
      profile: string;
    }>;
  }> {
    return this.request("/api/v1/spec/optimize", {
      method: "POST",
      body: JSON.stringify({ nodes, edges, target_profile: targetProfile }),
    });
  }

  async getStoryboardPreview(
    capsuleKey: string,
    runId: string,
    sceneCount: number = 3
  ): Promise<StoryboardPreview> {
    return this.request<StoryboardPreview>(
      `/api/v1/capsules/${capsuleKey}/runs/${runId}/preview?scene_count=${sceneCount}`
    );
  }

  async createGenerationRun(canvasId: string): Promise<GenerationRun> {
    return this.request<GenerationRun>("/api/v1/runs/", {
      method: "POST",
      body: JSON.stringify({ canvas_id: canvasId }),
    });
  }

  async getGenerationRun(runId: string): Promise<GenerationRun> {
    return this.request<GenerationRun>(`/api/v1/runs/${runId}`);
  }
}

export const api = new ApiClient();
