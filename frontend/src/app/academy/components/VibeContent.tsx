"use client";

import { TOOL_LINKS } from "../constants";
import { PageHeader, ContentCard, WhiteButton } from "./shared";

export function VibeContent() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="바이브" />
      <ContentCard highlight>
        <WhiteButton href={TOOL_LINKS.vibe} large>바이브 열기</WhiteButton>
      </ContentCard>
      <ContentCard>
        <p className="text-sm text-[var(--fg-muted)]">저장 후 변주 품질 향상</p>
      </ContentCard>
    </div>
  );
}
