"use client";

import { Suspense } from "react";
import { motion } from "framer-motion";
import CreatorPageFrame from "../_components/CreatorPageFrame";
import { RPVMetricsCard } from "@/components/creator/RPVMetricsCard";
import { EngagementChart } from "@/components/creator/EngagementChart";
import { PendingApprovalsPanel } from "@/components/creator/PendingApprovalsPanel";
import { AnomalyAlerts } from "@/components/creator/AnomalyAlerts";
import { RecentDeliveries } from "@/components/creator/RecentDeliveries";
import { Card, CardContent } from "@/components/ui/card";

// Skeleton components for loading states
function MetricsSkeleton() {
  return (
    <Card className="border border-white/5 bg-[var(--surface-1)]/70">
      <CardContent className="p-5">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="rounded-lg border border-white/5 bg-[var(--surface-2)]/60 p-4">
              <div className="h-4 bg-white/10 rounded w-20 mb-3 animate-pulse" />
              <div className="h-8 bg-white/10 rounded w-16 animate-pulse" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function ChartSkeleton() {
  return (
    <Card className="border border-white/5 bg-[var(--surface-1)]/70 h-72">
      <CardContent className="p-5">
        <div className="h-4 bg-white/10 rounded w-32 mb-4 animate-pulse" />
        <div className="h-40 bg-white/10 rounded animate-pulse" />
      </CardContent>
    </Card>
  );
}

function PanelSkeleton() {
  return (
    <Card className="border border-white/5 bg-[var(--surface-1)]/70">
      <CardContent className="p-5">
        <div className="h-4 bg-white/10 rounded w-40 mb-4 animate-pulse" />
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-16 bg-white/10 rounded mb-2 animate-pulse" />
        ))}
      </CardContent>
    </Card>
  );
}

export default function CreatorDashboardPage() {
  return (
    <CreatorPageFrame
      title="크리에이터 대시보드"
      subtitle="승인 현황, 수익 지표, 피드백 상태를 요약하는 메인 보드입니다."
      badge="DASHBOARD"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* RPV Metrics - Full Width */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-3"
        >
          <Suspense fallback={<MetricsSkeleton />}>
            <RPVMetricsCard />
          </Suspense>
        </motion.div>

        {/* Engagement Chart - 2 columns */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2"
        >
          <Suspense fallback={<ChartSkeleton />}>
            <EngagementChart period="7d" />
          </Suspense>
        </motion.div>

        {/* Anomaly Alerts - 1 column */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Suspense fallback={<PanelSkeleton />}>
            <AnomalyAlerts />
          </Suspense>
        </motion.div>

        {/* Pending Approvals - 2 columns */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="lg:col-span-2"
        >
          <Suspense fallback={<PanelSkeleton />}>
            <PendingApprovalsPanel />
          </Suspense>
        </motion.div>

        {/* Recent Deliveries - 1 column */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Suspense fallback={<PanelSkeleton />}>
            <RecentDeliveries />
          </Suspense>
        </motion.div>
      </div>
    </CreatorPageFrame>
  );
}
