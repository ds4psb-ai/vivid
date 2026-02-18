"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { FoundryPatternExtractionResponse } from "@/lib/api";
import { useFoundryData } from "@/hooks/useFoundryData";
import { FoundryPanelCard, ScoreBar, FoundryEmptyState } from "./shared";
import { DEMO_PATTERN_REQUEST, DEMO_PATTERN_RESPONSE } from "./demo-data";

export function PatternLibraryPanel() {
  const [useDemo, setUseDemo] = useState(false);

  const { data, isLoading, error, refresh } = useFoundryData<FoundryPatternExtractionResponse>(
    async () => {
      try {
        return await api.extractFoundryPatterns(DEMO_PATTERN_REQUEST);
      } catch {
        setUseDemo(true);
        return DEMO_PATTERN_RESPONSE;
      }
    }
  );

  const result = data || (useDemo ? DEMO_PATTERN_RESPONSE : null);

  return (
    <FoundryPanelCard title="Pattern Library" isLoading={isLoading} error={error} onRefresh={refresh}>
      {!result ? (
        <FoundryEmptyState message="No patterns extracted" />
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-[var(--fg-muted)]">
            <span>Scene: {result.scene_id}</span>
            <span>{result.total_shots} shots analyzed</span>
          </div>
          <div className="space-y-3">
            {result.pattern_atoms.map((atom) => (
              <div key={atom.atom_id} className="p-3 rounded-lg bg-[var(--surface-2)] space-y-2">
                <div className="flex flex-wrap gap-1.5">
                  <AtomTag value={atom.camera_angle} />
                  <AtomTag value={atom.camera_movement} />
                  <AtomTag value={atom.shot_size} />
                  <AtomTag value={atom.emotion_tone} />
                  <AtomTag value={atom.transition} />
                </div>
                <ScoreBar score={atom.confidence} label="Confidence" />
              </div>
            ))}
          </div>
          {result.transition_rules.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-xs font-medium text-[var(--fg-muted)] uppercase">Transitions</span>
              {result.transition_rules.map((rule) => (
                <div key={rule.rule} className="flex items-center justify-between text-xs">
                  <code className="text-[var(--fg-0)] font-mono">{rule.rule}</code>
                  <span className="text-[var(--fg-muted)]">x{rule.frequency}</span>
                </div>
              ))}
            </div>
          )}
          {useDemo && (
            <p className="text-xs text-[var(--fg-muted)] italic">Demo data (API unavailable)</p>
          )}
        </div>
      )}
    </FoundryPanelCard>
  );
}

function AtomTag({ value }: { value: string }) {
  return (
    <span className="px-2 py-0.5 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-mono">
      {value}
    </span>
  );
}
