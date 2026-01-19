"use client";

import CreatorPageFrame from "../_components/CreatorPageFrame";

export default function CreatorApprovalsPage() {
  return (
    <CreatorPageFrame
      title="승인 게이트"
      subtitle="신뢰도 기반 HITL 승인 요청을 정리하는 뷰입니다. 자동 승인/수동 검토 기준을 한눈에 확인합니다."
      badge="APPROVAL GATE"
      placeholders={[
        {
          title: "대기 승인 큐",
          description: "검토 대기 중인 체크포인트를 큐로 제공합니다.",
        },
        {
          title: "신뢰도 기준",
          description: "자동 승인/에스컬레이션 임계값을 안내합니다.",
          tone: "info",
        },
        {
          title: "처리 기록",
          description: "최근 승인/반려 히스토리가 표시됩니다.",
        },
      ]}
    />
  );
}
