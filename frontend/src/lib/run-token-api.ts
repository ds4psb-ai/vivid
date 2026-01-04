/**
 * Run Token API Client
 * 
 * 앱 실행 토큰 API 호출 함수
 */

// ============================================
// Types
// ============================================

export interface IssueTokenRequest {
    appId: string;
    creditsToReserve?: number;
    permissions?: string[];
}

export interface IssueTokenResponse {
    success: boolean;
    token?: string;
    runId?: string;
    expiresAt?: string;
    creditsReserved?: number;
    error?: string;
}

export interface ValidateTokenResponse {
    valid: boolean;
    userId?: string;
    appId?: string;
    runId?: string;
    creditsReserved?: number;
    creditsUsed?: number;
    creditsRemaining?: number;
    permissions?: string[];
    error?: string;
}

export interface DeductCreditsResponse {
    success: boolean;
    creditsUsed?: number;
    creditsRemaining?: number;
    error?: string;
}

export interface RefundCreditsResponse {
    success: boolean;
    refunded?: number;
    error?: string;
}

export interface RunStatus {
    runId: string;
    userId: string;
    appId: string;
    status: string;
    creditsReserved: number;
    creditsUsed: number;
    creditsRemaining: number;
    issuedAt: string;
    expiresAt: string;
}

// ============================================
// API Functions
// ============================================

/**
 * Run Token 발급
 */
export async function issueRunToken(request: IssueTokenRequest): Promise<IssueTokenResponse> {
    const response = await fetch("/api/v1/run-token/issue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
            app_id: request.appId,
            credits_to_reserve: request.creditsToReserve || 0,
            permissions: request.permissions || [],
        }),
    });

    if (!response.ok) {
        return { success: false, error: `Request failed: ${response.status}` };
    }

    const data = await response.json();
    return {
        success: data.success,
        token: data.token,
        runId: data.run_id,
        expiresAt: data.expires_at,
        creditsReserved: data.credits_reserved,
        error: data.error,
    };
}

/**
 * Run Token 검증
 */
export async function validateRunToken(token: string): Promise<ValidateTokenResponse> {
    const response = await fetch("/api/v1/run-token/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ token }),
    });

    if (!response.ok) {
        return { valid: false, error: `Request failed: ${response.status}` };
    }

    const data = await response.json();
    return {
        valid: data.valid,
        userId: data.user_id,
        appId: data.app_id,
        runId: data.run_id,
        creditsReserved: data.credits_reserved,
        creditsUsed: data.credits_used,
        creditsRemaining: data.credits_remaining,
        permissions: data.permissions,
        error: data.error,
    };
}

/**
 * 크레딧 차감
 */
export async function deductCredits(
    runId: string,
    token: string,
    amount: number,
    reason: string = "usage"
): Promise<DeductCreditsResponse> {
    const response = await fetch(`/api/v1/run-token/${runId}/deduct`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
        },
        credentials: "include",
        body: JSON.stringify({ amount, reason }),
    });

    if (!response.ok) {
        return { success: false, error: `Request failed: ${response.status}` };
    }

    const data = await response.json();
    return {
        success: data.success,
        creditsUsed: data.credits_used,
        creditsRemaining: data.credits_remaining,
        error: data.error,
    };
}

/**
 * 크레딧 환불
 */
export async function refundCredits(
    runId: string,
    token: string,
    amount?: number
): Promise<RefundCreditsResponse> {
    const response = await fetch(`/api/v1/run-token/${runId}/refund`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
        },
        credentials: "include",
        body: JSON.stringify({ amount }),
    });

    if (!response.ok) {
        return { success: false, error: `Request failed: ${response.status}` };
    }

    const data = await response.json();
    return {
        success: data.success,
        refunded: data.refunded,
        error: data.error,
    };
}

/**
 * 토큰 취소
 */
export async function revokeRunToken(runId: string, token: string): Promise<{ success: boolean; error?: string }> {
    const response = await fetch(`/api/v1/run-token/${runId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` },
        credentials: "include",
    });

    if (!response.ok) {
        return { success: false, error: `Request failed: ${response.status}` };
    }

    return { success: true };
}

/**
 * 실행 상태 조회
 */
export async function getRunStatus(runId: string, token: string): Promise<RunStatus | null> {
    const response = await fetch(`/api/v1/run-token/${runId}/status`, {
        headers: { "Authorization": `Bearer ${token}` },
        credentials: "include",
    });

    if (!response.ok) {
        return null;
    }

    const data = await response.json();
    return {
        runId: data.run_id,
        userId: data.user_id,
        appId: data.app_id,
        status: data.status,
        creditsReserved: data.credits_reserved,
        creditsUsed: data.credits_used,
        creditsRemaining: data.credits_remaining,
        issuedAt: data.issued_at,
        expiresAt: data.expires_at,
    };
}
