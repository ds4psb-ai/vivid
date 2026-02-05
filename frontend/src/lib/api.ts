import type { Edge, Node } from "@xyflow/react";
import type { AgentToolCall } from "@/types/agent";

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
  evidence_ops_only?: number;
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
  min_fitness_score?: number;
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

export interface CapsuleRefreshRequest {
  pattern_version?: string;
  dry_run?: boolean;
  only_active?: boolean;
}

export interface CapsuleRefreshResponse {
  pattern_version: string;
  updated: number;
  dry_run: boolean;
  only_active: boolean;
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

export interface RunTraceSummaryItem {
  date: string;
  run_count: number;
  avg_latency_ms: number | null;
  avg_cost_usd: number | null;
  total_cost_usd: number | null;
  status_breakdown: Record<string, number>;
}

export interface RunTraceSummary {
  items: RunTraceSummaryItem[];
  total_runs: number;
  period_start: string;
  period_end: string;
  overall_avg_latency_ms: number | null;
  overall_avg_cost_usd: number | null;
  overall_total_cost_usd: number | null;
}

export interface EvidenceCoverageByType {
  claim_type: string;
  total_claims: number;
  claims_with_evidence: number;
  coverage_rate: number;
}

export interface EvidenceCoverage {
  total_claims: number;
  claims_with_evidence: number;
  claims_without_evidence: number;
  coverage_rate: number;
  avg_evidence_per_claim: number;
  min_evidence_count: number;
  max_evidence_count: number;
  coverage_by_type: EvidenceCoverageByType[];
  calculated_at: string;
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

// Dimension Tools Config (SSoT from backend)
export interface DimensionToolConfig {
  toolId: string;
  dimension: string;
  displayName: string;
  displayNameEn: string;
  description: string;
  icon: string;
  color: string;
  stage: string;
  capsuleKey: string;
  endpoint: string;
  creditCost: number;
}

export interface DimensionToolsConfig {
  tools: DimensionToolConfig[];
  toolsById: Record<string, DimensionToolConfig>;
  stageOrder: string[];
  version: string;
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
  /** DirectorPack for DNA-based multi-scene consistency */
  director_pack?: Record<string, unknown>;
  /** Per-scene overrides for DNA rules */
  scene_overrides?: Record<string, Record<string, unknown>>;
  /** NarrativeArc for Story-First generation (arc_type, emotion curve, dissonance) */
  narrative_arc?: Record<string, unknown>;
  /** HookVariant for A/B testing hook styles (style, intensity, prompt_prefix) */
  hook_variant?: Record<string, unknown>;
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
  summary?: string | null;
  storyboard_cards?: Record<string, unknown>[];
  scenes: ScenePreview[];
  palette: string[];
  style_vector: number[];
  audio_overview?: {
    mood: string;
    tempo: string;
    notes: string;
  } | null;
  mind_map?: Array<{ label: string; note: string }>;
  output_language?: string;
  available_languages?: string[];
  pattern_version?: string;
  source_id?: string;
  sequence_len?: number;
  context_mode?: string;
  credit_cost?: number;
  latency_ms?: number;
  token_usage?: { input?: number; output?: number; total?: number };
  evidence_refs: string[];
  evidence_warnings?: string[];
  output_warnings?: string[];
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

export interface VideoGenerateResponse {
  run_id: string;
  status: string;
  shots_generated: number;
  shots_total: number;
  results: Array<{
    shot_id: string;
    status: string;
    video_url: string | null;
    iteration: number;
    latency_ms: number;
    model_version: string;
    error: string | null;
  }>;
  metrics: {
    total_shots: number;
    success_count: number;
    failure_count: number;
    success_rate: number;
    total_latency_ms: number;
    total_cost_usd: number;
    pipeline_duration_sec: number;
    provider: string;
  };
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

export interface SessionUser {
  user_id: string;
  email?: string | null;
  name?: string | null;
  role?: string | null;
  verified?: boolean | null;
}

export interface AuthSession {
  authenticated: boolean;
  user?: SessionUser;
}

export interface AgentMessageRecord {
  message_id: string;
  role: string;
  content: string;
  tool_calls: AgentToolCall[];
  tool_call_id?: string | null;
  name?: string | null;
  created_at: string;
}

export interface AgentArtifactRecord {
  artifact_id: string;
  artifact_type: string;
  payload: Record<string, unknown>;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface AgentSessionResponse {
  session_id: string;
  status: string;
  title?: string | null;
  agent_model?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  messages: AgentMessageRecord[];
  artifacts: AgentArtifactRecord[];
}

export interface AgentSessionStatusResponse {
  session_id: string;
  status: string;
  metadata: Record<string, unknown>;
  updated_at: string;
}

export interface AgentChatRequest {
  session_id?: string | null;
  message: string;
  metadata?: Record<string, unknown>;
  model?: string | null;
  attachments?: Record<string, unknown>[];
  page_context?: string | null;  // Current page path for context-aware responses
}

export interface AgentDecisionRequest {
  note?: string | null;
  metadata?: Record<string, unknown>;
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

// --- Node Execution Types ---

export interface NodeExecuteRequest {
  node_id: string;
  node_type: string;
  category: "input" | "generate" | "refine" | "validate" | "compose" | "output";
  input_data: Record<string, unknown>;
  upstream_results: Record<string, unknown>;
  params: Record<string, unknown>;
  ai_model?: string;
}

export interface NodeExecuteEvent {
  type: "status" | "chunk" | "validation" | "result" | "error";
  status?: string;
  message?: string;
  content?: string;
  progress?: number;
  rule?: string;
  passed?: boolean;
  details?: string;
  output?: Record<string, unknown>;
}

export interface NodeExecuteResult {
  node_id: string;
  status: "complete" | "error";
  output: Record<string, unknown>;
  execution_time_ms: number;
  token_usage: { input: number; output: number; total: number };
}

// --- Singularity (특이점) Types ---

export interface SingularityTemplate {
  id: string;
  title: string;
  description: string;
  thumbnail_url: string | null;
  dimension_source: string;
  dimension_sequence: string[];
  tags: string[];
  use_count: number;
  rating_avg: number;
  creator_name: string;
  is_featured: boolean;
  tool_names?: string[];
  // Detail fields (available when fetching single template)
  tool_sequence?: string[];
  input_preset?: Record<string, unknown>;
  output_example?: Record<string, unknown>;
  category?: string;
}

export interface SingularityTemplateList {
  items: SingularityTemplate[];
  total: number;
  page: number;
  page_size: number;
}

export interface SingularityTemplateParams {
  tag?: string;
  featured_only?: boolean;
  page?: number;
  pageSize?: number;
}

// --- Intent Preset Types ---

export interface IntentPresetSummary {
  name: string;
  description: string;
  mood: string;
  pace: string;
  target: string;
  keywords: string[];
}

export interface IntentPresetListResponse {
  count: number;
  presets: IntentPresetSummary[];
}

// --- Constellation (별자리) Types ---

export interface StarPoint {
  scene_number: number;
  singularity_id: string;
  singularity_name: string;
  status: "pending" | "generating" | "done" | "error";
  thumbnail_url: string | null;
  overrides: Record<string, unknown>;
  output_ref: string | null;
  created_at: string | null;
}

export interface SharedContext {
  characters: Record<string, { name: string; singularity_ref?: string }>;
  visual_style: string | null;
  audio_style: string | null;
  custom_params: Record<string, unknown>;
}

export interface Constellation {
  id: string;
  name: string;
  description: string;
  thumbnail_url: string | null;
  preset: "short_drama" | "medium" | "feature_film";
  target_scene_count: number;
  scene_count: number;
  completed_count: number;
  progress_percent: number;
  creator_id: string;
  creator_name: string;
  is_public: boolean;
  use_count: number;
  created_at: string;
  updated_at: string;
  shared_context?: SharedContext;
  star_points?: StarPoint[];
}

export interface ConstellationList {
  items: Constellation[];
  total: number;
  page: number;
  page_size: number;
}

export interface ConstellationParams {
  preset?: "short_drama" | "medium" | "feature_film";
  creator_id?: string;
  public_only?: boolean;
  sort_by?: "created_at" | "use_count" | "name";
  sort_order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export interface ConstellationCreateData {
  name: string;
  description?: string;
  preset?: "short_drama" | "medium" | "feature_film";
  target_scene_count?: number;
  shared_context?: Partial<SharedContext>;
  first_singularity_id?: string;
}

export interface StarAddData {
  singularity_id: string;
  overrides?: Record<string, unknown>;
  scene_number?: number;
}

export interface StarUpdateData {
  overrides?: Record<string, unknown>;
  status?: "pending" | "generating" | "done" | "error";
  thumbnail_url?: string;
  output_ref?: string;
}

export interface ConstellationUpdateData {
  name?: string;
  description?: string;
  thumbnail_url?: string;
  preset?: "short_drama" | "medium" | "feature_film";
  target_scene_count?: number;
  shared_context?: Partial<SharedContext>;
  is_public?: boolean;
}


class ApiClient {
  private getCsrfToken(): string | undefined {
    if (typeof document === "undefined") return undefined;
    const match = document.cookie.match(/csrf_token=([^;]+)/);
    return match?.[1];
  }

  private buildHeaders(extra?: HeadersInit): Record<string, string> {
    const csrfToken = this.getCsrfToken();
    const base: Record<string, string> = {
      "Content-Type": "application/json",
      ...(USER_ID ? { "X-User-Id": USER_ID } : {}),
      ...(ADMIN_MODE ? { "X-Admin-Mode": ADMIN_MODE } : {}),
      ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
    };

    if (!extra) return base;

    if (extra instanceof Headers) {
      extra.forEach((value, key) => {
        base[key] = value;
      });
      return base;
    }

    if (Array.isArray(extra)) {
      extra.forEach(([key, value]) => {
        base[key] = value;
      });
      return base;
    }

    return { ...base, ...extra };
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

    let response: Response;
    try {
      // Check if offline
      if (typeof window !== "undefined" && !navigator.onLine) {
        throw new Error("네트워크 연결이 끊어졌습니다. 인터넷 연결을 확인해주세요.");
      }

      response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        credentials: "include",
        headers: this.buildHeaders(options.headers),
        signal: controller.signal,
      });
    } catch (err) {
      clearTimeout(timeoutId);

      // Handle abort (timeout)
      if (err instanceof Error && err.name === "AbortError") {
        throw new Error("요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.");
      }

      // Handle offline/network errors
      if (err instanceof Error && err.message.includes("네트워크")) {
        throw err;
      }

      const origin =
        typeof window !== "undefined" && window.location?.origin
          ? window.location.origin
          : "";
      const target = API_BASE_URL || DEFAULT_API_BASE_URL;
      const originHint = origin ? ` (origin: ${origin})` : "";
      throw new Error(
        `서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요.${originHint ? ` API: ${target}` : ""}`
      );
    } finally {
      clearTimeout(timeoutId);
    }

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({}));
      const message = error.detail || "Request failed";

      // Handle authentication errors (JWT expired or invalid)
      if (response.status === 401) {
        // ⚠️ TEMP: 디자이너 프리뷰용 - 401에서 로그인 리다이렉트 비활성화
        // TODO: 리뷰 후 제거
        const SKIP_AUTH_REDIRECT = true;
        if (SKIP_AUTH_REDIRECT) {
          throw new Error("인증이 필요합니다.");
        }
        // Clear any cached session and redirect to login
        if (typeof window !== "undefined") {
          const currentPath = window.location.pathname;
          // /login 페이지에서는 리다이렉트 하지 않음 (무한 루프 방지)
          if (currentPath === "/login") {
            throw new Error("세션이 만료되었습니다. 다시 로그인해주세요.");
          }
          // Store current path for redirect after login
          const returnPath = currentPath + window.location.search;
          sessionStorage.setItem("auth_redirect", returnPath);
          window.location.href = "/login?expired=true";
        }
        throw new Error("세션이 만료되었습니다. 다시 로그인해주세요.");
      }

      if (response.status === 402) {
        throw new Error("크레딧이 부족합니다.");
      }

      if (response.status === 403) {
        throw new Error(`${message} (admin-only)`);
      }

      // Handle rate limiting (429)
      if (response.status === 429) {
        throw new Error("요청이 너무 많습니다. 잠시 후 다시 시도해주세요.");
      }

      if (response.status === 504) {
        throw new Error("서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.");
      }

      if (response.status >= 500) {
        throw new Error("서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
      }

      throw new Error(message);
    }

    // Handle 204 No Content responses
    if (response.status === 204) {
      return undefined as T;
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

  async getSession(): Promise<AuthSession> {
    return this.request<AuthSession>("/api/v1/auth/session");
  }

  /**
   * Ensure CSRF token is available.
   * Call this if you get CSRF errors on existing sessions.
   * Note: getSession() now auto-sets CSRF token if missing.
   */
  async refreshCsrfToken(): Promise<{ csrf_token: string }> {
    return this.request<{ csrf_token: string }>("/api/v1/auth/csrf");
  }

  async getAgentSession(sessionId: string): Promise<AgentSessionResponse> {
    return this.request<AgentSessionResponse>(`/api/v1/agent/sessions/${sessionId}`);
  }

  async approveAgentSession(
    sessionId: string,
    payload: AgentDecisionRequest = {}
  ): Promise<AgentSessionStatusResponse> {
    return this.request<AgentSessionStatusResponse>(`/api/v1/agent/sessions/${sessionId}/approve`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async rejectAgentSession(
    sessionId: string,
    payload: AgentDecisionRequest = {}
  ): Promise<AgentSessionStatusResponse> {
    return this.request<AgentSessionStatusResponse>(`/api/v1/agent/sessions/${sessionId}/reject`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async openAgentChatStream(
    payload: AgentChatRequest,
    signal?: AbortSignal,
  ): Promise<Response> {
    const baseUrl = this.resolveBaseUrl();
    const endpoint = baseUrl ? `${baseUrl}/api/v1/agent/chat` : "/api/v1/agent/chat";
    return fetch(endpoint, {
      method: "POST",
      credentials: "include",
      headers: this.buildHeaders({ Accept: "text/event-stream" }),
      body: JSON.stringify(payload),
      signal,
    });
  }

  async uploadFile(file: File): Promise<{
    file_uri: string;
    name: string;
    mime_type: string;
    display_name: string;
  }> {
    const baseUrl = this.resolveBaseUrl();
    const endpoint = `${baseUrl}/api/v1/agent/upload`;

    // Header setup without Content-Type (let browser set boundary)
    const headers = this.buildHeaders();
    delete headers["Content-Type"];

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(endpoint, {
      method: "POST",
      credentials: "include",
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "File upload failed");
    }
    return response.json();
  }

  // =============================================================================
  // Generic HTTP Methods (prefer these over fetchWithAuth)
  // =============================================================================

  /**
   * Generic GET request
   * @example
   * const data = await api.get<MyType>('/api/v1/endpoint');
   */
  async get<T>(endpoint: string, options: Omit<RequestInit, 'method' | 'body'> = {}): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  /**
   * Generic POST request
   * @example
   * const result = await api.post<ResultType>('/api/v1/endpoint', { data: 'value' });
   */
  async post<T>(endpoint: string, body?: unknown, options: Omit<RequestInit, 'method' | 'body'> = {}): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * Generic PUT request
   * @example
   * const result = await api.put<ResultType>('/api/v1/endpoint', { data: 'value' });
   */
  async put<T>(endpoint: string, body?: unknown, options: Omit<RequestInit, 'method' | 'body'> = {}): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * Generic PATCH request
   * @example
   * const result = await api.patch<ResultType>('/api/v1/endpoint', { field: 'newValue' });
   */
  async patch<T>(endpoint: string, body?: unknown, options: Omit<RequestInit, 'method' | 'body'> = {}): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * Generic DELETE request
   * @example
   * await api.delete('/api/v1/endpoint/123');
   */
  async delete<T = void>(endpoint: string, options: Omit<RequestInit, 'method' | 'body'> = {}): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  // --- Singularity (특이점) API ---

  async listSingularityTemplates(params?: SingularityTemplateParams): Promise<SingularityTemplateList> {
    const searchParams = new URLSearchParams();
    if (params?.tag) searchParams.set("tag", params.tag);
    if (params?.featured_only) searchParams.set("featured_only", "true");
    if (params?.page) searchParams.set("page", params.page.toString());
    if (params?.pageSize) searchParams.set("page_size", params.pageSize.toString());
    const query = searchParams.toString();
    return this.request<SingularityTemplateList>(`/api/v1/singularity/templates${query ? `?${query}` : ""}`);
  }

  async getSingularityTemplate(id: string): Promise<SingularityTemplate> {
    return this.request<SingularityTemplate>(`/api/v1/singularity/templates/${id}`);
  }

  async useSingularityTemplate(id: string): Promise<{ success: boolean; template_id: string; message: string }> {
    return this.request<{ success: boolean; template_id: string; message: string }>(`/api/v1/singularity/templates/${id}/use`, {
      method: "POST",
    });
  }

  async rateSingularityTemplate(id: string, rating: number, feedback?: string): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>(`/api/v1/singularity/templates/${id}/rate`, {
      method: "POST",
      body: JSON.stringify({ rating, feedback }),
    });
  }

  async createSingularityTemplate(data: {
    title: string;
    description: string;
    dimension_source: string;
    dimension_sequence: string[];
    tool_sequence: string[];
    input_preset: Record<string, unknown>;
    output_example: Record<string, unknown>;
    tags?: string[];
    category?: string;
  }): Promise<{ id: string; title: string }> {
    return this.request<{ id: string; title: string }>("/api/v1/singularity/templates", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // --- Intent Preset API ---

  async listIntentPresets(): Promise<IntentPresetListResponse> {
    return this.request<IntentPresetListResponse>("/api/v1/intent/presets");
  }

  async listIntentPresetsByCategory(category: "auteur" | "platform" | "general"): Promise<IntentPresetListResponse> {
    return this.request<IntentPresetListResponse>(`/api/v1/intent/presets/by-category/${category}`);
  }

  // --- Constellation (별자리) API ---

  async listConstellations(params?: ConstellationParams): Promise<ConstellationList> {
    const searchParams = new URLSearchParams();
    if (params?.preset) searchParams.set("preset", params.preset);
    if (params?.creator_id) searchParams.set("creator_id", params.creator_id);
    if (params?.public_only !== undefined) searchParams.set("public_only", params.public_only.toString());
    if (params?.sort_by) searchParams.set("sort_by", params.sort_by);
    if (params?.sort_order) searchParams.set("sort_order", params.sort_order);
    if (params?.page) searchParams.set("page", params.page.toString());
    if (params?.page_size) searchParams.set("page_size", params.page_size.toString());
    const query = searchParams.toString();
    return this.request<ConstellationList>(`/api/v1/constellation${query ? `?${query}` : ""}`);
  }

  async getConstellation(id: string): Promise<Constellation> {
    return this.request<Constellation>(`/api/v1/constellation/${id}`);
  }

  async createConstellation(data: ConstellationCreateData): Promise<Constellation> {
    return this.request<Constellation>("/api/v1/constellation", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateConstellation(id: string, data: ConstellationUpdateData): Promise<Constellation> {
    return this.request<Constellation>(`/api/v1/constellation/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteConstellation(id: string): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>(`/api/v1/constellation/${id}`, {
      method: "DELETE",
    });
  }

  async addStar(constellationId: string, data: StarAddData): Promise<StarPoint> {
    return this.request<StarPoint>(`/api/v1/constellation/${constellationId}/stars`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateStar(constellationId: string, sceneNumber: number, data: StarUpdateData): Promise<StarPoint> {
    return this.request<StarPoint>(`/api/v1/constellation/${constellationId}/stars/${sceneNumber}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteStar(constellationId: string, sceneNumber: number): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>(`/api/v1/constellation/${constellationId}/stars/${sceneNumber}`, {
      method: "DELETE",
    });
  }

  async generateStar(constellationId: string, sceneNumber: number): Promise<{
    redirect_url: string;
    singularity_id: string;
    constellation_id: string;
    scene_number: number;
    overrides: Record<string, unknown>;
  }> {
    return this.request(`/api/v1/constellation/${constellationId}/stars/${sceneNumber}/generate`, {
      method: "POST",
    });
  }

  // --- Payment (결제) API ---

  async confirmPayment(data: {
    tid: string;
    amount: number;
    application_id: string;
    amount_raw?: string;
    auth_token: string;
    signature: string;
    client_id: string;
    confirm_token?: string;
  }): Promise<{
    success: boolean;
    result_msg?: string;
  }> {
    return this.request<{ success: boolean; result_msg?: string }>("/api/v1/payment/confirm", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // --- Teaching Settings (BYOK) API ---

  async getTeachingSettings(): Promise<{
    has_api_key: boolean;
    api_key_preview: string | null;
    prompt_data: Record<string, unknown>;
    storyboard_data: Record<string, unknown>;
    image_tool_data: Record<string, unknown>;
    shot_catch_data: Record<string, unknown>;
    language: string;
    selected_model: string;
  }> {
    return this.request("/api/user/teaching-settings");
  }

  async updateTeachingSettings(data: Record<string, unknown>): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>("/api/user/teaching-settings", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async getTeachingApiKey(): Promise<{ api_key: string | null }> {
    return this.request<{ api_key: string | null }>("/api/user/teaching-settings/api-key");
  }

  async logout(): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>("/api/v1/auth/logout", {
      method: "POST",
    });
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

  async refreshCapsuleSpecs(payload: CapsuleRefreshRequest): Promise<CapsuleRefreshResponse> {
    return this.request<CapsuleRefreshResponse>("/api/v1/ops/capsules/refresh", {
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

  async getRunTraceSummary(days: number = 7): Promise<RunTraceSummary> {
    return this.request<RunTraceSummary>(`/api/v1/ops/run-trace-summary?days=${days}`);
  }

  async getEvidenceCoverage(clusterId?: string, minEvidence: number = 1): Promise<EvidenceCoverage> {
    const params = new URLSearchParams();
    if (clusterId) params.set("cluster_id", clusterId);
    params.set("min_evidence", String(minEvidence));
    return this.request<EvidenceCoverage>(`/api/v1/ops/evidence-coverage?${params}`);
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

  // MiniApp submissions
  async submitMiniApp(payload: {
    app_name: string;
    category: string;
    source_type: string;
    github_url?: string;
    zip_file_uri?: string;
    description: string;
    ai_tool?: string;
  }): Promise<{ id: string; status: string; message: string }> {
    return this.request<{ id: string; status: string; message: string }>("/api/v1/miniapps/submit", {
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
    targetProfile: string = "balanced",
    options?: { objective?: string; weights?: Record<string, number> }
  ): Promise<{
    recommendations: Array<{
      params: Record<string, unknown>;
      fitness_score: number;
      profile: string;
    }>;
  }> {
    return this.request("/api/v1/spec/optimize", {
      method: "POST",
      body: JSON.stringify({
        nodes,
        edges,
        target_profile: targetProfile,
        objective: options?.objective,
        weights: options?.weights,
      }),
    });
  }

  async getStoryboardPreview(
    capsuleKey: string,
    runId: string,
    sceneCount: number = 3,
    outputLanguage?: string
  ): Promise<StoryboardPreview> {
    const params = new URLSearchParams({ scene_count: String(sceneCount) });
    if (outputLanguage) {
      params.set("output_language", outputLanguage);
    }
    return this.request<StoryboardPreview>(
      `/api/v1/capsules/${capsuleKey}/runs/${runId}/preview?${params.toString()}`
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
    const source = new EventSource(`${baseUrl}/api/v1/capsules/run/${runId}/stream`, {
      withCredentials: true,
    });
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

  async listGenerationRuns(params: { canvas_id?: string; limit?: number } = {}): Promise<GenerationRun[]> {
    const query = new URLSearchParams();
    if (params.canvas_id) query.set("canvas_id", params.canvas_id);
    if (typeof params.limit === "number") query.set("limit", String(params.limit));
    const suffix = query.toString();
    return this.request<GenerationRun[]>(`/api/v1/runs/${suffix ? `?${suffix}` : ""}`);
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

  async generateVideo(
    runId: string,
    options: { provider?: "veo" | "kling" | "mock"; shot_indices?: number[] } = {},
  ): Promise<VideoGenerateResponse> {
    return this.request<VideoGenerateResponse>(`/api/v1/runs/${runId}/video`, {
      method: "POST",
      body: JSON.stringify({
        provider: options.provider || "veo",
        shot_indices: options.shot_indices,
      }),
    });
  }

  // --- Academy Access API ---

  /**
   * Check if the current user has academy access (paid enrollment).
   * Returns access info if enrolled, or throws 403 if not.
   */
  async checkAcademyAccess(): Promise<AcademyAccessResponse> {
    return this.request<AcademyAccessResponse>(`/api/v1/auth/academy/access`);
  }

  // --- Academy Admin API ---

  /**
   * Get academy applications list (admin only).
   */
  async getAcademyApplications(status?: string): Promise<AcademyApplicationsResponse> {
    const params = status ? `?status=${status}&limit=100` : "?limit=100";
    return this.request<AcademyApplicationsResponse>(`/api/v1/admin/academy/applications${params}`);
  }

  /**
   * Link academy application to Google account (admin only).
   */
  async linkAcademyAccount(name: string, googleEmail: string): Promise<AcademyLinkResponse> {
    return this.request<AcademyLinkResponse>(`/api/v1/admin/academy/link`, {
      method: "POST",
      body: JSON.stringify({ name, google_email: googleEmail }),
    });
  }

  // --- Credits API ---

  async getCreditsBalance(): Promise<CreditBalance> {
    // Backend extracts user_id from session cookie
    return this.request<CreditBalance>(`/api/v1/credits/balance`);
  }

  async getCreditsTransactions(
    limit: number = 20,
    offset: number = 0
  ): Promise<CreditTransactionList> {
    return this.request<CreditTransactionList>(
      `/api/v1/credits/transactions?limit=${limit}&offset=${offset}`
    );
  }

  async topupCredits(request: TopupRequest): Promise<TopupResponse> {
    return this.request<TopupResponse>(`/api/v1/credits/topup`, {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async deductCredits(request: { user_id?: string; amount: number; description: string; capsule_run_id?: string }): Promise<{ success: boolean; new_balance: number }> {
    return this.request<{ success: boolean; new_balance: number }>(`/api/v1/credits/deduct`, {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // --- Dimension API (Flow UI 연동) ---

  async execute1DPrompt(request: Dimension1DRequest): Promise<DimensionResponse> {
    return this.request<DimensionResponse>("/api/dimension/1d/generate", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async execute2DStoryboard(request: Dimension2DRequest): Promise<DimensionResponse> {
    return this.request<DimensionResponse>("/api/dimension/2d/create", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async execute3DImage(request: Dimension3DRequest): Promise<DimensionResponse> {
    return this.request<DimensionResponse>("/api/dimension/3d/generate", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async execute4DReference(request: Dimension4DRequest): Promise<DimensionResponse> {
    return this.request<DimensionResponse>("/api/dimension/4d/analyze", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  /**
   * Execute dimension tool by dimension key (1D, 2D, 3D, 4D, QC, AD, AI, VEO)
   * Unified interface for TrainWorkflowView
   */
  async executeDimension(
    dimension:
      | "1D"
      | "2D"
      | "3D"
      | "4D"
      | "QC"
      | "AD"
      | "AI"
      | "VEO"
      | "STORY"
      | "SOUND"
      | "SA"
      | "SC"
      | "STORYBOARD",
    inputs: Record<string, unknown>,
    model: string = "gemini-3-flash-preview"
  ): Promise<DimensionResponse> {
    switch (dimension) {
      case "1D":
        return this.execute1DPrompt({
          topic: String(inputs.topic || ""),
          style: String(inputs.style || "cinematic"),
          mood: String(inputs.mood || "neutral"),
          duration: String(inputs.duration || "15 seconds"),
          language: String(inputs.language || "ko"),
          model,
        });
      case "2D":
      case "STORYBOARD":
        return this.execute2DStoryboard({
          concept: String(inputs.concept || inputs.topic || ""),
          prompt: inputs.prompt ? String(inputs.prompt) : undefined,
          scene_count: Number(inputs.scene_count) || 5,
          language: String(inputs.language || "ko"),
          model,
        });
      case "3D":
        return this.execute3DImage({
          description: String(inputs.description || inputs.concept || ""),
          style: String(inputs.style || "photorealistic"),
          aspect_ratio: String(inputs.aspect_ratio || "16:9"),
          model,
        });
      case "4D":
        return this.execute4DReference({
          video_description: String(inputs.video_description || inputs.description || ""),
          focus_areas: Array.isArray(inputs.focus_areas)
            ? inputs.focus_areas.map(String)
            : ["composition", "lighting", "color", "movement"],
          model,
        });
      // Extended Dimension Capsules
      case "QC":
        return this.executeQualityCheck({
          content: String(inputs.content || inputs.description || ""),
          content_type: String(inputs.content_type || "video_prompt"),
          model,
        });
      case "AD":
        return this.executeAestheticDirect({
          concept: String(inputs.concept || inputs.description || ""),
          reference_style: inputs.reference_style ? String(inputs.reference_style) : undefined,
          model,
        });
      case "AI":
        return this.executePersonaAnalyze({
          subject: String(inputs.subject || inputs.description || ""),
          depth: String(inputs.depth || "deep"),
          model,
        });
      case "VEO":
        return this.executeVeoGenerate({
          prompt: String(inputs.prompt || inputs.description || ""),
          duration: Number(inputs.duration) || 5,
          aspect_ratio: String(inputs.aspect_ratio || "16:9"),
          model,
        });
      case "STORY":
      case "SA":
        return this.executeStoryArchitect({
          concept: String(inputs.concept || inputs.description || inputs.topic || ""),
          persona_data: (inputs.persona_data as Record<string, unknown>) || undefined,
          reference_analysis: (inputs.reference_analysis as Record<string, unknown>) || undefined,
          genre: inputs.genre ? String(inputs.genre) : undefined,
          duration: inputs.duration ? String(inputs.duration) : undefined,
          structure: inputs.structure ? String(inputs.structure) : undefined,
          language: inputs.language ? String(inputs.language) : "ko",
          model,
        });
      case "SOUND":
      case "SC":
        return this.executeSoundCraft({
          concept: String(inputs.concept || inputs.description || inputs.topic || ""),
          storyboard: Array.isArray(inputs.storyboard)
            ? (inputs.storyboard as Record<string, unknown>[])
            : undefined,
          sound_type: inputs.sound_type ? String(inputs.sound_type) : undefined,
          mood: inputs.mood ? String(inputs.mood) : undefined,
          genre: inputs.genre ? String(inputs.genre) : undefined,
          tempo: inputs.tempo ? String(inputs.tempo) : undefined,
          duration: inputs.duration ? String(inputs.duration) : undefined,
          target_platform: inputs.target_platform ? String(inputs.target_platform) : undefined,
          language: inputs.language ? String(inputs.language) : "ko",
          model,
        });
      default:
        throw new Error(`Unknown dimension: ${dimension}`);
    }
  }

  // --- Extended Dimension Capsule APIs ---

  async executeQualityCheck(params: {
    content: string;
    content_type?: string;
    model?: string;
  }): Promise<DimensionResponse> {
    return this.request<DimensionResponse>("/api/dimension/quality/check", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async executeAestheticDirect(params: {
    concept: string;
    reference_style?: string;
    model?: string;
  }): Promise<DimensionResponse> {
    return this.request<DimensionResponse>("/api/dimension/aesthetic/direct", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async executePersonaAnalyze(params: {
    subject: string;
    depth?: string;
    model?: string;
  }): Promise<DimensionResponse> {
    return this.request<DimensionResponse>("/api/dimension/persona/analyze", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async executeVeoGenerate(params: {
    prompt: string;
    duration?: number;
    aspect_ratio?: string;
    model?: string;
  }): Promise<DimensionResponse> {
    return this.request<DimensionResponse>("/api/dimension/veo/generate", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  /**
   * Execute Veo video generation with SSE progress streaming.
   * Returns callbacks for progress updates, completion, and errors.
   *
   * @example
   * const cleanup = api.executeVeoGenerateStream(
   *   { prompt: "A sunset over the ocean" },
   *   {
   *     onProgress: (p) => console.log(`${p.status}: ${p.message}`),
   *     onComplete: (result) => console.log(`Video: ${result.video_uri}`),
   *     onError: (error) => console.error(error),
   *   }
   * );
   * // Call cleanup() to abort the stream
   */
  executeVeoGenerateStream(
    params: {
      prompt: string;
      negative_prompt?: string;
      duration?: number;
      aspect_ratio?: string;
      style?: string;
      model?: string;
    },
    callbacks: {
      onProgress?: (progress: {
        status: string;
        elapsed_seconds: number;
        estimated_remaining_seconds: number | null;
        poll_count: number;
        message: string;
      }) => void;
      onComplete?: (result: {
        video_uri: string;
        duration_ms: number;
        credit_cost: number;
        metadata: Record<string, unknown>;
      }) => void;
      onError?: (error: string) => void;
      onHeartbeat?: () => void;
    }
  ): () => void {
    const abortController = new AbortController();

    const run = async () => {
      try {
        const baseUrl = this.resolveBaseUrl();
        const response = await fetch(`${baseUrl}/api/dimension/veo/generate/stream`, {
          method: "POST",
          headers: this.buildHeaders(),
          body: JSON.stringify(params),
          signal: abortController.signal,
        });

        if (!response.ok) {
          const errorText = await response.text();
          callbacks.onError?.(`HTTP ${response.status}: ${errorText}`);
          return;
        }

        const reader = response.body?.getReader();
        if (!reader) {
          callbacks.onError?.("No response body");
          return;
        }

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                switch (data.type) {
                  case "progress":
                    callbacks.onProgress?.({
                      status: data.status,
                      elapsed_seconds: data.elapsed_seconds,
                      estimated_remaining_seconds: data.estimated_remaining_seconds,
                      poll_count: data.poll_count,
                      message: data.message,
                    });
                    break;
                  case "complete":
                    callbacks.onComplete?.({
                      video_uri: data.video_uri,
                      duration_ms: data.duration_ms,
                      credit_cost: data.credit_cost,
                      metadata: data.metadata,
                    });
                    break;
                  case "error":
                    callbacks.onError?.(data.error);
                    break;
                  case "heartbeat":
                    callbacks.onHeartbeat?.();
                    break;
                }
              } catch {
                // Ignore parse errors
              }
            }
          }
        }
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          callbacks.onError?.((error as Error).message || "Stream error");
        }
      }
    };

    run();

    // Return cleanup function
    return () => abortController.abort();
  }

  // --- 4-Stage Workflow APIs ---

  async executeStoryArchitect(params: {
    concept: string;
    persona_data?: Record<string, unknown>;
    reference_analysis?: Record<string, unknown>;
    genre?: string;
    duration?: string;
    structure?: string;
    language?: string;
    model?: string;
  }): Promise<DimensionResponse> {
    return this.request<DimensionResponse>("/api/dimension/story/architect", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async executeSoundCraft(params: {
    concept: string;
    storyboard?: Record<string, unknown>[];
    sound_type?: string;
    mood?: string;
    genre?: string;
    tempo?: string;
    duration?: string;
    target_platform?: string;
    language?: string;
    model?: string;
  }): Promise<DimensionResponse> {
    return this.request<DimensionResponse>("/api/dimension/sound/craft", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // --- Dimension Tools Config (SSoT) ---

  async getDimensionToolsConfig(): Promise<DimensionToolsConfig> {
    return this.request<DimensionToolsConfig>("/api/dimension/tools");
  }

  // --- Dimension Multi-Generate API (2026 UQSL Integration) ---

  /**
   * Generate N candidates for 1D Prompt with UQSL quality selection
   * Uses 2026 Diversified Sampling strategies
   */
  async dimension1DMultiGenerate(
    request: DimensionMultiGenerateRequest
  ): Promise<DimensionMultiGenerateResponse> {
    return this.request<DimensionMultiGenerateResponse>("/api/dimension/1d/multi-generate", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  /**
   * SSE Streaming for 1D Multi-Generate
   * Yields events: progress, candidate, quality, selection, complete
   */
  async *dimension1DMultiGenerateStream(
    request: DimensionMultiGenerateRequest
  ): AsyncGenerator<DimensionMultiGenerateSSEEvent> {
    const baseUrl = this.resolveBaseUrl();
    const response = await fetch(`${baseUrl}/api/dimension/1d/multi-generate/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      credentials: "include",
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body");

    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const jsonStr = line.slice(6).trim();
            if (jsonStr && jsonStr !== "[DONE]") {
              try {
                const event = JSON.parse(jsonStr) as DimensionMultiGenerateSSEEvent;
                yield event;
              } catch {
                // Skip malformed JSON
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Submit selection for multi-generate session
   * Updates Thompson Sampling bandit arms
   */
  async dimension1DMultiGenerateSelect(
    sessionId: string,
    selectedIdx: number,
    rating?: number
  ): Promise<{ status: string; updated_arms: string[] }> {
    return this.request<{ status: string; updated_arms: string[] }>(
      `/api/dimension/1d/multi-generate/select`,
      {
        method: "POST",
        body: JSON.stringify({
          session_id: sessionId,
          selected_idx: selectedIdx,
          rating,
        }),
      }
    );
  }

  // --- UQSL (Universal Quality Selection Layer) API ---

  /**
   * Generate N candidates for a given prompt with quality scores
   * Uses multi-generate engine and quality evaluator
   */
  async uqslGenerateCandidates(
    request: UQSLGenerateCandidatesRequest
  ): Promise<UQSLGenerateCandidatesResponse> {
    return this.request<UQSLGenerateCandidatesResponse>("/api/v1/uqsl/generate", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  /**
   * Submit user selection for HITL mode
   */
  async uqslSelectBest(request: UQSLSelectBestRequest): Promise<{ status: string; session_id: string }> {
    return this.request<{ status: string; session_id: string }>("/api/v1/uqsl/select", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  /**
   * Submit feedback for Thompson Sampling update
   * Free tier: $0 cost (no LLM calls)
   */
  async uqslSubmitFeedback(request: UQSLFeedbackRequest): Promise<{
    status: string;
    updated_arms: string[];
  }> {
    return this.request<{ status: string; updated_arms: string[] }>("/api/v1/uqsl/feedback", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  /**
   * Get three-way comparison results (Ensemble++ NeurIPS 2025)
   * Returns A vs B vs A+B with recommended option
   */
  async uqslThreeWayComparison(request: UQSLThreeWayRequest): Promise<UQSLThreeWayResponse> {
    return this.request<UQSLThreeWayResponse>("/api/v1/uqsl/three-way", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  /**
   * Get quality metrics for an app
   */
  async uqslGetQualityMetrics(appKey: string): Promise<UQSLQualityMetrics> {
    return this.request<UQSLQualityMetrics>(`/api/v1/uqsl/metrics/${encodeURIComponent(appKey)}`);
  }

  /**
   * Stream N-candidate generation with real-time progress updates
   *
   * 2026 Best Practice:
   * - Real-time candidate generation streaming
   * - Quality score streaming as evaluated
   * - Thompson Sampling arm selection events
   *
   * @param request Generation request
   * @returns AsyncGenerator of SSE events
   */
  async *uqslGenerateCandidatesStream(
    request: UQSLGenerateCandidatesRequest
  ): AsyncGenerator<UQSLStreamEvent, void, unknown> {
    const baseUrl = API_BASE_URL || DEFAULT_API_BASE_URL;
    const response = await fetch(`${baseUrl}/api/v1/uqsl/generate/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        ...(USER_ID ? { "X-User-ID": USER_ID } : {}),
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    if (!response.body) {
      throw new Error("No response body");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              yield data as UQSLStreamEvent;
            } catch {
              // Ignore parse errors
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Stream three-way comparison with real-time updates
   *
   * Streams:
   * - Individual backend results (A, B)
   * - Ensemble merge result (A+B)
   * - Thompson Sampling recommendation
   *
   * @param request Three-way comparison request
   * @returns AsyncGenerator of SSE events
   */
  async *uqslThreeWayComparisonStream(
    request: UQSLThreeWayRequest
  ): AsyncGenerator<UQSLStreamEvent, void, unknown> {
    const baseUrl = API_BASE_URL || DEFAULT_API_BASE_URL;
    const response = await fetch(`${baseUrl}/api/v1/uqsl/three-way/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        ...(USER_ID ? { "X-User-ID": USER_ID } : {}),
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    if (!response.body) {
      throw new Error("No response body");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              yield data as UQSLStreamEvent;
            } catch {
              // Ignore parse errors
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Get Thompson Sampling arm statistics
   *
   * @param armType Optional filter by arm type (e.g., "backend", "reranker")
   */
  async uqslGetArmStats(armType?: string): Promise<UQSLArmStatsResponse> {
    const params = armType ? `?arm_type=${encodeURIComponent(armType)}` : "";
    return this.request<UQSLArmStatsResponse>(`/api/v1/uqsl/arms${params}`);
  }

  /**
   * Submit three-way selection for Thompson Sampling update
   *
   * @param comparisonId Comparison ID
   * @param selected Selected option ("a", "b", "ab", "skip")
   */
  async uqslSelectThreeWay(
    comparisonId: string,
    selected: "a" | "b" | "ab" | "skip"
  ): Promise<{ status: string; selected: string }> {
    return this.request<{ status: string; selected: string }>(
      `/api/v1/uqsl/three-way/select?comparison_id=${encodeURIComponent(comparisonId)}&selected=${selected}`,
      { method: "POST" }
    );
  }

  // --- Crebit API ---

  async applyCrebit(data: CrebitApplicationRequest): Promise<CrebitApplication> {
    return this.request<CrebitApplication>("/api/v1/crebit/apply", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async listCrebitApplications(params?: {
    status?: string;
    cohort?: string;
    limit?: number;
    offset?: number;
  }): Promise<CrebitApplicationList> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.cohort) searchParams.set("cohort", params.cohort);
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.offset) searchParams.set("offset", String(params.offset));
    const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return this.request<CrebitApplicationList>(`/api/v1/crebit/applications${query}`);
  }

  async getCrebitStats(): Promise<CrebitStats> {
    return this.request<CrebitStats>("/api/v1/crebit/stats");
  }

  // --- Analytics ---

  async trackAnalyticsEvent(payload: AnalyticsEventRequest): Promise<AnalyticsEventResponse> {
    return this.request<AnalyticsEventResponse>("/api/v1/analytics/events", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async getAnalyticsMetrics(days: number = 7): Promise<AnalyticsMetrics> {
    return this.request<AnalyticsMetrics>(`/api/v1/analytics/metrics?days=${days}`);
  }

  // --- Content Metrics API ---

  async getAggregateMetrics(params: {
    group_by?: "hook_style" | "platform" | "date";
    days?: number;
  } = {}): Promise<AggregateMetricsResponse> {
    const query = new URLSearchParams();
    if (params.group_by) query.set("group_by", params.group_by);
    if (params.days) query.set("days", String(params.days));
    const suffix = query.toString();
    return this.request<AggregateMetricsResponse>(
      `/api/v1/content-metrics/aggregate${suffix ? `?${suffix}` : ""}`
    );
  }

  async getViralInsights(params: {
    platform?: string;
    days?: number;
  } = {}): Promise<ViralInsightsResponse> {
    const query = new URLSearchParams();
    if (params.platform) query.set("platform", params.platform);
    if (params.days) query.set("days", String(params.days));
    const suffix = query.toString();
    return this.request<ViralInsightsResponse>(
      `/api/v1/content-metrics/insights${suffix ? `?${suffix}` : ""}`
    );
  }

  async getABTestResults(testId: string): Promise<ABTestResultResponse> {
    return this.request<ABTestResultResponse>(
      `/api/v1/content-metrics/ab-tests/${encodeURIComponent(testId)}`
    );
  }

  async listABTests(): Promise<ABTestResultResponse[]> {
    return this.request<ABTestResultResponse[]>("/api/v1/content-metrics/ab-tests");
  }

  // =========================================================================
  // Homepage API
  // =========================================================================

  /**
   * Get featured IP for cinematic hero section
   */
  async getHomepageFeatured(): Promise<HomepageFeaturedIP> {
    return this.request<HomepageFeaturedIP>("/api/v1/homepage/featured");
  }

  /**
   * Get featured characters for homepage section
   */
  async getHomepageCharacters(limit: number = 4): Promise<HomepageCharacter[]> {
    return this.request<HomepageCharacter[]>(`/api/v1/homepage/characters?limit=${limit}`);
  }

  /**
   * Get cinema cards for user AI cinema section
   */
  async getHomepageCinema(limit: number = 3): Promise<HomepageCinemaCard[]> {
    return this.request<HomepageCinemaCard[]>(`/api/v1/homepage/cinema?limit=${limit}`);
  }

  /**
   * Get creators for human cloud CTA section
   */
  async getHomepageCreators(limit: number = 3): Promise<HomepageCreator[]> {
    return this.request<HomepageCreator[]>(`/api/v1/homepage/creators?limit=${limit}`);
  }

  /**
   * Get variation cards for bento grid
   */
  async getHomepageVariations(sort: "popular" | "new" = "popular"): Promise<HomepageVariationCard[]> {
    return this.request<HomepageVariationCard[]>(`/api/v1/homepage/variations?sort=${sort}`);
  }

  /**
   * List all characters with search and filter support
   */
  async listCharacters(params: CharacterListParams = {}): Promise<CharacterListResponse> {
    const searchParams = new URLSearchParams();
    if (params.search) searchParams.set("search", params.search);
    if (params.category) searchParams.set("category", params.category);
    if (params.page) searchParams.set("page", String(params.page));
    if (params.pageSize) searchParams.set("page_size", String(params.pageSize));
    const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return this.request<CharacterListResponse>(`/api/v1/homepage/characters/list${query}`);
  }

  // =========================================================================
  // Prompty APIs (AI-free Workflow Guide Platform)
  // =========================================================================

  /**
   * Create a new prompty project
   */
  async createPromptyProject(data: PromptyProjectCreate): Promise<PromptyProject> {
    return this.request<PromptyProject>("/api/projects", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * List user's prompty projects
   */
  async listPromptyProjects(
    page: number = 1,
    pageSize: number = 20,
    status?: string
  ): Promise<PromptyProjectListResponse> {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (status) params.set("status", status);
    return this.request<PromptyProjectListResponse>(`/api/projects?${params}`);
  }

  /**
   * Get a prompty project by ID
   */
  async getPromptyProject(projectId: string): Promise<PromptyProject> {
    return this.request<PromptyProject>(`/api/projects/${projectId}`);
  }

  /**
   * Update prompty project state
   */
  async updatePromptyProjectState(
    projectId: string,
    data: PromptyProjectUpdate
  ): Promise<PromptyProject> {
    return this.request<PromptyProject>(`/api/projects/${projectId}/state`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  /**
   * Delete a prompty project
   */
  async deletePromptyProject(projectId: string): Promise<void> {
    await this.request<void>(`/api/projects/${projectId}`, {
      method: "DELETE",
    });
  }

  /**
   * List prompty templates
   */
  async listPromptyTemplates(
    page: number = 1,
    pageSize: number = 20,
    options?: { category?: string; featured_only?: boolean; search?: string }
  ): Promise<PromptyTemplateListResponse> {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (options?.category) params.set("category", options.category);
    if (options?.featured_only) params.set("featured_only", "true");
    if (options?.search) params.set("search", options.search);
    return this.request<PromptyTemplateListResponse>(`/api/templates?${params}`);
  }

  /**
   * Get prompty template details
   */
  async getPromptyTemplate(templateId: string): Promise<PromptyTemplate> {
    return this.request<PromptyTemplate>(`/api/templates/${templateId}`);
  }

  /**
   * Use a template to create a project
   */
  async usePromptyTemplate(templateId: string): Promise<{ project_id: string; template_title: string }> {
    return this.request<{ project_id: string; template_title: string }>(
      `/api/templates/${templateId}/use`,
      { method: "POST" }
    );
  }

  /**
   * Rate a prompty template
   */
  async ratePromptyTemplate(templateId: string, rating: number): Promise<void> {
    await this.request<void>(`/api/templates/${templateId}/rate`, {
      method: "POST",
      body: JSON.stringify({ rating }),
    });
  }

  /**
   * Submit critique for a project step
   */
  async submitPromptyCritique(
    projectId: string,
    data: Omit<PromptyCritiqueSubmit, "project_id">
  ): Promise<PromptyCritique> {
    return this.request<PromptyCritique>("/api/critique", {
      method: "POST",
      body: JSON.stringify({ ...data, project_id: projectId }),
    });
  }

  /**
   * Get critique history for a project
   */
  async getPromptyCritiqueHistory(projectId: string): Promise<PromptyCritiqueHistory> {
    return this.request<PromptyCritiqueHistory>(`/api/critique/${projectId}`);
  }

  /**
   * Get workflow guide for a project
   */
  async getPromptyGuide(projectId: string): Promise<PromptyGuideResponse> {
    return this.request<PromptyGuideResponse>(`/api/guide/${projectId}`);
  }

  /**
   * Advance to next step in workflow
   */
  async advancePromptyStep(projectId: string): Promise<PromptyNextStepResponse> {
    return this.request<PromptyNextStepResponse>(`/api/guide/${projectId}/next`, {
      method: "POST",
    });
  }

  /**
   * Log guide action for analytics
   */
  async logPromptyAction(
    projectId: string,
    action: string,
    stage?: string,
    stepId?: string,
    extraData?: Record<string, unknown>
  ): Promise<void> {
    await this.request<void>(`/api/guide/${projectId}/log`, {
      method: "POST",
      body: JSON.stringify({ action, stage, step_id: stepId, extra_data: extraData }),
    });
  }

  /**
   * Sync local STATE.md content to database
   * @param projectId - Project UUID
   * @param stateData - Either raw STATE.md content (string) or parsed JSON object
   */
  async syncPromptyState(
    projectId: string,
    stateData: string | object
  ): Promise<PromptyStateSyncResponse> {
    const body = typeof stateData === "string"
      ? { state_md_content: stateData }
      : { parsed_state: stateData };

    return this.request<PromptyStateSyncResponse>(`/api/state/${projectId}/sync`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  /**
   * Export project state as STATE.md format
   */
  async exportPromptyStateMd(projectId: string): Promise<PromptyStateExportResponse> {
    return this.request<PromptyStateExportResponse>(`/api/state/${projectId}/state.md`);
  }

  /**
   * Get parsed state from database
   */
  async getPromptyParsedState(projectId: string): Promise<PromptyStateParsed> {
    return this.request<PromptyStateParsed>(`/api/state/${projectId}/parsed`);
  }

  // =========================================================================
  // Prompty Community APIs
  // =========================================================================

  /**
   * List community projects (public gallery)
   */
  async listCommunityProjects(
    page: number = 1,
    pageSize: number = 20,
    options?: { sort?: "recent" | "top-scores" | "most-forked"; status?: "active" | "completed" }
  ): Promise<PromptyCommunityListResponse> {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (options?.sort) params.set("sort", options.sort);
    if (options?.status) params.set("status", options.status);
    return this.request<PromptyCommunityListResponse>(`/api/community?${params}`);
  }

  /**
   * Get community project details
   */
  async getCommunityProject(projectId: string): Promise<PromptyCommunityProject> {
    return this.request<PromptyCommunityProject>(`/api/community/${projectId}`);
  }

  /**
   * Fork a community project
   */
  async forkProject(projectId: string, name?: string): Promise<PromptyProject> {
    return this.request<PromptyProject>(`/api/projects/${projectId}/fork`, {
      method: "POST",
      body: JSON.stringify({ name }),
    });
  }

  /**
   * [Instructor] List all student projects
   */
  async listInstructorProjects(
    page: number = 1,
    pageSize: number = 50,
    options?: { sort?: "recent" | "user" | "score"; user_filter?: string }
  ): Promise<PromptyCommunityListResponse> {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (options?.sort) params.set("sort", options.sort);
    if (options?.user_filter) params.set("user_filter", options.user_filter);
    return this.request<PromptyCommunityListResponse>(`/api/community/instructor/all?${params}`);
  }

  /**
   * [Instructor] List all students
   */
  async listInstructorStudents(): Promise<{ students: string[]; total: number }> {
    return this.request<{ students: string[]; total: number }>("/api/community/instructor/students");
  }

  // =========================================================================
  // Prompty Tikitaka APIs (6-step Dual AI Workflow)
  // =========================================================================

  /**
   * Start tikitaka workflow for a project
   */
  async startPromptyTikitaka(
    projectId: string,
    anchorSceneId?: string
  ): Promise<TikitakaStartResponse> {
    return this.request<TikitakaStartResponse>(`/api/tikitaka/${projectId}/start`, {
      method: "POST",
      body: JSON.stringify({ anchor_scene_id: anchorSceneId }),
    });
  }

  /**
   * Get current tikitaka workflow state
   */
  async getPromptyTikitakaCurrent(projectId: string): Promise<TikitakaCurrentResponse> {
    return this.request<TikitakaCurrentResponse>(`/api/tikitaka/${projectId}/current`);
  }

  /**
   * Advance to next tikitaka step
   */
  async advancePromptyTikitaka(
    projectId: string,
    data: TikitakaAdvanceRequest
  ): Promise<TikitakaAdvanceResponse> {
    return this.request<TikitakaAdvanceResponse>(`/api/tikitaka/${projectId}/advance`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * Get tool-specific prompts
   */
  async getPromptyTikitakaToolPrompts(projectId: string): Promise<TikitakaToolPromptsResponse> {
    return this.request<TikitakaToolPromptsResponse>(`/api/tikitaka/${projectId}/prompts`);
  }

  /**
   * Jump to a specific tikitaka step
   */
  async gotoPromptyTikitakaStep(
    projectId: string,
    step: number,
    reason?: string
  ): Promise<{ step: number; reason?: string }> {
    return this.request<{ step: number; reason?: string }>(
      `/api/tikitaka/${projectId}/goto/${step}`,
      {
        method: "POST",
        body: JSON.stringify({ reason }),
      }
    );
  }

  /**
   * Set or update anchor scene for tikitaka workflow
   */
  async setPromptyTikitakaAnchor(
    projectId: string,
    anchorSceneId: string
  ): Promise<{ anchor_scene_id: string }> {
    return this.request<{ anchor_scene_id: string }>(
      `/api/tikitaka/${projectId}/anchor?anchor_scene_id=${encodeURIComponent(anchorSceneId)}`,
      { method: "PATCH" }
    );
  }

  // =========================================================================
  // Chain Session APIs (P7+: Workflow Chain Persistence)
  // =========================================================================

  /**
   * Create a new chain session
   */
  async createChainSession(data: ChainSessionCreate = {}): Promise<ChainSessionResponse> {
    return this.request<ChainSessionResponse>("/api/v1/chain/session", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * Get a chain session by ID
   */
  async getChainSession(sessionId: string): Promise<ChainSessionResponse> {
    return this.request<ChainSessionResponse>(`/api/v1/chain/session/${sessionId}`);
  }

  /**
   * Update a chain session with optimistic locking
   * Requires version field - will return 409 if version mismatch
   */
  async updateChainSession(
    sessionId: string,
    data: ChainSessionUpdate
  ): Promise<ChainSessionResponse> {
    return this.request<ChainSessionResponse>(`/api/v1/chain/session/${sessionId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  /**
   * Delete a chain session
   */
  async deleteChainSession(sessionId: string): Promise<void> {
    await this.request<void>(`/api/v1/chain/session/${sessionId}`, {
      method: "DELETE",
    });
  }

  /**
   * List user's chain sessions
   */
  async listChainSessions(
    limit: number = 20,
    offset: number = 0
  ): Promise<ChainSessionListItem[]> {
    return this.request<ChainSessionListItem[]>(
      `/api/v1/chain/user?limit=${limit}&offset=${offset}`
    );
  }

  /**
   * Get previous run output for a dimension
   */
  async getPreviousRun(dimensionKey: string): Promise<PreviousRunResponse> {
    return this.request<PreviousRunResponse>(`/api/v1/chain/${dimensionKey}/previous-run`);
  }

  // =========================================================================
  // DEPRECATED: Node Execution APIs - Only used by deprecated canvas
  // These will be removed in a future release
  // =========================================================================

  /**
   * Execute a node with SSE streaming support
   * Returns an async generator that yields events as they arrive
   * @deprecated Only used by deprecated canvas. Use Flow/Dimension APIs instead.
   */
  async *executeNodeStream(request: NodeExecuteRequest): AsyncGenerator<NodeExecuteEvent, void, unknown> {
    const baseUrl = this.resolveBaseUrl();
    const response = await fetch(`${baseUrl}/api/v1/nodes/execute`, {
      method: "POST",
      credentials: "include",
      headers: this.buildHeaders(),
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Node execution failed");
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body");

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          if (data === "[DONE]") return;
          try {
            yield JSON.parse(data) as NodeExecuteEvent;
          } catch {
            console.warn("Failed to parse SSE event:", data);
          }
        }
      }
    }
  }

  /**
   * Execute a node synchronously (non-streaming)
   * @deprecated Only used by deprecated canvas. Use Flow/Dimension APIs instead.
   */
  async executeNode(request: NodeExecuteRequest): Promise<NodeExecuteResult> {
    return this.request<NodeExecuteResult>("/api/v1/nodes/execute-sync", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }
}

// --- Academy Access Types ---

export interface AcademyAccessResponse {
  can_access: boolean;
  cohort: string | null;
  track: string | null;
  enrolled_at: string | null;
  is_admin?: boolean;
}

export interface AcademyApplication {
  id: string;
  name: string;
  email: string;
  phone: string;
  track: string;
  status: string;
  owner_id: string | null;
  paid_amount: number | null;
  paid_at: string | null;
}

export interface AcademyApplicationsResponse {
  applications: AcademyApplication[];
  total: number;
  limit: number;
  offset: number;
}

export interface AcademyLinkResponse {
  success: boolean;
  application_id?: string;
  user_id?: string;
  message: string;
}

// --- Crebit Types ---

export interface CrebitApplicationRequest {
  name: string;
  email: string;
  phone: string;
  track: "A" | "B";
}

export interface CrebitApplication {
  id: string;
  name: string;
  email: string;
  phone: string;
  track: string;
  status: string;
  cohort: string;
  created_at: string;
  confirm_token?: string;
  confirm_token_expires_at?: string;
}

export interface CrebitApplicationList {
  items: CrebitApplication[];
  total: number;
  offset: number;
  limit: number;
}

export interface CrebitStats {
  total: number;
  by_status: Record<string, number>;
  by_track: Record<string, number>;
  by_cohort: Record<string, number>;
}

// --- Analytics Types ---

export interface AnalyticsEventRequest {
  event_type:
  | "evidence_ref_opened"
  | "template_seeded"
  | "template_version_swapped"
  | "template_run_started"
  | "template_run_completed"
  // Crebit Apply flow events
  | "crebit_cta_click"
  | "crebit_modal_open"
  | "crebit_form_submit"
  | "crebit_form_error"
  // Prompty Tikitaka events (Phase 6)
  | "tikitaka_start"
  | "tikitaka_step_advance"
  | "tikitaka_complete"
  | "anchor_selected"
  | "tool_prompt_copied"
  | "verdict_action";
  template_id?: string;
  capsule_id?: string;
  run_id?: string;
  evidence_ref?: string;
  meta?: Record<string, unknown>;
}

export interface AnalyticsEventResponse {
  id: string;
  event_type: string;
  created_at: string;
}

export interface AnalyticsMetrics {
  evidence_click_count: number;
  template_seed_count: number;
  template_swap_count: number;
  evidence_click_rate: number | null;
  period_start: string;
  period_end: string;
}

// --- Content Metrics Types ---

export interface AggregateMetricsItem {
  group_key: string;
  total_content: number;
  avg_views: number;
  avg_engagement_rate: number;
  avg_viral_score: number;
  total_views: number;
}

export interface AggregateMetricsResponse {
  group_by: string;
  period_days: number;
  data: AggregateMetricsItem[];
}

export interface ViralInsightItem {
  insight_type: string;
  title: string;
  description: string;
  data: Record<string, unknown>;
  recommendation?: string;
}

export interface ViralInsightsResponse {
  period: string;
  total_content_analyzed: number;
  insights: ViralInsightItem[];
  top_performers: Record<string, unknown>[];
  hook_style_comparison: Record<string, Record<string, unknown>>;
}

export interface ABTestVariant {
  variant_id: string;
  style: string;
  views: number;
  engagement_rate: number;
  viral_score: number;
  is_winner: boolean;
}

export interface ABTestResultResponse {
  test_id: string;
  test_name: string;
  started_at: string;
  ended_at?: string;
  status: "running" | "completed" | "cancelled";
  variants: ABTestVariant[];
  winner_variant_id?: string;
  confidence_level?: number;
}

// --- Workflow Types (used by canvasSync) ---

export interface NarrativeDNA {
  core_theme: string;
  secondary_themes: string[];
  overall_tone: string;
  allowed_tones: string[];
  forbidden_tones: string[];
  protagonist_arc?: string;
  visual_style: string;
  color_palette: string[];
  reference_works: string[];
}

export interface WorkflowNode {
  id: string;
  type: string;
  label: string;
  description?: string;
  category?: "input" | "generate" | "refine" | "validate" | "compose" | "output";
  ai_model?: string;
  position: { x: number; y: number };
  data: Record<string, unknown>;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  source_handle?: string;
  target_handle?: string;
}

export interface WorkflowPlanResponse {
  workflow_id: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  narrative_dna: NarrativeDNA;
  estimated_duration_sec: number;
  agent_assignments: Record<string, string>;
  capsule_id?: string | null;
  logic_vector?: Record<string, number> | null;
  persona_vector?: Record<string, number> | null;
}

// --- Dimension API Types (Flow UI 연동) ---

export interface Dimension1DRequest {
  topic: string;
  style?: string;
  mood?: string;
  duration?: string;
  language?: string;
  model?: string;
}

export interface Dimension2DRequest {
  concept: string;
  prompt?: string;
  scene_count?: number;
  language?: string;
  model?: string;
}

export interface Dimension3DRequest {
  description: string;
  style?: string;
  aspect_ratio?: string;
  model?: string;
}

export interface Dimension4DRequest {
  video_description: string;
  focus_areas?: string[];
  model?: string;
}

export interface StoryArchitectRequest {
  concept: string;
  persona_data?: Record<string, unknown>;
  reference_analysis?: Record<string, unknown>;
  genre?: string;
  duration?: string;
  structure?: string;
  language?: string;
  model?: string;
}

export interface SoundCraftRequest {
  concept: string;
  storyboard?: Record<string, unknown>[];
  sound_type?: string;
  mood?: string;
  genre?: string;
  tempo?: string;
  duration?: string;
  target_platform?: string;
  language?: string;
  model?: string;
}

export interface DimensionMetrics {
  latency_ms: number;
  tokens: number;
  model: string;
  credit_cost?: number;
}

export interface DimensionResponse {
  success: boolean;
  capsule_id: string;
  output: Record<string, unknown>;
  error?: string;
  metrics?: DimensionMetrics;
}

// --- Dimension Multi-Generate Types (2026 UQSL Integration) ---

export type DimensionDiversityStrategy = "standard" | "verbalized" | "diversified" | "compute_optimal";

export interface DimensionMultiGenerateRequest {
  topic: string;
  style?: string;
  mood?: string;
  duration?: string;
  language?: string;
  model?: string;
  /** Number of candidates (2-5) */
  n_candidates?: number;
  /** Diversity strategy */
  strategy?: DimensionDiversityStrategy;
}

export interface DimensionMultiGenerateCandidate {
  idx: number;
  content: string;
  metadata: {
    seed: number;
    temperature: number;
    run_id?: string;
    strategy?: string;
    prompt_varied?: boolean;
  };
  latency_ms: number;
  backend_used: string;
  quality_score?: UQSLQualityScore;
}

export interface DimensionMultiGenerateResponse {
  success: boolean;
  session_id: string;
  candidates: DimensionMultiGenerateCandidate[];
  recommended_idx: number;
  thompson_arm: string;
  total_latency_ms: number;
  strategy_used: string;
}

/** SSE Event types for multi-generate streaming */
export type DimensionMultiGenerateEventType =
  | "progress"
  | "candidate"
  | "quality"
  | "selection"
  | "complete"
  | "error";

export interface DimensionMultiGenerateSSEEvent {
  type: DimensionMultiGenerateEventType;
  data: Record<string, unknown>;
  timestamp?: string;
}

// --- UQSL (Universal Quality Selection Layer) Types ---

export interface UQSLQualityScore {
  /** 거장 DNA 기반 그라운딩 (0-1) */
  groundedness: number;
  /** RAG 관련도 (0-1) */
  relevance: number;
  /** 일관성 (0-1) */
  coherence: number;
  /** 창의성 (0-1) */
  creativity: number;
  /** 안전성 (0-1) */
  safety: number;
  /** 가중 합산 점수 (0-1, optional) */
  weighted_score?: number;
  /** 가중 평균 총점 */
  total_score: number;
}

export interface UQSLCandidateResult {
  /** Candidate index */
  idx: number;
  /** Generated content */
  content: string;
  /** Metadata (seed, run_id, etc.) */
  metadata: Record<string, unknown>;
  /** Quality score */
  quality_score?: UQSLQualityScore;
  /** Latency in milliseconds */
  latency_ms: number;
  /** Backend used (e.g., "qdrant_hybrid", "notebooklm") */
  backend_used: string;
}

export interface UQSLGenerateCandidatesRequest {
  prompt: string;
  app_key: string;
  n_candidates?: number;
  strategy?: "auto" | "hitl" | "hybrid" | "llm_judge";
}

export interface UQSLGenerateCandidatesResponse {
  session_id: string;
  candidates: UQSLCandidateResult[];
  quality_scores: UQSLQualityScore[];
  recommended_idx: number;
  method: string;
}

export interface UQSLSelectBestRequest {
  session_id: string;
  selected_idx: number;
}

export interface UQSLFeedbackRequest {
  selection_id: string;
  feedback: "positive" | "negative";
  quality_override?: Partial<UQSLQualityScore>;
}

export interface UQSLThreeWayCandidateData {
  id: string;
  content: string;
  confidence?: number;
  backend_used?: string;
  metadata?: Record<string, unknown>;
}

export interface UQSLThreeWayRequest {
  query: string;
  dimension: string;
  auteur_key?: string;
}

export interface UQSLThreeWayResponse {
  results: {
    a: UQSLThreeWayCandidateData;
    b: UQSLThreeWayCandidateData;
    ab: UQSLThreeWayCandidateData;
  };
  recommended: "a" | "b" | "ab";
  arms_stats: Record<string, { alpha: number; beta: number }>;
}

export interface UQSLQualityMetrics {
  app_key: string;
  total_selections: number;
  positive_rate: number;
  avg_quality_score: number;
}

// --- UQSL SSE Event Types (2026 Best Practice) ---

/** Base SSE event structure */
export interface UQSLStreamEventBase {
  type: string;
}

/** Progress event */
export interface UQSLStreamProgressEvent extends UQSLStreamEventBase {
  type: "progress";
  percent: number;
  message: string;
  stage: "starting" | "processing" | "finalizing";
}

/** Individual candidate generation event */
export interface UQSLStreamCandidateEvent extends UQSLStreamEventBase {
  type: "candidate";
  idx: number;
  content_preview: string;
  backend_used: string;
}

/** Quality score event for individual candidate */
export interface UQSLStreamQualityEvent extends UQSLStreamEventBase {
  type: "quality";
  idx: number;
  groundedness: number;
  relevance: number;
  coherence: number;
  creativity: number;
  safety: number;
  weighted_score: number;
}

/** Final selection event with Thompson Sampling stats */
export interface UQSLStreamSelectionEvent extends UQSLStreamEventBase {
  type: "selection";
  selected_idx: number;
  method: string;
  confidence: number;
  arms_used: string[];
  arms_stats: Record<string, UQSLArmStats>;
}

/** Three-way result event (A, B, or A+B) */
export interface UQSLStreamResultEvent extends UQSLStreamEventBase {
  type: "result_a" | "result_b" | "result_ab";
  option: "A" | "B" | "A+B";
  source: "qdrant" | "notebooklm" | "ensemble";
  data: UQSLThreeWayCandidateData | null;
}

/** Thompson Sampling recommendation event */
export interface UQSLStreamRecommendationEvent extends UQSLStreamEventBase {
  type: "recommendation";
  recommended: "a" | "b" | "ab";
  arms_stats: Record<string, UQSLArmStats>;
}

/** Completion event with final data */
export interface UQSLStreamCompleteEvent extends UQSLStreamEventBase {
  type: "complete";
  success: boolean;
  data: Record<string, unknown>;
  metrics?: {
    latency_ms: number;
    n_candidates?: number;
    strategy?: string;
  };
}

/** Error event */
export interface UQSLStreamErrorEvent extends UQSLStreamEventBase {
  type: "error";
  error: string;
  code?: string;
  detail?: string;
}

/** Heartbeat event */
export interface UQSLStreamHeartbeatEvent extends UQSLStreamEventBase {
  type: "heartbeat";
  timestamp: number;
}

/** Union type for all UQSL SSE events */
export type UQSLStreamEvent =
  | UQSLStreamProgressEvent
  | UQSLStreamCandidateEvent
  | UQSLStreamQualityEvent
  | UQSLStreamSelectionEvent
  | UQSLStreamResultEvent
  | UQSLStreamRecommendationEvent
  | UQSLStreamCompleteEvent
  | UQSLStreamErrorEvent
  | UQSLStreamHeartbeatEvent;

/** Thompson Sampling arm statistics */
export interface UQSLArmStats {
  success_rate: number;
  confidence: number;
  total_trials: number;
  alpha: number;
  beta: number;
}

/** Arms statistics response */
export interface UQSLArmStatsResponse {
  arms: Record<string, UQSLArmStats>;
  total_arms: number;
}

// --- Chain Session Types (P7+: Workflow Chain Persistence) ---

/** Chain data output from a single dimension execution */
export interface ChainDataOutput {
  dimension_key: string;
  output: Record<string, unknown>;
  title: string;
  evidence_refs: string[];
  created_at: string;
}

/** Request to create a new chain session */
export interface ChainSessionCreate {
  mega_app?: string;
  title?: string;
  ip_slug?: string;
}

/** Request to update a chain session (requires version for optimistic locking) */
export interface ChainSessionUpdate {
  chain_data?: Record<string, ChainDataOutput>;
  accumulated_evidence_refs?: string[];
  current_dimension?: string;
  navigation_history?: string[];
  title?: string;
  version: number; // Required for optimistic locking
}

/** Full chain session response */
export interface ChainSessionResponse {
  id: string;
  user_id: string;
  chain_data: Record<string, ChainDataOutput>;
  accumulated_evidence_refs: string[];
  current_dimension: string | null;
  navigation_history: string[];
  mega_app: string | null;
  title: string | null;
  ip_slug: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

/** Abbreviated session for list views */
export interface ChainSessionListItem {
  id: string;
  title: string | null;
  mega_app: string | null;
  ip_slug: string | null;
  version: number;
  current_dimension: string | null;
  dimension_count: number;
  updated_at: string;
}

/** Version conflict error response (409) */
export interface ChainConflictError {
  error: "VERSION_CONFLICT";
  server_version: number;
  your_version: number;
  message: string;
}

/** Previous run response */
export interface PreviousRunResponse {
  run_id: string | null;
  dimension_key: string;
  output: Record<string, unknown>;
  evidence_refs: string[];
  created_at: string | null;
  found: boolean;
}

// --- Homepage Types ---

export interface HomepageFeaturedCharacter {
  name: string;
  description: string;
  status: string;
  imageUrl?: string;
}

export interface HomepageFeaturedIP {
  slug: string;
  title: string;
  titleAccent: string;
  description: string;
  bannerUrl: string;
  tags: string[];
  rating: number;
  remixCount: string;
  matchPercent: number;
  character?: HomepageFeaturedCharacter;
}

export interface HomepageCharacter {
  id: string;
  name: string;
  imageUrl: string;
  chatCount: string;
  quote: string;
  creator: string;
  badge?: "NEW" | "TOP_RATED";
  category?: string;
}

export interface HomepageCreatorInfo {
  name: string;
  avatarUrl: string;
}

export interface HomepageCinemaCard {
  id: string;
  title: string;
  description: string;
  thumbnailUrl: string;
  duration: string;
  category: string;
  categoryColor: string;
  creator: HomepageCreatorInfo;
  views: string;
  likePercent: number;
}

export interface HomepageCreator {
  id: string;
  initial: string;
  name: string;
  specialty: string;
  specialtyColor: "primary" | "blue" | "green";
  rating: number;
  description: string;
}

export interface HomepageVariationCard {
  id: string;
  name: string;
  description: string;
  thumbnailUrl: string;
  category: "visual" | "video" | "story" | "audio" | "interactive";
  badge?: string;
  badgeColor?: string;
  href: string;
  layout?: "tall" | "wide" | "normal";
}

export interface CharacterListParams {
  search?: string;
  category?: string;
  page?: number;
  pageSize?: number;
}

export interface CharacterListResponse {
  items: HomepageCharacter[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// =============================================================================
// Prompty Types (AI-free Workflow Guide Platform)
// =============================================================================

export interface PromptyProject {
  id: string;
  name: string;
  description?: string;
  thumbnail_url?: string;
  template_id?: string;
  state: Record<string, unknown>;
  current_stage: string;
  current_step: string;
  progress_percent: number;
  status: "active" | "paused" | "completed" | "archived";
  visibility: "private" | "prompts-only" | "full";
  forked_from_id?: string;
  fork_count: number;
  avg_score?: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  // Community-added fields (populated in community API)
  user_name?: string;
}

export interface PromptyProjectCreate {
  name: string;
  description?: string;
  template_id?: string;
}

export interface PromptyProjectUpdate {
  name?: string;
  description?: string;
  thumbnail_url?: string;
  state?: Record<string, unknown>;
  current_stage?: string;
  current_step?: string;
  progress_percent?: number;
  status?: string;
  visibility?: "private" | "prompts-only" | "full";
}

export interface PromptyProjectListResponse {
  items: PromptyProject[];
  total: number;
  page: number;
  page_size: number;
}

// Community types
export interface PromptyCommunityProject {
  id: string;
  name: string;
  description?: string;
  thumbnail_url?: string;
  user_id: string;
  user_name?: string;
  template_id?: string;
  state?: Record<string, unknown>;  // Only available for 'full' visibility
  current_stage: string;
  current_step: string;
  progress_percent: number;
  status: string;
  visibility: "private" | "prompts-only" | "full";
  forked_from_id?: string;
  avg_score?: number;
  fork_count: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  can_see_prompts: boolean;
}

export interface PromptyCommunityListResponse {
  items: PromptyCommunityProject[];
  total: number;
  page: number;
  page_size: number;
}

export interface PromptyTemplate {
  id: string;
  title: string;
  description: string;
  thumbnail_url?: string;
  category: string;
  tags: string[];
  use_count: number;
  rating_avg: number;
  creator_name: string;
  is_featured: boolean;
  workflow_config?: Record<string, unknown>;
  critique_config?: Record<string, unknown>;
  example_project_url?: string;
}

export interface PromptyTemplateListResponse {
  items: PromptyTemplate[];
  total: number;
  page: number;
  page_size: number;
}

export interface PromptyCritiqueScore {
  score: number;
  notes?: string;
}

export interface PromptyCritiqueSubmit {
  project_id?: string;  // Optional - can be set by API method
  stage: string;
  step_id: string;
  scores?: Record<string, PromptyCritiqueScore>;
  scores_detail?: Record<string, number>;  // Alternative: direct score values
  score?: number;  // Total score
  verdict?: "PASS" | "REVISE" | "REJECT";
  issues?: string[];
  suggestions?: string[];
  notes?: string;
}

export interface PromptyCritique {
  id: string;
  project_id: string;
  stage: string;
  step_id: string;
  scores: Record<string, PromptyCritiqueScore>;
  total_score: number;
  passed: boolean;
  revision_number: number;
  notes?: string;
  created_at: string;
}

export interface PromptyCritiqueHistory {
  items: PromptyCritique[];
  average_score: number;
  total_critiques: number;
  pass_rate: number;
}

export interface PromptyStepInfo {
  id: string;
  name: string;
  description?: string;
  prompt_text?: string;
  prompt_file?: string;
  external_tool?: string;
  external_url?: string;
  tips: string[];
  status: "pending" | "in_progress" | "completed";
  score?: number;
}

export interface PromptyStageInfo {
  id: string;
  name: string;
  description?: string;
  steps: PromptyStepInfo[];
  status: "pending" | "in_progress" | "completed";
}

export interface PromptyGuideResponse {
  project_id: string;
  project_name: string;
  current_stage: string;
  current_step: string;
  progress_percent: number;
  stages: PromptyStageInfo[];
  current_step_info?: PromptyStepInfo;
}

export interface PromptyNextStepResponse {
  new_stage: string;
  new_step: string;
  completed: boolean;
}

// STATE.md Sync Types
export interface PromptySceneProgress {
  scene: string;
  description: string;
  image_status: string;
  video_status: string;
  status_emoji: string;
}

export interface PromptyStageProgressItem {
  stage_id: string;
  name: string;
  percent: number;
  bar: string;
}

export interface PromptyStateParsed {
  scenes: PromptySceneProgress[];
  stages: PromptyStageProgressItem[];
  current_task?: string;
  anchor_scene?: string;
  tikitaka_count: number;
}

export interface PromptyStateSyncRequest {
  state_md_content: string;
}

export interface PromptyStateSyncResponse {
  synced: boolean;
  progress_percent: number;
  current_stage: string;
  current_step: string;
  scenes_total: number;
  scenes_completed: number;
  anchor_scene?: string;
}

export interface PromptyStateExportResponse {
  content: string;
  last_synced?: string;
}

// Tikitaka Types (6-step Dual AI Workflow)
export interface TikitakaStartResponse {
  project_id: string;
  tikitaka_id: string;
  current_step: number;
  anchor_scene_id?: string;
}

export interface TikitakaCurrentResponse {
  tikitaka_id: string;
  current_step: number;
  anchor_scene_id?: string;
  started_at: string;
  completed_at?: string;
  tool_prompts: Record<string, string>;
}

export interface TikitakaAdvanceRequest {
  gemini_output?: string;
  claude_output?: string;
  user_feedback?: string;
}

export interface TikitakaAdvanceResponse {
  new_step: number;
  completed: boolean;
}

export interface TikitakaToolPrompt {
  tool_id: string;
  tool_name: string;
  prompt_text: string;
  external_url?: string;
  recommended: boolean;
}

export interface TikitakaToolPromptsResponse {
  prompts: TikitakaToolPrompt[];
  recommended_tool: string;
}

export const api = new ApiClient();

// =============================================================================
// Legacy API Client (migrated from api-client.ts)
// =============================================================================
// P4.2 Enhanced with:
// - Retry with exponential backoff
// - Circuit breaker awareness
// - Retryable error detection
// - Max attempts configurable

// --- Legacy Types ---

export interface LegacyApiError {
  status: number;
  message: string;
  detail?: unknown;
  isRetryable?: boolean;
}

export interface LegacyApiResponse<T> {
  data: T | null;
  error: LegacyApiError | null;
  ok: boolean;
}

interface RetryConfig {
  maxRetries: number;
  initialDelayMs: number;
  maxDelayMs: number;
  backoffMultiplier: number;
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  initialDelayMs: 1000,
  maxDelayMs: 10000,
  backoffMultiplier: 2,
};

// --- Retry Utilities ---

/**
 * Check if an error is retryable
 */
function isRetryableError(status: number): boolean {
  // Retry on: rate limit, service unavailable, gateway errors
  return [429, 500, 502, 503, 504].includes(status);
}

/**
 * Sleep with jitter
 */
function sleep(ms: number): Promise<void> {
  const jitter = Math.random() * ms * 0.3;
  return new Promise((resolve) => setTimeout(resolve, ms + jitter));
}

/**
 * Execute with retry
 */
async function withRetry(
  fn: () => Promise<Response>,
  config: Partial<RetryConfig> = {}
): Promise<Response> {
  const { maxRetries, initialDelayMs, maxDelayMs, backoffMultiplier } = {
    ...DEFAULT_RETRY_CONFIG,
    ...config,
  };

  let lastError: Error | null = null;
  let delay = initialDelayMs;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fn();

      // Success or non-retryable error
      if (response.ok || !isRetryableError(response.status)) {
        return response;
      }

      // Retryable error
      if (attempt < maxRetries) {
        console.warn(
          `⚠️ Retryable error (${response.status}), attempt ${attempt + 1}/${maxRetries + 1}, waiting ${delay}ms...`
        );
        await sleep(delay);
        delay = Math.min(delay * backoffMultiplier, maxDelayMs);
      } else {
        return response; // Return last failed response
      }
    } catch (error) {
      lastError = error as Error;

      // Network errors are retryable
      if (attempt < maxRetries) {
        console.warn(
          `⚠️ Network error, attempt ${attempt + 1}/${maxRetries + 1}, waiting ${delay}ms...`
        );
        await sleep(delay);
        delay = Math.min(delay * backoffMultiplier, maxDelayMs);
      } else {
        throw error;
      }
    }
  }

  throw lastError || new Error("Max retries exceeded");
}

// --- Core Functions ---

function getLegacyAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

function enrichLegacyError(res: Response, error: unknown): LegacyApiError {
  const err = error as Record<string, unknown> | null;
  const detail = typeof err?.detail === "string" ? err.detail : undefined;
  const message = typeof err?.message === "string" ? err.message : undefined;

  const isCircuitOpen =
    detail?.includes?.("Circuit") || message?.includes?.("Circuit");

  return {
    status: res.status,
    message: isCircuitOpen
      ? "서비스가 일시적으로 불안정합니다. 잠시 후 다시 시도해주세요."
      : detail || message || `Error: ${res.status}`,
    detail: error,
    isRetryable: isRetryableError(res.status),
  };
}

async function handleLegacyResponse<T>(
  res: Response
): Promise<LegacyApiResponse<T>> {
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    return {
      data: null,
      error: enrichLegacyError(res, error),
      ok: false,
    };
  }

  const data = await res.json();
  return { data, error: null, ok: true };
}

// --- Simple API Client with Retry ---

export const simpleApi = {
  /**
   * GET request with auth and retry
   */
  async get<T>(endpoint: string, retry = true): Promise<LegacyApiResponse<T>> {
    const token = getLegacyAuthToken();
    const doFetch = () =>
      fetch(`${API_BASE_URL || DEFAULT_API_BASE_URL}${endpoint}`, {
        headers: {
          Authorization: token ? `Bearer ${token}` : "",
          "Content-Type": "application/json",
        },
      });

    const res = retry ? await withRetry(doFetch) : await doFetch();
    return handleLegacyResponse<T>(res);
  },

  /**
   * POST request with auth and retry
   */
  async post<T>(
    endpoint: string,
    body?: unknown,
    retry = true
  ): Promise<LegacyApiResponse<T>> {
    const token = getLegacyAuthToken();
    const doFetch = () =>
      fetch(`${API_BASE_URL || DEFAULT_API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: {
          Authorization: token ? `Bearer ${token}` : "",
          "Content-Type": "application/json",
        },
        body: body ? JSON.stringify(body) : undefined,
      });

    const res = retry ? await withRetry(doFetch) : await doFetch();
    return handleLegacyResponse<T>(res);
  },

  /**
   * PUT request with auth and retry
   */
  async put<T>(
    endpoint: string,
    body?: unknown,
    retry = true
  ): Promise<LegacyApiResponse<T>> {
    const token = getLegacyAuthToken();
    const doFetch = () =>
      fetch(`${API_BASE_URL || DEFAULT_API_BASE_URL}${endpoint}`, {
        method: "PUT",
        headers: {
          Authorization: token ? `Bearer ${token}` : "",
          "Content-Type": "application/json",
        },
        body: body ? JSON.stringify(body) : undefined,
      });

    const res = retry ? await withRetry(doFetch) : await doFetch();
    return handleLegacyResponse<T>(res);
  },

  /**
   * DELETE request with auth (no retry by default)
   */
  async delete<T>(
    endpoint: string,
    retry = false
  ): Promise<LegacyApiResponse<T>> {
    const token = getLegacyAuthToken();
    const doFetch = () =>
      fetch(`${API_BASE_URL || DEFAULT_API_BASE_URL}${endpoint}`, {
        method: "DELETE",
        headers: {
          Authorization: token ? `Bearer ${token}` : "",
          "Content-Type": "application/json",
        },
      });

    const res = retry ? await withRetry(doFetch) : await doFetch();
    return handleLegacyResponse<T>(res);
  },
};

// --- Legacy fetchWithAuth ---

/**
 * Legacy compatible fetch with auth and retry
 * @deprecated Use api.get/post from ApiClient instead
 *
 * Security Note (P0 Hardening):
 * - Removed X-Admin-Mode header from client side
 * - Admin verification must be done server-side via session/JWT
 * - X-User-Id is kept for development auth bypass (controlled by backend config)
 */
export async function fetchWithAuth<T>(
  url: string,
  options: RequestInit = {},
  retryConfig: Partial<RetryConfig> = {}
): Promise<T> {
  const token = getLegacyAuthToken();
  const fullUrl = url.startsWith("http")
    ? url
    : `${API_BASE_URL || DEFAULT_API_BASE_URL}${url}`;

  // Dev-only X-User-Id header (backend validates ENABLE_DEV_AUTH_BYPASS)
  const userId =
    typeof window !== "undefined"
      ? localStorage.getItem("userId") || "demo-user"
      : "demo-user";

  const doFetch = () =>
    fetch(fullUrl, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: token ? `Bearer ${token}` : "",
        "Content-Type": "application/json",
        "X-User-Id": userId,
        // P0 Security: X-Admin-Mode removed - admin rights verified server-side only
      },
    });

  const res = await withRetry(doFetch, retryConfig);

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));

    // 한국어 에러 메시지
    if (res.status === 401) {
      throw new Error("인증이 필요합니다. 로그인해주세요.");
    }
    if (res.status === 403) {
      throw new Error("권한이 없습니다. 관리자에게 문의하세요.");
    }
    if (res.status === 503 || error.detail?.includes?.("Circuit")) {
      throw new Error(
        "서비스가 일시적으로 불안정합니다. 잠시 후 다시 시도해주세요."
      );
    }
    if (res.status === 429) {
      throw new Error("요청이 너무 많습니다. 잠시 후 다시 시도해주세요.");
    }

    throw new Error(error.detail || `오류: ${res.status}`);
  }

  return res.json();
}

// --- Retry Hook for UI ---

export interface UseRetryOptions {
  maxRetries?: number;
  onRetry?: (attempt: number, error: Error) => void;
}

/**
 * Simple retry wrapper for component-level retry
 */
export async function retryAsync<T>(
  fn: () => Promise<T>,
  options: UseRetryOptions = {}
): Promise<T> {
  const { maxRetries = 3, onRetry } = options;
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      if (attempt < maxRetries) {
        onRetry?.(attempt + 1, lastError);
        await sleep(1000 * Math.pow(2, attempt));
      }
    }
  }

  throw lastError;
}

// --- Tool Recommendation Types (IP-First Phase 2.5) ---

export interface ToolRecommendation {
  tool_id: string;
  display_name: string;
  dimension: string;
  confidence: number;
  confidence_level: "high" | "medium" | "low";
  reason_codes: string[];
  evidence_refs: string[];
  estimated_credits: number;
  priority: number;
  description?: string;
}

export interface ToolRecommendationResponse {
  recommendations: ToolRecommendation[];
  total_estimated_credits: number;
  workflow_suggested: boolean;
  reason_summary: string;
  ip_context_used: boolean;
  trace_id?: string;
}

export interface ToolRecommendationRequest {
  ip_id?: string;
  preset_id?: string;
  scene_type?: string;
  user_history?: string[];
  dimension_context?: string;
  max_results?: number;
}

export interface ToolEvidenceResponse {
  tool_id: string;
  evidence_refs: string[];
  datasets_used: string[];
  reason_codes: string[];
  confidence: number;
  confidence_level: "high" | "medium" | "low";
}

export interface ToolDisplayInfo {
  tool_id: string;
  display_name_ko: string;
  display_name_en: string;
  dimension: string;
  description_ko: string;
  description_en: string;
  icon: string;
  base_credits: number;
}

// --- Tool Recommendation API namespace ---

export const toolsApi = {
  /**
   * Get tool recommendations based on context
   */
  async recommend(
    request: ToolRecommendationRequest
  ): Promise<LegacyApiResponse<ToolRecommendationResponse>> {
    return simpleApi.post<ToolRecommendationResponse>(
      "/api/v1/tools/recommend",
      request
    );
  },

  /**
   * Get recommendations for an IP by slug
   */
  async getIPRecommendations(
    slug: string,
    options?: {
      sceneType?: string;
      dimensionContext?: string;
      maxResults?: number;
    }
  ): Promise<LegacyApiResponse<ToolRecommendationResponse>> {
    const params = new URLSearchParams();
    if (options?.sceneType) params.set("scene_type", options.sceneType);
    if (options?.dimensionContext)
      params.set("dimension_context", options.dimensionContext);
    if (options?.maxResults)
      params.set("max_results", options.maxResults.toString());

    const query = params.toString() ? `?${params.toString()}` : "";
    return simpleApi.get<ToolRecommendationResponse>(
      `/api/v1/tools/ip/${encodeURIComponent(slug)}/recommendations${query}`
    );
  },

  /**
   * Get evidence for a tool selection
   */
  async getToolEvidence(
    toolId: string,
    ipId?: string
  ): Promise<LegacyApiResponse<ToolEvidenceResponse>> {
    const params = new URLSearchParams();
    if (ipId) params.set("ip_id", ipId);

    const query = params.toString() ? `?${params.toString()}` : "";
    return simpleApi.get<ToolEvidenceResponse>(
      `/api/v1/tools/${encodeURIComponent(toolId)}/evidence${query}`
    );
  },

  /**
   * List all available tools
   */
  async listTools(options?: {
    dimension?: string;
    stage?: string;
  }): Promise<LegacyApiResponse<ToolDisplayInfo[]>> {
    const params = new URLSearchParams();
    if (options?.dimension) params.set("dimension", options.dimension);
    if (options?.stage) params.set("stage", options.stage);

    const query = params.toString() ? `?${params.toString()}` : "";
    return simpleApi.get<ToolDisplayInfo[]>(`/api/v1/tools/list${query}`);
  },

  /**
   * Get info for a specific tool
   */
  async getToolInfo(
    toolId: string
  ): Promise<LegacyApiResponse<ToolDisplayInfo>> {
    return simpleApi.get<ToolDisplayInfo>(
      `/api/v1/tools/${encodeURIComponent(toolId)}/info`
    );
  },
};
