"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import {
  ArrowUpRight,
  CheckCircle2,
  CircleDot,
  Clock,
  Database,
  FileCheck2,
  MessageCircle,
  RefreshCcw,
  Sparkles,
} from "lucide-react";
import CreatorPageFrame from "../_components/CreatorPageFrame";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useLanguage } from "@/contexts/LanguageContext";
import { StatCard, type StatTone } from "@/components/shared/StatCard";
import type { LucideIcon } from "lucide-react";

interface DashboardStatConfig {
  title: string;
  value: string;
  helper: string;
  icon: LucideIcon;
  tone: StatTone;
}

export default function CreatorFeedbackPage() {
  const { language } = useLanguage();

  const copy = useMemo(() => {
    const ko = language === "ko";
    return {
      title: ko ? "피드백 루프" : "Feedback Loop",
      subtitle: ko
        ? "사용자 피드백이 학습 파이프라인으로 이어지는 과정을 추적합니다."
        : "Track how user feedback feeds into the learning pipeline.",
      overview: ko ? "피드백 흐름 요약" : "Feedback Flow Overview",
      pipeline: ko ? "학습 파이프라인" : "Learning Pipeline",
      pipelineDesc: ko
        ? "긍정/부정 피드백을 분기 처리하여 RAG 개선으로 연결합니다."
        : "Route positive/negative feedback into RAG improvements.",
      tabsAll: ko ? "전체" : "All",
      tabsPositive: ko ? "긍정" : "Positive",
      tabsNegative: ko ? "부정" : "Negative",
      timeline: ko ? "최근 피드백 이벤트" : "Recent Feedback Events",
      policy: ko ? "운영 가이드" : "Operational Guidance",
      policyDesc: ko
        ? "학습/교정 기준과 반영 주기를 확인합니다."
        : "Review ingestion criteria and cadence.",
      actionExport: ko ? "리포트 내보내기" : "Export Report",
      actionReview: ko ? "교정 큐 보기" : "Review Corrections",
      actionDocs: ko ? "가이드 열기" : "Open Guide",
      cards: {
        volume: ko ? "피드백 수집량" : "Feedback Volume",
        positiveRate: ko ? "긍정 비율" : "Positive Rate",
        negativeRate: ko ? "부정 비율" : "Negative Rate",
        ingestion: ko ? "인덱싱 대기" : "Ingestion Queue",
      },
      helper: {
        volume: ko ? "최근 7일 집계 (연동 예정)" : "Last 7 days (pending data)",
        positive: ko ? "RAG 학습 반영률 (연동 예정)" : "RAG ingestion ratio (pending data)",
        negative: ko ? "교정 요청 비중 (연동 예정)" : "Correction share (pending data)",
        ingestion: ko ? "Qdrant 인덱싱 대기 (연동 예정)" : "Pending Qdrant ingestions",
      },
      pipelineStages: [
        {
          title: ko ? "피드백 수집" : "Feedback Intake",
          desc: ko ? "채널별 피드백 수집/정규화" : "Collect and normalize feedback across channels",
          state: ko ? "실시간" : "Realtime",
        },
        {
          title: ko ? "검증/필터링" : "Validation & Filter",
          desc: ko ? "품질 등급 + 노이즈 제거" : "Quality scoring and noise filtering",
          state: ko ? "15분 배치" : "15m batch",
        },
        {
          title: ko ? "인덱싱" : "Indexing",
          desc: ko ? "RAG 컬렉션에 반영" : "Ingest into RAG collections",
          state: ko ? "대기" : "Queued",
        },
        {
          title: ko ? "교정 루프" : "Correction Loop",
          desc: ko ? "부정 피드백 교정 태스크" : "Negative feedback correction tasks",
          state: ko ? "운영 중" : "Active",
        },
      ],
      timelineItems: ko
        ? [
            "4D · 프리셋 추천 근거 보강 (평점 5)",
            "AD · 스타일 설명 교정 요청 접수",
            "QC · 결과물 품질 점검 완료",
          ]
        : [
            "4D · Recommendation evidence reinforced (rating 5)",
            "AD · Style description correction requested",
            "QC · Output quality check completed",
          ],
      policyItems: ko
        ? [
            "평점 4 이상 → 자동 인덱싱 후보",
            "부정 피드백 → 교정 큐 등록",
            "학습 사이클: 매일 02:00 UTC",
            "검토 SLA: 48시간 이내",
          ]
        : [
            "Ratings ≥ 4 → auto-ingestion candidates",
            "Negative feedback → correction queue",
            "Learning cycle runs daily at 02:00 UTC",
            "Review SLA: within 48 hours",
          ],
    };
  }, [language]);

  const stats: DashboardStatConfig[] = [
    {
      title: copy.cards.volume,
      value: "—",
      helper: copy.helper.volume,
      icon: MessageCircle,
      tone: "info",
    },
    {
      title: copy.cards.positiveRate,
      value: "—",
      helper: copy.helper.positive,
      icon: CheckCircle2,
      tone: "success",
    },
    {
      title: copy.cards.negativeRate,
      value: "—",
      helper: copy.helper.negative,
      icon: FileCheck2,
      tone: "warning",
    },
    {
      title: copy.cards.ingestion,
      value: "—",
      helper: copy.helper.ingestion,
      icon: Database,
      tone: "neutral",
    },
  ];

  return (
    <CreatorPageFrame title={copy.title} subtitle={copy.subtitle} badge="FEEDBACK LOOP">
      <div className="space-y-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-4"
        >
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-[var(--fg-0)]">{copy.overview}</div>
            <Button variant="outline" size="sm" className="gap-2">
              <ArrowUpRight className="h-4 w-4" />
              {copy.actionExport}
            </Button>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {stats.map((stat) => (
              <StatCard key={stat.title} variant="dashboard" {...stat} />
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
                      <CardTitle className="text-base">{copy.pipeline}</CardTitle>
                      <CardDescription>{copy.pipelineDesc}</CardDescription>
                    </div>
                    <Tabs defaultValue="all">
                      <TabsList className="flex gap-2">
                        <TabsTrigger value="all">{copy.tabsAll}</TabsTrigger>
                        <TabsTrigger value="positive">{copy.tabsPositive}</TabsTrigger>
                        <TabsTrigger value="negative">{copy.tabsNegative}</TabsTrigger>
                      </TabsList>
                    </Tabs>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {copy.pipelineStages.map((stage, index) => (
                    <div
                      key={stage.title}
                      className="flex items-center justify-between rounded-lg border border-white/5 bg-[var(--surface-2)]/50 px-4 py-3"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-violet-500/10 text-violet-400">
                          <CircleDot className="h-4 w-4" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-[var(--fg-0)]">{stage.title}</p>
                          <p className="text-xs text-[var(--fg-muted)]">{stage.desc}</p>
                        </div>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {stage.state}
                      </Badge>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
            >
              <Card className="border border-white/5 bg-[var(--surface-1)]/70">
                <CardHeader>
                  <CardTitle className="text-base">{copy.timeline}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {copy.timelineItems.map((item, index) => (
                    <div key={item} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-3">
                        <div className="h-2 w-2 rounded-full bg-emerald-400" />
                        <span className="text-[var(--fg-0)]">{item}</span>
                      </div>
                      <span className="text-xs text-[var(--fg-subtle)]">T-{index + 1}h</span>
                    </div>
                  ))}
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
                <CardContent className="space-y-4">
                  <ul className="space-y-2 text-xs text-[var(--fg-muted)]">
                    {copy.policyItems.map((item) => (
                      <li key={item} className="flex items-start gap-2">
                        <Sparkles className="h-4 w-4 text-violet-400" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="flex items-center gap-2 rounded-lg border border-white/5 bg-[var(--surface-2)]/60 p-3 text-xs text-[var(--fg-muted)]">
                    <Clock className="h-4 w-4 text-amber-400" />
                    <span>{language === "ko" ? "다음 학습 사이클: 02:00 UTC" : "Next learning cycle: 02:00 UTC"}</span>
                  </div>
                  <Button variant="secondary" size="sm" className="w-full gap-2">
                    <RefreshCcw className="h-4 w-4" />
                    {copy.actionReview}
                  </Button>
                  <Button variant="ghost" size="sm" className="w-full gap-2 text-[var(--fg-subtle)]">
                    <ArrowUpRight className="h-4 w-4" />
                    {copy.actionDocs}
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
