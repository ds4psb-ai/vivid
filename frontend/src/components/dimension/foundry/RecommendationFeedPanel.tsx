"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { FoundryRecommendationResponse } from "@/lib/api";
import { useFoundryData } from "@/hooks/useFoundryData";
import { FoundryPanelCard, DecisionBadge, ScoreBar, FoundryEmptyState } from "./shared";
import { DEMO_RECOMMENDATION_REQUEST, DEMO_RECOMMENDATION_RESPONSE } from "./demo-data";

export function RecommendationFeedPanel() {
  const [useDemo, setUseDemo] = useState(false);

  const { data, isLoading, error, refresh } = useFoundryData<FoundryRecommendationResponse>(
    async () => {
      try {
        return await api.getFoundryRecommendations(DEMO_RECOMMENDATION_REQUEST);
      } catch {
        setUseDemo(true);
        return DEMO_RECOMMENDATION_RESPONSE;
      }
    }
  );

  const result = data || (useDemo ? DEMO_RECOMMENDATION_RESPONSE : null);

  return (
    <FoundryPanelCard title="Recommendations" isLoading={isLoading} error={error} onRefresh={refresh}>
      {!result ? (
        <FoundryEmptyState message="No recommendations available" />
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-[var(--fg-muted)]">
            <span>Scene: {result.scene_id}</span>
            <span>Gate: {result.continuity_gate}</span>
          </div>
          {result.ranked.map((candidate, idx) => (
            <div key={candidate.candidate_id} className="p-3 rounded-lg bg-[var(--surface-2)] space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-[var(--fg-muted)]">#{idx + 1}</span>
                  <span className="text-sm font-medium text-[var(--fg-0)]">{candidate.title}</span>
                </div>
                <DecisionBadge decision={candidate.decision} />
              </div>
              <div className="space-y-1">
                <ScoreBar score={candidate.final_score} label="Final" />
                <ScoreBar score={candidate.continuity_score} label="Continuity" />
              </div>
              {candidate.reason_codes.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {candidate.reason_codes.map((code) => (
                    <span key={code} className="px-1.5 py-0.5 rounded text-[10px] bg-rose-500/10 text-rose-400 font-mono">
                      {code}
                    </span>
                  ))}
                </div>
              )}
              {candidate.recommendation_rationale.length > 0 && (
                <ul className="text-xs text-[var(--fg-muted)] space-y-0.5 mt-1">
                  {candidate.recommendation_rationale.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
          {useDemo && (
            <p className="text-xs text-[var(--fg-muted)] italic">Demo data (API unavailable)</p>
          )}
        </div>
      )}
    </FoundryPanelCard>
  );
}
