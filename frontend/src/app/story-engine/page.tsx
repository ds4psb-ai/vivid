"use client";

/**
 * Story Engine Hub - Mega App for System Prompt Generation
 *
 * Consolidates:
 * - Story (Story Architect)
 * - Prompt (Prompt Alchemy / Generator)
 * - System Prompt Generator - Converts Logic Vector to platform-specific prompts
 *
 * Workflow: DNA Lab (VPE + AD) → Story → Prompt → System Prompt → Production
 *
 * Phase 7: Overview 뷰 통합
 * - /story-engine                → Overview (3단계 한눈에)
 * - /story-engine?step=overview  → Overview (명시적)
 * - /story-engine?step=story     → Story Architect
 * - /story-engine?step=prompt    → Prompt Alchemy
 * - /story-engine?step=system-prompt → System Prompt
 *
 * Migration Note (2026.01):
 * Using UnifiedWorkflowShell for consistent cross-MegaApp behavior.
 * StoryEngineStepPanel wraps each panel for chain data integration.
 */

import { useSearchParams, useRouter } from "next/navigation";
import { useCallback, useMemo, Suspense } from "react";
import { UnifiedWorkflowShell, StoryEngineOverview } from "@/components/workflow";
import {
  StoryEngineStepPanel,
  type StoryEngineStepId,
} from "@/components/story-engine";

// Import existing panels
import StoryArchitectPanel from "@/components/dimension/StoryArchitectPanel";
import PromptGeneratorPanel from "@/components/dimension/PromptGeneratorPanel";
import SystemPromptPanel from "@/components/dimension/SystemPromptPanel";

/**
 * Valid step IDs for Story Engine
 */
const VALID_STEP_IDS: StoryEngineStepId[] = ["story", "prompt", "system-prompt"];

/**
 * Check if a string is a valid step ID
 */
function isValidStepId(step: string | null): step is StoryEngineStepId {
  return VALID_STEP_IDS.includes(step as StoryEngineStepId);
}

/**
 * Inner component that uses useSearchParams
 */
function StoryEnginePageInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const stepParam = searchParams.get("step");

  // Determine view mode
  // Overview: no step param, or step=overview
  // Step Detail: valid step ID (story, prompt, system-prompt)
  const showOverview = useMemo(() => {
    if (!stepParam) return true; // No param → Overview
    if (stepParam === "overview") return true; // Explicit overview
    if (!isValidStepId(stepParam)) return true; // Invalid → Overview
    return false;
  }, [stepParam]);

  // Handle step navigation from Overview
  const handleStepClick = useCallback(
    (stepId: string) => {
      router.push(`/story-engine?step=${stepId}`);
    },
    [router]
  );

  // Render Overview or Step Detail
  if (showOverview) {
    return (
      <UnifiedWorkflowShell
        appId="story-engine"
        showAurora={true}
        showWorkflowProgress={false}
        showChainSummary={false}
      >
        {() => <StoryEngineOverview onStepClick={handleStepClick} />}
      </UnifiedWorkflowShell>
    );
  }

  return (
    <UnifiedWorkflowShell
      appId="story-engine"
      showAurora={true}
      showWorkflowProgress={true}
      showChainSummary={true}
    >
      {(currentStepId) => <StepContent stepId={currentStepId as StoryEngineStepId} />}
    </UnifiedWorkflowShell>
  );
}

export default function StoryEnginePage() {
  return (
    <Suspense fallback={<StoryEngineLoadingFallback />}>
      <StoryEnginePageInner />
    </Suspense>
  );
}

/**
 * Loading fallback for Suspense boundary
 */
function StoryEngineLoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-black">
      <div className="flex flex-col items-center gap-4">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 animate-pulse" />
        <div className="text-sm text-white/50">Story Engine 로딩 중...</div>
      </div>
    </div>
  );
}

/**
 * Step content renderer with StoryEngineStepPanel wrapper
 *
 * Each panel is wrapped with StoryEngineStepPanel to provide:
 * - Input data banner (shows available/missing data)
 * - Production bridge (for system-prompt step)
 * - Chain data integration
 */
function StepContent({ stepId }: { stepId: StoryEngineStepId }) {
  switch (stepId) {
    case "story":
      return (
        <StoryEngineStepPanel stepId="story">
          <StoryArchitectPanel />
        </StoryEngineStepPanel>
      );

    case "prompt":
      return (
        <StoryEngineStepPanel stepId="prompt">
          <PromptGeneratorPanel />
        </StoryEngineStepPanel>
      );

    case "system-prompt":
      return (
        <StoryEngineStepPanel stepId="system-prompt" showProductionBridge>
          <div className="p-4">
            <SystemPromptPanel />
          </div>
        </StoryEngineStepPanel>
      );

    default:
      return (
        <StoryEngineStepPanel stepId="story">
          <StoryArchitectPanel />
        </StoryEngineStepPanel>
      );
  }
}
