"use client";

import { TOOL_LINKS, type TabKey } from "../constants";
import { PageHeader, ContentCard, WhiteButton, NextStepButton } from "./shared";

interface SetupContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function SetupContent({ setActiveTab }: SetupContentProps) {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="환경 설정" />
      <ContentCard highlight>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-3">1. Google AI Pro</h3>
        <a
          href="https://one.google.com/ai?utm_source=gemini&utm_medium=web&utm_campaign=geminiplanspage&sc=EgIIAQ&hl=ko&icid=geminiplanspage&g1_landing_page=75"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--color-brand-primary)] text-white text-sm font-bold hover:opacity-90 transition-all"
        >
          Google AI Pro 열기
          <span className="material-symbols-outlined text-sm">open_in_new</span>
        </a>
      </ContentCard>

      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-3">2. Antigravity</h3>
        <WhiteButton href={TOOL_LINKS.antigravity}>Antigravity 다운로드</WhiteButton>
      </ContentCard>

      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-4">바로가기</h3>
        <div className="space-y-3">
          <WhiteButton href={TOOL_LINKS.builder}>통합빌더</WhiteButton>
          <WhiteButton href={TOOL_LINKS.vibe}>바이브</WhiteButton>
        </div>
      </ContentCard>

      <NextStepButton onClick={() => setActiveTab("credit")} label="크레딧" />
    </div>
  );
}
