"use client";

/**
 * KPI Cards Component (Phase 9: Analytics Dashboard)
 *
 * Real-time KPI display with delta indicators and trend visualization.
 */

import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  DollarSign,
  Users,
  Zap,
  Activity,
  Target,
  RefreshCw,
  Wifi,
  WifiOff,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { DashboardKPIs, KPIValue } from "@/hooks/useAnalyticsDashboard";

interface KPICardsProps {
  kpis: DashboardKPIs | null;
  loading: boolean;
  isStreamConnected: boolean;
  onRefresh: () => void;
}

const KPI_CONFIG = {
  total_revenue: {
    label: "Total Revenue",
    labelKo: "총 수익",
    icon: DollarSign,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    format: "credits",
  },
  active_users: {
    label: "Active Users",
    labelKo: "활성 사용자",
    icon: Users,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    format: "number",
  },
  tool_executions: {
    label: "Tool Executions",
    labelKo: "도구 실행 수",
    icon: Zap,
    color: "text-violet-400",
    bgColor: "bg-violet-500/10",
    format: "number",
  },
  avg_engagement_score: {
    label: "Avg Engagement",
    labelKo: "평균 참여도",
    icon: Activity,
    color: "text-orange-400",
    bgColor: "bg-orange-500/10",
    format: "score",
  },
  conversion_rate: {
    label: "Conversion Rate",
    labelKo: "전환율",
    icon: Target,
    color: "text-cyan-400",
    bgColor: "bg-cyan-500/10",
    format: "percent",
  },
};

function formatValue(value: number, format: string): string {
  switch (format) {
    case "credits":
      if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
      if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
      return value.toLocaleString();
    case "number":
      if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
      if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
      return value.toLocaleString();
    case "score":
      return value.toFixed(1);
    case "percent":
      return `${(value * 100).toFixed(1)}%`;
    default:
      return value.toString();
  }
}

function TrendIndicator({ trend, deltaPct }: { trend: string; deltaPct: number | null }) {
  if (deltaPct === null) return null;

  const Icon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;
  const colorClass = trend === "up" ? "text-emerald-400" : trend === "down" ? "text-red-400" : "text-gray-400";

  return (
    <div className={`flex items-center gap-1 text-xs ${colorClass}`}>
      <Icon className="w-3 h-3" />
      <span>{deltaPct > 0 ? "+" : ""}{deltaPct.toFixed(1)}%</span>
    </div>
  );
}

function KPICard({
  kpiKey,
  kpi,
  index,
}: {
  kpiKey: keyof typeof KPI_CONFIG;
  kpi: KPIValue;
  index: number;
}) {
  const config = KPI_CONFIG[kpiKey];
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      <Card className="border border-white/5 bg-[var(--surface-1)]/70 hover:border-white/10 transition-colors">
        <CardContent className="pt-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${config.bgColor} ${config.color}`}>
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-[var(--fg-muted)]">{config.label}</p>
                <p className="text-xl font-semibold text-[var(--fg-0)]">
                  {formatValue(kpi.value, config.format)}
                </p>
              </div>
            </div>
            <TrendIndicator trend={kpi.trend} deltaPct={kpi.delta_pct} />
          </div>
          {kpi.updated_at && (
            <p className="text-[10px] text-[var(--fg-muted)] mt-3 opacity-60">
              Updated: {new Date(kpi.updated_at).toLocaleTimeString()}
            </p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

function KPISkeleton() {
  return (
    <Card className="border border-white/5 bg-[var(--surface-1)]/70">
      <CardContent className="pt-6">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-white/5 animate-pulse" />
          <div className="space-y-2">
            <div className="h-3 w-16 bg-white/5 rounded animate-pulse" />
            <div className="h-5 w-24 bg-white/10 rounded animate-pulse" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function KPICards({ kpis, loading, isStreamConnected, onRefresh }: KPICardsProps) {
  if (loading && !kpis) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-[var(--fg-0)]">Key Performance Indicators</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <KPISkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold text-[var(--fg-0)]">Key Performance Indicators</h2>
          <div className={`flex items-center gap-1.5 text-xs ${isStreamConnected ? "text-emerald-400" : "text-orange-400"}`}>
            {isStreamConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
            <span>{isStreamConnected ? "Live" : "Offline"}</span>
          </div>
        </div>
        <button
          onClick={onRefresh}
          className="flex items-center gap-1.5 text-xs text-[var(--fg-muted)] hover:text-[var(--fg-0)] transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {kpis ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {(Object.keys(KPI_CONFIG) as Array<keyof typeof KPI_CONFIG>).map((key, index) => {
            const kpi = kpis[key];
            if (!kpi) return null;
            return <KPICard key={key} kpiKey={key} kpi={kpi} index={index} />;
          })}
        </div>
      ) : (
        <div className="text-center py-8 text-[var(--fg-muted)]">No KPI data available</div>
      )}

      {kpis && (
        <div className="text-xs text-[var(--fg-muted)] text-right">
          Period: Last {kpis.period_days} days
        </div>
      )}
    </div>
  );
}

export default KPICards;
