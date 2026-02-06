"use client";

import { FREE_TRIAL_URL, type TabKey } from "../constants";
import { PageHeader, ContentCard, NextStepButton } from "./shared";

interface CreditContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function CreditContent({ setActiveTab }: CreditContentProps) {
  return (
    <div className="mx-auto w-full max-w-[var(--academy-content-max)] space-y-4">
      <PageHeader title="크레딧" sub="3단계" />

      <ContentCard highlight>
        <h3 className="mb-3 text-base font-semibold text-[var(--fg-0)]">1. 무료 크레딧</h3>
        <a
          href={FREE_TRIAL_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex min-h-11 w-full items-center justify-between rounded-xl bg-[var(--fg-0)] px-4 text-sm font-semibold text-[var(--bg-0)] transition-opacity hover:opacity-90"
        >
          <span className="inline-flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px]" aria-hidden>
              add
            </span>
            $300 받기
          </span>
          <span className="material-symbols-outlined text-[18px] opacity-80" aria-hidden>
            north_east
          </span>
        </a>
      </ContentCard>

      <ContentCard>
        <h3 className="mb-3 text-base font-semibold text-[var(--fg-0)]">2. API Key</h3>
        <a
          href="https://aistudio.google.com/app/apikey"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex min-h-11 w-full items-center justify-between rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] px-4 text-sm font-semibold text-[var(--fg-0)] transition-colors hover:bg-[var(--surface-3)]"
        >
          <span className="inline-flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px] text-[var(--color-brand-primary)]" aria-hidden>
              add
            </span>
            AI Studio 열기
          </span>
          <span className="material-symbols-outlined text-[18px] text-[var(--fg-muted)]" aria-hidden>
            north_east
          </span>
        </a>
      </ContentCard>

      <ContentCard>
        <h3 className="mb-2 text-base font-semibold text-[var(--fg-0)]">3. 앱 입력</h3>
        <p className="text-sm text-[var(--fg-muted)]">`API Key` 버튼에 붙여넣기</p>
      </ContentCard>

      <NextStepButton onClick={() => setActiveTab("upload")} label="다음: 업로드" />
    </div>
  );
}
