"use client";

import { Sparkles, Clock3, Coins } from "lucide-react";

interface PresetRailCardProps {
  title: string;
  description?: string;
  creditCost?: number;
  duration?: string;
  badge?: string;
}

export function PresetRailCard({
  title,
  description,
  creditCost,
  duration,
  badge,
}: PresetRailCardProps) {
  return (
    <div className="group h-full rounded-2xl border border-[var(--border-muted)] bg-[var(--surface-1)] p-4 hover:border-[var(--border-strong)] hover:-translate-y-1 transition-all relative overflow-hidden dimension-card-shimmer">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-[var(--fg-0)] line-clamp-1">{title}</p>
          {description && (
            <p className="mt-1 text-xs text-[var(--fg-muted)] line-clamp-2">{description}</p>
          )}
        </div>
        {badge && (
          <span className="flex items-center gap-1 rounded-full bg-violet-500/10 text-violet-400 px-2 py-0.5 text-[10px] font-semibold border border-violet-500/20">
            <Sparkles className="h-3 w-3" />
            {badge}
          </span>
        )}
      </div>
      <div className="mt-3 flex items-center gap-3 text-[10px] text-[var(--fg-muted)]">
        {creditCost !== undefined && (
          <span className="flex items-center gap-1">
            <Coins className="h-3 w-3" />
            {creditCost} 크레딧
          </span>
        )}
        {duration && (
          <span className="flex items-center gap-1">
            <Clock3 className="h-3 w-3" />
            {duration}
          </span>
        )}
      </div>
    </div>
  );
}
