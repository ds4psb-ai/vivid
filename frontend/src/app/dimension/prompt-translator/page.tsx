"use client";

/**
 * Platform Translator Page - AI Video Platform Prompt Optimizer
 *
 * Translates scene descriptions into optimized prompts for:
 * - Veo 3.1: Dialogue/narration-heavy viral videos
 * - Kling 2.6: High-quality silent cinematic videos (recommended)
 * - Sora Max 2 Pro: Animation-style videos
 */

import AppShell from "@/components/AppShell";
import PromptAlchemyPanel from "@/components/dimension/PromptAlchemyPanel";

export default function PlatformTranslatorPage() {
  return (
    <AppShell showTopBar={false}>
      <div className="h-screen">
        <PromptAlchemyPanel />
      </div>
    </AppShell>
  );
}
