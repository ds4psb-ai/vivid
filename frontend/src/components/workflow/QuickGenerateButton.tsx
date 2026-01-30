"use client";

/**
 * QuickGenerateButton - Quick Generate UI Component
 *
 * Phase 2-2: 메가앱별 "한번에 생성" 버튼 및 모달
 *
 * 기능:
 * - 확인 모달: 단계 목록 + 예상 크레딧
 * - 진행 프로그레스 바
 * - 에러 표시
 * - 완료 상태 (사용 크레딧 표시)
 */

import { useState, useCallback, useEffect } from "react";
import {
  Zap,
  Play,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
  Coins,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useQuickGenerate } from "./hooks/useQuickGenerate";
import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import type {
  MegaAppId,
  WorkflowStepMetadata,
  QuickGenerateState,
} from "./types";

// =============================================================================
// Types
// =============================================================================

export interface QuickGenerateButtonProps {
  /** Mega app ID */
  appId: MegaAppId;
  /** Workflow steps for display */
  steps: WorkflowStepMetadata[];
  /** Additional className */
  className?: string;
  /** Disabled state */
  disabled?: boolean;
  /** Korean labels */
  isKorean?: boolean;
}

// =============================================================================
// Labels
// =============================================================================

const LABELS = {
  ko: {
    quickGenerate: "한번에 생성",
    confirmTitle: "전체 워크플로우 실행",
    confirmDescription: "아래 단계를 순서대로 자동 실행합니다",
    estimatedCredits: "예상 크레딧",
    currentBalance: "현재 잔액",
    start: "시작",
    cancel: "취소",
    executing: "실행 중...",
    completed: "완료!",
    error: "오류 발생",
    creditsUsed: "사용 크레딧",
    insufficientCredits: "크레딧 부족",
    topUp: "충전하기",
    retry: "다시 시도",
    close: "닫기",
    step: "단계",
  },
  en: {
    quickGenerate: "Quick Generate",
    confirmTitle: "Execute Full Workflow",
    confirmDescription: "The following steps will be executed automatically",
    estimatedCredits: "Estimated Credits",
    currentBalance: "Current Balance",
    start: "Start",
    cancel: "Cancel",
    executing: "Executing...",
    completed: "Complete!",
    error: "Error",
    creditsUsed: "Credits Used",
    insufficientCredits: "Insufficient Credits",
    topUp: "Top Up",
    retry: "Retry",
    close: "Close",
    step: "Step",
  },
};

// =============================================================================
// Component
// =============================================================================

export function QuickGenerateButton({
  appId,
  steps,
  className,
  disabled = false,
  isKorean = true,
}: QuickGenerateButtonProps) {
  const labels = isKorean ? LABELS.ko : LABELS.en;
  const chainCtx = useDimensionChainOptional();
  const creditCtx = useCreditContextOptional();

  const [isModalOpen, setIsModalOpen] = useState(false);

  const {
    state,
    plan,
    execute,
    reset,
    isExecuting,
    isConfirming,
    planResult,
  } = useQuickGenerate({
    appId,
    onComplete: () => {
      // Refresh credit balance
      creditCtx?.refresh();
    },
    onError: () => {
      // Refresh credit balance (may have refund)
      creditCtx?.refresh();
    },
  });

  // Collect inputs from chain context
  const collectInputs = useCallback((): Record<string, unknown> => {
    if (!chainCtx) return {};

    const inputs: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(chainCtx.chainData)) {
      if (value?.output) {
        inputs[key] = value.output;
      }
    }
    return inputs;
  }, [chainCtx]);

  // Handle button click
  const handleClick = useCallback(async () => {
    if (disabled || isExecuting) return;

    setIsModalOpen(true);
    const inputs = collectInputs();
    await plan(inputs);
  }, [disabled, isExecuting, collectInputs, plan]);

  // Handle start execution
  const handleStart = useCallback(async () => {
    const inputs = collectInputs();
    await execute(inputs);
  }, [collectInputs, execute]);

  // Handle close modal
  const handleClose = useCallback(() => {
    setIsModalOpen(false);
    reset();
  }, [reset]);

  // Check if user has enough credits
  const hasEnoughCredits =
    !creditCtx || creditCtx.balance >= (planResult?.totalEstimatedCredits || 0);

  return (
    <>
      {/* Trigger Button */}
      <button
        onClick={handleClick}
        disabled={disabled || isExecuting}
        className={cn(
          "flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all",
          "bg-gradient-to-r from-amber-500 to-orange-500 text-white",
          "hover:from-amber-600 hover:to-orange-600",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          className
        )}
      >
        {isExecuting ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="hidden sm:inline">{labels.executing}</span>
          </>
        ) : (
          <>
            <Zap className="w-4 h-4" />
            <span className="hidden sm:inline">{labels.quickGenerate}</span>
          </>
        )}
      </button>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-md bg-[var(--surface-1)] border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-amber-500/20">
                  <Zap className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                  <h3 className="font-bold text-white">{labels.confirmTitle}</h3>
                  <p className="text-xs text-white/50">{labels.confirmDescription}</p>
                </div>
              </div>
              <button
                onClick={handleClose}
                className="p-1 rounded-lg text-white/40 hover:text-white/80 hover:bg-white/10 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="p-5 space-y-4">
              {/* Steps List */}
              <div className="space-y-2">
                {(planResult?.steps
                  ? planResult.steps.map((s) => ({
                      id: s.stepId,
                      label: s.label,
                      creditCost: s.estimatedCreditCost,
                    }))
                  : steps.map((s) => ({
                      id: s.id,
                      label: s.label,
                      creditCost: s.creditCost,
                    }))
                ).map((step, index) => {
                  const stepState = state.steps[index];
                  const label = step.label;
                  const creditCost = step.creditCost;

                  let statusIcon = <div className="w-5 h-5 rounded-full border-2 border-white/20" />;
                  let statusColor = "text-white/40";

                  if (stepState?.status === "completed") {
                    statusIcon = <CheckCircle className="w-5 h-5 text-green-400" />;
                    statusColor = "text-green-400";
                  } else if (stepState?.status === "running" || (isExecuting && index === state.currentStepIndex)) {
                    statusIcon = <Loader2 className="w-5 h-5 text-amber-400 animate-spin" />;
                    statusColor = "text-amber-400";
                  } else if (stepState?.status === "error") {
                    statusIcon = <AlertCircle className="w-5 h-5 text-red-400" />;
                    statusColor = "text-red-400";
                  }

                  return (
                    <div
                      key={index}
                      className={cn(
                        "flex items-center gap-3 p-3 rounded-lg bg-white/5",
                        stepState?.status === "running" && "ring-1 ring-amber-500/50"
                      )}
                    >
                      {statusIcon}
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-white/40">
                            {labels.step} {index + 1}
                          </span>
                          <ChevronRight className="w-3 h-3 text-white/20" />
                          <span className={cn("text-sm font-medium", statusColor)}>
                            {label}
                          </span>
                        </div>
                      </div>
                      {creditCost && (
                        <div className="flex items-center gap-1 text-xs text-white/40">
                          <Coins className="w-3 h-3" />
                          {creditCost}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Progress Bar (during execution) */}
              {isExecuting && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-white/60">{labels.executing}</span>
                    <span className="text-amber-400">
                      {state.currentStepIndex + 1} / {state.totalSteps}
                    </span>
                  </div>
                  <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-amber-500 to-orange-500 transition-all duration-500"
                      style={{
                        width: `${((state.currentStepIndex + 1) / state.totalSteps) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Credit Info */}
              <div className="p-3 rounded-lg bg-white/5 space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/60">{labels.estimatedCredits}</span>
                  <span className="font-bold text-amber-400">
                    {planResult?.totalEstimatedCredits || state.totalCreditCost}
                  </span>
                </div>
                {creditCtx && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white/60">{labels.currentBalance}</span>
                    <span
                      className={cn(
                        "font-medium",
                        hasEnoughCredits ? "text-green-400" : "text-red-400"
                      )}
                    >
                      {creditCtx.balance}
                    </span>
                  </div>
                )}
                {state.status === "completed" && state.usedCredits > 0 && (
                  <div className="flex items-center justify-between text-sm pt-2 border-t border-white/10">
                    <span className="text-white/60">{labels.creditsUsed}</span>
                    <span className="font-bold text-green-400">{state.usedCredits}</span>
                  </div>
                )}
              </div>

              {/* Error Message */}
              {state.error && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  {state.error}
                </div>
              )}

              {/* Insufficient Credits Warning */}
              {!hasEnoughCredits && state.status === "confirming" && (
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-sm">
                  {labels.insufficientCredits}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex gap-3 px-5 py-4 border-t border-white/10 bg-white/5">
              {state.status === "idle" || state.status === "confirming" ? (
                <>
                  <button
                    onClick={handleClose}
                    className="flex-1 px-4 py-2.5 rounded-lg font-medium text-sm bg-white/10 text-white/70 hover:bg-white/20 transition-colors"
                  >
                    {labels.cancel}
                  </button>
                  <button
                    onClick={handleStart}
                    disabled={!hasEnoughCredits || !planResult}
                    className="flex-1 px-4 py-2.5 rounded-lg font-medium text-sm bg-gradient-to-r from-amber-500 to-orange-500 text-white hover:from-amber-600 hover:to-orange-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <Play className="w-4 h-4" />
                    {labels.start}
                  </button>
                </>
              ) : state.status === "completed" ? (
                <button
                  onClick={handleClose}
                  className="flex-1 px-4 py-2.5 rounded-lg font-medium text-sm bg-green-500 text-white hover:bg-green-600 transition-colors flex items-center justify-center gap-2"
                >
                  <CheckCircle className="w-4 h-4" />
                  {labels.completed}
                </button>
              ) : state.status === "error" ? (
                <>
                  <button
                    onClick={handleClose}
                    className="flex-1 px-4 py-2.5 rounded-lg font-medium text-sm bg-white/10 text-white/70 hover:bg-white/20 transition-colors"
                  >
                    {labels.close}
                  </button>
                  <button
                    onClick={handleStart}
                    className="flex-1 px-4 py-2.5 rounded-lg font-medium text-sm bg-amber-500 text-white hover:bg-amber-600 transition-colors flex items-center justify-center gap-2"
                  >
                    {labels.retry}
                  </button>
                </>
              ) : (
                <button
                  disabled
                  className="flex-1 px-4 py-2.5 rounded-lg font-medium text-sm bg-white/10 text-white/50 cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {labels.executing}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
