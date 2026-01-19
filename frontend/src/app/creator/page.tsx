"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import CreatorPageFrame from "./_components/CreatorPageFrame";

export default function CreatorHubPage() {
  return (
    <CreatorPageFrame
      title="크리에이터 허브"
      subtitle="HITL 승인, 피드백, 실험, 정산을 한곳에서 관리할 수 있는 허브입니다."
      badge="HITL PHASE 7"
    >
      <div className="grid gap-4 md:grid-cols-2">
        {[
          {
            title: "크리에이터 대시보드",
            desc: "핵심 성과 지표와 승인 대기 상태를 확인합니다.",
            href: "/creator/dashboard",
          },
          {
            title: "승인 게이트",
            desc: "신뢰도 기반 승인 요청을 확인하고 피드백을 남깁니다.",
            href: "/creator/approvals",
          },
          {
            title: "피드백 루프",
            desc: "사용자 피드백과 학습 진행 상황을 추적합니다.",
            href: "/creator/feedback",
          },
          {
            title: "A/B 실험",
            desc: "실험 변형을 관리하고 성과를 비교합니다.",
            href: "/creator/experiments",
          },
        ].map((item) => (
          <Link
            key={item.title}
            href={item.href}
            className="group rounded-xl border border-white/10 bg-[var(--surface-1)]/70 p-5 transition hover:border-violet-500/30"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-sm font-semibold text-[var(--fg-0)]">{item.title}</div>
                <p className="mt-2 text-xs text-[var(--fg-muted)]">{item.desc}</p>
              </div>
              <ArrowUpRight className="h-4 w-4 text-violet-400 opacity-0 transition group-hover:opacity-100" />
            </div>
          </Link>
        ))}
      </div>
    </CreatorPageFrame>
  );
}
