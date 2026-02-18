"use client";

import { FoundryDashboardHeader } from "@/components/dimension/foundry/FoundryDashboardHeader";
import { RightsStatusPanel } from "@/components/dimension/foundry/RightsStatusPanel";
import { PatternLibraryPanel } from "@/components/dimension/foundry/PatternLibraryPanel";
import { RecommendationFeedPanel } from "@/components/dimension/foundry/RecommendationFeedPanel";
import { ExperimentResultsPanel } from "@/components/dimension/foundry/ExperimentResultsPanel";

export default function FoundryPage() {
  return (
    <div className="min-h-screen bg-[var(--bg-0)]">
      <FoundryDashboardHeader />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-6 max-w-7xl mx-auto">
        <RightsStatusPanel />
        <PatternLibraryPanel />
        <RecommendationFeedPanel />
        <ExperimentResultsPanel />
      </div>
    </div>
  );
}
