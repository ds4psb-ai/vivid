"use client";

/**
 * Workflow Step Navigation
 *
 * Dimension 앱에서 사용하는 워크플로우 단계 네비게이션 컴포넌트입니다.
 * - 현재 단계 진행률 표시
 * - 이전/다음 단계 버튼
 * - IP 컨텍스트 유지
 */

import React, { useMemo, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, ArrowRight, CheckCircle2, Home, RotateCcw } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  getWorkflowState,
  updateStepResult,
  buildStepUrl,
  parseWorkflowUrlParams,
  getWorkflowProgress,
  isStepCompleted,
  clearWorkflowState,
  type StepResult,
  type WorkflowStep,
} from "@/lib/workflow-state";

// =============================================================================
// Types
// =============================================================================

export interface WorkflowStepNavProps {
  /** 현재 앱 ID (e.g., "reference-decoder") */
  currentApp: string;
  /** 단계 완료 시 호출되는 콜백 */
  onComplete?: (result: StepResult) => void;
  /** 다음 단계 버튼 비활성화 */
  disabled?: boolean;
  /** 결과 데이터 (onComplete에 전달됨) */
  resultData?: Record<string, unknown>;
  /** 결과 요약 텍스트 */
  resultSummary?: string;
  /** 컴팩트 모드 (버튼만 표시) */
  compact?: boolean;
  /** 커스텀 클래스 */
  className?: string;
}

// =============================================================================
// Inner Component (uses useSearchParams - needs Suspense)
// =============================================================================

function WorkflowStepNavInner({
  currentApp,
  onComplete,
  disabled = false,
  resultData,
  resultSummary,
  compact = false,
  className = "",
}: WorkflowStepNavProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { language } = useLanguage();
  const ko = language === "ko";

  // URL에서 워크플로우 파라미터 파싱
  const urlParams = useMemo(
    () => parseWorkflowUrlParams(searchParams),
    [searchParams]
  );

  // 워크플로우 상태 가져오기
  const workflowState = useMemo(() => {
    if (!urlParams.ipSlug) return null;
    return getWorkflowState(urlParams.ipSlug);
  }, [urlParams.ipSlug]);

  // 현재 단계 번호 (URL 파라미터 또는 워크플로우 상태에서)
  const currentStep = urlParams.step || workflowState?.currentStep || 1;
  const totalSteps = workflowState?.totalSteps || 1;

  // 현재 단계 인덱스 (0-based)
  const currentStepIndex = currentStep - 1;

  // 이전/다음 단계 정보
  const prevStep: WorkflowStep | null =
    workflowState?.steps[currentStepIndex - 1] || null;
  const nextStep: WorkflowStep | null =
    workflowState?.steps[currentStepIndex + 1] || null;

  // 진행률
  const progress = workflowState ? getWorkflowProgress(urlParams.ipSlug!) : 0;

  // 워크플로우가 없으면 렌더링하지 않음
  if (!urlParams.ipSlug || !workflowState) {
    return null;
  }

  // 다음 단계로 이동
  const handleNextStep = () => {
    if (!nextStep || !urlParams.ipSlug || !urlParams.workflowKey) return;

    // 현재 단계 결과 저장
    const result: StepResult = {
      completedAt: new Date().toISOString(),
      outputSummary: resultSummary,
      outputData: resultData,
    };

    updateStepResult(urlParams.ipSlug, currentStep, result);

    // 콜백 호출
    onComplete?.(result);

    // 다음 단계 URL 생성 및 이동
    const nextUrl = buildStepUrl(
      nextStep,
      urlParams.ipSlug,
      currentStep + 1,
      urlParams.workflowKey,
      urlParams.prompt || undefined
    );

    router.push(nextUrl);
  };

  // 이전 단계로 이동
  const handlePrevStep = () => {
    if (!prevStep || !urlParams.ipSlug || !urlParams.workflowKey) return;

    const prevUrl = buildStepUrl(
      prevStep,
      urlParams.ipSlug,
      currentStep - 1,
      urlParams.workflowKey,
      urlParams.prompt || undefined
    );

    router.push(prevUrl);
  };

  // IP 페이지로 돌아가기
  const handleBackToIP = () => {
    if (!urlParams.ipSlug) return;
    router.push(`/ip/${urlParams.ipSlug}`);
  };

  // 워크플로우 초기화 (처음부터 다시 시작)
  const handleReset = () => {
    if (!urlParams.ipSlug) return;

    const confirmMsg = ko
      ? "워크플로우 진행 상황을 초기화하시겠습니까?\n모든 단계의 결과가 삭제됩니다."
      : "Reset workflow progress?\nAll step results will be deleted.";

    if (window.confirm(confirmMsg)) {
      clearWorkflowState(urlParams.ipSlug);
      router.push(`/ip/${urlParams.ipSlug}`);
    }
  };

  // 컴팩트 모드: 다음 단계 버튼만 표시
  if (compact) {
    if (!nextStep) return null;

    return (
      <button
        onClick={handleNextStep}
        disabled={disabled}
        className={`
          inline-flex items-center gap-2 px-4 py-2 rounded-xl
          bg-violet-600 hover:bg-violet-700 disabled:bg-slate-300 dark:disabled:bg-slate-700
          text-white text-sm font-medium
          transition-all
          ${disabled ? "cursor-not-allowed opacity-60" : ""}
          ${className}
        `}
      >
        {ko ? "다음: " : "Next: "}
        {ko ? nextStep.name_ko : nextStep.name_en}
        <ArrowRight className="w-4 h-4" />
      </button>
    );
  }

  // 전체 네비게이션 바
  return (
    <div
      className={`
        flex items-center justify-between gap-4 p-4
        bg-slate-50 dark:bg-slate-800/50
        border border-slate-200 dark:border-slate-700
        rounded-xl
        ${className}
      `}
    >
      {/* 왼쪽: IP 정보 + 진행률 */}
      <div className="flex items-center gap-4">
        {/* IP로 돌아가기 */}
        <button
          onClick={handleBackToIP}
          className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
          title={ko ? "IP 페이지로" : "Back to IP"}
        >
          <Home className="w-4 h-4 text-slate-500" />
        </button>

        {/* 초기화 버튼 */}
        <button
          onClick={handleReset}
          className="p-2 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors group"
          title={ko ? "처음부터 다시 시작" : "Start over"}
        >
          <RotateCcw className="w-4 h-4 text-slate-400 group-hover:text-red-500 transition-colors" />
        </button>

        {/* 진행률 */}
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
            {ko ? `${currentStep}단계` : `Step ${currentStep}`}
            <span className="text-slate-400 dark:text-slate-500">
              {" "}
              / {totalSteps}
            </span>
          </span>

          {/* 진행률 바 */}
          <div className="w-24 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-violet-500 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* 단계 점 표시 */}
          <div className="flex items-center gap-1">
            {workflowState.steps.map((step, index) => {
              const stepNum = index + 1;
              const completed = isStepCompleted(urlParams.ipSlug!, stepNum);
              const isCurrent = stepNum === currentStep;

              return (
                <div
                  key={step.app}
                  className={`
                    w-2 h-2 rounded-full transition-all
                    ${
                      completed
                        ? "bg-emerald-500"
                        : isCurrent
                          ? "bg-violet-500"
                          : "bg-slate-300 dark:bg-slate-600"
                    }
                  `}
                  title={ko ? step.name_ko : step.name_en}
                />
              );
            })}
          </div>
        </div>
      </div>

      {/* 오른쪽: 네비게이션 버튼 */}
      <div className="flex items-center gap-2">
        {/* 이전 단계 */}
        {prevStep && (
          <button
            onClick={handlePrevStep}
            className="
              inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg
              border border-slate-200 dark:border-slate-600
              text-slate-600 dark:text-slate-400
              hover:bg-slate-100 dark:hover:bg-slate-700
              text-sm transition-all
            "
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            {ko ? "이전" : "Prev"}
          </button>
        )}

        {/* 다음 단계 */}
        {nextStep ? (
          <button
            onClick={handleNextStep}
            disabled={disabled}
            className={`
              inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg
              bg-violet-600 hover:bg-violet-700 disabled:bg-slate-300 dark:disabled:bg-slate-700
              text-white text-sm font-medium
              transition-all
              ${disabled ? "cursor-not-allowed opacity-60" : ""}
            `}
          >
            {ko ? "다음: " : "Next: "}
            <span className="max-w-[120px] truncate">
              {ko ? nextStep.name_ko : nextStep.name_en}
            </span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        ) : (
          /* 완료 */
          <button
            onClick={handleBackToIP}
            className="
              inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg
              bg-emerald-600 hover:bg-emerald-700
              text-white text-sm font-medium
              transition-all
            "
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            {ko ? "완료" : "Complete"}
          </button>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Exported Component (with Suspense boundary)
// =============================================================================

export function WorkflowStepNav(props: WorkflowStepNavProps) {
  return (
    <Suspense fallback={null}>
      <WorkflowStepNavInner {...props} />
    </Suspense>
  );
}

export default WorkflowStepNav;
