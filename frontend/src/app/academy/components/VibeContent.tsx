"use client";

import { TOOL_LINKS } from "../constants";
import { PageHeader, ContentCard, WhiteButton } from "./shared";

export function VibeContent() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="바이브 철학관" sub="AI와 대화하며 나의 프로필을 만들어요" />
      <ContentCard highlight>
        <WhiteButton href={TOOL_LINKS.vibe} large>바이브 철학관 열기</WhiteButton>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-4">사용법</h3>
        <div className="space-y-2 text-sm text-[var(--fg-muted)]">
          <div>1. 기본 정보 입력</div>
          <div>2. AI와 대화 진행</div>
          <div>3. 50% 이상 도달 시 프로필 저장</div>
        </div>
        <div className="mt-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <p className="text-emerald-700 dark:text-emerald-300 text-sm">
            저장한 프로필은 변주 생성의 개인화 입력으로 사용됩니다.
          </p>
        </div>
      </ContentCard>
    </div>
  );
}
