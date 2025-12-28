/**
 * Centralized Auth Utilities
 * 
 * Single source of truth for authentication-related URLs and constants.
 * Eliminates hardcoding and duplication across components.
 * 
 * @example
 * import { getAuthStartUrl, AUTH_ROUTES } from "@/lib/auth";
 * 
 * // Get Google OAuth start URL
 * const authUrl = getAuthStartUrl();
 * 
 * // Check if route requires auth
 * if (AUTH_ROUTES.PROTECTED.includes(pathname)) { ... }
 */

/**
 * Auth-related route constants
 */
export const AUTH_ROUTES = {
    /** Routes that require authentication (middleware enforced) */
    PROTECTED: ["/settings", "/billing", "/usage"] as const,

    /** Routes open to guests (no auth check) */
    PUBLIC: ["/", "/login", "/api", "/_next", "/images", "/favicon"] as const,

    /** Auth endpoints */
    ENDPOINTS: {
        GOOGLE_START: "/api/v1/auth/google/start",
        SESSION: "/api/v1/auth/me",
        LOGOUT: "/api/v1/auth/logout",
    },
} as const;

/**
 * Generates the Google OAuth start URL
 * 
 * @param returnTo - Optional path to redirect after successful login
 * @returns Full URL to initiate Google OAuth flow
 * 
 * @example
 * const url = getAuthStartUrl("/canvas");
 * // Returns: "http://localhost:8100/api/v1/auth/google/start" or based on NEXT_PUBLIC_API_URL
 */
export function getAuthStartUrl(returnTo?: string): string {
    const base = process.env.NEXT_PUBLIC_API_URL || "";
    const endpoint = AUTH_ROUTES.ENDPOINTS.GOOGLE_START;

    // Build URL
    const url = base ? `${base}${endpoint}` : endpoint;

    // If returnTo is provided and backend supports it, append as query param
    if (returnTo) {
        const separator = url.includes("?") ? "&" : "?";
        return `${url}${separator}return_to=${encodeURIComponent(returnTo)}`;
    }

    return url;
}

/**
 * Type for protected route paths
 */
export type ProtectedRoute = (typeof AUTH_ROUTES.PROTECTED)[number];

/**
 * Check if a given path requires authentication
 * 
 * @param pathname - The path to check
 * @returns True if the path requires authentication
 */
export function isProtectedRoute(pathname: string): boolean {
    return AUTH_ROUTES.PROTECTED.some((route) => pathname.startsWith(route));
}
