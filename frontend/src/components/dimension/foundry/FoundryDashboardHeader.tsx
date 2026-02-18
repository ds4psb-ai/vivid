"use client";

import { Shield } from "lucide-react";
import { useFoundryData } from "@/hooks/useFoundryData";
import { api } from "@/lib/api";
import type { FoundryHealthResponse, FoundryKPISnapshotResponse } from "@/lib/api";
import { DEMO_KPI_RESPONSE } from "./demo-data";

export function FoundryDashboardHeader() {
  const health = useFoundryData<FoundryHealthResponse>(
    () => api.getFoundryHealth(),
    { refreshInterval: 30000 }
  );
  const kpi = useFoundryData<FoundryKPISnapshotResponse>(
    () => api.getFoundryKPISnapshot(),
    { refreshInterval: 60000 }
  );

  const kpiData = kpi.data || DEMO_KPI_RESPONSE;
  const isOnline = health.data?.status === "ok";

  return (
    <header className="border-b border-[var(--border-subtle)] bg-[var(--surface-1)]">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
              <Shield className="w-5 h-5 text-amber-500" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-[var(--fg-0)]">Original IP Foundry</h1>
              <p className="text-xs text-[var(--fg-muted)]">Rights · Patterns · Recommendations · Experiments</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${isOnline ? "bg-emerald-500" : "bg-rose-500"} ${isOnline ? "animate-pulse" : ""}`} />
            <span className="text-xs text-[var(--fg-muted)]">{isOnline ? "Online" : "Offline"}</span>
          </div>
        </div>
        {/* KPI Strip */}
        <div className="flex items-center gap-6 mt-3 text-xs text-[var(--fg-muted)]">
          <KPIChip label="P95 Latency" value={kpiData.p95_latency_ms != null ? `${kpiData.p95_latency_ms}ms` : "\u2014"} />
          <KPIChip label="P50 Latency" value={kpiData.p50_latency_ms != null ? `${kpiData.p50_latency_ms}ms` : "\u2014"} />
          <KPIChip label="Pattern Reuse" value={kpiData.pattern_reuse_rate != null ? `${(kpiData.pattern_reuse_rate * 100).toFixed(0)}%` : "\u2014"} />
          <KPIChip label="Continuity" value={kpiData.mean_continuity != null ? kpiData.mean_continuity.toFixed(2) : "\u2014"} />
          <KPIChip label="Uplift" value={kpiData.continuity_uplift != null ? `+${kpiData.continuity_uplift.toFixed(2)}` : "\u2014"} highlight />
        </div>
      </div>
    </header>
  );
}

function KPIChip({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex items-center gap-1.5">
      <span>{label}:</span>
      <span className={`font-mono font-medium ${highlight ? "text-amber-400" : "text-[var(--fg-0)]"}`}>{value}</span>
    </div>
  );
}
