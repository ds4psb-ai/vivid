/**
 * Admin API Client
 * 
 * 앱 관리 API 호출 함수
 */

import { api } from "@/lib/api";

// ============================================
// Types
// ============================================

export interface DimensionTheme {
    theme?: string;
    primaryColor?: string;
    accentColor?: string;
    borderStyle?: string;
}

export interface AppCredits {
    perRun?: number;
    perSave?: number;
    perMinute?: number;
}

export interface AppManifest {
    name: string;
    version: string;
    entry: string;
    description?: string;
    author?: string;
    dimension?: DimensionTheme;
    permissions?: string[];
    credits?: AppCredits;
    icon?: string;
    tags?: string[];
}

export interface ValidationResult {
    valid: boolean;
    errors: string[];
    warnings: string[];
}

export interface RegisteredApp {
    appId: string;
    name: string;
    version: string;
    status: string;
    createdAt: string;
    updatedAt: string;
    createdBy: string;
}

export interface AppDetail {
    appId: string;
    manifest: AppManifest;
    status: string;
    currentVersion: string;
    versions: Array<{
        version: string;
        buildHash: string;
        createdAt: string;
        status: string;
        notes?: string;
    }>;
    createdAt: string;
    updatedAt: string;
    createdBy: string;
    sandboxUrl: string;
}

export interface AppListResponse {
    apps: RegisteredApp[];
    total: number;
    limit: number;
    offset: number;
}

export interface RegisterResponse {
    success: boolean;
    appId?: string;
    error?: string;
    sandboxUrl?: string;
}

export interface BuildResponse {
    success: boolean;
    error?: string;
}

// ============================================
// API Functions
// ============================================

/**
 * 매니페스트 검증
 */
export async function validateManifest(manifest: AppManifest): Promise<ValidationResult> {
    const response = await fetch("/api/v1/admin/apps/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(manifest),
    });

    if (!response.ok) {
        throw new Error(`Validation failed: ${response.status}`);
    }

    return response.json();
}

/**
 * 앱 등록 (Base64 소스)
 */
export async function registerApp(
    manifest: AppManifest,
    sourceBase64: string
): Promise<RegisterResponse> {
    const response = await fetch("/api/v1/admin/apps/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ manifest, sourceBase64 }),
    });

    if (!response.ok) {
        return { success: false, error: `Request failed: ${response.status}` };
    }

    return response.json();
}

/**
 * 앱 등록 (파일 업로드)
 */
export async function registerAppWithFile(
    manifest: AppManifest,
    file: File
): Promise<RegisterResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("manifest_json", JSON.stringify(manifest));

    const response = await fetch("/api/v1/admin/apps/register/file", {
        method: "POST",
        credentials: "include",
        body: formData,
    });

    if (!response.ok) {
        return { success: false, error: `Request failed: ${response.status}` };
    }

    return response.json();
}

/**
 * 앱 빌드 (난독화 + SDK 주입)
 */
export async function buildApp(appId: string): Promise<BuildResponse> {
    const response = await fetch(`/api/v1/admin/apps/${appId}/build`, {
        method: "POST",
        credentials: "include",
    });

    if (!response.ok) {
        return { success: false, error: `Build failed: ${response.status}` };
    }

    return response.json();
}

/**
 * 앱 목록
 */
export async function listApps(options?: {
    status?: string;
    limit?: number;
    offset?: number;
}): Promise<AppListResponse> {
    const params = new URLSearchParams();
    if (options?.status) params.append("status", options.status);
    if (options?.limit) params.append("limit", String(options.limit));
    if (options?.offset) params.append("offset", String(options.offset));

    const response = await fetch(`/api/v1/admin/apps?${params}`, {
        credentials: "include",
    });

    if (!response.ok) {
        throw new Error(`List failed: ${response.status}`);
    }

    return response.json();
}

/**
 * 앱 상세
 */
export async function getApp(appId: string): Promise<AppDetail> {
    const response = await fetch(`/api/v1/admin/apps/${appId}`, {
        credentials: "include",
    });

    if (!response.ok) {
        throw new Error(`Get failed: ${response.status}`);
    }

    return response.json();
}

/**
 * 앱 상태 변경
 */
export async function updateAppStatus(
    appId: string,
    status: string
): Promise<BuildResponse> {
    const response = await fetch(`/api/v1/admin/apps/${appId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ status }),
    });

    if (!response.ok) {
        return { success: false, error: `Update failed: ${response.status}` };
    }

    return response.json();
}

/**
 * 앱 삭제
 */
export async function deleteApp(appId: string): Promise<BuildResponse> {
    const response = await fetch(`/api/v1/admin/apps/${appId}`, {
        method: "DELETE",
        credentials: "include",
    });

    if (!response.ok) {
        return { success: false, error: `Delete failed: ${response.status}` };
    }

    return response.json();
}

/**
 * 미리보기 URL
 */
export async function getPreviewUrl(appId: string): Promise<{
    previewUrl: string;
    expiresIn: number;
}> {
    const response = await fetch(`/api/v1/admin/apps/${appId}/preview-url`, {
        credentials: "include",
    });

    if (!response.ok) {
        throw new Error(`Preview failed: ${response.status}`);
    }

    return response.json();
}

/**
 * 파일을 Base64로 변환
 */
export function fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const result = reader.result as string;
            // data:application/zip;base64,... -> base64 부분만 추출
            const base64 = result.split(",")[1];
            resolve(base64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}
