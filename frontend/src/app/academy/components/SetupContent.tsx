"use client";

import { TOOL_LINKS, type TabKey } from "../constants";
import { PageHeader, ContentCard, WhiteButton, NextStepButton } from "./shared";

interface SetupContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function SetupContent({ setActiveTab }: SetupContentProps) {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="환경 설정" sub="Gemini Pro 구독 + Antigravity 설치" />
      <ContentCard highlight>
        <h3 className="text-lg font-bold text-white mb-4">⚡ Google AI Pro 구독 필수</h3>
        <p className="text-gray-400 mb-4">모든 핵심 도구 사용을 위해 필요합니다 (18세 이상)</p>
        <div className="p-4 rounded-xl bg-white text-gray-900">
          <p className="font-bold text-purple-600 mb-1">Google AI Pro</p>
          <div className="flex items-baseline gap-2 mb-2">
            <p className="text-2xl font-black text-gray-900">₩14,500/월</p>
            <p className="text-sm text-gray-400 line-through">₩29,000</p>
            <span className="text-xs bg-red-500 text-white px-2 py-0.5 rounded-full">2개월 프로모션</span>
          </div>
          <ul className="text-gray-600 text-sm space-y-1">
            <li>✓ <strong>Antigravity</strong> - AI 코딩 도우미</li>
            <li>✓ <strong>NanoBanana Pro</strong> - 한글 이미지 생성</li>
            <li>✓ <strong>Veo 3.1 + Flow</strong> - AI 영상 생성</li>
            <li>✓ AI 크레딧 1,000/월 (Flow, Whisk 사용)</li>
            <li>✓ 2TB 클라우드 스토리지</li>
          </ul>
          <a
            href="https://one.google.com/ai?utm_source=gemini&utm_medium=web&utm_campaign=geminiplanspage&sc=EgIIAQ&hl=ko&icid=geminiplanspage&g1_landing_page=75"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 text-white text-sm font-bold hover:bg-purple-700 transition-colors"
          >
            구독하기
            <span className="material-symbols-outlined text-sm">open_in_new</span>
          </a>
        </div>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">Antigravity 설치</h3>
        <p className="text-gray-400 mb-4">프레임 추출, 파일 정리 등을 대신 해주는 AI 코딩 도우미</p>
        <WhiteButton href={TOOL_LINKS.antigravity}>Antigravity 다운로드</WhiteButton>
        <p className="text-gray-500 text-xs mt-3">설치 후 Google 계정으로 로그인 (Pro 구독 필요)</p>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">도구 바로가기</h3>
        <div className="space-y-3">
          <WhiteButton href={TOOL_LINKS.builder}>🎬 통합빌더</WhiteButton>
          <WhiteButton href={TOOL_LINKS.vibe}>🔮 바이브 철학관</WhiteButton>
        </div>
      </ContentCard>

      <NextStepButton onClick={() => setActiveTab("credit")} label="$300 무료 크레딧" />
    </div>
  );
}
