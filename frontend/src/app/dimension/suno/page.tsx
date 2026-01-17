"use client";

/**
 * Suno Music Page - Suno AI Music Generation
 *
 * Features:
 * - Custom mode with title, style, lyrics
 * - Instrumental mode (no vocals)
 * - Genre and mood presets
 * - Composer style presets (Hans Zimmer, Joe Hisaishi, etc.)
 * - 2 songs per generation
 */

import AppShell from "@/components/AppShell";
import SunoPanel from "@/components/dimension/SunoPanel";

export default function SunoPage() {
  return (
    <AppShell showTopBar={false}>
      <div className="h-screen">
        <SunoPanel />
      </div>
    </AppShell>
  );
}
