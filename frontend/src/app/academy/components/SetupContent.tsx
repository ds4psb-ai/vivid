"use client";

import { TOOL_LINKS, type TabKey } from "../constants";
import { PageHeader, ContentCard, WhiteButton, NextStepButton } from "./shared";

interface SetupContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function SetupContent({ setActiveTab }: SetupContentProps) {
  return (
    <div className="mx-auto w-full max-w-[var(--academy-content-max)] space-y-4">
      <PageHeader title="시작" sub="필수 연결만 빠르게" />

      <ContentCard highlight>
        <h3 className="mb-3 text-base font-semibold text-[var(--fg-0)]">Google AI Pro</h3>
        <WhiteButton
          href="https://one.google.com/ai?utm_source=gemini&utm_medium=web&utm_campaign=geminiplanspage&sc=EgIIAQ&hl=ko&icid=geminiplanspage&g1_landing_page=75"
        >
          열기
        </WhiteButton>
      </ContentCard>

      <ContentCard>
        <h3 className="mb-3 text-base font-semibold text-[var(--fg-0)]">Antigravity</h3>
        <WhiteButton href={TOOL_LINKS.antigravity}>다운로드</WhiteButton>
      </ContentCard>

      <ContentCard>
        <h3 className="mb-3 text-base font-semibold text-[var(--fg-0)]">바로가기</h3>
        <div className="space-y-2">
          <WhiteButton href={TOOL_LINKS.builder}>프롬프터</WhiteButton>
          <WhiteButton href={TOOL_LINKS.vibe}>철학관</WhiteButton>
        </div>
      </ContentCard>

      <NextStepButton onClick={() => setActiveTab("credit")} label="다음: 크레딧" />
    </div>
  );
}
