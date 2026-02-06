"use client";

import type { AnchorInfo } from "@/lib/builder2-md-parser";
import { ContentCard } from "../shared";
import { AnchorHint } from "./AnchorHint";

interface AnchorGuidePanelProps {
  anchors: AnchorInfo[];
}

export function AnchorGuidePanel({ anchors }: AnchorGuidePanelProps) {
  if (anchors.length === 0) return null;

  return (
    <ContentCard>
      <div className="flex items-center gap-2 mb-4">
        <span className="material-symbols-outlined text-[var(--color-brand-primary)]">keep</span>
        <h3 className="text-lg font-bold text-[var(--fg-0)]">앵커</h3>
        <AnchorHint />
      </div>

      <div className="space-y-3">
        {anchors.map(anchor => (
          <div
            key={anchor.key}
            className="p-4 rounded-lg border border-[var(--border-muted)] bg-[var(--surface-2)]"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">{anchor.emoji}</span>
              <div>
                <h4 className="font-bold text-[var(--fg-0)]">{anchor.key} ANCHOR</h4>
                <p className="text-sm text-[var(--fg-muted)]">Scene {String(anchor.sceneNum).padStart(2, "0")}</p>
              </div>
            </div>

            <div className="mt-3 grid gap-2 text-xs">
              <code className="rounded bg-[var(--surface-3)] px-2 py-1 font-mono text-[var(--fg-0)]">
                {anchor.frameFile}
              </code>
              <code className="rounded bg-[var(--surface-3)] px-2 py-1 font-mono text-emerald-700 dark:text-emerald-300">
                anchor_{anchor.key.toLowerCase()}.jpg
              </code>
            </div>
          </div>
        ))}
      </div>
    </ContentCard>
  );
}
