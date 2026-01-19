"use client";

import CreatorPageFrame from "../_components/CreatorPageFrame";

export default function CreatorFeedbackPage() {
  return (
    <CreatorPageFrame
      title="피드백 루프"
      subtitle="사용자 피드백이 학습 파이프라인으로 반영되는 상태를 추적합니다."
      badge="FEEDBACK LOOP"
      placeholders={[
        {
          title: "긍정 피드백 수집",
          description: "RAG 인덱싱 대상 피드백을 정리합니다.",
        },
        {
          title: "부정 피드백 교정",
          description: "수정 요청과 검토 플래그가 표시됩니다.",
          tone: "warning",
        },
        {
          title: "학습 사이클",
          description: "일일/주간 학습 사이클 진행 상황을 확인합니다.",
        },
      ]}
    />
  );
}
