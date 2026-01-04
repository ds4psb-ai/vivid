/**
 * Telemetry API Client
 * 
 * Complete TypeScript API client for telemetry endpoints
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

// =============================================================================
// Types
// =============================================================================

export type ToolTier = "experimental" | "verified" | "certified";
export type SafetyRating = "safe" | "review" | "restricted";
export type RunStatus = "started" | "success" | "failed" | "timeout";

export interface ToolManifest {
    id: string;
    tool_key: string;
    display_name: string;
    description: string;
    version: string;
    category: string;
    tier: ToolTier;
    input_schema: Record<string, unknown>;
    output_schema: Record<string, unknown>;
    credit_cost: number;
    fork_count: number;
    usage_count: number;
    total_revenue: number;
    parent_tool_id: string | null;
    fork_depth: number;
    created_by: string;
    approved_at: string | null;
    safety_rating: SafetyRating;
    sandbox_required: boolean;
    is_active: boolean;
    test_pass_rate: number | null;
    quality_rating: number | null;
    human_cloud_success_rate: number | null;
    created_at: string;
    updated_at: string;
}

export interface ToolRunEvent {
    id: string;
    tool_id: string;
    tool_key: string;
    tool_version: string;
    user_id: string | null;
    session_id: string | null;
    status: RunStatus;
    inputs_summary: Record<string, unknown>;
    outputs_summary: Record<string, unknown>;
    error_message: string | null;
    latency_ms: number | null;
    token_usage: Record<string, number>;
    cost_usd_est: number | null;
    credits_charged: number;
    credits_refunded: number;
    user_rating: number | null;
    user_feedback: string | null;
    canvas_id: string | null;
    workflow_position: number | null;
    previous_tool_id: string | null;
    created_at: string;
    completed_at: string | null;
}

export interface ForkEvent {
    id: string;
    parent_tool_id: string;
    child_tool_id: string;
    fork_depth: number;
    forker_id: string;
    fork_reason: string | null;
    diff_lines_added: number;
    diff_lines_removed: number;
    diff_lines_modified: number;
    diff_score: number;
    test_passed: boolean;
    test_run_at: string | null;
    attribution_score: number;
    attribution_calculated_at: string | null;
    revenue_generated: number;
    revenue_shared: number;
    is_suspicious: boolean;
    suspicion_reason: string | null;
    created_at: string;
    updated_at: string;
}

export interface AttributionScore {
    fork_id: string;
    tool_id: string;
    diff_score: number;
    test_score: number;
    usage_score: number;
    revenue_score: number;
    quality_score: number;
    total_score: number;
    weights: {
        diff: number;
        test: number;
        usage: number;
        revenue: number;
        quality: number;
    };
    calculated_at: string;
}

export interface DashboardOverview {
    period_days: number;
    tools: {
        by_tier: Record<string, number>;
        total: number;
        top: Array<{ tool_key: string; usage_count: number }>;
    };
    runs: {
        total: number;
        successful: number;
        success_rate: number;
        revenue_credits: number;
    };
    forks: {
        total: number;
        suspicious: number;
    };
}

export interface CategoryStats {
    period_days: number;
    categories: Array<{
        category: string;
        tool_count: number;
        total_usage: number;
        total_revenue: number;
        avg_rating: number | null;
    }>;
}

// =============================================================================
// API Functions
// =============================================================================

async function fetchWithAuth<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    });

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || `API Error: ${res.status}`);
    }

    return res.json();
}

// Tools
export async function listTools(params?: {
    category?: string;
    tier?: ToolTier;
    created_by?: string;
    limit?: number;
}): Promise<ToolManifest[]> {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.set("category", params.category);
    if (params?.tier) searchParams.set("tier", params.tier);
    if (params?.created_by) searchParams.set("created_by", params.created_by);
    if (params?.limit) searchParams.set("limit", params.limit.toString());

    return fetchWithAuth(`/api/v1/telemetry/tools?${searchParams}`);
}

export async function getTool(toolKey: string): Promise<ToolManifest> {
    return fetchWithAuth(`/api/v1/telemetry/tools/${toolKey}`);
}

export async function createTool(data: {
    tool_key: string;
    display_name: string;
    description: string;
    category: string;
    credit_cost?: number;
    input_schema?: Record<string, unknown>;
    output_schema?: Record<string, unknown>;
    system_prompt?: string;
    parent_tool_id?: string;
}): Promise<ToolManifest> {
    return fetchWithAuth("/api/v1/telemetry/tools", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

export async function getToolAnalytics(
    toolId: string,
    days = 30
): Promise<{
    tool_id: string;
    tool_key: string;
    total_runs: number;
    successful_runs: number;
    success_rate: number;
    avg_latency_ms: number | null;
    total_credits: number;
    avg_rating: number | null;
    fork_count: number;
    tier: ToolTier;
}> {
    return fetchWithAuth(`/api/v1/telemetry/tools/${toolId}/analytics?days=${days}`);
}

// Runs
export async function listRuns(params?: {
    tool_key?: string;
    status?: RunStatus;
    limit?: number;
}): Promise<ToolRunEvent[]> {
    const searchParams = new URLSearchParams();
    if (params?.tool_key) searchParams.set("tool_key", params.tool_key);
    if (params?.status) searchParams.set("status", params.status);
    if (params?.limit) searchParams.set("limit", params.limit.toString());

    return fetchWithAuth(`/api/v1/telemetry/runs?${searchParams}`);
}

export async function submitRunFeedback(
    eventId: string,
    rating: number,
    feedback?: string
): Promise<ToolRunEvent> {
    return fetchWithAuth(`/api/v1/telemetry/runs/${eventId}/feedback`, {
        method: "POST",
        body: JSON.stringify({ rating, feedback }),
    });
}

// Forks
export async function listForks(params?: {
    parent_tool_id?: string;
    is_suspicious?: boolean;
    limit?: number;
}): Promise<ForkEvent[]> {
    const searchParams = new URLSearchParams();
    if (params?.parent_tool_id) searchParams.set("parent_tool_id", params.parent_tool_id);
    if (params?.is_suspicious !== undefined)
        searchParams.set("is_suspicious", params.is_suspicious.toString());
    if (params?.limit) searchParams.set("limit", params.limit.toString());

    return fetchWithAuth(`/api/v1/telemetry/forks?${searchParams}`);
}

export async function createFork(data: {
    parent_tool_id: string;
    child_tool_id: string;
    fork_reason?: string;
    diff_lines_added: number;
    diff_lines_removed: number;
    diff_lines_modified: number;
}): Promise<ForkEvent> {
    return fetchWithAuth("/api/v1/telemetry/forks", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

export async function calculateAttribution(forkId: string): Promise<AttributionScore> {
    return fetchWithAuth(`/api/v1/telemetry/forks/${forkId}/attribution`, {
        method: "POST",
    });
}

// Dashboard
export async function getDashboardOverview(days = 7): Promise<DashboardOverview> {
    return fetchWithAuth(`/api/v1/telemetry/dashboard/overview?days=${days}`);
}

export async function getCategoryStats(days = 30): Promise<CategoryStats> {
    return fetchWithAuth(`/api/v1/telemetry/dashboard/categories?days=${days}`);
}
