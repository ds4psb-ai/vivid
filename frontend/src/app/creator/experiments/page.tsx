"use client";

import CreatorPageFrame from "../_components/CreatorPageFrame";

export default function CreatorExperimentsPage() {
  return (
    <CreatorPageFrame
      title="A/B 실험"
      subtitle="생성 파라미터 실험을 구성하고 변형별 성과를 비교합니다."
      badge="A/B TESTING"
      placeholders={[
        {
          title: "실험 개요",
          description: "실행 중인 실험 요약과 상태를 제공합니다.",
        },
        {
          title: "변형 성과",
          description: "통제군/실험군 성과를 비교합니다.",
          tone: "info",
        },
        {
          title: "전환 지표",
          description: "전환율, 완료율 등 핵심 지표를 정리합니다.",
        },
      ]}
    />
  );
}
