"use client";

/**
 * Recent Deliveries Component (Phase 7 HITL Enhancement)
 *
 * Displays recent delivery history for the creator.
 */

import { useEffect, useState } from "react";
import {
  Package,
  Loader2,
  AlertCircle,
  CheckCircle,
  XCircle,
  Star,
  RotateCcw,
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface DeliveryRecord {
  delivery_id: string;
  project_title: string;
  delivered_at: string;
  rating: number | null;
  credits_earned: number;
  revision_count: number;
  on_time: boolean;
}

interface DeliveriesResponse {
  items: DeliveryRecord[];
  total: number;
}

export function RecentDeliveries() {
  const { language } = useLanguage();
  const [data, setData] = useState<DeliveryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const labels = {
    title: language === "ko" ? "최근 납품" : "Recent Deliveries",
    noDeliveries: language === "ko" ? "납품 이력이 없습니다" : "No deliveries yet",
    errorMsg: language === "ko" ? "데이터를 불러올 수 없습니다" : "Failed to load data",
    onTime: language === "ko" ? "정시" : "On time",
    late: language === "ko" ? "지연" : "Late",
    revisions: language === "ko" ? "수정" : "revisions",
    credits: language === "ko" ? "크레딧" : "credits",
  };

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await api.get<DeliveriesResponse>(
          "/api/v1/creator/deliveries?limit=5"
        );
        setData(response.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : labels.errorMsg);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [labels.errorMsg]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString(language === "ko" ? "ko-KR" : "en-US", {
      month: "short",
      day: "numeric",
    });
  };

  const formatCredits = (n: number) => {
    if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
    return n.toString();
  };

  return (
    <Card className="border border-white/5 bg-[var(--surface-1)]/70 h-full">
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-4">
        <div className="flex items-center gap-2">
          <Package className="w-4 h-4 text-blue-400" />
          <CardTitle className="text-base">{labels.title}</CardTitle>
        </div>
      </CardHeader>

      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="w-6 h-6 text-violet-400 animate-spin" />
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-32 gap-2 text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span className="text-sm">{error}</span>
          </div>
        ) : data.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-[var(--fg-subtle)]">
            <Package className="w-8 h-8 mb-2 opacity-50" />
            <span className="text-sm">{labels.noDeliveries}</span>
          </div>
        ) : (
          <div className="space-y-3">
            {data.map((item) => (
              <div
                key={item.delivery_id}
                className="rounded-lg border border-white/5 bg-[var(--surface-2)]/60 p-3 transition-colors hover:border-white/10"
              >
              {/* Project title and date */}
              <div className="flex items-start justify-between mb-2">
                <h4 className="text-sm font-medium text-[var(--fg-0)] line-clamp-1 flex-1 mr-2">
                  {item.project_title}
                </h4>
                <span className="text-xs text-[var(--fg-subtle)] whitespace-nowrap">
                  {formatDate(item.delivered_at)}
                </span>
              </div>

              {/* Stats row */}
              <div className="flex items-center gap-3 text-xs">
                {/* Rating */}
                {item.rating !== null ? (
                  <div className="flex items-center gap-1">
                    <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
                    <span className="text-yellow-400">{item.rating.toFixed(1)}</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1 text-[var(--fg-subtle)]">
                    <Star className="w-3 h-3" />
                    <span>-</span>
                  </div>
                )}

                {/* On-time status */}
                <div className="flex items-center gap-1">
                  {item.on_time ? (
                    <>
                      <CheckCircle className="w-3 h-3 text-green-400" />
                      <span className="text-green-400">{labels.onTime}</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="w-3 h-3 text-red-400" />
                      <span className="text-red-400">{labels.late}</span>
                    </>
                  )}
                </div>

                {/* Revisions */}
                {item.revision_count > 0 && (
                  <div className="flex items-center gap-1 text-[var(--fg-muted)]">
                    <RotateCcw className="w-3 h-3" />
                    <span>{item.revision_count}</span>
                  </div>
                )}

                {/* Credits earned */}
                <div className="flex items-center gap-1 ml-auto">
                  <span className="text-green-400 font-medium">
                    +{formatCredits(item.credits_earned)}
                  </span>
                  <span className="text-[var(--fg-subtle)]">{labels.credits}</span>
                </div>
              </div>
            </div>
          ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default RecentDeliveries;
