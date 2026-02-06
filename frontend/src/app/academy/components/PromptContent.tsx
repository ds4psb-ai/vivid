"use client";

import { TOOL_LINKS, type TabKey } from "../constants";
import { PageHeader, ContentCard, WhiteButton, NextStepButton } from "./shared";

interface PromptContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function PromptContent({ setActiveTab }: PromptContentProps) {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="통합빌더" />
      <ContentCard highlight>
        <WhiteButton href={TOOL_LINKS.builder} large>통합빌더 열기</WhiteButton>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-4">모드</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-[var(--surface-2)] border border-[var(--border-muted)]">
            <p className="text-[var(--color-brand-primary)] font-bold">오마주</p>
          </div>
          <div className="p-4 rounded-xl bg-[var(--surface-2)] border border-[var(--border-muted)]">
            <p className="text-[var(--info)] font-bold">변주</p>
          </div>
        </div>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-4">빠른 이동</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <WhiteButton href={TOOL_LINKS.vibe}>바이브</WhiteButton>
          <button
            onClick={() => setActiveTab("parse")}
            className="w-full px-6 py-4 rounded-2xl bg-[var(--fg-0)] text-[var(--bg-0)] font-bold hover:opacity-90 transition-all"
          >
            파싱
          </button>
        </div>
      </ContentCard>

      <NextStepButton onClick={() => setActiveTab("parse")} label="파싱" />
    </div>
  );
}
