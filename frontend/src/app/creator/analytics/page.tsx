"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  BarChart3,
  LineChart,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import CreatorPageFrame from "../_components/CreatorPageFrame";
import { AnomalyAlerts } from "@/components/creator/AnomalyAlerts";
import { EngagementChart } from "@/components/creator/EngagementChart";
import { RecentDeliveries } from "@/components/creator/RecentDeliveries";
import { RPVMetricsCard } from "@/components/creator/RPVMetricsCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useLanguage } from "@/contexts/LanguageContext";

export default function CreatorAnalyticsPage() {
  const { language } = useLanguage();

  const copy = useMemo(() => {
    const ko = language === "ko";
    return {
      title: ko ? "크리에이터 분석" : "Creator Analytics",
      subtitle: ko
        ? "참여도, 수익, 이상 탐지 지표를 통합적으로 보여줍니다."
        : "Unified view of engagement, revenue, and anomaly signals.",
      summary: ko ? "성과 요약" : "Performance Summary",
      summaryDesc: ko
        ? "핵심 지표를 빠르게 확인하고 이상 징후를 감지합니다."
        : "Quickly scan core metrics and detect anomalies.",
      timelineTitle: ko ? "참여도 추이" : "Engagement Trend",
      timelineDesc: ko
        ? "조회·좋아요·공유 등 채널별 흐름을 보여줍니다."
        : "Track views, likes, and shares over time.",
      insightTitle: ko ? "리스크 & 인사이트" : "Risk & Insights",
      insightDesc: ko
        ? "성과 변화와 위험 신호를 요약합니다."
        : "Summary of performance swings and risks.",
      actions: {
        export: ko ? "리포트 내보내기" : "Export Report",
        configure: ko ? "알림 설정" : "Configure Alerts",
      },
      tabs: {
        week: ko ? "7일" : "7D",
        month: ko ? "30일" : "30D",
        quarter: ko ? "90일" : "90D",
      },
      highlights: ko
        ? [
            { label: "콘텐츠 완주율", value: "+4.2%", icon: TrendingUp },
            { label: "신뢰도 스코어", value: "0.88", icon: ShieldCheck },
            { label: "이상 감지", value: "2건", icon: AlertTriangle },
          ]
        : [
            { label: "Completion Rate", value: "+4.2%", icon: TrendingUp },
            { label: "Trust Score", value: "0.88", icon: ShieldCheck },
            { label: "Anomalies", value: "2", icon: AlertTriangle },
          ],
      insights: ko
        ? [
            "최근 7일 참여도 상승으로 신규 캠페인 확장 권장",
            "수정율이 증가 중이며 QC 단계 조정이 필요",
            "이상 탐지 2건은 승인 게이트 큐로 전송",
          ]
        : [
            "Engagement lifted in the last 7 days — expand new campaigns.",
            "Revision rate climbing — QC stage tuning recommended.",
            "Two anomalies routed to the approval gate queue.",
          ],
    };
  }, [language]);

  return (
    <CreatorPageFrame title={copy.title} subtitle={copy.subtitle} badge="ANALYTICS">
      <div className="space-y-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-4"
        >
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-sm font-semibold text-[var(--fg-0)]">{copy.summary}</div>
              <p className="text-xs text-[var(--fg-muted)]">{copy.summaryDesc}</p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" className="gap-2">
                <ArrowUpRight className="h-4 w-4" />
                {copy.actions.export}
              </Button>
              <Button size="sm" className="gap-2">
                <Sparkles className="h-4 w-4" />
                {copy.actions.configure}
              </Button>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {copy.highlights.map((item) => (
              <Card key={item.label} className="border border-white/5 bg-[var(--surface-1)]/70">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/10 text-violet-400">
                      <item.icon className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-xs text-[var(--fg-muted)]">{item.label}</p>
                      <p className="text-xl font-semibold text-[var(--fg-0)]">{item.value}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
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
              <RPVMetricsCard />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
            >
              <EngagementChart period="7d" />
            </motion.div>
          </div>

          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
            >
              <AnomalyAlerts />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.15 }}
            >
              <Card className="border border-white/5 bg-[var(--surface-1)]/70">
                <CardHeader>
                  <CardTitle className="text-base">{copy.insightTitle}</CardTitle>
                  <CardDescription>{copy.insightDesc}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-xs text-[var(--fg-muted)]">
                  {copy.insights.map((item) => (
                    <div key={item} className="flex items-start gap-2">
                      <Activity className="h-4 w-4 text-violet-400" />
                      <span>{item}</span>
                    </div>
                  ))}
                  <div className="grid grid-cols-3 gap-2 pt-2">
                    <Badge variant="secondary" className="justify-center gap-1">
                      <LineChart className="h-3 w-3" /> KPI
                    </Badge>
                    <Badge variant="secondary" className="justify-center gap-1">
                      <BarChart3 className="h-3 w-3" /> CTR
                    </Badge>
                    <Badge variant="secondary" className="justify-center gap-1">
                      <TrendingUp className="h-3 w-3" /> RPV
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
            >
              <RecentDeliveries />
            </motion.div>
          </div>
        </div>
      </div>
    </CreatorPageFrame>
  );
}
