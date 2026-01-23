"use client";

/**
 * Creative Editor Page - AI-powered Editorial Review
 *
 * Provides editorial review and improvement of creative content
 * with narrative, visual, and pacing analysis.
 */

import AppShell from "@/components/AppShell";
import CreativeEditorPanel from "@/components/dimension/CreativeEditorPanel";

export default function CreativeEditorPage() {
  return (
    <AppShell showTopBar={false}>
      <div className="h-screen">
        <CreativeEditorPanel />
      </div>
    </AppShell>
  );
}
