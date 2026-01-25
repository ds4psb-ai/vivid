"use client";

/**
 * Pending Approvals Panel Component (Phase 7 HITL Enhancement)
 *
 * Displays pending approval checkpoints for the creator.
 */

import { useCallback, useEffect, useState } from "react";
import {
  ClipboardCheck,
  Loader2,
  AlertCircle,
  Clock,
  Check,
  X,
  ChevronRight,
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { fetchWithAuth } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

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

  const loadData = useCallback(async () => {
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
  }, [labels.errorMsg]);

  useEffect(() => {
    loadData();
  }, [loadData]);

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
    <Card className="border border-white/5 bg-[var(--surface-1)]/70 h-full">
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-4">
        <div className="flex items-center gap-2">
          <ClipboardCheck className="w-4 h-4 text-violet-400" />
          <CardTitle className="text-base">{labels.title}</CardTitle>
          {total > 0 && (
            <Badge className="bg-violet-600/20 text-violet-200 border-violet-500/30 text-xs">
              {total}
            </Badge>
          )}
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
            <ClipboardCheck className="w-8 h-8 mb-2 opacity-50" />
            <span className="text-sm">{labels.noItems}</span>
          </div>
        ) : (
          <div className="space-y-3">
            {data.map((item) => (
              <div
                key={item.checkpoint_id}
                className="rounded-lg border border-white/5 bg-[var(--surface-2)]/60 p-3 transition-colors hover:border-white/10"
              >
              {/* Top row */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {item.dimension && (
                      <Badge variant="secondary" className="text-[10px]">{item.dimension}</Badge>
                    )}
                    <span className="text-xs text-[var(--fg-subtle)]">
                      {item.node_id}
                    </span>
                  </div>
                  <p className="text-sm text-[var(--fg-muted)] line-clamp-2">
                    {truncatePreview(item.output_preview)}
                  </p>
                </div>
              </div>

              {/* Bottom row */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 text-xs">
                  <div className="flex items-center gap-1">
                    <span className="text-[var(--fg-subtle)]">{labels.confidence}:</span>
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
                  <div className="flex items-center gap-1 text-[var(--fg-subtle)]">
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
      </CardContent>
    </Card>
  );
}

export default PendingApprovalsPanel;
