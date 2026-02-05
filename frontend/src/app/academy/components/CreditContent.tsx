"use client";

import { FREE_TRIAL_URL, type TabKey } from "../constants";
import { PageHeader, ContentCard, NextStepButton } from "./shared";

interface CreditContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function CreditContent({ setActiveTab }: CreditContentProps) {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="$300 무료 크레딧" sub="Google Cloud 가입하면 90일간 40만원 상당 무료" />

      {/* Step 1 */}
      <ContentCard highlight>
        <div className="flex items-center gap-3 mb-4">
          <span className="w-7 h-7 rounded-full bg-emerald-500/20 text-emerald-400 text-sm font-bold flex items-center justify-center">1</span>
          <p className="text-white font-bold">무료 크레딧 신청</p>
        </div>
        <div className="space-y-3 text-sm text-gray-300 mb-4">
          <div className="flex gap-3"><span className="text-emerald-400 font-bold">1.</span><span>아래 버튼 클릭해서 신청 페이지로 이동</span></div>
          <div className="flex gap-3"><span className="text-emerald-400 font-bold">2.</span><span>Google 계정으로 로그인</span></div>
          <div className="flex gap-3"><span className="text-emerald-400 font-bold">3.</span><span>결제 정보 입력</span></div>
        </div>
        <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 mb-6">
          <p className="text-emerald-300 text-sm">결제 정보 입력해도 바로 결제 안 됨</p>
          <p className="text-emerald-300/70 text-xs mt-1">$300 크레딧 먼저 소진 / 유료 전환 버튼 안 누르면 자동 결제 없음</p>
        </div>
        <a
          href={FREE_TRIAL_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full py-4 bg-white text-gray-900 font-bold text-center rounded-xl hover:bg-gray-100 transition-all"
        >
          $300 무료 크레딧 받기
        </a>
      </ContentCard>

      {/* Step 2 */}
      <ContentCard>
        <div className="flex items-center gap-3 mb-4">
          <span className="w-7 h-7 rounded-full bg-purple-500/20 text-purple-400 text-sm font-bold flex items-center justify-center">2</span>
          <p className="text-white font-bold">API Key 만들기</p>
        </div>
        <div className="space-y-3 text-sm text-gray-300 mb-4">
          <div className="flex gap-3"><span className="text-purple-400 font-bold">1.</span><span>아래 버튼 클릭 → Google AI Studio 이동</span></div>
          <div className="flex gap-3"><span className="text-purple-400 font-bold">2.</span><span>왼쪽 위 파란색 "Create API Key" 버튼 클릭</span></div>
          <div className="flex gap-3"><span className="text-purple-400 font-bold">3.</span><span>생성된 키(AIza...) 복사</span></div>
        </div>
        <a
          href="https://aistudio.google.com/app/apikey"
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full py-3 bg-white text-gray-900 font-bold text-center rounded-xl hover:bg-gray-100 transition-all"
        >
          Google AI Studio 열기
        </a>
      </ContentCard>

      {/* Step 3 */}
      <ContentCard>
        <div className="flex items-center gap-3 mb-4">
          <span className="w-7 h-7 rounded-full bg-pink-500/20 text-pink-400 text-sm font-bold flex items-center justify-center">3</span>
          <p className="text-white font-bold">키 입력</p>
        </div>
        <div className="space-y-2 text-sm text-gray-300">
          <p>앱 사이드바 하단 → <span className="text-white font-medium">API Key</span> 버튼 클릭</p>
          <p>→ 복사한 키 붙여넣기</p>
        </div>
      </ContentCard>

      {/* 주의사항 */}
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">주의사항</h3>
        <div className="space-y-3 text-sm">
          <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
            <p className="text-yellow-300 font-medium">90일(3개월) 한정</p>
            <p className="text-yellow-300/70 text-xs mt-1">$300 다 쓰거나 90일 지나면 종료</p>
          </div>
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
            <p className="text-red-300 font-medium">사용량 반영 시간차 있음</p>
            <p className="text-red-300/70 text-xs mt-1">실시간 아님 → 남은 크레딧 자주 확인</p>
          </div>
          <div className="p-3 rounded-lg bg-gray-500/10 border border-gray-500/20">
            <p className="text-gray-300 font-medium">크레딧 확인</p>
            <p className="text-gray-300/70 text-xs mt-1">Google Cloud Console → 결제 → 크레딧</p>
          </div>
        </div>
      </ContentCard>

      <p className="text-center text-xs text-gray-600">API Key는 브라우저에만 저장되고 서버로 전송되지 않음</p>

      <NextStepButton onClick={() => setActiveTab("upload")} label="영상 업로드" />
    </div>
  );
}
