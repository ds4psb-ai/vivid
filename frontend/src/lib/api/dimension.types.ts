/**
 * Dimension API Types
 * 
 * Types for dimension tools, capsule runs, and storyboard generation.
 */

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
    director_pack?: Record<string, unknown>;
    scene_overrides?: Record<string, Record<string, unknown>>;
    narrative_arc?: Record<string, unknown>;
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

// Singularity (특이점) Types
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

// Intent Preset Types
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
