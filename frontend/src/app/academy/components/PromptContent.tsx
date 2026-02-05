"use client";

import { TOOL_LINKS, type TabKey } from "../constants";
import { PageHeader, ContentCard, WhiteButton, NextStepButton } from "./shared";

interface PromptContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function PromptContent({ setActiveTab }: PromptContentProps) {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="통합빌더" sub="영상 → 씬 분석 → 이미지/모션 프롬프트 생성" />
      <ContentCard highlight>
        <WhiteButton href={TOOL_LINKS.builder} large>🎬 통합빌더 열기</WhiteButton>
        <p className="text-gray-500 text-xs mt-3 text-center">Google AI Studio에서 실행됩니다</p>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">워크플로우</h3>
        <div className="space-y-3 text-sm">
          <div className="flex gap-3"><span className="text-purple-400 font-bold">STEP 1</span><span className="text-gray-300">씬 분석 + 오마주 스타일 입력</span></div>
          <div className="flex gap-3"><span className="text-purple-400 font-bold">STEP 2</span><span className="text-gray-300">IMAGE 프롬프트 생성</span></div>
          <div className="flex gap-3"><span className="text-purple-400 font-bold">STEP 3</span><span className="text-gray-300">MOTION 프롬프트 생성</span></div>
          <div className="flex gap-3"><span className="text-purple-400 font-bold">STEP 4</span><span className="text-gray-300">오마주 워크플로우 다운로드</span></div>
          <div className="flex gap-3"><span className="text-cyan-400 font-bold">STEP 5</span><span className="text-gray-300">변주 워크플로우 (선택)</span></div>
        </div>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">오마주 vs 변주</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20">
            <p className="text-purple-400 font-bold mb-2">🎭 오마주 (STEP 4)</p>
            <p className="text-gray-400 text-sm">구도/타이밍 100% 유지</p>
            <p className="text-gray-500 text-xs mt-2">인종/문화/의상만 변경</p>
          </div>
          <div className="p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/20">
            <p className="text-cyan-400 font-bold mb-2">✨ 변주 (STEP 5)</p>
            <p className="text-gray-400 text-sm">구도/내용 변경 가능</p>
            <p className="text-gray-500 text-xs mt-2">A/B/C 옵션 선택</p>
          </div>
        </div>
        {/* 변주 개인화 팁 */}
        <div className="mt-4 p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
          <p className="text-purple-300 text-sm flex items-center gap-2">
            <span className="material-symbols-outlined text-base">psychology</span>
            <span>
              <strong>변주 개인화 팁:</strong> 바이브 철학관에서 프로필을 만들면 나만의 감성이 담긴 변주를 생성할 수 있어요!
            </span>
          </p>
          <a
            href={TOOL_LINKS.vibe}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 inline-flex items-center gap-1.5 text-purple-400 text-xs hover:text-purple-300 transition-colors"
          >
            <span>🔮 바이브 철학관 열기</span>
            <span className="material-symbols-outlined text-sm">open_in_new</span>
          </a>
        </div>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">다운로드 후 다음 단계</h3>
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
          <p className="text-emerald-300 text-sm mb-2">📥 오마쥬.md 또는 변주.md 다운로드 완료 후</p>
          <p className="text-emerald-400 font-medium">→ 파싱 + 복사 탭에서 씬별 프롬프트 복사</p>
        </div>
      </ContentCard>

      <NextStepButton onClick={() => setActiveTab("parse")} label="파싱 + 복사" />
    </div>
  );
}
