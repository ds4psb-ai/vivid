"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Wallet,
  TrendingUp,
  Activity,
  Download,
  ArrowUpRight,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";
import { api, type CreditBalance, type CreditTransaction } from "@/lib/api";
import { normalizeApiError } from "@/lib/errors";

export default function UsagePage() {
  const { language } = useLanguage();
  const [balance, setBalance] = useState<CreditBalance | null>(null);
  const [transactions, setTransactions] = useState<CreditTransaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [period, setPeriod] = useState("this_month");
  const [runTypeFilter, setRunTypeFilter] = useState("all");
  const userId = process.env.NEXT_PUBLIC_USER_ID || "demo-user";

  const loadErrorFallback =
    language === "ko" ? "사용량 데이터를 불러오지 못했습니다." : "Unable to load usage data.";

  const loadUsage = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const [balanceData, ledger] = await Promise.all([
        api.getCreditsBalance(userId),
        api.getCreditsTransactions(userId, 50, 0),
      ]);
      setBalance(balanceData);
      setTransactions(ledger.transactions);
    } catch (err) {
      setLoadError(normalizeApiError(err, loadErrorFallback));
    } finally {
      setIsLoading(false);
    }
  }, [loadErrorFallback, userId]);

  useEffect(() => {
    void loadUsage();
  }, [loadUsage]);

  const usageTransactions = useMemo(
    () => transactions.filter((tx) => tx.event_type === "usage"),
    [transactions]
  );

  const usedThisMonth = useMemo(() => {
    const now = new Date();
    return usageTransactions
      .filter((tx) => {
        const ts = new Date(tx.created_at);
        return ts.getFullYear() === now.getFullYear() && ts.getMonth() === now.getMonth();
      })
      .reduce((sum, tx) => sum + Math.abs(tx.amount), 0);
  }, [usageTransactions]);

  const filteredUsage = useMemo(() => {
    const now = new Date();
    const isInPeriod = (value: string) => {
      if (period === "all") return true;
      const ts = new Date(value);
      if (Number.isNaN(ts.getTime())) return false;
      if (period === "this_month") {
        return ts.getFullYear() === now.getFullYear() && ts.getMonth() === now.getMonth();
      }
      const days = period === "last_7" ? 7 : period === "last_30" ? 30 : 90;
      const start = new Date(now);
      start.setDate(now.getDate() - days);
      return ts >= start;
    };

    return usageTransactions.filter((tx) => {
      if (!isInPeriod(tx.created_at)) return false;
      if (runTypeFilter === "all") return true;
      const runType = typeof tx.meta?.run_type === "string" ? tx.meta.run_type : "";
      return runType === runTypeFilter;
    });
  }, [period, runTypeFilter, usageTransactions]);

  const usageMetrics = useMemo(() => {
    let latencySum = 0;
    let latencyCount = 0;
    let costSum = 0;
    let costCount = 0;
    let tokenSum = 0;
    let tokenCount = 0;
    for (const tx of filteredUsage) {
      const meta = tx.meta as Record<string, unknown> | undefined;
      if (meta && typeof meta.latency_ms === "number") {
        latencySum += meta.latency_ms;
        latencyCount += 1;
      }
      if (meta && typeof meta.cost_usd_est === "number") {
        costSum += meta.cost_usd_est;
        costCount += 1;
      }
      const tokenUsage =
        meta && typeof meta.token_usage === "object" && meta.token_usage !== null
          ? (meta.token_usage as { input?: number; output?: number; total?: number })
          : null;
      const tokenTotal =
        tokenUsage && typeof tokenUsage.total === "number"
          ? tokenUsage.total
          : tokenUsage && typeof tokenUsage.input === "number" && typeof tokenUsage.output === "number"
            ? tokenUsage.input + tokenUsage.output
            : null;
      if (tokenTotal !== null) {
        tokenSum += tokenTotal;
        tokenCount += 1;
      }
    }
    return {
      avgLatencyMs: latencyCount ? Math.round(latencySum / latencyCount) : null,
      avgCostUsd: costCount ? Number((costSum / costCount).toFixed(3)) : null,
      avgTokens: tokenCount ? Math.round(tokenSum / tokenCount) : null,
    };
  }, [filteredUsage]);

  const totalRuns = filteredUsage.length;
  const totalSpend = filteredUsage.reduce((sum, tx) => sum + Math.abs(tx.amount), 0);
  const avgCost = totalRuns ? Math.round(totalSpend / totalRuns) : 0;

  const labels = {
    title: language === "ko" ? "사용량" : "Usage",
    subtitle:
      language === "ko"
        ? "크레딧 사용 현황과 최근 실행 내역을 확인합니다."
        : "Track credit usage and recent runs.",
    balance: language === "ko" ? "총 잔액" : "Total Balance",
    credits: language === "ko" ? "크레딧" : "credits",
    monthSpend: language === "ko" ? "이번 달 사용" : "Month-to-date spend",
    totalRuns: language === "ko" ? "총 실행" : "Total runs",
    avgCost: language === "ko" ? "평균 비용" : "Avg cost",
    avgLatency: language === "ko" ? "평균 지연" : "Avg latency",
    avgCostUsd: language === "ko" ? "평균 비용 (USD)" : "Avg cost (USD)",
    avgTokens: language === "ko" ? "평균 토큰" : "Avg tokens",
    latency: language === "ko" ? "지연" : "Latency",
    costEstimate: language === "ko" ? "비용 추정" : "Cost est",
    tokenUsage: language === "ko" ? "토큰" : "Tokens",
    subscription: language === "ko" ? "구독 크레딧" : "Subscription credits",
    topup: language === "ko" ? "추가 충전" : "Top-up credits",
    promo: language === "ko" ? "프로모션" : "Promo credits",
    recentRuns: language === "ko" ? "최근 실행 내역" : "Recent runs",
    exportCsv: language === "ko" ? "CSV 내보내기" : "Export CSV",
    loading: language === "ko" ? "사용량 불러오는 중..." : "Loading usage...",
    noRuns: language === "ko" ? "실행 내역이 없습니다." : "No usage history yet.",
    runId: language === "ko" ? "실행 ID" : "Run ID",
    runType: language === "ko" ? "실행 유형" : "Run type",
    resourceId: language === "ko" ? "대상" : "Resource",
    filterPeriod: language === "ko" ? "기간" : "Period",
    filterRunType: language === "ko" ? "유형" : "Type",
    periodThisMonth: language === "ko" ? "이번 달" : "This month",
    periodLast7: language === "ko" ? "최근 7일" : "Last 7 days",
    periodLast30: language === "ko" ? "최근 30일" : "Last 30 days",
    periodLast90: language === "ko" ? "최근 90일" : "Last 90 days",
    periodAll: language === "ko" ? "전체" : "All time",
    runTypeAll: language === "ko" ? "전체" : "All",
    runTypeCapsule: language === "ko" ? "캡슐" : "Capsule",
    runTypeGeneration: language === "ko" ? "생성" : "Generation",
  };

  const handleExportCsv = useCallback(() => {
    if (filteredUsage.length === 0) return;
    const headers = ["created_at", "amount", "description", "capsule_run_id", "run_type", "meta_json"];
    const escapeValue = (value: string) => `"${value.replace(/"/g, '""')}"`;
    const rows = filteredUsage.map((tx) => [
      tx.created_at,
      String(tx.amount),
      tx.description || "",
      tx.capsule_run_id || "",
      typeof tx.meta?.run_type === "string" ? tx.meta.run_type : "",
      JSON.stringify(tx.meta || {}),
    ]);
    const csv = [headers.join(","), ...rows.map((row) => row.map(escapeValue).join(","))].join(
      "\n"
    );
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const today = new Date().toISOString().slice(0, 10);
    link.href = url;
    link.download = `vivid_usage_${today}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }, [filteredUsage]);

  return (
    <AppShell showTopBar={false}>
      <div className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
        <div className="mx-auto max-w-5xl">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 sm:mb-8"
          >
            <h1 className="text-xl font-bold text-[var(--fg-0)] sm:text-2xl">{labels.title}</h1>
            <p className="mt-1 text-sm text-[var(--fg-muted)] sm:text-base">{labels.subtitle}</p>
          </motion.div>

          {loadError && (
            <div className="mb-4 rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
              {loadError}
            </div>
          )}

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-6 rounded-2xl border border-white/10 bg-gradient-to-br from-sky-500/10 via-transparent to-emerald-500/10 p-5 sm:p-6"
          >
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 text-xs text-[var(--fg-muted)] sm:text-sm">
                  <Wallet className="h-4 w-4" aria-hidden="true" />
                  {labels.balance}
                </div>
                <div className="mt-2 text-3xl font-bold text-[var(--fg-0)] sm:text-4xl">
                  {isLoading ? "..." : balance?.balance.toLocaleString() || "0"}
                  <span className="ml-2 text-base font-normal text-[var(--fg-muted)] sm:text-lg">
                    {labels.credits}
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs text-[var(--fg-muted)] sm:grid-cols-3">
                <div className="rounded-lg border border-white/10 bg-white/5 px-3 py-2">
                  <div className="flex items-center gap-1">
                    <TrendingUp className="h-3 w-3 text-amber-300" aria-hidden="true" />
                    {labels.monthSpend}
                  </div>
                <div className="mt-1 text-sm font-semibold text-[var(--fg-0)]">
                  {period === "this_month" ? usedThisMonth : totalSpend}
                </div>
                </div>
                <div className="rounded-lg border border-white/10 bg-white/5 px-3 py-2">
                  <div className="flex items-center gap-1">
                    <Activity className="h-3 w-3 text-sky-300" aria-hidden="true" />
                    {labels.totalRuns}
                  </div>
                  <div className="mt-1 text-sm font-semibold text-[var(--fg-0)]">{totalRuns}</div>
                </div>
                <div className="rounded-lg border border-white/10 bg-white/5 px-3 py-2">
                  <div className="flex items-center gap-1">
                    <ArrowUpRight className="h-3 w-3 text-emerald-300" aria-hidden="true" />
                    {labels.avgCost}
                  </div>
                  <div className="mt-1 text-sm font-semibold text-[var(--fg-0)]">{avgCost}</div>
                </div>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mb-6 grid gap-3 sm:grid-cols-3"
          >
            {[
              {
                label: labels.avgLatency,
                value:
                  usageMetrics.avgLatencyMs !== null ? `${usageMetrics.avgLatencyMs}ms` : "-",
              },
              {
                label: labels.avgCostUsd,
                value:
                  usageMetrics.avgCostUsd !== null ? `$${usageMetrics.avgCostUsd}` : "-",
              },
              {
                label: labels.avgTokens,
                value:
                  usageMetrics.avgTokens !== null
                    ? usageMetrics.avgTokens.toLocaleString()
                    : "-",
              },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-xl border border-white/10 bg-slate-950/60 p-4"
              >
                <div className="text-xs text-[var(--fg-muted)]">{item.label}</div>
                <div className="mt-2 text-xl font-semibold text-[var(--fg-0)]">{item.value}</div>
              </div>
            ))}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="mb-6 grid gap-3 sm:grid-cols-3"
          >
            {[
              { label: labels.subscription, value: balance?.subscription_credits ?? 0, tone: "text-sky-200" },
              { label: labels.topup, value: balance?.topup_credits ?? 0, tone: "text-emerald-200" },
              { label: labels.promo, value: balance?.promo_credits ?? 0, tone: "text-amber-200" },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-xl border border-white/10 bg-slate-950/60 p-4"
              >
                <div className="text-xs text-[var(--fg-muted)]">{item.label}</div>
                <div className={`mt-2 text-xl font-semibold ${item.tone}`}>
                  {isLoading ? "..." : item.value.toLocaleString()}
                </div>
              </div>
            ))}
          </motion.div>

          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            aria-labelledby="usage-heading"
          >
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3 sm:mb-4">
              <div className="flex flex-wrap items-center gap-3">
                <h2 id="usage-heading" className="text-base font-semibold text-[var(--fg-0)] sm:text-lg">
                  {labels.recentRuns}
                </h2>
                <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--fg-muted)]">
                  <label className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2">
                    {labels.filterPeriod}
                    <select
                      value={period}
                      onChange={(event) => setPeriod(event.target.value)}
                      className="bg-transparent text-xs text-slate-200 outline-none"
                    >
                      <option value="this_month">{labels.periodThisMonth}</option>
                      <option value="last_7">{labels.periodLast7}</option>
                      <option value="last_30">{labels.periodLast30}</option>
                      <option value="last_90">{labels.periodLast90}</option>
                      <option value="all">{labels.periodAll}</option>
                    </select>
                  </label>
                  <label className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2">
                    {labels.filterRunType}
                    <select
                      value={runTypeFilter}
                      onChange={(event) => setRunTypeFilter(event.target.value)}
                      className="bg-transparent text-xs text-slate-200 outline-none"
                    >
                      <option value="all">{labels.runTypeAll}</option>
                      <option value="capsule">{labels.runTypeCapsule}</option>
                      <option value="generation">{labels.runTypeGeneration}</option>
                    </select>
                  </label>
                </div>
              </div>
              <button
                type="button"
                onClick={handleExportCsv}
                disabled={filteredUsage.length === 0}
                className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-slate-200 transition-colors hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
                aria-label={labels.exportCsv}
              >
                <Download className="h-4 w-4" aria-hidden="true" />
                {labels.exportCsv}
              </button>
            </div>
            <div className="overflow-hidden rounded-xl border border-white/10 bg-slate-900/40">
              {isLoading ? (
                <div className="px-5 py-6 text-sm text-slate-500">{labels.loading}</div>
              ) : filteredUsage.length === 0 ? (
                <div className="px-5 py-6 text-sm text-slate-500">{labels.noRuns}</div>
              ) : (
                <div className="divide-y divide-white/5">
                  {filteredUsage.map((tx) => (
                    <div
                      key={tx.id}
                      className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 text-sm text-slate-200"
                    >
                      {(() => {
                        const runType =
                          typeof tx.meta?.run_type === "string" ? tx.meta.run_type : "";
                        const resourceId =
                          (typeof tx.meta?.capsule_id === "string" && tx.meta.capsule_id) ||
                          (typeof tx.meta?.canvas_id === "string" && tx.meta.canvas_id) ||
                          "";
                        const breakdown =
                          tx.meta &&
                          typeof tx.meta === "object" &&
                          typeof (tx.meta as { breakdown?: unknown }).breakdown === "object"
                            ? ((tx.meta as { breakdown?: Record<string, number> }).breakdown ?? null)
                            : null;
                        const latencyMs =
                          typeof (tx.meta as { latency_ms?: unknown })?.latency_ms === "number"
                            ? (tx.meta as { latency_ms: number }).latency_ms
                            : null;
                        const costUsd =
                          typeof (tx.meta as { cost_usd_est?: unknown })?.cost_usd_est === "number"
                            ? (tx.meta as { cost_usd_est: number }).cost_usd_est
                            : null;
                        const tokenUsage =
                          tx.meta && typeof (tx.meta as { token_usage?: unknown }).token_usage === "object"
                            ? (tx.meta as { token_usage: { input?: number; output?: number; total?: number } }).token_usage
                            : null;
                        const tokenTotal =
                          tokenUsage && typeof tokenUsage.total === "number"
                            ? tokenUsage.total
                            : tokenUsage && typeof tokenUsage.input === "number" && typeof tokenUsage.output === "number"
                              ? tokenUsage.input + tokenUsage.output
                              : null;
                        return (
                          <div>
                            <div className="font-medium">
                              {tx.description || labels.recentRuns}
                            </div>
                            <div className="mt-1 text-xs text-[var(--fg-muted)]">
                              {labels.runId}: {tx.capsule_run_id || "-"}
                            </div>
                            {(runType || resourceId) && (
                              <div className="mt-1 text-[10px] text-slate-500">
                                {runType && (
                                  <span className="mr-2">
                                    {labels.runType}: {runType}
                                  </span>
                                )}
                                {resourceId && (
                                  <span>
                                    {labels.resourceId}: {resourceId}
                                  </span>
                                )}
                              </div>
                            )}
                            {breakdown && (
                              <div className="mt-1 text-[10px] text-slate-500">
                                {labels.promo}: {breakdown.promo ?? 0},{" "}
                                {labels.subscription}: {breakdown.subscription ?? 0},{" "}
                                {labels.topup}: {breakdown.topup ?? 0}
                              </div>
                            )}
                            {(latencyMs !== null || costUsd !== null || tokenTotal !== null) && (
                              <div className="mt-1 text-[10px] text-slate-500">
                                {latencyMs !== null && (
                                  <span className="mr-2">
                                    {labels.latency}: {latencyMs}ms
                                  </span>
                                )}
                                {costUsd !== null && (
                                  <span className="mr-2">
                                    {labels.costEstimate}: ${costUsd.toFixed(3)}
                                  </span>
                                )}
                                {tokenTotal !== null && (
                                  <span>
                                    {labels.tokenUsage}: {tokenTotal}
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })()}
                      <div className="text-right">
                        <div className="font-mono text-rose-300">
                          {tx.amount}
                        </div>
                        <div className="text-[10px] text-[var(--fg-muted)]">
                          {new Date(tx.created_at).toLocaleString(
                            language === "ko" ? "ko-KR" : "en-US"
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.section>
        </div>
      </div>
    </AppShell>
  );
}
