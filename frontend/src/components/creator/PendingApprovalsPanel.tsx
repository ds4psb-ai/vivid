"use client";

/**
 * Pending Approvals Panel Component (Phase 7 HITL Enhancement)
 *
 * Displays pending approval checkpoints for the creator.
 */

import { useEffect, useState } from "react";
import {
  ClipboardCheck,
  Loader2,
  AlertCircle,
  Clock,
  Check,
  X,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { fetchWithAuth } from "@/lib/api-client";

interface PendingApproval {
  checkpoint_id: string;
  execution_id: string;
  node_id: string;
  output_preview: string;
  confidence: number;
  dimension: string | null;
  expires_at: string;
  created_at: string;
}

interface PendingApprovalsResponse {
  items: PendingApproval[];
  total: number;
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.85) return "text-green-400";
  if (confidence >= 0.5) return "text-yellow-400";
  return "text-red-400";
}

function getConfidenceBadge(confidence: number, language: string): string {
  if (confidence >= 0.85) return language === "ko" ? "높음" : "High";
  if (confidence >= 0.5) return language === "ko" ? "중간" : "Medium";
  return language === "ko" ? "낮음" : "Low";
}

export function PendingApprovalsPanel() {
  const { language } = useLanguage();
  const [data, setData] = useState<PendingApproval[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingId, setProcessingId] = useState<string | null>(null);

  const labels = {
    title: language === "ko" ? "대기 중인 승인" : "Pending Approvals",
    noItems: language === "ko" ? "대기 중인 항목이 없습니다" : "No pending items",
    errorMsg: language === "ko" ? "데이터를 불러올 수 없습니다" : "Failed to load data",
    confidence: language === "ko" ? "신뢰도" : "Confidence",
    expiresAt: language === "ko" ? "만료" : "Expires",
    approve: language === "ko" ? "승인" : "Approve",
    reject: language === "ko" ? "거부" : "Reject",
    viewDetails: language === "ko" ? "상세 보기" : "View Details",
    showMore: language === "ko" ? "더 보기" : "Show More",
  };

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      const response = await fetchWithAuth<PendingApprovalsResponse>(
        "/api/v1/creator/pending-approvals?limit=10"
      );
      setData(response.items);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : labels.errorMsg);
    } finally {
      setLoading(false);
    }
  }

  async function handleApproval(checkpointId: string, action: "approve" | "reject") {
    try {
      setProcessingId(checkpointId);
      await fetchWithAuth(`/api/v1/approval-gate/${checkpointId}/resolve`, {
        method: "POST",
        body: JSON.stringify({
          action: action === "approve" ? "approve_continue" : "reject",
        }),
      });
      // Remove from list
      setData((prev) => prev.filter((item) => item.checkpoint_id !== checkpointId));
      setTotal((prev) => prev - 1);
    } catch (err) {
      console.error("Failed to process approval:", err);
    } finally {
      setProcessingId(null);
    }
  }

  const formatTimeRemaining = (expiresAt: string) => {
    const now = new Date();
    const expires = new Date(expiresAt);
    const diffMs = expires.getTime() - now.getTime();

    if (diffMs <= 0) return language === "ko" ? "만료됨" : "Expired";

    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `${days}${language === "ko" ? "일" : "d"}`;
    }
    if (hours > 0) return `${hours}${language === "ko" ? "시간" : "h"}`;
    return `${minutes}${language === "ko" ? "분" : "m"}`;
  };

  const truncatePreview = (text: string, maxLength = 100) => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + "...";
  };

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5 h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <ClipboardCheck className="w-4 h-4 text-violet-400" />
          <h3 className="text-sm font-medium text-white">{labels.title}</h3>
          {total > 0 && (
            <span className="px-2 py-0.5 bg-violet-600/30 text-violet-300 text-xs rounded-full">
              {total}
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
          <ClipboardCheck className="w-8 h-8 mb-2 opacity-50" />
          <span className="text-sm">{labels.noItems}</span>
        </div>
      ) : (
        <div className="space-y-3">
          {data.map((item) => (
            <div
              key={item.checkpoint_id}
              className="bg-gray-900/50 border border-gray-700 rounded-lg p-3 hover:border-gray-600 transition-colors"
            >
              {/* Top row */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {item.dimension && (
                      <span className="px-2 py-0.5 bg-blue-600/20 text-blue-300 text-xs rounded">
                        {item.dimension}
                      </span>
                    )}
                    <span className="text-xs text-gray-500">
                      {item.node_id}
                    </span>
                  </div>
                  <p className="text-sm text-gray-300 line-clamp-2">
                    {truncatePreview(item.output_preview)}
                  </p>
                </div>
              </div>

              {/* Bottom row */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 text-xs">
                  <div className="flex items-center gap-1">
                    <span className="text-gray-500">{labels.confidence}:</span>
                    <span className={getConfidenceColor(item.confidence)}>
                      {(item.confidence * 100).toFixed(0)}%
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                      item.confidence >= 0.85 ? "bg-green-500/20 text-green-400" :
                      item.confidence >= 0.5 ? "bg-yellow-500/20 text-yellow-400" :
                      "bg-red-500/20 text-red-400"
                    }`}>
                      {getConfidenceBadge(item.confidence, language)}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-gray-500">
                    <Clock className="w-3 h-3" />
                    <span>{formatTimeRemaining(item.expires_at)}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleApproval(item.checkpoint_id, "approve")}
                    disabled={processingId === item.checkpoint_id}
                    className="flex items-center gap-1 px-2 py-1 bg-green-600/20 text-green-400
                             hover:bg-green-600/30 rounded text-xs transition-colors disabled:opacity-50"
                  >
                    {processingId === item.checkpoint_id ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <Check className="w-3 h-3" />
                    )}
                    {labels.approve}
                  </button>
                  <button
                    onClick={() => handleApproval(item.checkpoint_id, "reject")}
                    disabled={processingId === item.checkpoint_id}
                    className="flex items-center gap-1 px-2 py-1 bg-red-600/20 text-red-400
                             hover:bg-red-600/30 rounded text-xs transition-colors disabled:opacity-50"
                  >
                    <X className="w-3 h-3" />
                    {labels.reject}
                  </button>
                </div>
              </div>
            </div>
          ))}

          {/* Show more */}
          {total > data.length && (
            <button
              className="w-full flex items-center justify-center gap-1 py-2 text-sm text-violet-400
                       hover:text-violet-300 transition-colors"
              onClick={() => window.location.href = "/creator/approvals"}
            >
              {labels.showMore} ({total - data.length} {language === "ko" ? "개 더" : "more"})
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default PendingApprovalsPanel;
