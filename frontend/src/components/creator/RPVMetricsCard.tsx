"use client";

/**
 * RPV Metrics Card Component (Phase 7 HITL Enhancement)
 *
 * Displays Revenue Per View and key creator metrics.
 */

import { useEffect, useState } from "react";
import {
  DollarSign,
  Eye,
  TrendingUp,
  Star,
  Package,
  Clock,
  RotateCcw,
  Briefcase,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { fetchWithAuth } from "@/lib/api-client";

interface CreatorMetrics {
  rpv: number;
  total_views: number;
  total_revenue: number;
  engagement_rate: number;
  avg_rating: number | null;
  total_deliveries: number;
  on_time_rate: number;
  revision_rate: number;
  active_projects: number;
  period_days: number;
}

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: "purple" | "blue" | "green" | "yellow" | "red" | "orange";
  suffix?: string;
}

const COLOR_MAP: Record<string, { icon: string; bg: string }> = {
  purple: { icon: "text-purple-400", bg: "bg-purple-500/10" },
  blue: { icon: "text-blue-400", bg: "bg-blue-500/10" },
  green: { icon: "text-green-400", bg: "bg-green-500/10" },
  yellow: { icon: "text-yellow-400", bg: "bg-yellow-500/10" },
  red: { icon: "text-red-400", bg: "bg-red-500/10" },
  orange: { icon: "text-orange-400", bg: "bg-orange-500/10" },
};

function StatCard({ title, value, icon: Icon, color, suffix }: StatCardProps) {
  const colors = COLOR_MAP[color];
  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 hover:border-gray-600 transition-colors">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-400">{title}</span>
        <div className={`p-1.5 ${colors.bg} rounded-lg`}>
          <Icon className={`w-3.5 h-3.5 ${colors.icon}`} />
        </div>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold text-white">{value}</span>
        {suffix && <span className="text-sm text-gray-500">{suffix}</span>}
      </div>
    </div>
  );
}

export function RPVMetricsCard() {
  const { language } = useLanguage();
  const [metrics, setMetrics] = useState<CreatorMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const labels = {
    title: language === "ko" ? "핵심 메트릭" : "Key Metrics",
    period: language === "ko" ? "최근 30일" : "Last 30 days",
    rpv: language === "ko" ? "조회당 수익 (RPV)" : "Revenue Per View",
    totalViews: language === "ko" ? "총 조회수" : "Total Views",
    totalRevenue: language === "ko" ? "총 수익" : "Total Revenue",
    engagementRate: language === "ko" ? "참여율" : "Engagement Rate",
    avgRating: language === "ko" ? "평균 평점" : "Avg Rating",
    deliveries: language === "ko" ? "납품 완료" : "Deliveries",
    onTimeRate: language === "ko" ? "정시 납품률" : "On-Time Rate",
    revisionRate: language === "ko" ? "수정 비율" : "Revision Rate",
    activeProjects: language === "ko" ? "진행 중 프로젝트" : "Active Projects",
    errorMsg: language === "ko" ? "메트릭을 불러올 수 없습니다" : "Failed to load metrics",
  };

  useEffect(() => {
    async function loadMetrics() {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchWithAuth<CreatorMetrics>("/api/v1/creator/metrics?period_days=30");
        setMetrics(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : labels.errorMsg);
      } finally {
        setLoading(false);
      }
    }
    loadMetrics();
  }, []);

  if (loading) {
    return (
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 text-violet-400 animate-spin" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5">
        <div className="flex items-center gap-3 text-red-400">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  const formatNumber = (n: number) => {
    if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
    return n.toString();
  };

  const formatCurrency = (n: number) => {
    return new Intl.NumberFormat(language === "ko" ? "ko-KR" : "en-US", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(n);
  };

  const formatPercent = (n: number) => `${(n * 100).toFixed(1)}%`;

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-white">{labels.title}</h3>
        <span className="text-xs text-gray-500">{labels.period}</span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
        <StatCard
          title={labels.rpv}
          value={`$${formatCurrency(metrics.rpv)}`}
          icon={DollarSign}
          color="green"
        />
        <StatCard
          title={labels.totalViews}
          value={formatNumber(metrics.total_views)}
          icon={Eye}
          color="blue"
        />
        <StatCard
          title={labels.totalRevenue}
          value={formatNumber(metrics.total_revenue)}
          icon={TrendingUp}
          color="purple"
          suffix="credits"
        />
        <StatCard
          title={labels.engagementRate}
          value={formatPercent(metrics.engagement_rate)}
          icon={TrendingUp}
          color="yellow"
        />
        <StatCard
          title={labels.avgRating}
          value={metrics.avg_rating?.toFixed(1) ?? "-"}
          icon={Star}
          color="orange"
        />
        <StatCard
          title={labels.deliveries}
          value={metrics.total_deliveries}
          icon={Package}
          color="blue"
        />
        <StatCard
          title={labels.onTimeRate}
          value={formatPercent(metrics.on_time_rate)}
          icon={Clock}
          color="green"
        />
        <StatCard
          title={labels.revisionRate}
          value={formatPercent(metrics.revision_rate)}
          icon={RotateCcw}
          color="red"
        />
        <StatCard
          title={labels.activeProjects}
          value={metrics.active_projects}
          icon={Briefcase}
          color="purple"
        />
      </div>
    </div>
  );
}

export default RPVMetricsCard;
