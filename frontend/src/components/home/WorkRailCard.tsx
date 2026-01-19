"use client";

import { CheckCircle2, Loader2, AlertTriangle } from "lucide-react";

type WorkStatus = "draft" | "in_progress" | "complete" | "error";

interface WorkRailCardProps {
  title: string;
  subtitle?: string;
  status?: WorkStatus;
  updatedAt?: string;
}

const STATUS_META: Record<WorkStatus, { label: string; icon: typeof Loader2; className: string }> = {
  draft: {
    label: "초안",
    icon: Loader2,
    className: "text-slate-400 border-slate-400/30 bg-slate-500/10",
  },
  in_progress: {
    label: "진행중",
    icon: Loader2,
    className: "text-sky-400 border-sky-400/30 bg-sky-500/10",
  },
  complete: {
    label: "완료",
    icon: CheckCircle2,
    className: "text-emerald-400 border-emerald-400/30 bg-emerald-500/10",
  },
  error: {
    label: "오류",
    icon: AlertTriangle,
    className: "text-rose-400 border-rose-400/30 bg-rose-500/10",
  },
};

export function WorkRailCard({
  title,
  subtitle,
  status = "draft",
  updatedAt,
}: WorkRailCardProps) {
  const meta = STATUS_META[status];
  const StatusIcon = meta.icon;

  return (
    <div className="group h-full rounded-2xl border border-[var(--border-muted)] bg-[var(--surface-1)] p-4 hover:border-[var(--border-strong)] transition-all">
      <div className="flex items-center justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-[var(--fg-0)] line-clamp-1">{title}</p>
          {subtitle && (
            <p className="mt-1 text-xs text-[var(--fg-muted)] line-clamp-1">{subtitle}</p>
          )}
        </div>
        <span className={`flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold ${meta.className}`}>
          <StatusIcon className={`h-3 w-3 ${status === "in_progress" ? "animate-spin" : ""}`} />
          {meta.label}
        </span>
      </div>
      {updatedAt && (
        <div className="mt-3 text-[10px] text-[var(--fg-muted)]">
          업데이트: {updatedAt}
        </div>
      )}
    </div>
  );
}
