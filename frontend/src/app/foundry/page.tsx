"use client";

import { useCallback, useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import {
  api,
  type FoundryChannelMonitoringResponse,
  type FoundryHealthResponse,
  type FoundryKPISnapshotResponse,
  type FoundryStatusResponse,
  type FoundryExperimentSummaryResponse,
  type FoundryVendorDrillResponse,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-[var(--glass-border)] bg-[var(--surface-1)] p-4">
      <h2 className="mb-3 text-sm font-semibold text-[var(--fg-0)]">{title}</h2>
      {children}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="flex items-baseline justify-between gap-2 py-1">
      <span className="text-xs text-[var(--fg-muted)]">{label}</span>
      <span className="font-mono text-sm text-[var(--fg-0)]">{value ?? "—"}</span>
    </div>
  );
}

function Badge({ ok }: { ok: boolean }) {
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
        ok ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"
      }`}
    >
      {ok ? "OK" : "DOWN"}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function FoundryAdminPage() {
  const [health, setHealth] = useState<FoundryHealthResponse | null>(null);
  const [status, setStatus] = useState<FoundryStatusResponse | null>(null);
  const [kpi, setKpi] = useState<FoundryKPISnapshotResponse | null>(null);
  const [channels, setChannels] = useState<FoundryChannelMonitoringResponse | null>(null);
  const [experiment, setExperiment] = useState<FoundryExperimentSummaryResponse | null>(null);
  const [drill, setDrill] = useState<FoundryVendorDrillResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [drillLoading, setDrillLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAll = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const [h, s, k, ch] = await Promise.all([
        api.getFoundryHealth(),
        api.getFoundryStatus(),
        api.getFoundryKPISnapshot(),
        api.getFoundryChannelMonitoring(),
      ]);
      setHealth(h);
      setStatus(s);
      setKpi(k);
      setChannels(ch);

      // Experiment summary — use default key, ignore 404
      try {
        const exp = await api.getFoundryExperimentSummary("default");
        setExperiment(exp);
      } catch {
        /* no experiments yet */
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Foundry 조회 실패");
    } finally {
      setLoading(false);
    }
  }, []);

  const runDrill = async () => {
    setDrillLoading(true);
    try {
      const res = await api.runFoundryVendorDrill();
      setDrill(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Vendor drill 실패");
    } finally {
      setDrillLoading(false);
    }
  };

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  return (
    <AppShell showTopBar={false}>
      <div className="mx-auto max-w-7xl px-6 py-8 space-y-6">
        {/* Header */}
        <header className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-2xl font-bold text-[var(--fg-0)]">
              Original-IP Foundry Dashboard
            </h1>
            <p className="text-sm text-[var(--fg-muted)]">
              Runtime health, KPI metrics, experiments, channel monitoring, rights gate
            </p>
          </div>
          <button
            onClick={() => void loadAll()}
            disabled={loading}
            className="rounded-lg border border-[var(--glass-border)] px-3 py-2 text-sm hover:bg-black/5 disabled:opacity-50"
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
        </header>

        {error && (
          <div className="rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Row 1: Health + KPI + Experiment */}
        <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {/* Health & Status */}
          <Card title="Health & Status">
            <div className="flex items-center gap-2 mb-3">
              <Badge ok={health?.status === "ok"} />
              <span className="text-xs text-[var(--fg-muted)]">
                {health?.access_scope ?? "—"}
              </span>
            </div>
            <Stat label="Foundry Enabled" value={status?.enabled ? "Yes" : "No"} />
            <Stat label="Write Enabled" value={status?.write_enabled ? "Yes" : "No"} />
            <Stat label="Worker Provider" value={status?.worker_provider} />
            <Stat label="Allowlist" value={`${status?.allowlist_count ?? 0} users`} />
          </Card>

          {/* KPI Panel */}
          <Card title="KPI Snapshot">
            <Stat label="p95 Latency" value={kpi?.p95_latency_ms != null ? `${kpi.p95_latency_ms}ms` : null} />
            <Stat label="p50 Latency" value={kpi?.p50_latency_ms != null ? `${kpi.p50_latency_ms}ms` : null} />
            <Stat
              label="Pattern Reuse"
              value={kpi?.pattern_reuse_rate != null ? `${(kpi.pattern_reuse_rate * 100).toFixed(1)}%` : null}
            />
            <Stat
              label="Continuity Uplift"
              value={
                kpi?.continuity_uplift != null
                  ? `${kpi.continuity_uplift > 0 ? "+" : ""}${(kpi.continuity_uplift * 100).toFixed(1)}%`
                  : null
              }
            />
            <div className="mt-2 border-t border-[var(--glass-border)] pt-2">
              <Stat label="Latency samples" value={kpi?.sample_counts?.latency} />
              <Stat label="Continuity samples" value={kpi?.sample_counts?.continuity} />
            </div>
          </Card>

          {/* Experiment Panel */}
          <Card title="Experiment Summary">
            {experiment ? (
              <>
                <Stat label="Experiment" value={experiment.experiment_key} />
                <Stat label="Total Events" value={experiment.total_events} />
                <div className="mt-2 space-y-1">
                  {Object.entries(experiment.variants).map(([variant, stats]) => (
                    <div
                      key={variant}
                      className="flex items-center justify-between rounded-lg bg-black/5 px-2 py-1"
                    >
                      <span className="text-xs font-medium">{variant}</span>
                      <span className="text-xs text-[var(--fg-muted)]">
                        accept: {(stats.accept_rate * 100).toFixed(0)}% &middot;
                        edit: {(stats.edit_rate * 100).toFixed(0)}% &middot;
                        n={stats.total}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="text-xs text-[var(--fg-muted)]">No experiments yet</p>
            )}
          </Card>
        </section>

        {/* Row 2: Channel Monitoring + Rights Gate */}
        <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {/* Channel Monitoring */}
          <Card title="Channel Monitoring">
            {channels ? (
              <>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                  {channels.supported_channels.map((ch) => (
                    <div key={ch} className="rounded-lg bg-black/5 px-3 py-2 text-center">
                      <div className="text-lg font-bold text-[var(--fg-0)]">
                        {channels.event_counts[ch] ?? 0}
                      </div>
                      <div className="text-xs text-[var(--fg-muted)]">{ch}</div>
                    </div>
                  ))}
                </div>
                <div className="mt-3">
                  <Stat label="Active Dedup" value={`${channels.active_dedup_entries} entries`} />
                </div>
              </>
            ) : (
              <p className="text-xs text-[var(--fg-muted)]">Loading...</p>
            )}
          </Card>

          {/* Vendor Switch Drill */}
          <Card title="Vendor Switch Drill">
            <p className="mb-3 text-xs text-[var(--fg-muted)]">
              Run a vendor substitution rehearsal to validate port contracts.
            </p>
            <button
              onClick={() => void runDrill()}
              disabled={drillLoading}
              className="rounded-lg bg-[var(--color-brand-primary)] px-3 py-2 text-sm text-white disabled:opacity-60"
            >
              {drillLoading ? "Running drill..." : "Run Vendor Drill"}
            </button>
            {drill && (
              <div className="mt-3 space-y-2">
                <div className="flex items-center gap-2">
                  <Badge ok={drill.overall_status === "pass"} />
                  <span className="text-xs">
                    {drill.total_passed} passed, {drill.total_failed} failed
                  </span>
                </div>
                {drill.drills.map((d) => (
                  <div key={d.drill_name} className="rounded-lg bg-black/5 px-3 py-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium">{d.drill_name}</span>
                      <span
                        className={`text-xs font-medium ${
                          d.status === "pass" ? "text-emerald-600" : "text-red-600"
                        }`}
                      >
                        {d.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="text-xs text-[var(--fg-muted)]">
                      {d.tests_passed}/{d.tests_passed + d.tests_failed} tests
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </section>
      </div>
    </AppShell>
  );
}
