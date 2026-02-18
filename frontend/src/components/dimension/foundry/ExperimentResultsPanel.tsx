"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { FoundryExperimentSummaryResponse } from "@/lib/api";
import { useFoundryData } from "@/hooks/useFoundryData";
import { FoundryPanelCard, FoundryEmptyState } from "./shared";
import { DEMO_EXPERIMENT_RESPONSE } from "./demo-data";

export function ExperimentResultsPanel() {
  const [useDemo, setUseDemo] = useState(false);

  const { data, isLoading, error, refresh } = useFoundryData<FoundryExperimentSummaryResponse>(
    async () => {
      try {
        return await api.getFoundryExperimentSummary("default");
      } catch {
        setUseDemo(true);
        return DEMO_EXPERIMENT_RESPONSE;
      }
    }
  );

  const result = data || (useDemo ? DEMO_EXPERIMENT_RESPONSE : null);

  return (
    <FoundryPanelCard title="Experiment Results" isLoading={isLoading} error={error} onRefresh={refresh}>
      {!result ? (
        <FoundryEmptyState message="No experiment data" />
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-[var(--fg-muted)]">
            <span>Key: {result.experiment_key}</span>
            <span>{result.total_events} events</span>
          </div>
          <div className="space-y-3">
            {Object.entries(result.variants).map(([variant, stats]) => (
              <div key={variant} className="p-3 rounded-lg bg-[var(--surface-2)] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-[var(--fg-0)]">Variant {variant}</span>
                  <span className="text-xs text-[var(--fg-muted)]">{stats.total} samples</span>
                </div>
                <div className="space-y-1.5">
                  <RateBar label="Accept" rate={stats.accept_rate} color="bg-emerald-500" />
                  <RateBar label="Edit" rate={stats.edit_rate} color="bg-amber-500" />
                  <RateBar label="Reject" rate={stats.reject_rate} color="bg-rose-500" />
                </div>
                <div className="text-xs text-[var(--fg-muted)]">
                  Avg completion: {stats.avg_completion_seconds.toFixed(1)}s
                </div>
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

function RateBar({ label, rate, color }: { label: string; rate: number; color: string }) {
  const pct = Math.min(100, Math.max(0, rate * 100));
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-[var(--fg-muted)] w-14 shrink-0">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-[var(--surface-1)] overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-[var(--fg-muted)] w-12 text-right">{(rate * 100).toFixed(1)}%</span>
    </div>
  );
}
