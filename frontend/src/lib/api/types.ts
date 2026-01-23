/**
 * API Core Types - Shared base types for all API modules
 * 
 * This module contains foundational types used across all API domains.
 * For domain-specific types, see the corresponding module (e.g., ./canvas.types.ts)
 */

// Re-export from @xyflow/react for canvas types
export type { Edge, Node } from "@xyflow/react";

// Environment configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";
export const DEFAULT_API_BASE_URL = "http://127.0.0.1:8100";
export const USER_ID = process.env.NEXT_PUBLIC_USER_ID || "";
export const ADMIN_MODE = process.env.NEXT_PUBLIC_ADMIN_MODE || "";

// Base error interface
export interface ApiError {
    detail?: string;
}

// Authentication types
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

// Common pagination types
export interface PaginatedList<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
}

// Common stage summary (used in Pipeline, etc.)
export interface StageSummary {
    total: number;
    latest?: string | null;
}
