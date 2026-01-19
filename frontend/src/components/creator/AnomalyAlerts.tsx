"use client";

/**
 * Anomaly Alerts Component (Phase 7 HITL Enhancement)
 *
 * Displays AI-detected anomalies in creator metrics.
 */

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Loader2,
  AlertCircle,
  TrendingDown,
  RotateCcw,
  Clock,
  DollarSign,
  Activity,
  Check,
  X,
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { fetchWithAuth } from "@/lib/api-client";

interface AnomalyAlert {
  id: string;
  type: string;
  severity: string;
  metric_name: string;
  metric_value: number;
  expected_range: number[];
  description: string;
  detected_at: string;
}

interface AnomaliesResponse {
  items: AnomalyAlert[];
  total: number;
}

const SEVERITY_CONFIG: Record<string, { bg: string; border: string; icon: string }> = {
  critical: { bg: "bg-red-500/10", border: "border-red-500/30", icon: "text-red-400" },
  warning: { bg: "bg-yellow-500/10", border: "border-yellow-500/30", icon: "text-yellow-400" },
  info: { bg: "bg-blue-500/10", border: "border-blue-500/30", icon: "text-blue-400" },
};

const TYPE_ICONS: Record<string, React.ElementType> = {
  rating_drop: TrendingDown,
  revision_spike: RotateCcw,
  delivery_delay: Clock,
  credit_anomaly: DollarSign,
  engagement_drop: Activity,
};

export function AnomalyAlerts() {
  const { language } = useLanguage();
  const [data, setData] = useState<AnomalyAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  const labels = {
    title: language === "ko" ? "이상 감지 알림" : "Anomaly Alerts",
    noAlerts: language === "ko" ? "감지된 이상이 없습니다" : "No anomalies detected",
    errorMsg: language === "ko" ? "데이터를 불러올 수 없습니다" : "Failed to load data",
    resolve: language === "ko" ? "해결" : "Resolve",
    dismiss: language === "ko" ? "무시" : "Dismiss",
    detected: language === "ko" ? "감지" : "Detected",
    expected: language === "ko" ? "예상 범위" : "Expected",
    actual: language === "ko" ? "실제" : "Actual",
    critical: language === "ko" ? "심각" : "Critical",
    warning: language === "ko" ? "경고" : "Warning",
    info: language === "ko" ? "정보" : "Info",
    typeLabels: {
      rating_drop: language === "ko" ? "평점 하락" : "Rating Drop",
      revision_spike: language === "ko" ? "수정 급증" : "Revision Spike",
      delivery_delay: language === "ko" ? "납품 지연" : "Delivery Delay",
      credit_anomaly: language === "ko" ? "크레딧 이상" : "Credit Anomaly",
      engagement_drop: language === "ko" ? "참여도 하락" : "Engagement Drop",
    } as Record<string, string>,
  };

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      const response = await fetchWithAuth<AnomaliesResponse>(
        "/api/v1/creator/anomalies?limit=10"
      );
      setData(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : labels.errorMsg);
    } finally {
      setLoading(false);
    }
  }

  async function handleResolve(anomalyId: string) {
    try {
      setResolvingId(anomalyId);
      await fetchWithAuth(`/api/v1/creator/anomalies/${anomalyId}/resolve`, {
        method: "POST",
        body: JSON.stringify({ resolution_notes: "Resolved from dashboard" }),
      });
      // Remove from list
      setData((prev) => prev.filter((item) => item.id !== anomalyId));
    } catch (err) {
      console.error("Failed to resolve anomaly:", err);
    } finally {
      setResolvingId(null);
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString(language === "ko" ? "ko-KR" : "en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getSeverityLabel = (severity: string) => {
    if (severity === "critical") return labels.critical;
    if (severity === "warning") return labels.warning;
    return labels.info;
  };

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5 h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-yellow-400" />
          <h3 className="text-sm font-medium text-white">{labels.title}</h3>
          {data.length > 0 && (
            <span className="px-2 py-0.5 bg-yellow-600/30 text-yellow-300 text-xs rounded-full">
              {data.length}
            </span>
          )}
        </div>
      </div>

      {/* Content */}
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
        <div className="flex flex-col items-center justify-center h-32 text-gray-500">
          <Check className="w-8 h-8 mb-2 text-green-400 opacity-50" />
          <span className="text-sm">{labels.noAlerts}</span>
        </div>
      ) : (
        <div className="space-y-3 max-h-80 overflow-y-auto">
          {data.map((item) => {
            const config = SEVERITY_CONFIG[item.severity] || SEVERITY_CONFIG.info;
            const Icon = TYPE_ICONS[item.type] || AlertTriangle;

            return (
              <div
                key={item.id}
                className={`${config.bg} ${config.border} border rounded-lg p-3`}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Icon className={`w-4 h-4 ${config.icon}`} />
                    <div>
                      <span className="text-sm font-medium text-white">
                        {labels.typeLabels[item.type] || item.type}
                      </span>
                      <span className={`ml-2 px-1.5 py-0.5 text-[10px] rounded ${config.bg} ${
                        item.severity === "critical" ? "text-red-300" :
                        item.severity === "warning" ? "text-yellow-300" :
                        "text-blue-300"
                      }`}>
                        {getSeverityLabel(item.severity)}
                      </span>
                    </div>
                  </div>
                  <span className="text-xs text-gray-500">
                    {formatDate(item.detected_at)}
                  </span>
                </div>

                {/* Description */}
                <p className="text-xs text-gray-300 mb-2 line-clamp-2">
                  {item.description}
                </p>

                {/* Metrics */}
                <div className="flex items-center gap-4 text-xs mb-2">
                  <div>
                    <span className="text-gray-500">{labels.actual}: </span>
                    <span className="text-white font-medium">
                      {item.metric_value.toFixed(2)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">{labels.expected}: </span>
                    <span className="text-gray-400">
                      {item.expected_range[0].toFixed(2)} - {item.expected_range[1].toFixed(2)}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-end gap-2">
                  <button
                    onClick={() => handleResolve(item.id)}
                    disabled={resolvingId === item.id}
                    className="flex items-center gap-1 px-2 py-1 bg-green-600/20 text-green-400
                             hover:bg-green-600/30 rounded text-xs transition-colors disabled:opacity-50"
                  >
                    {resolvingId === item.id ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <Check className="w-3 h-3" />
                    )}
                    {labels.resolve}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default AnomalyAlerts;
