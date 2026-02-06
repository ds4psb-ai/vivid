"use client";

import type { TabKey } from "../../constants";
import { ContentCard, PageHeader } from "../shared";
import { IMAGE_TOOLS, VIDEO_TOOLS } from "./toolsData";

interface ToolsContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function ToolsContent({ setActiveTab }: ToolsContentProps) {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <PageHeader title="툴" />

      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-4">이미지</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {IMAGE_TOOLS.map((tool) => (
            <a
              key={tool.id}
              href={tool.url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-4"
            >
              <div className="flex items-center justify-between gap-2">
                <p className="font-semibold text-[var(--fg-0)]">{tool.title}</p>
                <span className="text-xs text-[var(--fg-muted)]">{tool.badge}</span>
              </div>
            </a>
          ))}
        </div>
      </ContentCard>

      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-4">영상</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {VIDEO_TOOLS.map((tool) => (
            <a
              key={tool.id}
              href={tool.url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-4"
            >
              <div className="flex items-center justify-between gap-2">
                <p className="font-semibold text-[var(--fg-0)]">{tool.title}</p>
                <span className="text-xs text-[var(--fg-muted)]">{tool.badge}</span>
              </div>
            </a>
          ))}
        </div>
      </ContentCard>

      <div className="text-center py-4">
        <button
          onClick={() => setActiveTab("homework")}
          className="px-6 py-3 rounded-xl bg-[var(--fg-0)] text-[var(--bg-0)] font-bold hover:opacity-90 transition-all inline-flex items-center gap-2"
        >
          <span className="material-symbols-outlined">assignment</span>
          과제 확인하기
        </button>
      </div>
    </div>
  );
}
