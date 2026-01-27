"use client";

import { BookOpen, Layers, Wand2, FileCode } from "lucide-react";
import { MegaAppShell, type MegaAppTab } from "@/components/mega-app";

// Import existing panels
import StoryArchitectPanel from "@/components/dimension/StoryArchitectPanel";
import PromptGeneratorPanel from "@/components/dimension/PromptGeneratorPanel";
import SystemPromptPanel from "@/components/dimension/SystemPromptPanel";

/**
 * Story Engine Hub - Mega App for System Prompt Generation
 *
 * Consolidates:
 * - Story (Story Architect)
 * - Prompt (Prompt Alchemy / Generator)
 * - System Prompt Generator - Converts Logic Vector to platform-specific prompts
 *
 * Workflow: Logic Vector -> Story Structure -> System Prompt for VEO/Kling
 */

const TABS: MegaAppTab[] = [
  {
    value: "story",
    label: "시나리오 생성기",
    labelEn: "Story Architect",
    icon: <Layers className="w-4 h-4" />,
    description: "DNA와 스타일을 결합한 시나리오 작성",
  },
  {
    value: "prompt",
    label: "프롬프트 연금술",
    labelEn: "Prompt Alchemy",
    icon: <Wand2 className="w-4 h-4" />,
    description: "AI 비디오 프롬프트 생성",
  },
  {
    value: "system-prompt",
    label: "시스템 프롬프트",
    labelEn: "System Prompt",
    icon: <FileCode className="w-4 h-4" />,
    description: "Logic Vector -> VEO/Kling용 System Prompt 변환",
    isNew: true,
  },
];

export default function StoryEnginePage() {
  return (
    <MegaAppShell
      appId="story-engine"
      title="Story Engine"
      subtitle="스토리 구성 및 System Prompt 생성"
      icon={BookOpen}
      tabs={TABS}
      defaultTab="story"
      showAurora={true}
      tabParamName="tab"
    >
      {(activeTab) => (
        <>
          {activeTab === "story" && <StoryArchitectPanel />}
          {activeTab === "prompt" && <PromptGeneratorPanel />}
          {activeTab === "system-prompt" && (
            <div className="p-4">
              <SystemPromptPanel />
            </div>
          )}
        </>
      )}
    </MegaAppShell>
  );
}
