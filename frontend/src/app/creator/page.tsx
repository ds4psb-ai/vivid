"use client";

import { useMemo } from "react";
import Link from "next/link";
import {
  ArrowUpRight,
  BarChart3,
  ArrowUpRight as ArrowUpRightSmall,
  FlaskConical,
  LayoutDashboard,
  MessageSquareText,
  ShieldCheck,
  Wallet,
} from "lucide-react";
import CreatorPageFrame from "./_components/CreatorPageFrame";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useLanguage } from "@/contexts/LanguageContext";
import { StatCard, type StatTone } from "@/components/shared/StatCard";
import type { LucideIcon } from "lucide-react";

interface StripeStatConfig {
  label: string;
  value: string;
  helper: string;
  icon: LucideIcon;
  tone: StatTone;
}

export default function CreatorHubPage() {
  const { language } = useLanguage();

  const copy = useMemo(() => {
    const ko = language === "ko";
    return {
      title: ko ? "크리에이터 허브" : "Creator Hub",
      subtitle: ko
        ? "HITL 승인, 피드백, 실험, 정산을 한곳에서 관리하는 운영 허브입니다."
        : "Operate HITL approvals, feedback loops, experiments, and settlements in one hub.",
      kpiTitle: ko ? "운영 KPI 요약" : "Operational KPI Snapshot",
      kpiDesc: ko
        ? "승인 SLA, 피드백 처리율, 정산 상태를 한눈에 확인하세요."
        : "Track approval SLA, feedback throughput, and settlement status at a glance.",
      kpiCtaPrimary: ko ? "승인 게이트 열기" : "Open Approval Gate",
      kpiCtaSecondary: ko ? "대시보드 보기" : "View Dashboard",
      summary: ko ? "운영 요약" : "Operational Summary",
      cards: {
        approvals: ko ? "승인 대기" : "Pending Approvals",
        feedback: ko ? "피드백 루프" : "Feedback Loop",
        experiments: ko ? "실험 진행" : "Active Experiments",
      },
      helper: {
        approvals: ko ? "최근 24시간 기준 (연동 예정)" : "Last 24h snapshot (pending data)",
        feedback: ko ? "학습 파이프라인 상태" : "Learning pipeline status",
        experiments: ko ? "실험 변형 운영 현황" : "Experiment variants running",
      },
      sections: ko ? "핵심 섹션" : "Core Sections",
      sectionDesc: ko
        ? "각 모듈로 바로 이동해 작업을 이어가세요."
        : "Jump into each module to continue operations.",
      items: [
        {
          title: ko ? "크리에이터 대시보드" : "Creator Dashboard",
          desc: ko ? "핵심 성과 지표와 승인 대기 상태를 확인합니다." : "Review KPIs and approval queues.",
          href: "/creator/dashboard",
          icon: LayoutDashboard,
          badge: ko ? "LIVE" : "LIVE",
        },
        {
          title: ko ? "승인 게이트" : "Approval Gate",
          desc: ko ? "신뢰도 기반 승인 요청을 확인하고 피드백을 남깁니다." : "Review HITL approvals and feedback.",
          href: "/creator/approvals",
          icon: ShieldCheck,
          badge: ko ? "HITL" : "HITL",
        },
        {
          title: ko ? "피드백 루프" : "Feedback Loop",
          desc: ko ? "사용자 피드백과 학습 진행 상황을 추적합니다." : "Track feedback ingestion and learning.",
          href: "/creator/feedback",
          icon: MessageSquareText,
          badge: ko ? "NEW" : "NEW",
        },
        {
          title: ko ? "A/B 실험" : "A/B Experiments",
          desc: ko ? "실험 변형을 관리하고 성과를 비교합니다." : "Manage experiment variants and compare lift.",
          href: "/creator/experiments",
          icon: FlaskConical,
          badge: ko ? "BETA" : "BETA",
        },
        {
          title: ko ? "크리에이터 분석" : "Creator Analytics",
          desc: ko ? "성과·리스크·이상 탐지를 통합적으로 확인합니다." : "Unified view of performance and risks.",
          href: "/creator/analytics",
          icon: BarChart3,
          badge: ko ? "INSIGHTS" : "INSIGHTS",
        },
        {
          title: ko ? "정산" : "Settlements",
          desc: ko ? "수익 정산 및 지급 현황을 관리합니다." : "Manage revenue settlements and payouts.",
          href: "/settlements",
          icon: Wallet,
          badge: ko ? "FINANCE" : "FINANCE",
        },
      ],
    };
  }, [language]);

  const stats: StripeStatConfig[] = [
    {
      label: copy.cards.approvals,
      value: "—",
      helper: copy.helper.approvals,
      icon: ShieldCheck,
      tone: "warning",
    },
    {
      label: copy.cards.feedback,
      value: "—",
      helper: copy.helper.feedback,
      icon: MessageSquareText,
      tone: "info",
    },
    {
      label: copy.cards.experiments,
      value: "—",
      helper: copy.helper.experiments,
      icon: FlaskConical,
      tone: "neutral",
    },
  ];

  return (
    <CreatorPageFrame title={copy.title} subtitle={copy.subtitle} badge="HITL PHASE 7">
      <div className="space-y-6">
        <Card className="border border-white/5 bg-[var(--surface-1)]/70 overflow-hidden">
          <div className="h-1 w-full bg-gradient-to-r from-violet-500/70 via-sky-500/50 to-emerald-500/50" />
          <CardContent className="p-5 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-2">
              <Badge variant="secondary" className="text-[10px]">
                KPI SNAPSHOT
              </Badge>
              <div className="text-base font-semibold text-[var(--fg-0)]">{copy.kpiTitle}</div>
              <p className="text-xs text-[var(--fg-muted)]">{copy.kpiDesc}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link href="/creator/approvals">
                <Button size="sm" className="gap-2">
                  {copy.kpiCtaPrimary}
                  <ArrowUpRightSmall className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/creator/dashboard">
                <Button variant="outline" size="sm" className="gap-2">
                  {copy.kpiCtaSecondary}
                  <ArrowUpRightSmall className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <div className="text-sm font-semibold text-[var(--fg-0)]">{copy.summary}</div>
          <div className="grid gap-4 md:grid-cols-3">
            {stats.map((stat) => (
              <StatCard key={stat.label} variant="stripe" {...stat} />
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <div className="text-sm font-semibold text-[var(--fg-0)]">{copy.sections}</div>
            <p className="text-xs text-[var(--fg-muted)]">{copy.sectionDesc}</p>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {copy.items.map((item) => (
              <Link key={item.title} href={item.href} className="group">
                <Card className="border border-white/5 bg-[var(--surface-1)]/70 transition-all group-hover:border-violet-500/30 group-hover:-translate-y-0.5">
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        <div className="h-10 w-10 rounded-xl bg-violet-500/10 text-violet-400 flex items-center justify-center">
                          <item.icon className="h-5 w-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <div className="text-sm font-semibold text-[var(--fg-0)]">{item.title}</div>
                            <Badge variant="secondary" className="text-[10px]">
                              {item.badge}
                            </Badge>
                          </div>
                          <p className="mt-2 text-xs text-[var(--fg-muted)]">{item.desc}</p>
                        </div>
                      </div>
                      <ArrowUpRight className="h-4 w-4 text-violet-400 opacity-0 transition group-hover:opacity-100" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </CreatorPageFrame>
  );
}
