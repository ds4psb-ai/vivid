"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import {
  ArrowUpRight,
  BarChart3,
  Beaker,
  CheckCircle2,
  CircleDashed,
  Flag,
  FlaskConical,
  Sparkles,
  Timer,
  TrendingUp,
} from "lucide-react";
import CreatorPageFrame from "../_components/CreatorPageFrame";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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

export default function CreatorExperimentsPage() {
  const { language } = useLanguage();

  const copy = useMemo(() => {
    const ko = language === "ko";
    return {
      title: ko ? "A/B 실험" : "A/B Experiments",
      subtitle: ko
        ? "생성 파라미터 실험을 설계하고 변형별 성과를 비교합니다."
        : "Design generation parameter experiments and compare variant performance.",
      overview: ko ? "실험 현황" : "Experiment Overview",
      filters: ko ? "상태 필터" : "Status Filters",
      actionCreate: ko ? "실험 생성" : "Create Experiment",
      actionExport: ko ? "리포트 내보내기" : "Export Report",
      cards: {
        active: ko ? "진행 중 실험" : "Active Experiments",
        variants: ko ? "활성 변형" : "Active Variants",
        uplift: ko ? "평균 상승" : "Avg Uplift",
        runtime: ko ? "평균 러닝타임" : "Avg Runtime",
      },
      helper: {
        active: ko ? "최근 30일 기준 (연동 예정)" : "Last 30 days (pending data)",
        variants: ko ? "현재 운영 중 변형 수" : "Variants currently running",
        uplift: ko ? "전환율 기준 평균 변화" : "Mean conversion uplift",
        runtime: ko ? "실험 종료까지 평균 시간" : "Avg time to decision",
      },
      tabs: {
        all: ko ? "전체" : "All",
        running: ko ? "진행 중" : "Running",
        completed: ko ? "완료" : "Completed",
        draft: ko ? "초안" : "Draft",
      },
      listTitle: ko ? "실험 목록" : "Experiment List",
      listDesc: ko
        ? "주요 지표, 통계 신뢰도, 변형 설정을 요약합니다."
        : "Summary of primary metrics, confidence, and variant setup.",
      variantTitle: ko ? "변형 비교" : "Variant Comparison",
      variantDesc: ko
        ? "컨트롤 대비 상승폭과 신뢰도를 확인합니다."
        : "Compare lift and confidence against control.",
      insightTitle: ko ? "실험 인사이트" : "Experiment Insights",
      insightDesc: ko
        ? "최근 학습 결과를 기반으로 추천 행동을 제안합니다."
        : "Suggested actions based on recent learning results.",
      insights: ko
        ? [
            "Variant B가 6.2% 상승, 신뢰도 92%로 승격 후보입니다.",
            "실험 기간이 5일 미만인 경우 결론 보류를 권장합니다.",
            "저신뢰도 실험은 HITL 승인 게이트로 라우팅됩니다.",
          ]
        : [
            "Variant B shows +6.2% lift at 92% confidence, ready to promote.",
            "Hold conclusions for experiments running under 5 days.",
            "Low-confidence experiments route to HITL approval gate.",
          ],
      experiments: ko
        ? [
            {
              name: "AD Style Tuning",
              metric: "Completion Rate",
              status: "running",
              confidence: "92%",
              lift: "+6.2%",
              sample: "12.4k",
              duration: "6d",
            },
            {
              name: "2D Character Prompt",
              metric: "User Rating",
              status: "running",
              confidence: "68%",
              lift: "+2.1%",
              sample: "4.1k",
              duration: "3d",
            },
            {
              name: "QC Final Pass",
              metric: "Revision Rate",
              status: "completed",
              confidence: "95%",
              lift: "-4.8%",
              sample: "18.7k",
              duration: "12d",
            },
          ]
        : [
            {
              name: "AD Style Tuning",
              metric: "Completion Rate",
              status: "running",
              confidence: "92%",
              lift: "+6.2%",
              sample: "12.4k",
              duration: "6d",
            },
            {
              name: "2D Character Prompt",
              metric: "User Rating",
              status: "running",
              confidence: "68%",
              lift: "+2.1%",
              sample: "4.1k",
              duration: "3d",
            },
            {
              name: "QC Final Pass",
              metric: "Revision Rate",
              status: "completed",
              confidence: "95%",
              lift: "-4.8%",
              sample: "18.7k",
              duration: "12d",
            },
          ],
      variants: ko
        ? [
            { label: "Control", lift: "0%", confidence: "—", color: "bg-slate-500/40" },
            { label: "Variant A", lift: "+3.8%", confidence: "78%", color: "bg-blue-500/50" },
            { label: "Variant B", lift: "+6.2%", confidence: "92%", color: "bg-emerald-500/60" },
          ]
        : [
            { label: "Control", lift: "0%", confidence: "—", color: "bg-slate-500/40" },
            { label: "Variant A", lift: "+3.8%", confidence: "78%", color: "bg-blue-500/50" },
            { label: "Variant B", lift: "+6.2%", confidence: "92%", color: "bg-emerald-500/60" },
          ],
    };
  }, [language]);

  const stats: StatCardProps[] = [
    {
      title: copy.cards.active,
      value: "—",
      helper: copy.helper.active,
      icon: FlaskConical,
      tone: "info",
    },
    {
      title: copy.cards.variants,
      value: "—",
      helper: copy.helper.variants,
      icon: Beaker,
      tone: "neutral",
    },
    {
      title: copy.cards.uplift,
      value: "—",
      helper: copy.helper.uplift,
      icon: TrendingUp,
      tone: "success",
    },
    {
      title: copy.cards.runtime,
      value: "—",
      helper: copy.helper.runtime,
      icon: Timer,
      tone: "warning",
    },
  ];

  return (
    <CreatorPageFrame title={copy.title} subtitle={copy.subtitle} badge="A/B TESTING">
      <div className="space-y-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-4"
        >
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-[var(--fg-0)]">{copy.overview}</div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" className="gap-2">
                <ArrowUpRight className="h-4 w-4" />
                {copy.actionExport}
              </Button>
              <Button size="sm" className="gap-2">
                <Sparkles className="h-4 w-4" />
                {copy.actionCreate}
              </Button>
            </div>
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
                      <CardTitle className="text-base">{copy.listTitle}</CardTitle>
                      <CardDescription>{copy.listDesc}</CardDescription>
                    </div>
                    <Tabs defaultValue="all">
                      <TabsList className="flex gap-2">
                        <TabsTrigger value="all">{copy.tabs.all}</TabsTrigger>
                        <TabsTrigger value="running">{copy.tabs.running}</TabsTrigger>
                        <TabsTrigger value="completed">{copy.tabs.completed}</TabsTrigger>
                        <TabsTrigger value="draft">{copy.tabs.draft}</TabsTrigger>
                      </TabsList>
                    </Tabs>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {copy.experiments.map((item) => (
                    <div
                      key={item.name}
                      className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-white/5 bg-[var(--surface-2)]/60 px-4 py-3"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-[var(--fg-0)]">{item.name}</span>
                          <Badge variant="secondary" className="text-[10px]">
                            {item.status === "running" ? (language === "ko" ? "진행 중" : "Running") : (language === "ko" ? "완료" : "Completed")}
                          </Badge>
                        </div>
                        <div className="text-xs text-[var(--fg-muted)]">{item.metric}</div>
                      </div>
                      <div className="flex flex-wrap items-center gap-4 text-xs text-[var(--fg-subtle)]">
                        <div className="flex items-center gap-1">
                          <CircleDashed className="h-3.5 w-3.5 text-violet-400" />
                          {item.confidence}
                        </div>
                        <div className="flex items-center gap-1">
                          <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                          {item.lift}
                        </div>
                        <div className="flex items-center gap-1">
                          <BarChart3 className="h-3.5 w-3.5 text-blue-400" />
                          {item.sample}
                        </div>
                        <div className="flex items-center gap-1">
                          <Timer className="h-3.5 w-3.5 text-amber-400" />
                          {item.duration}
                        </div>
                      </div>
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
                  <CardTitle className="text-base">{copy.variantTitle}</CardTitle>
                  <CardDescription>{copy.variantDesc}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {copy.variants.map((variant) => (
                    <div key={variant.label} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-[var(--fg-0)]">{variant.label}</span>
                        <span className="text-xs text-[var(--fg-subtle)]">
                          {variant.lift} · {variant.confidence}
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-white/5">
                        <div className={cn("h-2 rounded-full", variant.color)} style={{ width: variant.lift === "0%" ? "40%" : variant.lift.includes("6") ? "78%" : "62%" }} />
                      </div>
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
                  <CardTitle className="text-base">{copy.insightTitle}</CardTitle>
                  <CardDescription>{copy.insightDesc}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-xs text-[var(--fg-muted)]">
                  {copy.insights.map((item) => (
                    <div key={item} className="flex items-start gap-2">
                      <Flag className="h-4 w-4 text-violet-400" />
                      <span>{item}</span>
                    </div>
                  ))}
                  <Button variant="secondary" size="sm" className="mt-3 w-full gap-2">
                    <CheckCircle2 className="h-4 w-4" />
                    {language === "ko" ? "승격 요청" : "Promote Winner"}
                  </Button>
                  <Button variant="ghost" size="sm" className="w-full gap-2 text-[var(--fg-subtle)]">
                    <ArrowUpRight className="h-4 w-4" />
                    {language === "ko" ? "통계 상세 보기" : "View Stats"}
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
