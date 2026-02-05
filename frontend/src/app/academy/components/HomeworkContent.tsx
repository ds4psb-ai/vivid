"use client";

import { PageHeader, ContentCard } from "./shared";

export function HomeworkContent() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="과제 안내" sub="📅 2강 예정: 2026년 2월 6일 (목)" />
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">필수 과제</h3>
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-white text-gray-900">
            <p className="font-bold mb-2">1. 이미지 프롬프트 생성기 완료</p>
            <ul className="text-gray-600 text-sm space-y-1">
              <li>• 본인이 선정한 바이럴 영상 분석</li>
              <li>• 결과물(.md) 저장</li>
            </ul>
          </div>
          <div className="p-4 rounded-xl bg-white text-gray-900">
            <p className="font-bold mb-2">2. 바이브 철학관 세션</p>
            <ul className="text-gray-600 text-sm space-y-1">
              <li>• 최소 50% 깊이 도달</li>
              <li>• 프로필(.json) 다운로드</li>
            </ul>
          </div>
          <div className="p-4 rounded-xl bg-white text-gray-900">
            <p className="font-bold mb-2">3. Google 계정 준비</p>
            <ul className="text-gray-600 text-sm space-y-1">
              <li>• 최소 <span className="font-bold text-purple-600">3개</span> 계정 생성</li>
              <li>• 하나의 핸드폰 번호로 5개까지 가능</li>
            </ul>
          </div>
        </div>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">제출 방법</h3>
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
          <p className="text-emerald-300 font-medium mb-2">📤 디스코드 #과제제출 채널에 업로드</p>
          <ul className="text-emerald-200/70 text-sm space-y-1">
            <li>• 이미지 프롬프트 생성기 결과물 (.md)</li>
          </ul>
        </div>
        <p className="text-gray-500 text-xs mt-3">※ 바이브 철학관 프로필은 개인정보이므로 제출하지 않습니다</p>
      </ContentCard>
    </div>
  );
}
