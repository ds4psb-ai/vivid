"use client";

import { TOOL_LINKS } from "../constants";
import { PageHeader, ContentCard, WhiteButton } from "./shared";

export function VibeContent() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="바이브 철학관" sub="AI와 대화하며 나의 프로필을 만들어요" />
      <ContentCard highlight>
        <WhiteButton href={TOOL_LINKS.vibe} large>🔮 바이브 철학관 열기</WhiteButton>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">사용법</h3>
        <div className="space-y-3 text-sm">
          <div className="flex gap-3"><span className="text-purple-400 font-bold">1.</span><span className="text-gray-300">기본 정보 입력 (이름, 생년월일)</span></div>
          <div className="flex gap-3"><span className="text-purple-400 font-bold">2.</span><span className="text-gray-300">AI와 자연스럽게 대화</span></div>
          <div className="flex gap-3"><span className="text-purple-400 font-bold">3.</span><span className="text-gray-300">50% 이상 도달 시 프로필 저장</span></div>
        </div>
        <div className="mt-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <p className="text-emerald-300 text-sm">💡 저장한 프로필은 패러디 엔진에서 사용 → 나의 감성이 담긴 변주 생성</p>
        </div>
      </ContentCard>
    </div>
  );
}
