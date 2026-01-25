"use client";

/**
 * Analytics Dashboard Page (Phase 9: Monetization & Analytics)
 *
 * Unified dashboard for revenue attribution, engagement analytics, and real-time KPIs.
 */

import { useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
  BarChart3,
  ArrowUpRight,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useLanguage } from "@/contexts/LanguageContext";
import { useAnalyticsDashboard } from "@/hooks/useAnalyticsDashboard";
import {
  KPICards,
  RevenueWaterfall,
  FunnelChart,
  RetentionMatrix,
  LeaderboardTable,
  TopToolsTable,
} from "./components";

export default function AnalyticsDashboardPage() {
  const { language } = useLanguage();
  const {
    // KPIs
    kpis,
    kpisLoading,
    kpisError,
    refreshKPIs,
    isStreamConnected,
    // Leaderboard
    leaderboard,
    leaderboardLoading,
    fetchLeaderboard,
    // Revenue waterfall
    waterfall,
    waterfallLoading,
    fetchWaterfall,
    // Funnel
    funnel,
    funnelLoading,
    fetchFunnel,
    // Cohorts
    cohorts,
    cohortsLoading,
    fetchCohorts,
    // Top tools
    topTools,
    topToolsLoading,
    fetchTopTools,
  } = useAnalyticsDashboard({
    enableStreaming: true,
    periodDays: 30,
  });

  // Initial data load
  useEffect(() => {
    fetchLeaderboard("revenue", "weekly");
    fetchWaterfall(30);
    fetchTopTools(30, 10);
  }, [fetchLeaderboard, fetchWaterfall, fetchTopTools]);

  const copy = useMemo(() => {
    const ko = language === "ko";
    return {
      title: ko ? "분석 대시보드" : "Analytics Dashboard",
      subtitle: ko
        ? "수익 귀속, 참여도 분석, 실시간 KPI를 통합적으로 확인합니다."
        : "Unified view of revenue attribution, engagement analytics, and real-time KPIs.",
      badge: ko ? "Phase 9" : "Phase 9",
      actions: {
        export: ko ? "리포트 내보내기" : "Export Report",
        configure: ko ? "알림 설정" : "Configure Alerts",
      },
      sections: {
        kpis: ko ? "핵심 성과 지표" : "Key Performance Indicators",
        revenue: ko ? "수익 분석" : "Revenue Analysis",
        engagement: ko ? "참여도 분석" : "Engagement Analysis",
        leaderboard: ko ? "리더보드" : "Leaderboard",
      },
    };
  }, [language]);

  return (
    <div className="min-h-screen bg-[var(--bg-0)]">
      {/* Header */}
      <div className="border-b border-white/5 bg-[var(--surface-1)]/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 shadow-lg shadow-violet-500/20">
                <BarChart3 className="h-6 w-6 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-semibold text-[var(--fg-0)]">
                    {copy.title}
                  </h1>
                  <Badge variant="secondary" className="text-xs">
                    {copy.badge}
                  </Badge>
                </div>
                <p className="text-sm text-[var(--fg-muted)]">{copy.subtitle}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
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
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* KPI Cards */}
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <KPICards
            kpis={kpis}
            loading={kpisLoading}
            isStreamConnected={isStreamConnected}
            onRefresh={refreshKPIs}
          />
          {kpisError && (
            <div className="mt-2 text-sm text-red-400">
              Error loading KPIs: {kpisError.message}
            </div>
          )}
        </motion.section>

        {/* Revenue & Tools Section */}
        <div className="grid gap-6 lg:grid-cols-2">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 }}
          >
            <RevenueWaterfall
              data={waterfall}
              loading={waterfallLoading}
              onFetch={fetchWaterfall}
            />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
          >
            <TopToolsTable
              data={topTools}
              loading={topToolsLoading}
              onFetch={fetchTopTools}
            />
          </motion.div>
        </div>

        {/* Funnel & Retention Section */}
        <div className="grid gap-6 lg:grid-cols-2">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.15 }}
          >
            <FunnelChart
              data={funnel}
              loading={funnelLoading}
              onFetch={fetchFunnel}
            />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
          >
            <RetentionMatrix
              data={cohorts}
              loading={cohortsLoading}
              onFetch={fetchCohorts}
            />
          </motion.div>
        </div>

        {/* Leaderboard Section */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.25 }}
          className="max-w-2xl"
        >
          <LeaderboardTable
            data={leaderboard}
            loading={leaderboardLoading}
            onFetch={fetchLeaderboard}
          />
        </motion.div>

        {/* Footer */}
        <div className="pt-8 border-t border-white/5 text-center text-xs text-[var(--fg-muted)]">
          <p>
            Phase 9: Monetization & Analytics • Revenue Attribution • Engagement Analytics
          </p>
          <p className="mt-1">
            Powered by Multi-touch Attribution (Shapley-inspired) & RFM Scoring
          </p>
        </div>
      </div>
    </div>
  );
}
