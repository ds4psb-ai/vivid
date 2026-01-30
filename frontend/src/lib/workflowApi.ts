/**
 * Workflow API Client
 *
 * Phase 2-2: Quick Generate를 위한 워크플로우 API 클라이언트
 * 기존 backend /workflow/* 엔드포인트를 활용합니다.
 *
 * Endpoints:
 * - POST /workflow/plan - 워크플로우 계획
 * - POST /workflow/session/{id}/start - 세션 시작 (크레딧 예약)
 * - POST /workflow/session/{id}/execute - 전체 실행
 * - GET /workflow/session/{id} - 상태 조회
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

// =============================================================================
// Types
// =============================================================================

export interface WorkflowPlanRequest {
  appId: string;
  inputs: Record<string, unknown>;
  auteurKey?: string;
  targetPlatform?: string;
}

export interface WorkflowPlanStep {
  stepId: string;
  label: string;
  estimatedCreditCost: number;
  required: boolean;
  inputs: string[];
  outputs: string[];
}

export interface WorkflowPlanResponse {
  success: boolean;
  sessionId: string;
  steps: WorkflowPlanStep[];
  totalEstimatedCredits: number;
  estimatedDurationSeconds: number;
}

export interface WorkflowStartRequest {
  reserveCredits?: boolean;
}

export interface WorkflowStartResponse {
  success: boolean;
  sessionId: string;
  reservedCredits: number;
  status: "ready" | "insufficient_credits" | "error";
  error?: string;
}

export interface WorkflowExecuteRequest {
  parallel?: boolean;
  stopOnError?: boolean;
}

export interface WorkflowStepResult {
  stepId: string;
  status: "completed" | "error" | "skipped";
  output?: Record<string, unknown>;
  creditUsed: number;
  durationMs: number;
  error?: string;
}

export interface WorkflowExecuteResponse {
  success: boolean;
  sessionId: string;
  status: "completed" | "partial" | "failed";
  steps: WorkflowStepResult[];
  totalCreditsUsed: number;
  refundedCredits: number;
  durationMs: number;
  error?: string;
}

export interface WorkflowStatusResponse {
  sessionId: string;
  appId: string;
  status: "planning" | "ready" | "running" | "completed" | "failed";
  currentStepIndex: number;
  totalSteps: number;
  steps: Array<{
    stepId: string;
    status: "pending" | "running" | "completed" | "error" | "skipped";
    creditUsed?: number;
  }>;
  totalCreditsUsed: number;
  startedAt?: string;
  completedAt?: string;
  error?: string;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Plan a workflow execution
 * Creates a session and estimates credit cost
 */
export async function plan(request: WorkflowPlanRequest): Promise<WorkflowPlanResponse> {
  const response = await fetch(`${API_BASE}/api/workflow/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Start a workflow session (reserve credits)
 */
export async function start(
  sessionId: string,
  request: WorkflowStartRequest = {}
): Promise<WorkflowStartResponse> {
  const response = await fetch(
    `${API_BASE}/api/workflow/session/${sessionId}/start`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));

    // Handle 402 Payment Required
    if (response.status === 402) {
      return {
        success: false,
        sessionId,
        reservedCredits: 0,
        status: "insufficient_credits",
        error: errorData.detail || "크레딧이 부족합니다",
      };
    }

    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Execute all steps in a workflow session
 */
export async function executeAll(
  sessionId: string,
  request: WorkflowExecuteRequest = {}
): Promise<WorkflowExecuteResponse> {
  const response = await fetch(
    `${API_BASE}/api/workflow/session/${sessionId}/execute`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Get workflow session status
 */
export async function getStatus(sessionId: string): Promise<WorkflowStatusResponse> {
  const response = await fetch(
    `${API_BASE}/api/workflow/session/${sessionId}`,
    {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Cancel a running workflow session
 */
export async function cancel(sessionId: string): Promise<{ success: boolean; refundedCredits: number }> {
  const response = await fetch(
    `${API_BASE}/api/workflow/session/${sessionId}/cancel`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// =============================================================================
// High-Level Helpers
// =============================================================================

/**
 * Execute a complete workflow in one call
 * Handles planning, starting, and executing
 */
export async function executeWorkflow(
  request: WorkflowPlanRequest,
  onProgress?: (status: WorkflowStatusResponse) => void
): Promise<WorkflowExecuteResponse> {
  // Step 1: Plan
  const planResult = await plan(request);

  // Step 2: Start (reserve credits)
  const startResult = await start(planResult.sessionId, { reserveCredits: true });

  if (!startResult.success || startResult.status === "insufficient_credits") {
    throw new Error(startResult.error || "크레딧이 부족합니다");
  }

  // Step 3: Execute
  const executeResult = await executeAll(planResult.sessionId);

  // Report final status if callback provided
  if (onProgress) {
    const status = await getStatus(planResult.sessionId);
    onProgress(status);
  }

  return executeResult;
}

// =============================================================================
// Export
// =============================================================================

export const workflowApi = {
  plan,
  start,
  executeAll,
  getStatus,
  cancel,
  executeWorkflow,
};

export default workflowApi;
