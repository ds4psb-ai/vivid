"use client";

/**
 * Engagement Chart Component (Phase 7 HITL Enhancement)
 *
 * Displays engagement timeline with views, likes, comments, shares.
 */

import { useEffect, useState } from "react";
import {
  BarChart3,
  Loader2,
  AlertCircle,
  Eye,
  Heart,
  MessageCircle,
  Share2,
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { fetchWithAuth } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface EngagementData {
  date: string;
  views: number;
  likes: number;
  comments: number;
  shares: number;
  engagement_rate: number;
}

interface EngagementTimelineResponse {
  period: string;
  data: EngagementData[];
}

interface EngagementChartProps {
  period?: "7d" | "30d" | "90d";
}

const PERIOD_OPTIONS = [
  { value: "7d", label: "7일", labelEn: "7 Days" },
  { value: "30d", label: "30일", labelEn: "30 Days" },
  { value: "90d", label: "90일", labelEn: "90 Days" },
];

export function EngagementChart({ period: initialPeriod = "7d" }: EngagementChartProps) {
  const { language } = useLanguage();
  const [period, setPeriod] = useState<"7d" | "30d" | "90d">(initialPeriod);
  const [data, setData] = useState<EngagementData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const labels = {
    title: language === "ko" ? "참여도 추이" : "Engagement Timeline",
    views: language === "ko" ? "조회" : "Views",
    likes: language === "ko" ? "좋아요" : "Likes",
    comments: language === "ko" ? "댓글" : "Comments",
    shares: language === "ko" ? "공유" : "Shares",
    noData: language === "ko" ? "데이터가 없습니다" : "No data available",
    errorMsg: language === "ko" ? "데이터를 불러올 수 없습니다" : "Failed to load data",
  };

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchWithAuth<EngagementTimelineResponse>(
          `/api/v1/creator/engagement?period=${period}`
        );
        setData(response.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : labels.errorMsg);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [period]);

  // Calculate max values for scaling
  const maxViews = Math.max(...data.map((d) => d.views), 1);
  const maxLikes = Math.max(...data.map((d) => d.likes), 1);
  const maxComments = Math.max(...data.map((d) => d.comments), 1);
  const maxShares = Math.max(...data.map((d) => d.shares), 1);

  // Calculate totals for legend
  const totals = data.reduce(
    (acc, d) => ({
      views: acc.views + d.views,
      likes: acc.likes + d.likes,
      comments: acc.comments + d.comments,
      shares: acc.shares + d.shares,
    }),
    { views: 0, likes: 0, comments: 0, shares: 0 }
  );

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString(language === "ko" ? "ko-KR" : "en-US", {
      month: "short",
      day: "numeric",
    });
  };

  const formatNumber = (n: number) => {
    if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
    return n.toString();
  };

  return (
    <Card className="border border-white/5 bg-[var(--surface-1)]/70 h-full">
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-violet-400" />
          <CardTitle className="text-base">{labels.title}</CardTitle>
        </div>

        {/* Period Selector */}
        <div className="flex gap-1">
          {PERIOD_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setPeriod(opt.value as "7d" | "30d" | "90d")}
              className={`px-3 py-1 text-xs rounded-lg border transition-colors ${
                period === opt.value
                  ? "bg-violet-600/90 text-white border-violet-500/60"
                  : "bg-[var(--surface-2)]/60 text-[var(--fg-subtle)] border-white/5 hover:bg-[var(--surface-2)]"
              }`}
            >
              {language === "ko" ? opt.label : opt.labelEn}
            </button>
          ))}
        </div>
      </CardHeader>

      {/* Content */}
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="w-6 h-6 text-violet-400 animate-spin" />
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-48 gap-2 text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        ) : data.length === 0 ? (
          <div className="flex items-center justify-center h-48 text-[var(--fg-subtle)]">
            {labels.noData}
          </div>
        ) : (
          <>
          {/* Legend */}
          <div className="flex flex-wrap gap-4 mb-4 text-xs">
            <div className="flex items-center gap-1.5">
              <Eye className="w-3.5 h-3.5 text-blue-400" />
              <span className="text-[var(--fg-subtle)]">{labels.views}</span>
              <span className="text-[var(--fg-0)] font-medium">{formatNumber(totals.views)}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Heart className="w-3.5 h-3.5 text-red-400" />
              <span className="text-[var(--fg-subtle)]">{labels.likes}</span>
              <span className="text-[var(--fg-0)] font-medium">{formatNumber(totals.likes)}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <MessageCircle className="w-3.5 h-3.5 text-green-400" />
              <span className="text-[var(--fg-subtle)]">{labels.comments}</span>
              <span className="text-[var(--fg-0)] font-medium">{formatNumber(totals.comments)}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Share2 className="w-3.5 h-3.5 text-yellow-400" />
              <span className="text-[var(--fg-subtle)]">{labels.shares}</span>
              <span className="text-[var(--fg-0)] font-medium">{formatNumber(totals.shares)}</span>
            </div>
          </div>

          {/* Simple Bar Chart */}
          <div className="h-40 flex items-end gap-1">
            {data.map((item, idx) => (
              <div
                key={idx}
                className="flex-1 flex flex-col items-center gap-0.5 group relative"
              >
                {/* Stacked bars */}
                <div className="w-full flex flex-col-reverse gap-0.5">
                  <div
                    className="w-full bg-blue-500/60 rounded-t transition-all group-hover:bg-blue-500"
                    style={{ height: `${(item.views / maxViews) * 80}px`, minHeight: item.views > 0 ? 2 : 0 }}
                  />
                  <div
                    className="w-full bg-red-500/60 rounded transition-all group-hover:bg-red-500"
                    style={{ height: `${(item.likes / maxLikes) * 30}px`, minHeight: item.likes > 0 ? 2 : 0 }}
                  />
                  <div
                    className="w-full bg-green-500/60 rounded transition-all group-hover:bg-green-500"
                    style={{ height: `${(item.comments / maxComments) * 20}px`, minHeight: item.comments > 0 ? 2 : 0 }}
                  />
                  <div
                    className="w-full bg-yellow-500/60 rounded transition-all group-hover:bg-yellow-500"
                    style={{ height: `${(item.shares / maxShares) * 15}px`, minHeight: item.shares > 0 ? 2 : 0 }}
                  />
                </div>

                {/* Date label */}
                {(idx === 0 || idx === data.length - 1 || idx === Math.floor(data.length / 2)) && (
                  <span className="text-[10px] text-gray-500 mt-1">{formatDate(item.date)}</span>
                )}

                {/* Tooltip */}
                <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-[var(--surface-3)] border border-white/10 rounded-lg p-2 text-xs opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 whitespace-nowrap">
                  <div className="font-medium text-[var(--fg-0)] mb-1">{formatDate(item.date)}</div>
                  <div className="text-blue-400">Views: {formatNumber(item.views)}</div>
                  <div className="text-red-400">Likes: {formatNumber(item.likes)}</div>
                  <div className="text-green-400">Comments: {item.comments}</div>
                  <div className="text-yellow-400">Shares: {item.shares}</div>
                  <div className="text-violet-400 mt-1">
                    Rate: {(item.engagement_rate * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
        )}
      </CardContent>
    </Card>
  );
}

export default EngagementChart;
