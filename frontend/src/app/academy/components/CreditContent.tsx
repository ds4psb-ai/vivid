"use client";

import { FREE_TRIAL_URL, type TabKey } from "../constants";
import { PageHeader, ContentCard, NextStepButton } from "./shared";

interface CreditContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function CreditContent({ setActiveTab }: CreditContentProps) {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="$300 무료 크레딧" sub="필수 절차 3단계" />

      <ContentCard highlight>
        <div className="flex items-center gap-3 mb-4">
          <span className="w-7 h-7 rounded-full bg-emerald-500/20 text-emerald-600 text-sm font-bold flex items-center justify-center">1</span>
          <p className="text-[var(--fg-0)] font-bold">무료 크레딧 신청</p>
        </div>
        <div className="space-y-2 text-sm text-[var(--fg-muted)] mb-4">
          <p>Google Cloud 가입 후 결제정보를 등록합니다.</p>
          <p>유료 전환 버튼을 누르지 않으면 자동 결제되지 않습니다.</p>
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
        <div className="space-y-2 text-sm text-[var(--fg-muted)] mb-4">
          <p>Google AI Studio에서 `Create API Key`를 눌러 생성합니다.</p>
          <p>생성된 키(`AIza...`)를 복사해둡니다.</p>
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
          <p>사이드바 하단 `API Key` 버튼을 열고 키를 붙여넣습니다.</p>
          <p>키는 브라우저 저장소에만 저장됩니다.</p>
        </div>
      </ContentCard>

      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-3">주의사항</h3>
        <ul className="space-y-2 text-sm text-[var(--fg-muted)]">
          <li>90일 또는 $300 소진 시 종료</li>
          <li>사용량 반영에 시간차가 있음</li>
          <li>잔여 크레딧은 Cloud Console에서 확인</li>
        </ul>
      </ContentCard>

      <NextStepButton onClick={() => setActiveTab("upload")} label="영상 업로드" />
    </div>
  );
}
