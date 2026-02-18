"use client";

import { RefreshCw, AlertCircle, Inbox } from "lucide-react";

// --- FoundryPanelCard ---
export function FoundryPanelCard({
  title,
  children,
  isLoading,
  error,
  onRefresh,
  className = "",
}: {
  title: string;
  children: React.ReactNode;
  isLoading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  className?: string;
}) {
  return (
    <div className={`rounded-2xl bg-[var(--surface-1)] border border-[var(--border-subtle)] p-5 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-[var(--fg-0)] uppercase tracking-wide">{title}</h3>
        {onRefresh && <RefreshButton onClick={onRefresh} isLoading={isLoading} />}
      </div>
      {error ? <FoundryErrorState message={error} /> : isLoading && !children ? <FoundryLoadingState /> : children}
    </div>
  );
}

// --- DecisionBadge ---
const DECISION_COLORS: Record<string, string> = {
  allow: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  review: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  block: "bg-rose-500/15 text-rose-400 border-rose-500/30",
  hold: "bg-blue-500/15 text-blue-400 border-blue-500/30",
};

export function DecisionBadge({ decision }: { decision: string }) {
  const colors = DECISION_COLORS[decision] || DECISION_COLORS.hold;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colors}`}>
      {decision.toUpperCase()}
    </span>
  );
}

// --- ScoreBar ---
export function ScoreBar({ score, max = 1, label }: { score: number; max?: number; label?: string }) {
  const pct = Math.min(100, Math.max(0, (score / max) * 100));
  const color = pct >= 80 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-500" : "bg-rose-500";
  return (
    <div className="flex items-center gap-2">
      {label && <span className="text-xs text-[var(--fg-muted)] w-24 shrink-0">{label}</span>}
      <div className="flex-1 h-2 rounded-full bg-[var(--surface-2)] overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-[var(--fg-muted)] w-10 text-right">{score.toFixed(2)}</span>
    </div>
  );
}

// --- RefreshButton ---
export function RefreshButton({ onClick, isLoading }: { onClick: () => void; isLoading?: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={isLoading}
      className="p-1.5 rounded-lg hover:bg-[var(--surface-2)] text-[var(--fg-muted)] hover:text-[var(--fg-0)] transition-colors disabled:opacity-50"
    >
      <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
    </button>
  );
}

// --- FoundryEmptyState ---
export function FoundryEmptyState({ message = "No data available" }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-[var(--fg-muted)]">
      <Inbox className="w-8 h-8 mb-2 opacity-50" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

// --- FoundryErrorState ---
export function FoundryErrorState({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-2 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
      <AlertCircle className="w-4 h-4 shrink-0" />
      <span>{message}</span>
    </div>
  );
}

// --- FoundryLoadingState ---
export function FoundryLoadingState() {
  return (
    <div className="flex items-center justify-center py-8">
      <div className="w-6 h-6 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
    </div>
  );
}
