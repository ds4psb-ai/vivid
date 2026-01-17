"use client";

/**
 * Kling Video Page - Kling 2.6 AI Video Generation
 *
 * Features:
 * - Text-to-video and Image-to-video generation
 * - Motion Control (slow, normal, fast, dramatic)
 * - Camera Control (pan, tilt, zoom, dolly, orbit)
 * - Elements (up to 4 reference images for character consistency)
 * - End Frame for shot sequencing
 * - Native audio generation
 */

import AppShell from "@/components/AppShell";
import KlingPanel from "@/components/dimension/KlingPanel";

export default function KlingPage() {
  return (
    <AppShell showTopBar={false}>
      <div className="h-screen">
        <KlingPanel />
      </div>
    </AppShell>
  );
}
