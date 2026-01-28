"use client";

/**
 * HITL (Human-in-the-Loop) Review Dashboard
 *
 * Manages review items for:
 * - Vector Drift: Logic Vector version upgrades
 * - QC Failure: Quality check adjustments
 * - Prompt Pattern: System prompt patches
 *
 * Features:
 * - Severity-based filtering
 * - One-click approve with auto-apply
 * - Reject with reason tracking
 */

import { useState, useEffect, useCallback } from "react";
import {
  Shield,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  AlertTriangle,
  TrendingUp,
  Sparkles,
  FileText,
  RefreshCw,
  ChevronDown,
} from "lucide-react";

import { fetchWithAuth } from "@/lib/api-client";
import { StatCard, StatusBadge, PageHeader, EmptyState } from "@/components/shared";
import AppShell from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

// =============================================================================
// Types
// =============================================================================

interface HITLItem {
  id: string;
  review_type: string;
  severity: string;
  ip_id?: string;
  trace_id?: string;
  payload: Record<string, unknown>;
  suggested_action?: Record<string, unknown>;
  status: string;
  assigned_to?: string;
  decision?: string;
  decision_by?: string;
  decision_at?: string;
  decision_notes?: string;
  auto_applied: boolean;
  applied_at?: string;
  apply_result?: Record<string, unknown>;
  created_at: string;
  expires_at?: string;
}

interface HITLCounts {
  total: number;
  vector_drift?: number;
  qc_failure?: number;
  prompt_pattern?: number;
}

// =============================================================================
// Constants
// =============================================================================

const SEVERITY_COLORS: Record<string, string> = {
  critical: "text-red-400 bg-red-500/20",
  high: "text-orange-400 bg-orange-500/20",
  medium: "text-yellow-400 bg-yellow-500/20",
  low: "text-blue-400 bg-blue-500/20",
};

const REVIEW_TYPE_ICONS: Record<string, typeof TrendingUp> = {
  vector_drift: TrendingUp,
  qc_failure: AlertTriangle,
  prompt_pattern: FileText,
};

const REVIEW_TYPE_LABELS: Record<string, string> = {
  vector_drift: "Vector Drift",
  qc_failure: "QC Failure",
  prompt_pattern: "Prompt Pattern",
};

// =============================================================================
// Components
// =============================================================================

function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${SEVERITY_COLORS[severity] || SEVERITY_COLORS.medium}`}>
      {severity.toUpperCase()}
    </span>
  );
}

function HITLCard({
  item,
  onApprove,
  onReject,
}: {
  item: HITLItem;
  onApprove: () => void;
  onReject: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const TypeIcon = REVIEW_TYPE_ICONS[item.review_type] || Sparkles;

  const expiresAt = item.expires_at ? new Date(item.expires_at) : null;
  const isExpiringSoon = expiresAt && (expiresAt.getTime() - Date.now()) < 4 * 60 * 60 * 1000;

  return (
    <div className="bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-xl p-5 hover:border-purple-500/50 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${SEVERITY_COLORS[item.severity] || SEVERITY_COLORS.medium}`}>
            <TypeIcon className="w-4 h-4" />
          </div>
          <div>
            <div className="font-medium text-[var(--fg-0)]">
              {REVIEW_TYPE_LABELS[item.review_type] || item.review_type}
            </div>
            {item.ip_id && (
              <div className="text-sm text-[var(--fg-muted)]">
                IP: {item.ip_id}
              </div>
            )}
          </div>
        </div>
        <SeverityBadge severity={item.severity} />
      </div>

      {/* Key Info */}
      {item.review_type === "vector_drift" && item.payload && (() => {
        const driftScore = typeof item.payload.drift_score === 'number' ? item.payload.drift_score : 0;
        const driftReason = typeof item.payload.drift_reason === 'string' ? item.payload.drift_reason : null;
        return (
          <div className="mb-4 p-3 bg-[var(--surface-2)] rounded-lg">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-[var(--fg-muted)]">Drift Score</span>
              <span className={driftScore > 0.3 ? "text-red-400" : "text-yellow-400"}>
                {(driftScore * 100).toFixed(1)}%
              </span>
            </div>
            <div className="h-2 bg-[var(--surface-3)] rounded-full overflow-hidden">
              <div
                className={`h-full ${driftScore > 0.3 ? "bg-red-500" : "bg-yellow-500"}`}
                style={{ width: `${Math.min(100, driftScore * 100)}%` }}
              />
            </div>
            {driftReason && (
              <div className="mt-2 text-xs text-[var(--fg-muted)]">
                Reason: {driftReason.replace(/_/g, " ")}
              </div>
            )}
          </div>
        );
      })()}

      {/* Expiry Warning */}
      {isExpiringSoon && (
        <div className="mb-4 p-2 bg-orange-500/10 border border-orange-500/30 rounded-lg flex items-center gap-2 text-sm text-orange-400">
          <Clock className="w-4 h-4" />
          Expires soon: {expiresAt?.toLocaleTimeString()}
        </div>
      )}

      {/* Expandable Details */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between text-sm text-[var(--fg-muted)] hover:text-[var(--fg-0)] mb-4"
      >
        <span>View Details</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${expanded ? "rotate-180" : ""}`} />
      </button>

      {expanded && (
        <div className="mb-4 p-3 bg-[var(--surface-2)] rounded-lg overflow-auto max-h-48">
          <pre className="text-xs text-[var(--fg-muted)]">
            {JSON.stringify(item.payload, null, 2)}
          </pre>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          className="flex-1 bg-green-500/10 border-green-500/30 text-green-400 hover:bg-green-500/20"
          onClick={onApprove}
        >
          <CheckCircle className="w-4 h-4 mr-2" />
          Approve
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="flex-1 bg-red-500/10 border-red-500/30 text-red-400 hover:bg-red-500/20"
          onClick={onReject}
        >
          <XCircle className="w-4 h-4 mr-2" />
          Reject
        </Button>
      </div>

      {/* Metadata */}
      <div className="mt-4 pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between text-xs text-[var(--fg-muted)]">
        <span>Created: {new Date(item.created_at).toLocaleString()}</span>
        {item.trace_id && <span>Trace: {item.trace_id.slice(0, 8)}...</span>}
      </div>
    </div>
  );
}

// =============================================================================
// Main Page
// =============================================================================

export default function HITLDashboardPage() {
  const [items, setItems] = useState<HITLItem[]>([]);
  const [counts, setCounts] = useState<HITLCounts>({ total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>("all");
  const [processing, setProcessing] = useState<string | null>(null);

  const fetchItems = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const reviewType = activeTab === "all" ? undefined : activeTab;
      const params = reviewType ? `?review_type=${reviewType}` : "";

      const data = await fetchWithAuth<{ items: HITLItem[]; counts: HITLCounts }>(`/api/hitl/pending${params}`);
      setItems(data.items || []);
      setCounts(data.counts || { total: 0 });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const handleApprove = async (itemId: string) => {
    try {
      setProcessing(itemId);

      await fetchWithAuth<{ success: boolean }>(`/api/hitl/${itemId}/approve`, {
        method: "POST",
        body: JSON.stringify({ notes: "Approved via dashboard" }),
      });

      // Refresh list
      await fetchItems();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setProcessing(null);
    }
  };

  const handleReject = async (itemId: string) => {
    const reason = window.prompt("Enter rejection reason:");
    if (!reason) return;

    try {
      setProcessing(itemId);

      await fetchWithAuth<{ success: boolean }>(`/api/hitl/${itemId}/reject`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      });

      await fetchItems();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rejection failed");
    } finally {
      setProcessing(null);
    }
  };

  return (
    <AppShell>
      <div className="p-6 max-w-7xl mx-auto">
        {/* Header */}
        <PageHeader
          title="HITL Review Queue"
          subtitle="Human-in-the-Loop review items requiring approval"
          icon={Shield}
          actions={
            <Button
              variant="outline"
              size="sm"
              onClick={fetchItems}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          }
        />

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <StatCard
            title="Total Pending"
            value={counts.total}
            icon={Clock}
          />
          <StatCard
            title="Vector Drift"
            value={counts.vector_drift || 0}
            icon={TrendingUp}
            color={counts.vector_drift && counts.vector_drift > 5 ? "red" : "yellow"}
          />
          <StatCard
            title="QC Failures"
            value={counts.qc_failure || 0}
            icon={AlertTriangle}
          />
          <StatCard
            title="Prompt Patterns"
            value={counts.prompt_pattern || 0}
            icon={FileText}
          />
        </div>

        {/* Filter Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
          <TabsList className="bg-[var(--surface-1)]">
            <TabsTrigger value="all">All ({counts.total})</TabsTrigger>
            <TabsTrigger value="vector_drift">
              Vector Drift ({counts.vector_drift || 0})
            </TabsTrigger>
            <TabsTrigger value="qc_failure">
              QC Failure ({counts.qc_failure || 0})
            </TabsTrigger>
            <TabsTrigger value="prompt_pattern">
              Prompt Pattern ({counts.prompt_pattern || 0})
            </TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Error Banner */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={CheckCircle}
            title="No Pending Reviews"
            description="All items have been reviewed. Check back later."
          />
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map((item) => (
              <HITLCard
                key={item.id}
                item={item}
                onApprove={() => handleApprove(item.id)}
                onReject={() => handleReject(item.id)}
              />
            ))}
          </div>
        )}

        {/* Processing Overlay */}
        {processing && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-[var(--surface-1)] p-6 rounded-xl flex items-center gap-4">
              <Loader2 className="w-6 h-6 animate-spin text-purple-400" />
              <span>Processing...</span>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
