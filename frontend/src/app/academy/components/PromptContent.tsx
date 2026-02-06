"use client";

import { TOOL_LINKS, type TabKey } from "../constants";
import { PageHeader, ContentCard, WhiteButton, NextStepButton } from "./shared";

interface PromptContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function PromptContent({ setActiveTab }: PromptContentProps) {
  return (
    <div className="mx-auto w-full max-w-[var(--academy-content-max)] space-y-4">
      <PageHeader title="프롬프터" sub="열고 바로 생성" />

      <ContentCard highlight>
        <WhiteButton href={TOOL_LINKS.builder} large>
          프롬프터 열기
        </WhiteButton>
      </ContentCard>

      <ContentCard>
        <h3 className="mb-3 text-base font-semibold text-[var(--fg-0)]">모드</h3>
        <div className="grid grid-cols-2 gap-2">
          <div className="inline-flex min-h-11 items-center justify-center rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] text-sm font-medium text-[var(--fg-0)]">
            오마주
          </div>
          <div className="inline-flex min-h-11 items-center justify-center rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] text-sm font-medium text-[var(--fg-0)]">
            변주
          </div>
        </div>
      </ContentCard>

      <ContentCard>
        <h3 className="mb-3 text-base font-semibold text-[var(--fg-0)]">빠른 이동</h3>
        <div className="grid gap-2 sm:grid-cols-2">
          <WhiteButton href={TOOL_LINKS.vibe}>철학관</WhiteButton>
          <button
            type="button"
            onClick={() => setActiveTab("parse")}
            className="inline-flex min-h-11 items-center justify-between rounded-xl border border-[var(--border-muted)] bg-[var(--fg-0)] px-4 text-sm font-semibold text-[var(--bg-0)] transition-opacity hover:opacity-90"
          >
            <span className="inline-flex items-center gap-2">
              <span className="material-symbols-outlined text-[18px]" aria-hidden>
                add
              </span>
              파싱
            </span>
            <span className="material-symbols-outlined text-[18px] opacity-80" aria-hidden>
              arrow_forward
            </span>
          </button>
        </div>
      </ContentCard>

      <NextStepButton onClick={() => setActiveTab("parse")} label="다음: 파싱" />
    </div>
  );
}
