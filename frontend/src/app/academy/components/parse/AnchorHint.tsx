"use client";

import { Tooltip } from "@/components/ui/tooltip";

const ANCHOR_HELP_TEXT =
  "앵커 = 캐릭터 기준샷. 한 장만 먼저 고정하면 뒤 씬 얼굴/스타일 흔들림이 줄어요.";

export function AnchorHint() {
  return (
    <Tooltip
      content={<p className="text-xs leading-relaxed">{ANCHOR_HELP_TEXT}</p>}
      position="top"
      delay={160}
      maxWidth={280}
    >
      <button
        type="button"
        className="inline-flex h-7 items-center rounded-full border border-[var(--border-muted)] bg-[var(--surface-2)] px-2 text-[11px] font-medium text-[var(--fg-muted)] transition-colors hover:text-[var(--fg-0)]"
      >
        앵커?
      </button>
    </Tooltip>
  );
}
