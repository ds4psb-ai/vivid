"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Filter,
  MessageSquareText,
  ShieldCheck,
  Timer,
} from "lucide-react";
import CreatorPageFrame from "../_components/CreatorPageFrame";
import { PendingApprovalsPanel } from "@/components/creator/PendingApprovalsPanel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useLanguage } from "@/contexts/LanguageContext";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string;
  helper: string;
  icon: React.ElementType;
  tone?: "success" | "warning" | "neutral" | "info";
}

function StatCard({ title, value, helper, icon: Icon, tone = "neutral" }: StatCardProps) {
  const toneStyles = {
    success: "bg-emerald-500/10 text-emerald-400",
    warning: "bg-amber-500/10 text-amber-400",
    neutral: "bg-slate-500/10 text-slate-300",
    info: "bg-violet-500/10 text-violet-400",
  };

  return (
    <Card className="border border-white/5 bg-[var(--surface-1)]/70">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn("h-10 w-10 rounded-xl flex items-center justify-center", toneStyles[tone])}>
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs text-[var(--fg-muted)]">{title}</p>
              <p className="text-xl font-semibold text-[var(--fg-0)]">{value}</p>
            </div>
          </div>
          <Badge variant="outline" className="text-xs">
            BETA
          </Badge>
        </div>
        <p className="mt-3 text-xs text-[var(--fg-subtle)]">{helper}</p>
      </CardContent>
    </Card>
  );
}

export default function CreatorApprovalsPage() {
  const { language } = useLanguage();

  const copy = useMemo(() => {
    const ko = language === "ko";
    return {
      title: ko ? "승인 게이트" : "Approval Gate",
      subtitle: ko
        ? "HITL 승인 큐를 운영하고 신뢰도 기준을 조정하는 컨트롤 타워입니다."
        : "Operate HITL approval queues and tune confidence-based routing.",
      overview: ko ? "승인 운영 현황" : "Approval Overview",
      filters: ko ? "큐 필터" : "Queue Filters",
      filtersDesc: ko
        ? "신뢰도, 상태, 차원별로 승인 요청을 분류하세요."
        : "Filter approval requests by confidence, status, and dimension.",
      policy: ko ? "승인 정책" : "Approval Policy",
      policyDesc: ko
        ? "자동 승인/에스컬레이션 기준과 SLA를 확인합니다."
        : "Review auto-approval thresholds and SLA targets.",
      history: ko ? "최근 처리 기록" : "Recent Resolutions",
      historyDesc: ko
        ? "최근 승인/반려 기록을 요약합니다."
        : "Snapshot of recent approve/reject actions.",
      searchPlaceholder: ko ? "체크포인트, 노드, 키워드 검색" : "Search checkpoint, node, keyword",
      filterAll: ko ? "전체" : "All",
      filterNeedsReview: ko ? "검토 필요" : "Needs Review",
      filterEscalated: ko ? "에스컬레이션" : "Escalated",
      filterAuto: ko ? "자동 승인" : "Auto Approved",
      filterExpiring: ko ? "만료 임박" : "Expiring Soon",
      filterDimension: ko ? "차원별 필터" : "Dimension Filters",
      actionExport: ko ? "CSV 내보내기" : "Export CSV",
      actionPolicy: ko ? "정책 업데이트 요청" : "Request Policy Update",
      autoApprove: ko ? "자동 승인율" : "Auto-Approval Rate",
      pendingQueue: ko ? "대기 승인" : "Pending Queue",
      avgLatency: ko ? "평균 처리 시간" : "Avg. Resolution",
      sla: ko ? "SLA 준수율" : "SLA Compliance",
      helperAuto: ko ? "최근 7일 기준 (연동 예정)" : "Last 7 days (pending data)",
      helperQueue: ko ? "현재 큐 상태 (연동 예정)" : "Current queue snapshot (pending data)",
      helperLatency: ko ? "승인 완료까지 평균 소요 (연동 예정)" : "Avg time to resolve (pending data)",
      helperSla: ko ? "승인 SLA 기준 충족률 (연동 예정)" : "Percent meeting SLA (pending data)",
      policyItems: [
        {
          label: ko ? "자동 승인" : "Auto approve",
          value: ko ? "신뢰도 ≥ 0.85" : "Confidence ≥ 0.85",
        },
        {
          label: ko ? "수동 검토" : "Manual review",
          value: ko ? "0.50 ~ 0.85" : "0.50 ~ 0.85",
        },
        {
          label: ko ? "에스컬레이션" : "Escalation",
          value: ko ? "신뢰도 < 0.50" : "Confidence < 0.50",
        },
        {
          label: ko ? "기본 SLA" : "Default SLA",
          value: ko ? "60분 이내 응답" : "60 min response",
        },
      ],
      routingNotesTitle: ko ? "라우팅 가이드" : "Routing Notes",
      routingNotes: ko
        ? [
            "저신뢰도 항목은 휴먼클라우드 검토 큐로 자동 전환됩니다.",
            "승인 시 피드백이 RAG 학습 파이프라인에 반영됩니다.",
            "만료 임박 항목은 우선순위가 자동 상승합니다.",
          ]
        : [
            "Low-confidence items are routed to the Human Cloud review queue.",
            "Approval feedback is ingested into the RAG learning loop.",
            "Expiring items are automatically elevated in priority.",
          ],
      historyItems: ko
        ? [
            "AD · capsule_execute · 0.92 → 자동 승인",
            "2D · character_style · 0.47 → 수동 검토 요청",
            "QC · final_review · 0.71 → 승인 + 피드백",
          ]
        : [
            "AD · capsule_execute · 0.92 → auto-approved",
            "2D · character_style · 0.47 → escalated",
            "QC · final_review · 0.71 → approved w/ feedback",
          ],
    };
  }, [language]);

  const stats: StatCardProps[] = [
    {
      title: copy.autoApprove,
      value: "—",
      helper: copy.helperAuto,
      icon: CheckCircle2,
      tone: "success",
    },
    {
      title: copy.pendingQueue,
      value: "—",
      helper: copy.helperQueue,
      icon: AlertTriangle,
      tone: "warning",
    },
    {
      title: copy.avgLatency,
      value: "—",
      helper: copy.helperLatency,
      icon: Clock3,
      tone: "info",
    },
    {
      title: copy.sla,
      value: "—",
      helper: copy.helperSla,
      icon: Timer,
      tone: "neutral",
    },
  ];

  return (
    <CreatorPageFrame title={copy.title} subtitle={copy.subtitle} badge="APPROVAL GATE">
      <div className="space-y-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-4"
        >
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-[var(--fg-0)]">{copy.overview}</div>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {stats.map((stat) => (
              <StatCard key={stat.title} {...stat} />
            ))}
          </div>
        </motion.div>

        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.05 }}
            >
              <Card className="border border-white/5 bg-[var(--surface-1)]/70">
                <CardHeader className="pb-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <CardTitle className="text-base">{copy.filters}</CardTitle>
                      <CardDescription>{copy.filtersDesc}</CardDescription>
                    </div>
                    <Button variant="outline" size="sm" className="gap-2">
                      <Filter className="h-4 w-4" />
                      {copy.actionExport}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Input placeholder={copy.searchPlaceholder} />
                  <Tabs defaultValue="all">
                    <TabsList className="flex flex-wrap gap-2">
                      <TabsTrigger value="all">{copy.filterAll}</TabsTrigger>
                      <TabsTrigger value="review">{copy.filterNeedsReview}</TabsTrigger>
                      <TabsTrigger value="escalated">{copy.filterEscalated}</TabsTrigger>
                      <TabsTrigger value="auto">{copy.filterAuto}</TabsTrigger>
                      <TabsTrigger value="expiring">{copy.filterExpiring}</TabsTrigger>
                    </TabsList>
                  </Tabs>
                  <div className="flex flex-wrap gap-2">
                    <Badge className="gap-1" variant="secondary">
                      <ShieldCheck className="h-3 w-3" />
                      1D
                    </Badge>
                    <Badge className="gap-1" variant="secondary">
                      2D
                    </Badge>
                    <Badge className="gap-1" variant="secondary">
                      3D
                    </Badge>
                    <Badge className="gap-1" variant="secondary">
                      AD
                    </Badge>
                    <Badge className="gap-1" variant="secondary">
                      QC
                    </Badge>
                    <span className="text-xs text-[var(--fg-subtle)]">{copy.filterDimension}</span>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              className="space-y-4"
            >
              <PendingApprovalsPanel />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.15 }}
            >
              <Card className="border border-white/5 bg-[var(--surface-1)]/70">
                <CardHeader>
                  <CardTitle className="text-base">{copy.history}</CardTitle>
                  <CardDescription>{copy.historyDesc}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {copy.historyItems.map((item, index) => (
                      <div key={item} className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-3">
                          <div className="h-2 w-2 rounded-full bg-violet-400" />
                          <span className="text-[var(--fg-0)]">{item}</span>
                        </div>
                        <span className="text-xs text-[var(--fg-subtle)]">T-{index + 1}h</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
            >
              <Card className="border border-white/5 bg-[var(--surface-1)]/70">
                <CardHeader>
                  <CardTitle className="text-base">{copy.policy}</CardTitle>
                  <CardDescription>{copy.policyDesc}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm">
                    {copy.policyItems.map((item) => (
                      <div key={item.label} className="flex items-center justify-between">
                        <span className="text-[var(--fg-muted)]">{item.label}</span>
                        <span className="text-[var(--fg-0)] font-medium">{item.value}</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 flex items-center gap-2 text-xs text-[var(--fg-subtle)]">
                    <ShieldCheck className="h-4 w-4 text-violet-400" />
                    <span>{copy.routingNotesTitle}</span>
                  </div>
                  <ul className="mt-3 space-y-2 text-xs text-[var(--fg-muted)]">
                    {copy.routingNotes.map((note) => (
                      <li key={note} className="flex items-start gap-2">
                        <span className="mt-1 h-1.5 w-1.5 rounded-full bg-violet-400" />
                        <span>{note}</span>
                      </li>
                    ))}
                  </ul>
                  <Button variant="secondary" size="sm" className="mt-4 w-full gap-2">
                    <MessageSquareText className="h-4 w-4" />
                    {copy.actionPolicy}
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </div>
    </CreatorPageFrame>
  );
}
