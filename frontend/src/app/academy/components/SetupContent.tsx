"use client";

import { TOOL_LINKS, type TabKey } from "../constants";
import { PageHeader, ContentCard, WhiteButton, NextStepButton } from "./shared";

interface SetupContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function SetupContent({ setActiveTab }: SetupContentProps) {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="환경 설정" sub="필수 2단계만 완료하면 시작할 수 있습니다" />
      <ContentCard highlight>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-3">1. Google AI Pro 구독</h3>
        <p className="text-[var(--fg-muted)] mb-4">
          통합빌더, Veo/Flow 등 핵심 기능 사용을 위해 필요합니다.
        </p>
        <a
          href="https://one.google.com/ai?utm_source=gemini&utm_medium=web&utm_campaign=geminiplanspage&sc=EgIIAQ&hl=ko&icid=geminiplanspage&g1_landing_page=75"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--color-brand-primary)] text-white text-sm font-bold hover:opacity-90 transition-all"
        >
          Google AI Pro 열기
          <span className="material-symbols-outlined text-sm">open_in_new</span>
        </a>
        <details className="mt-4 rounded-lg border border-[var(--border-muted)] bg-[var(--surface-2)] p-3">
          <summary className="cursor-pointer text-sm font-semibold text-[var(--fg-0)]">
            상세 포함 기능 보기
          </summary>
          <ul className="mt-3 text-[var(--fg-muted)] text-sm space-y-1">
            <li>Antigravity</li>
            <li>NanoBanana Pro</li>
            <li>Veo 3.1 + Flow</li>
            <li>AI 크레딧/스토리지 포함</li>
          </ul>
        </details>
      </ContentCard>

      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-3">2. Antigravity 설치</h3>
        <p className="text-[var(--fg-muted)] mb-4">
          프레임 추출과 파일 정리를 자동화합니다.
        </p>
        <WhiteButton href={TOOL_LINKS.antigravity}>Antigravity 다운로드</WhiteButton>
      </ContentCard>

      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-4">빠른 시작</h3>
        <div className="space-y-3">
          <WhiteButton href={TOOL_LINKS.builder}>통합빌더</WhiteButton>
          <WhiteButton href={TOOL_LINKS.vibe}>바이브 철학관 (선택)</WhiteButton>
        </div>
      </ContentCard>

      <NextStepButton onClick={() => setActiveTab("credit")} label="$300 무료 크레딧" />
    </div>
  );
}
