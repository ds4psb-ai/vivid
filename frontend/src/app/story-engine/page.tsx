"use client";

/**
 * Story Engine Hub - Mega App for System Prompt Generation
 *
 * Consolidates:
 * - Story (Story Architect)
 * - Prompt (Prompt Alchemy / Generator)
 * - System Prompt Generator - Converts Logic Vector to platform-specific prompts
 *
 * Workflow: Logic Vector -> Story Structure -> System Prompt for VEO/Kling
 *
 * Migration Note (2026.01):
 * Using UnifiedWorkflowShell for consistent cross-MegaApp behavior.
 * Step-based workflow replaces tab-based navigation.
 */

import { UnifiedWorkflowShell } from "@/components/workflow";

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
      {(currentStepId) => <StepContent stepId={currentStepId} />}
    </UnifiedWorkflowShell>
  );
}

/**
 * Step content renderer
 */
function StepContent({ stepId }: { stepId: string }) {
  switch (stepId) {
    case "story":
      return <StoryArchitectPanel />;

    case "prompt":
      return <PromptGeneratorPanel />;

    case "system-prompt":
      return (
        <div className="p-4">
          <SystemPromptPanel />
        </div>
      );

    default:
      return <StoryArchitectPanel />;
  }
}
