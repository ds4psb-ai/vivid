"use client";

import { FREE_TRIAL_URL, type TabKey } from "../constants";
import { PageHeader, ContentCard, NextStepButton } from "./shared";

interface CreditContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function CreditContent({ setActiveTab }: CreditContentProps) {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="크레딧" />

      <ContentCard highlight>
        <div className="flex items-center gap-3 mb-4">
          <span className="w-7 h-7 rounded-full bg-emerald-500/20 text-emerald-600 text-sm font-bold flex items-center justify-center">1</span>
          <p className="text-[var(--fg-0)] font-bold">무료 크레딧</p>
        </div>
        <a
          href={FREE_TRIAL_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full py-4 bg-[var(--fg-0)] text-[var(--bg-0)] font-bold text-center rounded-xl hover:opacity-90 transition-all"
        >
          $300 무료 크레딧 받기
        </a>
      </ContentCard>

      <ContentCard>
        <div className="flex items-center gap-3 mb-4">
          <span className="w-7 h-7 rounded-full bg-[var(--color-brand-primary)]/20 text-[var(--color-brand-primary)] text-sm font-bold flex items-center justify-center">2</span>
          <p className="text-[var(--fg-0)] font-bold">API Key 만들기</p>
        </div>
        <a
          href="https://aistudio.google.com/app/apikey"
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full py-3 bg-[var(--fg-0)] text-[var(--bg-0)] font-bold text-center rounded-xl hover:opacity-90 transition-all"
        >
          Google AI Studio 열기
        </a>
      </ContentCard>

      <ContentCard>
        <div className="flex items-center gap-3 mb-4">
          <span className="w-7 h-7 rounded-full bg-pink-500/20 text-pink-600 text-sm font-bold flex items-center justify-center">3</span>
          <p className="text-[var(--fg-0)] font-bold">앱에 키 입력</p>
        </div>
        <div className="space-y-2 text-sm text-[var(--fg-muted)]">
          <p>`API Key` 버튼에 붙여넣기</p>
        </div>
      </ContentCard>

      <NextStepButton onClick={() => setActiveTab("upload")} label="영상 업로드" />
    </div>
  );
}
