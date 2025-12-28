"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Activity, Clock, DollarSign, TrendingUp } from "lucide-react";
import { api, RunTraceSummary } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { normalizeApiError } from "@/lib/errors";

interface RunTraceDashboardProps {
    className?: string;
    days?: number;
}

export default function RunTraceDashboard({ className = "", days = 7 }: RunTraceDashboardProps) {
    const { language } = useLanguage();
    const [data, setData] = useState<RunTraceSummary | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const labels = {
        title: language === "ko" ? "실행 추적 대시보드" : "Run Trace Dashboard",
        subtitle: language === "ko" ? "비용 및 지연 모니터링 (Phase 2.3)" : "Cost & Latency Monitoring (Phase 2.3)",
        totalRuns: language === "ko" ? "총 실행" : "Total Runs",
        avgLatency: language === "ko" ? "평균 지연" : "Avg Latency",
        avgCost: language === "ko" ? "평균 비용" : "Avg Cost",
        totalCost: language === "ko" ? "총 비용" : "Total Cost",
        noData: language === "ko" ? "실행 데이터가 없습니다." : "No run data available.",
        loadError: language === "ko" ? "데이터를 불러오지 못했습니다." : "Failed to load data.",
        loading: language === "ko" ? "로딩 중..." : "Loading...",
        daily: language === "ko" ? "일별 추이" : "Daily Trend",
        date: language === "ko" ? "날짜" : "Date",
        runs: language === "ko" ? "실행" : "Runs",
        latency: language === "ko" ? "지연(ms)" : "Latency(ms)",
        cost: language === "ko" ? "비용($)" : "Cost($)",
        status: language === "ko" ? "상태" : "Status",
    };

    useEffect(() => {
        let active = true;
        const fetchData = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const result = await api.getRunTraceSummary(days);
                if (active) {
                    setData(result);
                }
            } catch (err) {
                if (active) {
                    setError(normalizeApiError(err, labels.loadError));
                }
            } finally {
                if (active) setIsLoading(false);
            }
        };
        void fetchData();
        return () => {
            active = false;
        };
    }, [days, labels.loadError]);

    const formatLatency = (ms: number | null) => {
        if (ms === null) return "-";
        if (ms < 1000) return `${Math.round(ms)}ms`;
        return `${(ms / 1000).toFixed(1)}s`;
    };

    const formatCost = (usd: number | null) => {
        if (usd === null) return "-";
        if (usd < 0.01) return `$${usd.toFixed(4)}`;
        return `$${usd.toFixed(2)}`;
    };

    if (isLoading) {
        return (
            <div className={`rounded-xl border border-white/10 bg-slate-950/60 p-5 ${className}`}>
                <div className="text-sm text-[var(--fg-muted)]">{labels.loading}</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={`rounded-xl border border-rose-500/30 bg-rose-500/10 p-5 ${className}`}>
                <div className="text-sm text-rose-200">{error}</div>
            </div>
        );
    }

    if (!data || data.items.length === 0) {
        return (
            <div className={`rounded-xl border border-white/10 bg-slate-950/60 p-5 ${className}`}>
                <div className="flex items-center gap-2 mb-2">
                    <Activity className="h-4 w-4 text-[var(--accent)]" />
                    <h3 className="text-sm font-semibold text-[var(--fg-0)]">{labels.title}</h3>
                </div>
                <div className="text-xs text-[var(--fg-muted)]">{labels.noData}</div>
            </div>
        );
    }

    return (
        <div className={`rounded-xl border border-white/10 bg-slate-950/60 p-5 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-sky-500/20 to-emerald-500/20">
                        <TrendingUp className="h-4 w-4 text-sky-200" />
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-[var(--fg-0)]">{labels.title}</h3>
                        <p className="text-xs text-[var(--fg-muted)]">{labels.subtitle}</p>
                    </div>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
                <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-lg bg-white/5 p-3 border border-white/5"
                >
                    <div className="flex items-center gap-1 text-xs text-[var(--fg-muted)] mb-1">
                        <Activity className="h-3 w-3" />
                        {labels.totalRuns}
                    </div>
                    <div className="text-lg font-semibold text-[var(--fg-0)]">{data.total_runs.toLocaleString()}</div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.05 }}
                    className="rounded-lg bg-white/5 p-3 border border-white/5"
                >
                    <div className="flex items-center gap-1 text-xs text-[var(--fg-muted)] mb-1">
                        <Clock className="h-3 w-3" />
                        {labels.avgLatency}
                    </div>
                    <div className="text-lg font-semibold text-[var(--fg-0)]">{formatLatency(data.overall_avg_latency_ms)}</div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="rounded-lg bg-white/5 p-3 border border-white/5"
                >
                    <div className="flex items-center gap-1 text-xs text-[var(--fg-muted)] mb-1">
                        <DollarSign className="h-3 w-3" />
                        {labels.avgCost}
                    </div>
                    <div className="text-lg font-semibold text-[var(--fg-0)]">{formatCost(data.overall_avg_cost_usd)}</div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 }}
                    className="rounded-lg bg-white/5 p-3 border border-white/5"
                >
                    <div className="flex items-center gap-1 text-xs text-[var(--fg-muted)] mb-1">
                        <DollarSign className="h-3 w-3" />
                        {labels.totalCost}
                    </div>
                    <div className="text-lg font-semibold text-emerald-200">{formatCost(data.overall_total_cost_usd)}</div>
                </motion.div>
            </div>

            {/* Daily Table */}
            <div className="text-xs font-semibold text-[var(--fg-muted)] mb-2">{labels.daily}</div>
            <div className="overflow-x-auto">
                <table className="w-full text-xs">
                    <thead>
                        <tr className="border-b border-white/10 text-[var(--fg-muted)]">
                            <th className="py-2 text-left font-medium">{labels.date}</th>
                            <th className="py-2 text-right font-medium">{labels.runs}</th>
                            <th className="py-2 text-right font-medium">{labels.latency}</th>
                            <th className="py-2 text-right font-medium">{labels.cost}</th>
                            <th className="py-2 text-right font-medium">{labels.status}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.items.map((item, idx) => (
                            <motion.tr
                                key={item.date}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 0.05 * idx }}
                                className="border-b border-white/5 text-slate-200"
                            >
                                <td className="py-2">{item.date}</td>
                                <td className="py-2 text-right">{item.run_count}</td>
                                <td className="py-2 text-right">{formatLatency(item.avg_latency_ms)}</td>
                                <td className="py-2 text-right">{formatCost(item.total_cost_usd)}</td>
                                <td className="py-2 text-right">
                                    <div className="flex justify-end gap-1 flex-wrap">
                                        {Object.entries(item.status_breakdown).map(([status, count]) => (
                                            <span
                                                key={status}
                                                className={`rounded-full px-1.5 py-0.5 text-[10px] ${status === "done"
                                                    ? "bg-emerald-500/20 text-emerald-200"
                                                    : status === "failed"
                                                        ? "bg-rose-500/20 text-rose-200"
                                                        : "bg-white/10 text-slate-300"
                                                    }`}
                                            >
                                                {status}: {count}
                                            </span>
                                        ))}
                                    </div>
                                </td>
                            </motion.tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
