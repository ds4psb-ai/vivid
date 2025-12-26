import type { Edge, Node } from "@xyflow/react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";
const DEFAULT_API_BASE_URL = "http://127.0.0.1:8100";
const USER_ID = process.env.NEXT_PUBLIC_USER_ID || "";
const ADMIN_MODE = process.env.NEXT_PUBLIC_ADMIN_MODE || "";

interface ApiError {
  detail?: string;
}

export interface CanvasGraph {
  nodes: Node[];
  edges: Edge[];
  meta?: Record<string, unknown>;
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

export interface TemplateSeedPayload {
  notebook_id: string;
  slug: string;
  title: string;
  description?: string;
  capsule_key: string;
  capsule_version: string;
  tags?: string[];
  is_public?: boolean;
  creator_id?: string | null;
}

export interface PipelineStageSummary {
  total: number;
  latest?: string | null;
}

export interface PipelineStatus {
  raw_assets: PipelineStageSummary;
  raw_restricted: number;
  video_segments: PipelineStageSummary;
  notebook_library: PipelineStageSummary;
  notebook_assets: PipelineStageSummary;
  evidence_records: PipelineStageSummary;
  evidence_missing_source_pack?: number;
  pattern_candidates: PipelineStageSummary;
  pattern_candidate_status: Record<string, number>;
  patterns: PipelineStageSummary;
  pattern_status: Record<string, number>;
  pattern_trace: PipelineStageSummary;
  pattern_version?: string | null;
  pattern_version_at?: string | null;
  pattern_versions?: PatternVersion[];
  capsule_specs: PipelineStageSummary;
  templates: PipelineStageSummary;
  templates_public: number;
  templates_missing_provenance?: number;
  template_versions: PipelineStageSummary;
  canvases: PipelineStageSummary;
  capsule_runs: PipelineStageSummary;
  capsule_run_status: Record<string, number>;
  generation_runs: PipelineStageSummary;
  generation_run_status: Record<string, number>;
  quarantine_total?: number;
  quarantine_by_sheet?: Record<string, number>;
  quarantine_by_reason?: Record<string, number>;
  quarantine_items?: Array<{ sheet: string; reason: string; count: number }>;
  quarantine_sample?: Array<{ sheet: string; reason: string; row: string; created_at: string }>;
}

export interface PatternPromotionRequest {
  derive_from_evidence?: boolean;
  min_confidence?: number;
  min_sources?: number;
  allow_empty_evidence?: boolean;
  allow_missing_raw?: boolean;
  note?: string;
  dry_run?: boolean;
}

export interface PatternPromotionResponse {
  changed: boolean;
  stats: Record<string, number>;
  derived_candidates?: number;
  pattern_version?: string | null;
  note?: string | null;
}

export interface SheetsSyncResponse {
  status: string;
  duration_ms: number;
  quarantine_total: number;
  quarantine_by_sheet: Record<string, number>;
  quarantine_by_reason: Record<string, number>;
}

export interface OpsActionLog {
  id: string;
  action_type: string;
  status: string;
  note?: string | null;
  payload: Record<string, unknown>;
  stats: Record<string, unknown>;
  duration_ms?: number | null;
  actor_id?: string | null;
  created_at: string;
}

export interface AffiliateProfile {
  user_id: string;
  affiliate_code: string;
  referral_link?: string | null;
  total_referrals: number;
  total_earned: number;
  pending_count: number;
}

export interface AffiliateReferral {
  id: string;
  referee_label?: string | null;
  status: string;
  reward_status: string;
  reward_amount: number;
  referee_reward_amount: number;
  created_at: string;
}

export interface AffiliateTrackRequest {
  affiliate_code: string;
  referee_label?: string;
}

export interface AffiliateRewardRequest {
  referral_id: string;
  referrer_reward?: number;
  referee_reward?: number;
  note?: string;
}

export interface AffiliateRewardResponse {
  referral_id: string;
  status: string;
  reward_status: string;
  referrer_reward: number;
  referee_reward: number;
  reward_ledger_id?: string | null;
  referee_reward_ledger_id?: string | null;
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
  token_usage?: Record<string, unknown>;
  latency_ms?: number | null;
  cost_usd_est?: number | null;
  cached?: boolean;
}

export interface CapsuleRunHistoryItem {
  run_id: string;
  status: string;
  summary: Record<string, unknown>;
  evidence_refs: string[];
  version: string;
  token_usage?: Record<string, unknown>;
  latency_ms?: number | null;
  cost_usd_est?: number | null;
  created_at: string;
}

export interface CapsuleRunRequest {
  canvas_id?: string;
  node_id?: string;
  capsule_id: string;
  capsule_version: string;
  inputs: Record<string, unknown>;
  params: Record<string, unknown>;
  upstream_context?: Record<string, unknown>;
  async_mode?: boolean;
}

export interface CapsuleRunStatus {
  run_id: string;
  capsule_id: string;
  status: string;
  summary: Record<string, unknown>;
  evidence_refs: string[];
  version: string;
  token_usage?: Record<string, unknown>;
  latency_ms?: number | null;
  cost_usd_est?: number | null;
  created_at: string;
  updated_at: string;
}

export type CapsuleRunStreamEventType =
  | "run.queued"
  | "run.started"
  | "run.progress"
  | "run.partial"
  | "run.completed"
  | "run.failed"
  | "run.cancelled";

export interface CapsuleRunStreamEvent {
  event_id: string;
  run_id: string;
  type: CapsuleRunStreamEventType;
  seq: number;
  ts: string;
  payload: Record<string, unknown>;
}

export interface CapsuleRunStreamHandlers {
  onEvent: (event: CapsuleRunStreamEvent) => void;
  onError?: (error: Error) => void;
  onOpen?: () => void;
  onClose?: () => void;
}

export interface CapsuleRunStreamController {
  close: () => void;
  cancel: () => void;
  transport: "ws" | "sse";
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
  pattern_version?: string;
  source_id?: string;
  sequence_len?: number;
  context_mode?: string;
  credit_cost?: number;
  evidence_refs: string[];
  evidence_warnings?: string[];
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

export interface ShotFeedbackPayload {
  shot_id: string;
  rating?: number | null;
  note?: string | null;
  tags?: string[];
}

export interface GenerationRunFeedbackRequest {
  shots?: ShotFeedbackPayload[];
  overall_note?: string;
}

export interface NotebookLibraryItem {
  id: string;
  notebook_id: string;
  title: string;
  notebook_ref: string;
  owner_id?: string | null;
  cluster_id?: string | null;
  cluster_label?: string | null;
  cluster_tags: string[];
  guide_scope?: string | null;
  curator_notes?: string | null;
  source_ids: string[];
  source_count?: number | null;
  created_at: string;
  updated_at: string;
}

export interface NotebookAssetItem {
  id: string;
  notebook_id: string;
  asset_id: string;
  asset_type: string;
  asset_ref?: string | null;
  title?: string | null;
  tags: string[];
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DerivedInsight {
  id: string;
  source_id: string;
  summary: string;
  guide_type?: string | null;
  story_beats?: Record<string, unknown>[] | null;
  storyboard_cards?: Record<string, unknown>[] | null;
  labels: string[];
  signature_motifs: string[];
  output_type: string;
  output_language: string;
  notebook_id?: string | null;
  generated_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RawAsset {
  id: string;
  source_id: string;
  source_url: string;
  source_type: string;
  title?: string | null;
  director?: string | null;
  year?: number | null;
  duration_sec?: number | null;
  language?: string | null;
  tags: string[];
  scene_ranges?: string | null;
  notes?: string | null;
  rights_status?: string | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PatternItem {
  id: string;
  name: string;
  pattern_type: string;
  description?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PatternTraceItem {
  id: string;
  source_id: string;
  pattern_id: string;
  pattern_name?: string | null;
  pattern_type?: string | null;
  weight?: number | null;
  evidence_ref?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PatternVersion {
  id: string;
  version: string;
  note?: string | null;
  created_at: string;
}

// --- Credits Types ---

export interface CreditBalance {
  user_id: string;
  balance: number;
  subscription_credits: number;
  topup_credits: number;
  promo_credits: number;
  promo_expires_at?: string | null;
}

export interface CreditTransaction {
  id: string;
  event_type: "topup" | "usage" | "reward" | "promo" | "refund";
  amount: number;
  balance_snapshot: number;
  description?: string | null;
  capsule_run_id?: string | null;
  meta?: Record<string, unknown>;
  created_at: string;
}

export interface CreditTransactionList {
  transactions: CreditTransaction[];
  total: number;
}

export interface TopupRequest {
  amount: number;
  pack_id?: string;
}

export interface TopupResponse {
  success: boolean;
  new_balance: number;
  transaction_id: string;
}

class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    let response: Response;
    try {
      response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...(USER_ID ? { "X-User-Id": USER_ID } : {}),
          ...(ADMIN_MODE ? { "X-Admin-Mode": ADMIN_MODE } : {}),
          ...(options.headers || {}),
        },
      });
    } catch {
      const origin =
        typeof window !== "undefined" && window.location?.origin
          ? window.location.origin
          : "";
      const target = API_BASE_URL || DEFAULT_API_BASE_URL;
      const originHint = origin ? ` (origin: ${origin})` : "";
      throw new Error(
        `Failed to reach API at ${target}. Is the backend running and CORS allowed${originHint}?`
      );
    }

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({}));
      const message = error.detail || "Request failed";
      if (response.status === 403) {
        throw new Error(`${message} (admin-only)`);
      }
      throw new Error(message);
    }

    return response.json();
  }

  private resolveBaseUrl(): string {
    if (API_BASE_URL) return API_BASE_URL;
    if (typeof window !== "undefined" && window.location?.origin) {
      return window.location.origin;
    }
    return "";
  }

  private resolveWsBaseUrl(): string {
    const base = this.resolveBaseUrl();
    if (!base) return "";
    if (base.startsWith("https://")) {
      return base.replace("https://", "wss://");
    }
    if (base.startsWith("http://")) {
      return base.replace("http://", "ws://");
    }
    return base;
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

  async listCapsules(): Promise<CapsuleSpec[]> {
    return this.request<CapsuleSpec[]>("/api/v1/capsules/");
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

  async seedTemplateFromEvidence(payload: TemplateSeedPayload): Promise<Template> {
    return this.request<Template>("/api/v1/templates/seed/from-evidence", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async getPipelineStatus(): Promise<PipelineStatus> {
    return this.request<PipelineStatus>("/api/v1/ops/pipeline");
  }

  async promotePatterns(payload: PatternPromotionRequest): Promise<PatternPromotionResponse> {
    return this.request<PatternPromotionResponse>("/api/v1/ops/patterns/promote", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async syncSheets(): Promise<SheetsSyncResponse> {
    return this.request<SheetsSyncResponse>("/api/v1/ops/sheets/sync", {
      method: "POST",
    });
  }

  async listOpsActions(limit: number = 8): Promise<OpsActionLog[]> {
    return this.request<OpsActionLog[]>(`/api/v1/ops/actions?limit=${limit}`);
  }

  async getAffiliateProfile(): Promise<AffiliateProfile> {
    return this.request<AffiliateProfile>("/api/v1/affiliate/profile");
  }

  async listAffiliateReferrals(limit: number = 20): Promise<AffiliateReferral[]> {
    return this.request<AffiliateReferral[]>(
      `/api/v1/affiliate/referrals?limit=${limit}`
    );
  }

  async trackAffiliateClick(payload: AffiliateTrackRequest): Promise<AffiliateReferral> {
    return this.request<AffiliateReferral>("/api/v1/affiliate/track", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async registerAffiliate(payload: AffiliateTrackRequest): Promise<AffiliateReferral> {
    return this.request<AffiliateReferral>("/api/v1/affiliate/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async grantAffiliateReward(payload: AffiliateRewardRequest): Promise<AffiliateRewardResponse> {
    return this.request<AffiliateRewardResponse>("/api/v1/affiliate/reward", {
      method: "POST",
      body: JSON.stringify(payload),
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

  async computeSpec(
    nodes: Node[],
    edges: Edge[],
    meta?: Record<string, unknown>
  ): Promise<{ spec: Record<string, unknown>; generated: boolean }> {
    return this.request("/api/v1/spec/compute", {
      method: "POST",
      body: JSON.stringify({ nodes, edges, meta }),
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

  streamCapsuleRun(
    runId: string,
    handlers: CapsuleRunStreamHandlers,
    transport: "ws" | "sse" = "ws"
  ): CapsuleRunStreamController {
    const handlePayload = (data: string) => {
      try {
        const parsed = JSON.parse(data) as Partial<CapsuleRunStreamEvent>;
        if (!parsed || typeof parsed.type !== "string" || typeof parsed.run_id !== "string") {
          return;
        }
        handlers.onEvent(parsed as CapsuleRunStreamEvent);
      } catch (err) {
        handlers.onError?.(err instanceof Error ? err : new Error("Stream parse error"));
      }
    };

    const cancelViaHttp = () => {
      void this.cancelCapsuleRun(runId).catch(() => undefined);
    };

    if (transport === "ws" && typeof WebSocket !== "undefined") {
      const wsBase = this.resolveWsBaseUrl();
      if (wsBase) {
        const socket = new WebSocket(`${wsBase}/ws/runs/${runId}`);
        socket.onopen = () => handlers.onOpen?.();
        socket.onmessage = (event) => handlePayload(event.data);
        socket.onerror = () => handlers.onError?.(new Error("WebSocket stream error"));
        socket.onclose = () => handlers.onClose?.();
        return {
          transport: "ws",
          close: () => socket.close(),
          cancel: () => {
            if (socket.readyState === WebSocket.OPEN) {
              socket.send(JSON.stringify({ type: "cancel" }));
            } else {
              cancelViaHttp();
            }
          },
        };
      }
    }

    const baseUrl = this.resolveBaseUrl();
    const source = new EventSource(`${baseUrl}/api/v1/capsules/run/${runId}/stream`);
    const onMessage = (event: MessageEvent) => handlePayload(event.data);
    const eventTypes: CapsuleRunStreamEventType[] = [
      "run.queued",
      "run.started",
      "run.progress",
      "run.partial",
      "run.completed",
      "run.failed",
      "run.cancelled",
    ];
    eventTypes.forEach((eventType) => {
      source.addEventListener(eventType, onMessage as EventListener);
    });
    source.onopen = () => handlers.onOpen?.();
    source.onerror = () => {
      handlers.onError?.(new Error("SSE stream error"));
      source.close();
      handlers.onClose?.();
    };
    return {
      transport: "sse",
      close: () => {
        source.close();
        handlers.onClose?.();
      },
      cancel: () => {
        cancelViaHttp();
      },
    };
  }

  async createGenerationRun(canvasId: string): Promise<GenerationRun> {
    return this.request<GenerationRun>("/api/v1/runs/", {
      method: "POST",
      body: JSON.stringify({ canvas_id: canvasId }),
    });
  }

  async getRawAsset(sourceId: string): Promise<RawAsset> {
    return this.request<RawAsset>(`/api/v1/ingest/raw/${encodeURIComponent(sourceId)}`);
  }

  async listNotebookLibrary(params: {
    search?: string;
    cluster_id?: string;
    guide_scope?: string;
    skip?: number;
    limit?: number;
  } = {}): Promise<NotebookLibraryItem[]> {
    const query = new URLSearchParams();
    if (params.search) query.set("search", params.search);
    if (params.cluster_id) query.set("cluster_id", params.cluster_id);
    if (params.guide_scope) query.set("guide_scope", params.guide_scope);
    if (typeof params.skip === "number") query.set("skip", String(params.skip));
    if (typeof params.limit === "number") query.set("limit", String(params.limit));
    const suffix = query.toString();
    return this.request<NotebookLibraryItem[]>(
      `/api/v1/ingest/notebook${suffix ? `?${suffix}` : ""}`
    );
  }

  async listNotebookAssets(params: {
    notebook_id?: string;
    asset_type?: string;
    search?: string;
    skip?: number;
    limit?: number;
  } = {}): Promise<NotebookAssetItem[]> {
    const query = new URLSearchParams();
    if (params.notebook_id) query.set("notebook_id", params.notebook_id);
    if (params.asset_type) query.set("asset_type", params.asset_type);
    if (params.search) query.set("search", params.search);
    if (typeof params.skip === "number") query.set("skip", String(params.skip));
    if (typeof params.limit === "number") query.set("limit", String(params.limit));
    const suffix = query.toString();
    return this.request<NotebookAssetItem[]>(
      `/api/v1/ingest/notebook-assets${suffix ? `?${suffix}` : ""}`
    );
  }

  async listDerivedInsights(params: {
    source_id?: string;
    notebook_id?: string;
    output_type?: string;
    guide_type?: string;
    skip?: number;
    limit?: number;
  } = {}): Promise<DerivedInsight[]> {
    const query = new URLSearchParams();
    if (params.source_id) query.set("source_id", params.source_id);
    if (params.notebook_id) query.set("notebook_id", params.notebook_id);
    if (params.output_type) query.set("output_type", params.output_type);
    if (params.guide_type) query.set("guide_type", params.guide_type);
    if (typeof params.skip === "number") query.set("skip", String(params.skip));
    if (typeof params.limit === "number") query.set("limit", String(params.limit));
    const suffix = query.toString();
    return this.request<DerivedInsight[]>(
      `/api/v1/ingest/derive${suffix ? `?${suffix}` : ""}`
    );
  }

  async listPatterns(params: {
    search?: string;
    pattern_type?: string;
    status?: string;
    skip?: number;
    limit?: number;
  } = {}): Promise<PatternItem[]> {
    const query = new URLSearchParams();
    if (params.search) query.set("search", params.search);
    if (params.pattern_type) query.set("pattern_type", params.pattern_type);
    if (params.status) query.set("status", params.status);
    if (typeof params.skip === "number") query.set("skip", String(params.skip));
    if (typeof params.limit === "number") query.set("limit", String(params.limit));
    const suffix = query.toString();
    return this.request<PatternItem[]>(
      `/api/v1/ingest/patterns${suffix ? `?${suffix}` : ""}`
    );
  }

  async listPatternTrace(params: {
    search?: string;
    source_id?: string;
    pattern_id?: string;
    pattern_type?: string;
    skip?: number;
    limit?: number;
  } = {}): Promise<PatternTraceItem[]> {
    const query = new URLSearchParams();
    if (params.search) query.set("search", params.search);
    if (params.source_id) query.set("source_id", params.source_id);
    if (params.pattern_id) query.set("pattern_id", params.pattern_id);
    if (params.pattern_type) query.set("pattern_type", params.pattern_type);
    if (typeof params.skip === "number") query.set("skip", String(params.skip));
    if (typeof params.limit === "number") query.set("limit", String(params.limit));
    const suffix = query.toString();
    return this.request<PatternTraceItem[]>(
      `/api/v1/ingest/pattern-trace${suffix ? `?${suffix}` : ""}`
    );
  }

  async listPatternVersions(limit: number = 10): Promise<PatternVersion[]> {
    return this.request<PatternVersion[]>(
      `/api/v1/ingest/pattern-versions?limit=${limit}`
    );
  }

  async cancelCapsuleRun(runId: string): Promise<CapsuleRunStatus> {
    return this.request<CapsuleRunStatus>(`/api/v1/capsules/run/${runId}/cancel`, {
      method: "POST",
    });
  }

  async getGenerationRun(runId: string): Promise<GenerationRun> {
    return this.request<GenerationRun>(`/api/v1/runs/${runId}`);
  }

  async submitGenerationFeedback(
    runId: string,
    payload: GenerationRunFeedbackRequest,
  ): Promise<GenerationRun> {
    return this.request<GenerationRun>(`/api/v1/runs/${runId}/feedback`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // --- Credits API ---

  async getCreditsBalance(userId: string = "demo-user"): Promise<CreditBalance> {
    return this.request<CreditBalance>(`/api/v1/credits/balance?user_id=${encodeURIComponent(userId)}`);
  }

  async getCreditsTransactions(
    userId: string = "demo-user",
    limit: number = 20,
    offset: number = 0
  ): Promise<CreditTransactionList> {
    return this.request<CreditTransactionList>(
      `/api/v1/credits/transactions?user_id=${encodeURIComponent(userId)}&limit=${limit}&offset=${offset}`
    );
  }

  async topupCredits(amount: number, packId?: string, userId: string = "demo-user"): Promise<TopupResponse> {
    return this.request<TopupResponse>(`/api/v1/credits/topup?user_id=${encodeURIComponent(userId)}`, {
      method: "POST",
      body: JSON.stringify({ amount, pack_id: packId }),
    });
  }
}

export const api = new ApiClient();
