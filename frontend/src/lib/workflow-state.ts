/**
 * Workflow State Management
 *
 * 워크플로우 진행 상태를 세션 스토리지에 저장하고 관리합니다.
 * IP 상세 페이지에서 시작한 워크플로우의 컨텍스트를 각 Dimension 앱에서 사용할 수 있습니다.
 */

// =============================================================================
// Types
// =============================================================================

export interface WorkflowStep {
  app: string;
  href: string;
  badge: string;
  name_ko: string;
  name_en: string;
  titleKo?: string;
  title?: string;
}

export interface StepResult {
  completedAt: string;
  outputSummary?: string;
  outputData?: Record<string, unknown>;
  nextStepPrompt?: string;
}

export interface WorkflowState {
  ipSlug: string;
  workflowKey: string; // "character-variation" | "anime-mv" | "vertical-shortform" | ...
  currentStep: number;
  totalSteps: number;
  steps: WorkflowStep[];
  startedAt: string;
  results: Record<number, StepResult>; // 각 단계 결과 저장 (1-indexed)
  userPrompt?: string; // 초기 사용자 프롬프트
}

// =============================================================================
// Storage Key Helper
// =============================================================================

const STORAGE_PREFIX = "vivid-workflow-";

function getStorageKey(ipSlug: string): string {
  return `${STORAGE_PREFIX}${ipSlug}`;
}

// =============================================================================
// Public API
// =============================================================================

/**
 * 워크플로우 상태 저장
 */
export function saveWorkflowState(state: WorkflowState): void {
  if (typeof window === "undefined") return;

  try {
    const key = getStorageKey(state.ipSlug);
    sessionStorage.setItem(key, JSON.stringify(state));
  } catch (err) {
    console.error("Failed to save workflow state:", err);
  }
}

/**
 * 워크플로우 상태 조회
 */
export function getWorkflowState(ipSlug: string): WorkflowState | null {
  if (typeof window === "undefined") return null;

  try {
    const key = getStorageKey(ipSlug);
    const stored = sessionStorage.getItem(key);
    if (!stored) return null;

    return JSON.parse(stored) as WorkflowState;
  } catch (err) {
    console.error("Failed to get workflow state:", err);
    return null;
  }
}

/**
 * 현재 단계 업데이트
 */
export function updateCurrentStep(ipSlug: string, step: number): void {
  const state = getWorkflowState(ipSlug);
  if (!state) return;

  state.currentStep = step;
  saveWorkflowState(state);
}

/**
 * 단계 결과 저장
 */
export function updateStepResult(
  ipSlug: string,
  step: number,
  result: StepResult
): void {
  const state = getWorkflowState(ipSlug);
  if (!state) return;

  state.results[step] = result;
  // 현재 단계도 업데이트 (완료된 단계 + 1)
  if (step >= state.currentStep && step < state.totalSteps) {
    state.currentStep = step + 1;
  }
  saveWorkflowState(state);
}

/**
 * 워크플로우 상태 삭제
 */
export function clearWorkflowState(ipSlug: string): void {
  if (typeof window === "undefined") return;

  try {
    const key = getStorageKey(ipSlug);
    sessionStorage.removeItem(key);
  } catch (err) {
    console.error("Failed to clear workflow state:", err);
  }
}

/**
 * 특정 단계 완료 여부 확인
 */
export function isStepCompleted(ipSlug: string, step: number): boolean {
  const state = getWorkflowState(ipSlug);
  if (!state) return false;

  return !!state.results[step];
}

/**
 * 이전 단계의 결과 데이터 가져오기
 */
export function getPreviousStepResult(
  ipSlug: string,
  currentStep: number
): StepResult | null {
  if (currentStep <= 1) return null;

  const state = getWorkflowState(ipSlug);
  if (!state) return null;

  return state.results[currentStep - 1] || null;
}

/**
 * 다음 단계 정보 가져오기
 */
export function getNextStep(ipSlug: string): WorkflowStep | null {
  const state = getWorkflowState(ipSlug);
  if (!state) return null;

  const nextStepIndex = state.currentStep; // 0-indexed array, currentStep is 1-indexed
  if (nextStepIndex >= state.totalSteps) return null;

  return state.steps[nextStepIndex] || null;
}

/**
 * 워크플로우 진행률 계산 (0-100)
 */
export function getWorkflowProgress(ipSlug: string): number {
  const state = getWorkflowState(ipSlug);
  if (!state || state.totalSteps === 0) return 0;

  const completedCount = Object.keys(state.results).length;
  return Math.round((completedCount / state.totalSteps) * 100);
}

/**
 * 전체 워크플로우 완료 여부
 */
export function isWorkflowCompleted(ipSlug: string): boolean {
  const state = getWorkflowState(ipSlug);
  if (!state) return false;

  return Object.keys(state.results).length >= state.totalSteps;
}

/**
 * 단계 정보를 기반으로 전체 URL 생성
 */
export function buildStepUrl(
  step: WorkflowStep,
  ipSlug: string,
  stepNumber: number,
  workflowKey: string,
  userPrompt?: string
): string {
  const url = new URL(step.href, "http://placeholder");
  url.searchParams.set("ip", ipSlug);
  url.searchParams.set("step", String(stepNumber));
  url.searchParams.set("workflow", workflowKey);
  if (userPrompt) {
    url.searchParams.set("prompt", userPrompt);
  }
  return url.pathname + url.search;
}

/**
 * URL 쿼리 파라미터에서 워크플로우 정보 파싱
 */
export interface WorkflowUrlParams {
  ipSlug: string | null;
  step: number | null;
  workflowKey: string | null;
  prompt: string | null;
}

export function parseWorkflowUrlParams(
  searchParams: URLSearchParams
): WorkflowUrlParams {
  return {
    ipSlug: searchParams.get("ip"),
    step: searchParams.get("step") ? parseInt(searchParams.get("step")!, 10) : null,
    workflowKey: searchParams.get("workflow"),
    prompt: searchParams.get("prompt"),
  };
}

/**
 * 활성 워크플로우 목록 가져오기 (모든 IP 슬러그에서)
 */
export function getAllActiveWorkflows(): WorkflowState[] {
  if (typeof window === "undefined") return [];

  const workflows: WorkflowState[] = [];
  try {
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key?.startsWith(STORAGE_PREFIX)) {
        const data = sessionStorage.getItem(key);
        if (data) {
          workflows.push(JSON.parse(data));
        }
      }
    }
  } catch (err) {
    console.error("Failed to get all workflows:", err);
  }

  return workflows;
}
