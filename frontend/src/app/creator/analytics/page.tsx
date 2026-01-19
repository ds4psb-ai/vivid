"use client";

import CreatorPageFrame from "../_components/CreatorPageFrame";

export default function CreatorAnalyticsPage() {
  return (
    <CreatorPageFrame
      title="크리에이터 분석"
      subtitle="참여도, 수익, 이상 탐지 지표를 통합적으로 보여주는 분석 대시보드입니다."
      badge="ANALYTICS"
      placeholders={[
        {
          title: "참여도 트렌드",
          description: "최근 7일/30일 참여도 변화를 시각화합니다.",
        },
        {
          title: "수익 지표",
          description: "RPV 및 수익 흐름을 요약합니다.",
          tone: "info",
        },
        {
          title: "이상 탐지",
          description: "급격한 성과 변동을 경고합니다.",
          tone: "warning",
        },
      ]}
    />
  );
}
