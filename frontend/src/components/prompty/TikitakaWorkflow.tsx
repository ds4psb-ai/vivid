"use client";

import { useState, useCallback } from "react";
import { api } from "@/lib/api";
import {
  TIKITAKA_STEPS,
  getTikitakaStep,
  getAiRoleDisplayName,
  getAiRoleColorClass,
  TikitakaAiRole,
} from "@/lib/tikitaka-prompts";
import { CopyPromptButton } from "./CopyPromptButton";

interface TikitakaWorkflowProps {
  projectId: string;
  initialStep?: number;
  anchorSceneId?: string;
  onStepChange?: (step: number) => void;
  onComplete?: () => void;
}

/**
 * TikitakaWorkflow - 6단계 Dual AI 워크플로우 컴포넌트
 *
 * Gemini <-> Claude 티키타카를 통해 98% 품질 달성
 */
export function TikitakaWorkflow({
  projectId,
  initialStep = 1,
  anchorSceneId,
  onStepChange,
  onComplete,
}: TikitakaWorkflowProps) {
  const [currentStep, setCurrentStep] = useState(initialStep);
  const [isAdvancing, setIsAdvancing] = useState(false);
  const [checkedAttachments, setCheckedAttachments] = useState<Set<string>>(new Set());

  const stepConfig = getTikitakaStep(currentStep);

  const handleAdvance = useCallback(async () => {
    if (!stepConfig) return;

    setIsAdvancing(true);
    try {
      const response = await api.advancePromptyTikitaka(projectId, {});

      if (response.completed) {
        onComplete?.();
      } else {
        setCurrentStep(response.new_step);
        setCheckedAttachments(new Set());
        onStepChange?.(response.new_step);
      }
    } catch (error) {
      console.error("Failed to advance step:", error);
    } finally {
      setIsAdvancing(false);
    }
  }, [projectId, stepConfig, onComplete, onStepChange]);

  const handleGotoStep = useCallback(
    async (step: number, reason?: string) => {
      try {
        await api.gotoPromptyTikitakaStep(projectId, step, reason);
        setCurrentStep(step);
        setCheckedAttachments(new Set());
        onStepChange?.(step);
      } catch (error) {
        console.error("Failed to goto step:", error);
      }
    },
    [projectId, onStepChange]
  );

  const toggleAttachment = (name: string) => {
    setCheckedAttachments((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const allRequiredAttachmentsChecked =
    stepConfig?.attachments
      .filter((a) => a.required)
      .every((a) => checkedAttachments.has(a.name)) ?? false;

  if (!stepConfig) {
    return (
      <div className="text-center py-16 rounded-xl border border-border bg-card">
        <div className="text-6xl mb-4">Error</div>
        <p className="text-muted-foreground">Invalid step: {currentStep}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Step Progress */}
      <StepProgress currentStep={currentStep} onGotoStep={handleGotoStep} />

      {/* Step Header */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center gap-4 mb-4">
          <StepBadge step={currentStep} />
          <div>
            <h2 className="text-2xl font-bold">{stepConfig.name}</h2>
            <AiRoleBadge role={stepConfig.aiRole} />
          </div>
        </div>

        <p className="text-muted-foreground">{stepConfig.expectedOutput}</p>
      </div>

      {/* Prompt Section */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold flex items-center gap-2">
            <span className={getAiRoleColorClass(stepConfig.aiRole) + " px-2 py-1 rounded text-xs"}>
              {getAiRoleDisplayName(stepConfig.aiRole)}
            </span>
            에게 보내기
          </h3>
          <CopyPromptButton
            promptText={stepConfig.promptTemplate}
            onCopy={() => {
              api.logPromptyAction(projectId, "copy_tikitaka_prompt", `step_${currentStep}`, undefined);
            }}
          />
        </div>

        <pre className="p-4 bg-muted rounded-lg text-sm overflow-x-auto whitespace-pre-wrap font-mono max-h-96">
          {stepConfig.promptTemplate}
        </pre>
      </div>

      {/* Attachments Checklist */}
      {stepConfig.attachments.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-6">
          <h3 className="font-semibold mb-4">
            {stepConfig.aiRole === "user" ? "준비물" : "필수 첨부"}
          </h3>
          <div className="space-y-3">
            {stepConfig.attachments.map((attachment) => (
              <label
                key={attachment.name}
                className="flex items-center gap-3 cursor-pointer group"
              >
                <input
                  type="checkbox"
                  checked={checkedAttachments.has(attachment.name)}
                  onChange={() => toggleAttachment(attachment.name)}
                  className="w-5 h-5 rounded border-border text-primary focus:ring-primary"
                />
                <div className="flex-1">
                  <span className="font-medium group-hover:text-primary transition">
                    {attachment.name}
                    {attachment.required && <span className="text-red-500 ml-1">*</span>}
                  </span>
                  <p className="text-sm text-muted-foreground">{attachment.description}</p>
                </div>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Tips */}
      {stepConfig.tips.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-6">
          <h3 className="font-semibold mb-4">Tips</h3>
          <ul className="space-y-2">
            {stepConfig.tips.map((tip, index) => (
              <li key={index} className="flex items-start gap-2 text-sm">
                <span className="text-primary">-</span>
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-between items-center p-6 rounded-xl border border-border bg-card">
        {currentStep > 1 && (
          <button
            onClick={() => handleGotoStep(currentStep - 1)}
            className="px-6 py-3 border border-border rounded-lg hover:bg-accent transition"
          >
            Previous
          </button>
        )}
        {currentStep === 1 && <div />}

        <div className="flex items-center gap-4">
          {!allRequiredAttachmentsChecked && stepConfig.attachments.some((a) => a.required) && (
            <span className="text-sm text-muted-foreground">Check required attachments</span>
          )}
          <button
            onClick={handleAdvance}
            disabled={
              isAdvancing || (stepConfig.attachments.some((a) => a.required) && !allRequiredAttachmentsChecked)
            }
            className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isAdvancing ? "Processing..." : currentStep >= 6 ? "Complete" : "Next Step"}
          </button>
        </div>
      </div>

      {/* Verdict Actions (for Step 5-6) */}
      {currentStep >= 5 && (
        <div className="rounded-xl border border-border bg-card p-6">
          <h3 className="font-semibold mb-4">Verdict Actions</h3>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => handleGotoStep(2, "REJECT")}
              className="px-4 py-2 bg-red-500/10 text-red-500 rounded-lg hover:bg-red-500/20 transition"
            >
              REJECT - Step 2
            </button>
            {currentStep === 6 && (
              <button
                onClick={() => handleGotoStep(5)}
                className="px-4 py-2 bg-yellow-500/10 text-yellow-500 rounded-lg hover:bg-yellow-500/20 transition"
              >
                Retry Step 5
              </button>
            )}
            <button
              onClick={handleAdvance}
              disabled={isAdvancing}
              className="px-4 py-2 bg-green-500/10 text-green-500 rounded-lg hover:bg-green-500/20 transition disabled:opacity-50"
            >
              PASS - 85+
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Sub-components

function StepProgress({
  currentStep,
  onGotoStep,
}: {
  currentStep: number;
  onGotoStep: (step: number) => void;
}) {
  const steps = [1, 2, 3, 4, 5, 6];

  return (
    <div className="flex items-center justify-between">
      {steps.map((step, index) => {
        const config = TIKITAKA_STEPS[step];
        const isActive = step === currentStep;
        const isCompleted = step < currentStep;

        return (
          <div key={step} className="flex items-center">
            <button
              onClick={() => onGotoStep(step)}
              className={`
                flex flex-col items-center gap-1 p-2 rounded-lg transition
                ${isActive ? "bg-primary/10" : "hover:bg-accent"}
              `}
            >
              <div
                className={`
                  w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold
                  ${isCompleted ? "bg-green-500 text-white" : ""}
                  ${isActive ? "bg-primary text-primary-foreground" : ""}
                  ${!isCompleted && !isActive ? "bg-muted text-muted-foreground" : ""}
                `}
              >
                {isCompleted ? "O" : step}
              </div>
              <span
                className={`text-xs ${isActive ? "font-semibold" : "text-muted-foreground"}`}
              >
                {config?.name}
              </span>
            </button>
            {index < steps.length - 1 && (
              <div
                className={`w-8 h-0.5 ${
                  step < currentStep ? "bg-green-500" : "bg-muted"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function StepBadge({ step }: { step: number }) {
  return (
    <div className="w-14 h-14 rounded-xl bg-primary text-primary-foreground flex items-center justify-center text-xl font-bold">
      {step}/6
    </div>
  );
}

function AiRoleBadge({ role }: { role: TikitakaAiRole }) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs ${getAiRoleColorClass(role)}`}>
      {role === "gemini" && "G Gemini"}
      {role === "claude" && "C Claude"}
      {role === "user" && "U You"}
    </span>
  );
}

export default TikitakaWorkflow;
