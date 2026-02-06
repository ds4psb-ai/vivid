"use client";

import type { TabKey } from "../../constants";
import { ContentCard, PageHeader } from "../shared";
import { IMAGE_TOOLS, VIDEO_TOOLS } from "./toolsData";

interface ToolsContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function ToolsContent({ setActiveTab }: ToolsContentProps) {
  return (
    <div className="mx-auto w-full max-w-[var(--academy-content-max)] space-y-4">
      <PageHeader title="툴" sub="바로 열기" />

      <ContentCard>
        <h3 className="mb-3 text-base font-semibold text-[var(--fg-0)]">이미지</h3>
        <div className="grid gap-2 sm:grid-cols-2">
          {IMAGE_TOOLS.map((tool) => (
            <a
              key={tool.id}
              href={tool.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex min-h-11 items-center justify-between rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] px-4 text-sm font-medium text-[var(--fg-0)] transition-colors hover:bg-[var(--surface-3)]"
            >
              <span className="inline-flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px] text-[var(--color-brand-primary)]" aria-hidden>
                  add
                </span>
                {tool.title}
              </span>
              <span className="material-symbols-outlined text-[18px] text-[var(--fg-muted)]" aria-hidden>
                north_east
              </span>
            </a>
          ))}
        </div>
      </ContentCard>

      <ContentCard>
        <h3 className="mb-3 text-base font-semibold text-[var(--fg-0)]">영상</h3>
        <div className="grid gap-2 sm:grid-cols-2">
          {VIDEO_TOOLS.map((tool) => (
            <a
              key={tool.id}
              href={tool.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex min-h-11 items-center justify-between rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] px-4 text-sm font-medium text-[var(--fg-0)] transition-colors hover:bg-[var(--surface-3)]"
            >
              <span className="inline-flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px] text-[var(--color-brand-primary)]" aria-hidden>
                  add
                </span>
                {tool.title}
              </span>
              <span className="material-symbols-outlined text-[18px] text-[var(--fg-muted)]" aria-hidden>
                north_east
              </span>
            </a>
          ))}
        </div>
      </ContentCard>

      <button
        type="button"
        onClick={() => setActiveTab("homework")}
        className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-[var(--fg-0)] px-4 text-sm font-semibold text-[var(--bg-0)] transition-opacity hover:opacity-90"
      >
        <span className="material-symbols-outlined text-[18px]" aria-hidden>
          arrow_forward
        </span>
        과제로 이동
      </button>
    </div>
  );
}
