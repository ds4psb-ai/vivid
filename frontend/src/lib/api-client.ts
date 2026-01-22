/**
 * Centralized API Client
 * 
 * P4.2 Enhanced with:
 * - Retry with exponential backoff
 * - Circuit breaker awareness
 * - Retryable error detection
 * - Max attempts configurable
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

// =============================================================================
// Types
// =============================================================================

export interface ApiError {
    status: number;
    message: string;
    detail?: unknown;
    isRetryable?: boolean;
}

export interface ApiResponse<T> {
    data: T | null;
    error: ApiError | null;
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

// =============================================================================
// Retry Utilities
// =============================================================================

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

// =============================================================================
// Core Functions
// =============================================================================

function getAuthToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("token");
}

function enrichError(res: Response, error: unknown): ApiError {
    const err = error as Record<string, unknown> | null;
    const detail = typeof err?.detail === "string" ? err.detail : undefined;
    const message = typeof err?.message === "string" ? err.message : undefined;

    const isCircuitOpen = detail?.includes?.("Circuit") ||
        message?.includes?.("Circuit");

    return {
        status: res.status,
        message: isCircuitOpen
            ? "서비스가 일시적으로 불안정합니다. 잠시 후 다시 시도해주세요."
            : detail || message || `Error: ${res.status}`,
        detail: error,
        isRetryable: isRetryableError(res.status),
    };
}

async function handleResponse<T>(res: Response): Promise<ApiResponse<T>> {
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        return {
            data: null,
            error: enrichError(res, error),
            ok: false,
        };
    }

    const data = await res.json();
    return { data, error: null, ok: true };
}

// =============================================================================
// API Client with Retry
// =============================================================================

export const api = {
    /**
     * GET request with auth and retry
     */
    async get<T>(endpoint: string, retry = true): Promise<ApiResponse<T>> {
        const token = getAuthToken();
        const doFetch = () => fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                Authorization: token ? `Bearer ${token}` : "",
                "Content-Type": "application/json",
            },
        });

        const res = retry ? await withRetry(doFetch) : await doFetch();
        return handleResponse<T>(res);
    },

    /**
     * POST request with auth and retry
     */
    async post<T>(endpoint: string, body?: unknown, retry = true): Promise<ApiResponse<T>> {
        const token = getAuthToken();
        const doFetch = () => fetch(`${API_BASE_URL}${endpoint}`, {
            method: "POST",
            headers: {
                Authorization: token ? `Bearer ${token}` : "",
                "Content-Type": "application/json",
            },
            body: body ? JSON.stringify(body) : undefined,
        });

        const res = retry ? await withRetry(doFetch) : await doFetch();
        return handleResponse<T>(res);
    },

    /**
     * PUT request with auth and retry
     */
    async put<T>(endpoint: string, body?: unknown, retry = true): Promise<ApiResponse<T>> {
        const token = getAuthToken();
        const doFetch = () => fetch(`${API_BASE_URL}${endpoint}`, {
            method: "PUT",
            headers: {
                Authorization: token ? `Bearer ${token}` : "",
                "Content-Type": "application/json",
            },
            body: body ? JSON.stringify(body) : undefined,
        });

        const res = retry ? await withRetry(doFetch) : await doFetch();
        return handleResponse<T>(res);
    },

    /**
     * DELETE request with auth (no retry by default)
     */
    async delete<T>(endpoint: string, retry = false): Promise<ApiResponse<T>> {
        const token = getAuthToken();
        const doFetch = () => fetch(`${API_BASE_URL}${endpoint}`, {
            method: "DELETE",
            headers: {
                Authorization: token ? `Bearer ${token}` : "",
                "Content-Type": "application/json",
            },
        });

        const res = retry ? await withRetry(doFetch) : await doFetch();
        return handleResponse<T>(res);
    },
};

// =============================================================================
// Convenience Functions
// =============================================================================

/**
 * Legacy compatible fetch with auth and retry
 * @deprecated Use api.get/post instead
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
    const token = getAuthToken();
    const fullUrl = url.startsWith("http") ? url : `${API_BASE_URL}${url}`;

    // Dev-only X-User-Id header (backend validates ENABLE_DEV_AUTH_BYPASS)
    const userId = typeof window !== "undefined" ? localStorage.getItem("userId") || "demo-user" : "demo-user";

    const doFetch = () => fetch(fullUrl, {
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
            throw new Error("서비스가 일시적으로 불안정합니다. 잠시 후 다시 시도해주세요.");
        }
        if (res.status === 429) {
            throw new Error("요청이 너무 많습니다. 잠시 후 다시 시도해주세요.");
        }

        throw new Error(error.detail || `오류: ${res.status}`);
    }

    return res.json();
}

// =============================================================================
// Retry Hook for UI
// =============================================================================

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

// =============================================================================
// Tool Recommendation API (IP-First Phase 2.5)
// =============================================================================

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

/**
 * Tool Recommendation API namespace
 */
export const toolsApi = {
    /**
     * Get tool recommendations based on context
     */
    async recommend(
        request: ToolRecommendationRequest
    ): Promise<ApiResponse<ToolRecommendationResponse>> {
        return api.post<ToolRecommendationResponse>(
            "/api/v1/tools/recommend",
            request
        );
    },

    /**
     * Get recommendations for an IP by slug
     */
    async getIPRecommendations(
        slug: string,
        options?: { sceneType?: string; dimensionContext?: string; maxResults?: number }
    ): Promise<ApiResponse<ToolRecommendationResponse>> {
        const params = new URLSearchParams();
        if (options?.sceneType) params.set("scene_type", options.sceneType);
        if (options?.dimensionContext) params.set("dimension_context", options.dimensionContext);
        if (options?.maxResults) params.set("max_results", options.maxResults.toString());

        const query = params.toString() ? `?${params.toString()}` : "";
        return api.get<ToolRecommendationResponse>(
            `/api/v1/tools/ip/${encodeURIComponent(slug)}/recommendations${query}`
        );
    },

    /**
     * Get evidence for a tool selection
     */
    async getToolEvidence(
        toolId: string,
        ipId?: string
    ): Promise<ApiResponse<ToolEvidenceResponse>> {
        const params = new URLSearchParams();
        if (ipId) params.set("ip_id", ipId);

        const query = params.toString() ? `?${params.toString()}` : "";
        return api.get<ToolEvidenceResponse>(
            `/api/v1/tools/${encodeURIComponent(toolId)}/evidence${query}`
        );
    },

    /**
     * List all available tools
     */
    async listTools(options?: {
        dimension?: string;
        stage?: string;
    }): Promise<ApiResponse<ToolDisplayInfo[]>> {
        const params = new URLSearchParams();
        if (options?.dimension) params.set("dimension", options.dimension);
        if (options?.stage) params.set("stage", options.stage);

        const query = params.toString() ? `?${params.toString()}` : "";
        return api.get<ToolDisplayInfo[]>(`/api/v1/tools/list${query}`);
    },

    /**
     * Get info for a specific tool
     */
    async getToolInfo(toolId: string): Promise<ApiResponse<ToolDisplayInfo>> {
        return api.get<ToolDisplayInfo>(
            `/api/v1/tools/${encodeURIComponent(toolId)}/info`
        );
    },
};

export default api;
