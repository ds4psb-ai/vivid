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
 * Migration Note (2026.01):
 * Using UnifiedWorkflowShell for consistent cross-MegaApp behavior.
 * StoryEngineStepPanel wraps each panel for chain data integration.
 */

import { UnifiedWorkflowShell } from "@/components/workflow";
import {
  StoryEngineStepPanel,
  type StoryEngineStepId,
} from "@/components/story-engine";

// Import existing panels
import StoryArchitectPanel from "@/components/dimension/StoryArchitectPanel";
import PromptGeneratorPanel from "@/components/dimension/PromptGeneratorPanel";
import SystemPromptPanel from "@/components/dimension/SystemPromptPanel";

export default function StoryEnginePage() {
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
