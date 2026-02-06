"use client";

import { Tooltip } from "@/components/ui/tooltip";

const ANCHOR_HELP_TEXT =
  "앵커 = 캐릭터 기준샷이에요. 먼저 1장만 고정해두면 뒤 씬에서 얼굴/스타일이 덜 흔들려요.";

export function AnchorHint() {
  return (
    <Tooltip
      content={<p className="text-xs leading-relaxed">{ANCHOR_HELP_TEXT}</p>}
      position="top"
      delay={180}
      maxWidth={280}
    >
      <button
        type="button"
        className="inline-flex items-center rounded-full border border-[var(--border-muted)] bg-[var(--surface-2)] px-2 py-0.5 text-[11px] font-semibold text-[var(--fg-muted)] hover:text-[var(--fg-0)] hover:bg-[var(--surface-3)] transition-colors"
      >
        앵커?
      </button>
    </Tooltip>
  );
}
