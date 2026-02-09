"use client";

/**
 * Story Engine Hub - Mega App for System Prompt Generation
 *
 * Phase 1-3: Story Engine Step Simplification
 * Consolidates (merged):
 * - Story (Story Architect)
 * - Prompt (Unified: Prompt Alchemy + System Prompt Generator)
 *
 * Workflow: DNA Lab (Analysis) → Story → Prompt → Production
 *
 * Phase 7: Overview 뷰 통합
 * - /story-engine                → Overview (2단계 한눈에)
 * - /story-engine?step=overview  → Overview (명시적)
 * - /story-engine?step=story     → Story Architect
 * - /story-engine?step=prompt    → Unified Prompt Generator (merged)
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

// Import panels
import StoryArchitectPanel from "@/components/dimension/StoryArchitectPanel";
import UnifiedPromptPanel from "@/components/dimension/UnifiedPromptPanel";

/**
 * Valid step IDs for Story Engine
 * Phase 1-3: Reduced to 2 steps (system-prompt merged into prompt)
 */
const VALID_STEP_IDS: StoryEngineStepId[] = ["story", "prompt"];

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
  // Step Detail: valid step ID (story, prompt)
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
      {(currentStepId, disclosureLevel) => (
        <StepContent
          stepId={currentStepId as StoryEngineStepId}
          disclosureLevel={disclosureLevel}
        />
      )}
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
    <div className="flex items-center justify-center min-h-screen bg-stitch-dark">
      <div className="flex flex-col items-center gap-4">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--stitch-primary)]/20 to-[var(--stitch-primary-accent)]/20 animate-pulse" />
        <div className="text-sm text-white/50">Story Engine 로딩 중...</div>
      </div>
    </div>
  );
}

/** Disclosure level for progressive UI complexity */
type DisclosureLevel = "basic" | "intermediate" | "advanced";

/**
 * Step content renderer with StoryEngineStepPanel wrapper
 *
 * Phase 1-3: Simplified to 2 steps (prompt merged with system-prompt)
 * Phase 2-1: Added disclosureLevel prop for progressive disclosure
 *
 * Each panel is wrapped with StoryEngineStepPanel to provide:
 * - Input data banner (shows available/missing data)
 * - Production bridge (for prompt step - now final step)
 * - Chain data integration
 */
function StepContent({
  stepId,
  disclosureLevel = "intermediate",
}: {
  stepId: StoryEngineStepId;
  disclosureLevel?: DisclosureLevel;
}) {
  switch (stepId) {
    case "story":
      return (
        <StoryEngineStepPanel stepId="story">
          <StoryArchitectPanel />
        </StoryEngineStepPanel>
      );

    case "prompt":
      // Phase 1-3: Unified Prompt Panel (outputs both prompt and system-prompt)
      return (
        <StoryEngineStepPanel stepId="prompt" showProductionBridge>
          <div className="p-4">
            <UnifiedPromptPanel disclosureLevel={disclosureLevel} />
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
