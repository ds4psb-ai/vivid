"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { Coins, Clock, X, FileText, ExternalLink, Wifi, WifiOff } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { EvidenceCard } from "@/components/ui/EvidenceCard";

interface GenerationProgressProps {
  slug: string;
  generationId: string;
  onComplete?: () => void;
  onCancel?: () => void;
}

interface GenerationProgress {
  generation_id: string;
  status: string;
  progress_percent: number;
  current_step: string | null;
  credits_consumed: number;
  latency_ms: number;
  error_message: string | null;
}

interface EvidenceData {
  generation_id: string;
  evidence_refs: string[];
  pattern_version: string | null;
  ip_slug: string;
  preset_type: string;
  auteur_key: string | null;
  credits_consumed: number;
  latency_ms: number;
  workflow_trace: WorkflowTraceItem[];
}

interface WorkflowTraceItem {
  evidence_id: string;
  source: string;
  ref: string;
  confidence: number | null;
  status: string | null;
  timestamp: string | null;
}

/**
 * Connection mode for progress streaming
 * SSE (Server-Sent Events) is preferred for efficiency
 * Polling is fallback for environments where SSE fails
 */
type ConnectionMode = "sse" | "polling" | "disconnected";

export default function GenerationProgress({
  slug,
  generationId,
  onComplete,
  onCancel,
}: GenerationProgressProps) {
  const { language, t } = useLanguage();

  const [progress, setProgress] = useState<GenerationProgress | null>(null);
  const [evidence, setEvidence] = useState<EvidenceData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [connectionMode, setConnectionMode] = useState<ConnectionMode>("sse");

  const eventSourceRef = useRef<EventSource | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Fetch evidence data after completion
   */
  const fetchEvidence = useCallback(async () => {
    try {
      const evidenceRes = await fetch(
        `/api/v1/ip/${slug}/generation/${generationId}/evidence`
      );
      if (evidenceRes.ok) {
        setEvidence(await evidenceRes.json());
      }
    } catch (err) {
      console.error("Failed to fetch evidence:", err);
    }
  }, [slug, generationId]);

  /**
   * Handle status updates from either SSE or polling
   */
  const handleProgressUpdate = useCallback(
    (data: GenerationProgress) => {
      setProgress(data);

      if (data.status === "completed") {
        fetchEvidence();
        onComplete?.();
      } else if (data.status === "failed" || data.status === "cancelled") {
        setError(data.error_message || "Generation failed");
      }
    },
    [fetchEvidence, onComplete]
  );

  /**
   * Fallback polling mechanism
   * 2026 Best Practice: Use polling only as fallback when SSE unavailable
   */
  const startPolling = useCallback(() => {
    if (pollingIntervalRef.current) return;

    setConnectionMode("polling");
    console.log("[GenerationProgress] Falling back to polling mode");

    async function pollProgress() {
      try {
        const response = await fetch(
          `/api/v1/ip/${slug}/generation/${generationId}/progress`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch progress");
        }

        const data = await response.json();
        handleProgressUpdate(data);

        // Stop polling on terminal states
        if (["completed", "failed", "cancelled"].includes(data.status)) {
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }

    // Initial fetch
    pollProgress();
    // Poll every 2 seconds
    pollingIntervalRef.current = setInterval(pollProgress, 2000);
  }, [slug, generationId, handleProgressUpdate]);

  /**
   * SSE (Server-Sent Events) streaming
   * 2026 Best Practice: Use SSE for real-time updates, more efficient than polling
   */
  useEffect(() => {
    // Cleanup function
    function cleanup() {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    }

    // Initialize SSE connection
    const sseUrl = `/api/v1/ip/${slug}/generation/${generationId}/stream`;
    const eventSource = new EventSource(sseUrl);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setConnectionMode("sse");
      console.log("[GenerationProgress] SSE connection established");
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as GenerationProgress;
        handleProgressUpdate(data);

        // Close SSE on terminal states
        if (["completed", "failed", "cancelled"].includes(data.status)) {
          eventSource.close();
        }
      } catch (err) {
        console.error("Failed to parse SSE message:", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE connection error:", err);
      eventSource.close();

      // Fallback to polling if SSE fails
      if (connectionMode !== "polling") {
        startPolling();
      }
    };

    return cleanup;
  }, [slug, generationId, handleProgressUpdate, connectionMode, startPolling]);

  const handleCancel = useCallback(async () => {
    setCancelling(true);
    try {
      const response = await fetch(
        "/api/v1/ip/" + slug + "/generation/" + generationId + "/cancel",
        { method: "POST" }
      );

      if (response.ok) {
        onCancel?.();
      }
    } catch (err) {
      console.error("Failed to cancel:", err);
    } finally {
      setCancelling(false);
    }
  }, [slug, generationId, onCancel]);

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-4">
          <X className="w-6 h-6 text-red-500" />
        </div>
        <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
          {language === "ko" ? "생성 실패" : "Generation Failed"}
        </h3>
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">{error}</p>
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700"
        >
          {language === "ko" ? "닫기" : "Close"}
        </button>
      </div>
    );
  }

  const isCompleted = progress?.status === "completed";

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">
          {isCompleted
            ? (language === "ko" ? "생성 완료" : "Generation Complete")
            : (language === "ko" ? "생성 중..." : "Generating...")}
        </h2>
        {!isCompleted && (
          <button
            onClick={handleCancel}
            disabled={cancelling}
            className="text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
          >
            {cancelling ? (language === "ko" ? "취소 중..." : "Cancelling...") : (language === "ko" ? "취소" : "Cancel")}
          </button>
        )}
      </div>

      {/* Progress bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-slate-600 dark:text-slate-400">
            {progress?.current_step || (language === "ko" ? "준비 중" : "Preparing")}
          </span>
          <span className="text-sm font-medium text-slate-900 dark:text-white">
            {progress?.progress_percent || 0}%
          </span>
        </div>
        <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
          <div
            className={"h-full rounded-full transition-all duration-500 " + (isCompleted ? "bg-green-500" : "bg-violet-500")}
            style={{ width: (progress?.progress_percent || 0) + "%" }}
          />
        </div>
      </div>

      {/* Current step info */}
      {!isCompleted && (
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 mb-6">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                <Coins className="w-4 h-4 text-violet-500" />
                <span>{progress?.credits_consumed || 0}</span>
                <span>{language === "ko" ? "크레딧 사용 중" : "credits used"}</span>
              </span>
              <span className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                <Clock className="w-4 h-4 text-violet-500" />
                <span>{Math.floor((progress?.latency_ms || 0) / 1000)}s</span>
              </span>
            </div>
            {/* Connection status indicator */}
            <span
              className={`flex items-center gap-1.5 text-xs ${
                connectionMode === "sse"
                  ? "text-green-600 dark:text-green-400"
                  : connectionMode === "polling"
                  ? "text-yellow-600 dark:text-yellow-400"
                  : "text-red-500"
              }`}
              title={connectionMode === "sse" ? "Real-time streaming" : "Polling fallback"}
            >
              {connectionMode === "sse" ? (
                <Wifi className="w-3 h-3" />
              ) : (
                <WifiOff className="w-3 h-3" />
              )}
              <span className="hidden sm:inline">
                {connectionMode === "sse" ? "Live" : "Polling"}
              </span>
            </span>
          </div>
        </div>
      )}

      {/* Evidence section */}
      {evidence && (
        <div className="border-t border-slate-200 dark:border-slate-700 pt-6">
          <h3 className="text-sm font-medium text-slate-900 dark:text-white mb-3 flex items-center gap-2">
            <FileText className="w-4 h-4" />
            {language === "ko" ? "증거 & 추적" : "Evidence & Trace"}
          </h3>

          <div className="space-y-2">
            {evidence.pattern_version && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500 dark:text-slate-400">
                  {language === "ko" ? "패턴" : "Pattern"}
                </span>
                <span className="text-slate-900 dark:text-white font-mono text-xs">
                  {evidence.pattern_version}
                </span>
              </div>
            )}

            {evidence.auteur_key && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500 dark:text-slate-400">
                  {language === "ko" ? "스타일" : "Style"}
                </span>
                <span className="text-slate-900 dark:text-white">
                  {evidence.auteur_key}
                </span>
              </div>
            )}

            {evidence.evidence_refs.length > 0 || evidence.workflow_trace?.length > 0 ? (
              <div className="mt-3">
                <EvidenceCard
                  variant="evidence"
                  title={t("evidenceDataTitle")}
                  confidenceLevel="medium"
                  reasonCodes={[]}
                  evidenceRefs={evidence.evidence_refs}
                  reasonSummary={t("evidenceSummaryDefault")}
                  workflowTrace={evidence.workflow_trace}
                  isCollapsible
                />
              </div>
            ) : null}
          </div>

          {/* Final stats */}
          <div className="mt-4 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 flex items-center justify-between">
            <span className="text-sm text-green-700 dark:text-green-400">
              {language === "ko" ? "완료" : "Completed"}
            </span>
            <div className="flex items-center gap-4 text-sm text-green-600 dark:text-green-400">
              <span>{evidence.credits_consumed} credits</span>
              <span>{(evidence.latency_ms / 1000).toFixed(1)}s</span>
            </div>
          </div>
        </div>
      )}

      {/* Result preview (when completed) */}
      {isCompleted && (
        <div className="mt-6">
          <button
            onClick={() => {
              // Navigate to result or show preview
            }}
            className="w-full py-3 px-4 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-medium flex items-center justify-center gap-2"
          >
            <ExternalLink className="w-5 h-5" />
            {language === "ko" ? "결과 보기" : "View Result"}
          </button>
        </div>
      )}
    </div>
  );
}
