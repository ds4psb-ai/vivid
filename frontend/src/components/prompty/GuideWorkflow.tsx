"use client";

import type { PromptyStageInfo, PromptyStepInfo } from "@/lib/api";

interface GuideWorkflowProps {
  stages: PromptyStageInfo[];
  currentStage: string;
  currentStep: string;
  progressPercent: number;
}

function getStageStatus(stage: PromptyStageInfo): string {
  if (stage.status === "completed") return "✅";
  if (stage.status === "in_progress") return "◉";
  return "○";
}

function getStepStatus(step: PromptyStepInfo): string {
  if (step.status === "completed") return "✅";
  if (step.status === "in_progress") return "🔄";
  return "○";
}

/**
 * GuideWorkflow - 워크플로우 진행 상황 사이드바
 *
 * Stage/Step 계층 구조를 표시하고 현재 위치를 하이라이트
 */
export function GuideWorkflow({
  stages,
  currentStage,
  currentStep,
  progressPercent,
}: GuideWorkflowProps) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <h2 className="font-semibold mb-4">진행 상황</h2>

      {/* Overall Progress */}
      <div className="mb-6">
        <div className="flex justify-between text-sm mb-1">
          <span>전체 진행률</span>
          <span>{progressPercent}%</span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Stages */}
      <div className="space-y-3">
        {stages.map((stage) => (
          <div key={stage.id} className="space-y-2">
            <div className="flex items-center gap-2">
              <span>{getStageStatus(stage)}</span>
              <span
                className={`font-medium ${
                  stage.id === currentStage
                    ? "text-primary"
                    : stage.status === "completed"
                    ? "text-muted-foreground"
                    : ""
                }`}
              >
                {stage.name}
              </span>
            </div>

            {/* Steps (expanded if current stage) */}
            {stage.id === currentStage && stage.steps.length > 0 && (
              <div className="ml-6 space-y-1">
                {stage.steps.map((step) => (
                  <div
                    key={step.id}
                    className={`text-sm flex items-center gap-2 ${
                      step.id === currentStep
                        ? "text-primary font-medium"
                        : "text-muted-foreground"
                    }`}
                  >
                    <span className="text-xs">{getStepStatus(step)}</span>
                    <span>{step.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default GuideWorkflow;
