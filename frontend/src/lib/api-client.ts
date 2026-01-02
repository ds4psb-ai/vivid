/**
 * Centralized API Client
 * 
 * Single source of truth for all API calls:
 * - Auto-injects auth token
 * - Standardized error handling
 * - Type-safe responses
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// =============================================================================
// Types
// =============================================================================

export interface ApiError {
    status: number;
    message: string;
    detail?: any;
}

export interface ApiResponse<T> {
    data: T | null;
    error: ApiError | null;
    ok: boolean;
}

// =============================================================================
// Core Functions
// =============================================================================

function getAuthToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("token");
}

async function handleResponse<T>(res: Response): Promise<ApiResponse<T>> {
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        return {
            data: null,
            error: {
                status: res.status,
                message: error.detail || error.message || `Error: ${res.status}`,
                detail: error,
            },
            ok: false,
        };
    }

    const data = await res.json();
    return { data, error: null, ok: true };
}

// =============================================================================
// API Client
// =============================================================================

export const api = {
    /**
     * GET request with auth
     */
    async get<T>(endpoint: string): Promise<ApiResponse<T>> {
        const token = getAuthToken();
        const res = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                Authorization: token ? `Bearer ${token}` : "",
                "Content-Type": "application/json",
            },
        });
        return handleResponse<T>(res);
    },

    /**
     * POST request with auth
     */
    async post<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
        const token = getAuthToken();
        const res = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: "POST",
            headers: {
                Authorization: token ? `Bearer ${token}` : "",
                "Content-Type": "application/json",
            },
            body: body ? JSON.stringify(body) : undefined,
        });
        return handleResponse<T>(res);
    },

    /**
     * PUT request with auth
     */
    async put<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
        const token = getAuthToken();
        const res = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: "PUT",
            headers: {
                Authorization: token ? `Bearer ${token}` : "",
                "Content-Type": "application/json",
            },
            body: body ? JSON.stringify(body) : undefined,
        });
        return handleResponse<T>(res);
    },

    /**
     * DELETE request with auth
     */
    async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
        const token = getAuthToken();
        const res = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: "DELETE",
            headers: {
                Authorization: token ? `Bearer ${token}` : "",
                "Content-Type": "application/json",
            },
        });
        return handleResponse<T>(res);
    },
};

// =============================================================================
// Convenience Functions
// =============================================================================

/**
 * Legacy compatible fetch with auth (for gradual migration)
 * @deprecated Use api.get/post instead
 */
export async function fetchWithAuth<T>(
    url: string,
    options: RequestInit = {}
): Promise<T> {
    const token = getAuthToken();
    const res = await fetch(url.startsWith("http") ? url : `${API_BASE_URL}${url}`, {
        ...options,
        headers: {
            ...options.headers,
            Authorization: token ? `Bearer ${token}` : "",
            "Content-Type": "application/json",
        },
    });

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || `Error: ${res.status}`);
    }

    return res.json();
}

export default api;
