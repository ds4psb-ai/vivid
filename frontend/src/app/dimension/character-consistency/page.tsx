"use client";

/**
 * Character Consistency Page - StoryMem Character Library
 *
 * Features:
 * - Character library with CRUD operations
 * - StoryMem memory bank (arXiv:2512.19539)
 * - Platform sync (Veo, Kling, Runway, Hailuo)
 * - Similar character search via Qdrant
 */

import AppShell from "@/components/AppShell";
import CharacterConsistencyPanel from "@/components/dimension/CharacterConsistencyPanel";

export default function CharacterConsistencyPage() {
  return (
    <AppShell showTopBar={false}>
      <div className="h-screen">
        <CharacterConsistencyPanel />
      </div>
    </AppShell>
  );
}
