"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { FoundryRightsEvaluationResponse } from "@/lib/api";
import { useFoundryData } from "@/hooks/useFoundryData";
import { FoundryPanelCard, DecisionBadge, FoundryEmptyState } from "./shared";
import { DEMO_RIGHTS_REQUEST, DEMO_RIGHTS_RESPONSE } from "./demo-data";

export function RightsStatusPanel() {
  const [useDemo, setUseDemo] = useState(false);

  const { data, isLoading, error, refresh } = useFoundryData<FoundryRightsEvaluationResponse>(
    async () => {
      try {
        return await api.evaluateFoundryRights(DEMO_RIGHTS_REQUEST);
      } catch {
        setUseDemo(true);
        return DEMO_RIGHTS_RESPONSE;
      }
    }
  );

  const result = data || (useDemo ? DEMO_RIGHTS_RESPONSE : null);

  return (
    <FoundryPanelCard title="Rights Gate" isLoading={isLoading} error={error} onRefresh={refresh}>
      {!result ? (
        <FoundryEmptyState message="No rights evaluation data" />
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-[var(--fg-muted)]">Overall Decision</span>
            <DecisionBadge decision={result.decision} />
          </div>
          <div className="space-y-2">
            {result.per_asset.map((asset) => (
              <div
                key={asset.asset_id}
                className="flex items-center justify-between p-3 rounded-lg bg-[var(--surface-2)]"
              >
                <div>
                  <span className="text-sm font-medium text-[var(--fg-0)]">{asset.asset_id}</span>
                  {asset.reason_codes.length > 0 && (
                    <p className="text-xs text-[var(--fg-muted)] mt-0.5">
                      {asset.reason_codes.join(", ")}
                    </p>
                  )}
                </div>
                <DecisionBadge decision={asset.decision} />
              </div>
            ))}
          </div>
          {useDemo && (
            <p className="text-xs text-[var(--fg-muted)] italic">Demo data (API unavailable)</p>
          )}
        </div>
      )}
    </FoundryPanelCard>
  );
}
