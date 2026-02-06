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
      <div className="mb-3 flex items-center gap-2">
        <h3 className="text-base font-semibold text-[var(--fg-0)]">앵커</h3>
        <AnchorHint />
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        {anchors.map((anchor) => (
          <div
            key={anchor.key}
            className="rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-3"
          >
            <p className="text-sm font-semibold text-[var(--fg-0)]">
              {anchor.emoji} {anchor.key}
            </p>
            <p className="mt-1 text-xs text-[var(--fg-muted)]">
              Scene {String(anchor.sceneNum).padStart(2, "0")}
            </p>
            <div className="mt-2 space-y-1 text-xs font-mono">
              <code className="block rounded bg-[var(--surface-3)] px-2 py-1 text-[var(--fg-0)]">
                {anchor.frameFile}
              </code>
              <code className="block rounded bg-[var(--surface-3)] px-2 py-1 text-emerald-700 dark:text-emerald-300">
                anchor_{anchor.key.toLowerCase()}.jpg
              </code>
            </div>
          </div>
        ))}
      </div>
    </ContentCard>
  );
}
