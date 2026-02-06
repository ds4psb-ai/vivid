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
        <WhiteButton href={TOOL_LINKS.builder} large>통합빌더 열기</WhiteButton>
        <p className="text-[var(--fg-muted)] text-xs mt-3 text-center">Google AI Studio에서 실행됩니다</p>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-4">핵심 순서</h3>
        <div className="space-y-2 text-sm text-[var(--fg-muted)]">
          <div>1. 씬 분석 + 오마주 스타일 입력</div>
          <div>2. IMAGE 프롬프트 생성</div>
          <div>3. MOTION 프롬프트 생성</div>
          <div>4. 오마주 워크플로우 다운로드</div>
          <div>5. 변주 워크플로우 (선택)</div>
        </div>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-4">오마주 vs 변주</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-[var(--surface-2)] border border-[var(--border-muted)]">
            <p className="text-[var(--color-brand-primary)] font-bold mb-2">오마주 (STEP 4)</p>
            <p className="text-[var(--fg-muted)] text-sm">구도/타이밍 유지</p>
            <p className="text-[var(--fg-muted)] text-xs mt-2">문화/의상 등 요소만 변경</p>
          </div>
          <div className="p-4 rounded-xl bg-[var(--surface-2)] border border-[var(--border-muted)]">
            <p className="text-[var(--info)] font-bold mb-2">변주 (STEP 5)</p>
            <p className="text-[var(--fg-muted)] text-sm">구도/내용 변경 가능</p>
            <p className="text-[var(--fg-muted)] text-xs mt-2">A/B/C 옵션 선택</p>
          </div>
        </div>
        <div className="mt-4 p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--border-muted)]">
          <p className="text-[var(--fg-muted)] text-sm flex items-center gap-2">
            <span className="material-symbols-outlined text-base">psychology</span>
            <span>
              <strong>변주 개인화:</strong> 바이브 철학관 프로필을 연결하면 개인화 품질이 높아집니다.
            </span>
          </p>
          <a
            href={TOOL_LINKS.vibe}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 inline-flex items-center gap-1.5 text-[var(--color-brand-primary)] text-xs hover:opacity-85 transition-colors"
          >
            <span>바이브 철학관 열기</span>
            <span className="material-symbols-outlined text-sm">open_in_new</span>
          </a>
        </div>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-4">다음 단계</h3>
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
          <p className="text-emerald-700 dark:text-emerald-300 text-sm mb-2">
            오마주.md 또는 변주.md 다운로드 후
          </p>
          <p className="text-emerald-800 dark:text-emerald-400 font-medium">
            `파싱 + 복사` 탭에서 씬별 프롬프트를 복사하세요.
          </p>
        </div>
      </ContentCard>

      <NextStepButton onClick={() => setActiveTab("parse")} label="파싱 + 복사" />
    </div>
  );
}
