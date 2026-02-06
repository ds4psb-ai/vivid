"use client";

import { TOOL_LINKS } from "../constants";
import { PageHeader, ContentCard, WhiteButton } from "./shared";

export function VibeContent() {
  return (
    <div className="mx-auto w-full max-w-[var(--academy-content-max)] space-y-4">
      <PageHeader title="바이브" sub="저장 후 변주" />
      <ContentCard highlight>
        <WhiteButton href={TOOL_LINKS.vibe} large>
          바이브 열기
        </WhiteButton>
      </ContentCard>
    </div>
  );
}
