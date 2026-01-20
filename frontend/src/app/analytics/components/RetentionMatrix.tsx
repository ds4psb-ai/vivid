"use client";

/**
 * Retention Matrix Component (Phase 9: Analytics Dashboard)
 *
 * Displays cohort-based retention heatmap with weekly/monthly breakdown.
 */

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Loader2,
  AlertCircle,
  Grid3X3,
  CalendarDays,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { RetentionCohortsData, CohortRow } from "@/hooks/useAnalyticsDashboard";

interface RetentionMatrixProps {
  data: RetentionCohortsData | null;
  loading: boolean;
  onFetch: (type?: string, periodType?: string) => void;
}

const COHORT_TYPES = [
  { value: "first_tool", label: "First Tool" },
  { value: "signup", label: "Signup" },
  { value: "first_payment", label: "First Payment" },
];

const PERIOD_TYPES = [
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

function getRetentionColor(rate: number): string {
  if (rate >= 0.8) return "bg-emerald-500";
  if (rate >= 0.6) return "bg-emerald-500/80";
  if (rate >= 0.4) return "bg-violet-500";
  if (rate >= 0.2) return "bg-violet-500/60";
  if (rate > 0) return "bg-violet-500/30";
  return "bg-white/5";
}

function formatDate(dateStr: string, periodType: string): string {
  const date = new Date(dateStr);
  if (periodType === "monthly") {
    return date.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
  }
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function CohortHeatmapRow({
  cohort,
  periodType,
  maxPeriods,
  index,
}: {
  cohort: CohortRow;
  periodType: string;
  maxPeriods: number;
  index: number;
}) {
  return (
    <motion.tr
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.2, delay: index * 0.03 }}
      className="group"
    >
      {/* Cohort date */}
      <td className="py-2 pr-4 text-xs text-[var(--fg-muted)] whitespace-nowrap">
        {formatDate(cohort.cohort_date, periodType)}
      </td>

      {/* Cohort size */}
      <td className="py-2 pr-4 text-xs text-[var(--fg-subtle)] text-right">
        {cohort.cohort_size.toLocaleString()}
      </td>

      {/* Retention rates */}
      {Array.from({ length: maxPeriods }).map((_, periodIdx) => {
        const rate = cohort.retention_rates[periodIdx];
        const hasData = rate !== undefined && rate !== null;

        return (
          <td key={periodIdx} className="p-0.5">
            <div
              className={`w-10 h-8 rounded flex items-center justify-center text-[10px] font-medium transition-all ${
                hasData
                  ? `${getRetentionColor(rate)} text-white group-hover:ring-1 ring-white/30`
                  : "bg-white/5 text-[var(--fg-muted)]"
              }`}
              title={
                hasData
                  ? `${formatDate(cohort.cohort_date, periodType)}, Period ${periodIdx}: ${(rate * 100).toFixed(1)}%`
                  : "No data"
              }
            >
              {hasData ? `${(rate * 100).toFixed(0)}%` : "-"}
            </div>
          </td>
        );
      })}
    </motion.tr>
  );
}

export function RetentionMatrix({ data, loading, onFetch }: RetentionMatrixProps) {
  const [cohortType, setCohortType] = useState("first_tool");
  const [periodType, setPeriodType] = useState("weekly");

  const handleFetch = () => {
    onFetch(cohortType, periodType);
  };

  if (loading && !data) {
    return (
      <Card className="border border-white/5 bg-[var(--surface-1)]/70">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Grid3X3 className="w-4 h-4 text-violet-400" />
            Retention Cohorts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-48">
            <Loader2 className="w-6 h-6 text-violet-400 animate-spin" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const maxPeriods = data ? data.periods : 12;

  return (
    <Card className="border border-white/5 bg-[var(--surface-1)]/70">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base flex items-center gap-2">
          <Grid3X3 className="w-4 h-4 text-violet-400" />
          Retention Cohorts
        </CardTitle>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <select
            value={cohortType}
            onChange={(e) => setCohortType(e.target.value)}
            className="text-xs bg-[var(--surface-2)] border border-white/10 rounded-lg px-2 py-1 text-[var(--fg-0)]"
          >
            {COHORT_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          <select
            value={periodType}
            onChange={(e) => setPeriodType(e.target.value)}
            className="text-xs bg-[var(--surface-2)] border border-white/10 rounded-lg px-2 py-1 text-[var(--fg-0)]"
          >
            {PERIOD_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          <button
            onClick={handleFetch}
            className="text-xs bg-violet-600/90 hover:bg-violet-600 text-white px-3 py-1 rounded-lg transition-colors"
          >
            Load
          </button>
        </div>
      </CardHeader>

      <CardContent>
        {!data ? (
          <div className="flex flex-col items-center justify-center h-48 gap-2">
            <AlertCircle className="w-5 h-5 text-[var(--fg-muted)]" />
            <p className="text-sm text-[var(--fg-muted)]">
              Select cohort type and period, then click Load
            </p>
          </div>
        ) : data.cohorts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 gap-2">
            <CalendarDays className="w-5 h-5 text-[var(--fg-muted)]" />
            <p className="text-sm text-[var(--fg-muted)]">No cohort data available</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="py-2 pr-4 text-left text-xs text-[var(--fg-muted)] font-medium">
                    Cohort
                  </th>
                  <th className="py-2 pr-4 text-right text-xs text-[var(--fg-muted)] font-medium">
                    Size
                  </th>
                  {Array.from({ length: maxPeriods }).map((_, idx) => (
                    <th
                      key={idx}
                      className="p-0.5 text-center text-[10px] text-[var(--fg-muted)] font-medium"
                    >
                      {data.period_type === "weekly" ? `W${idx}` : `M${idx}`}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.cohorts.map((cohort, index) => (
                  <CohortHeatmapRow
                    key={cohort.cohort_date}
                    cohort={cohort}
                    periodType={data.period_type}
                    maxPeriods={maxPeriods}
                    index={index}
                  />
                ))}
              </tbody>
            </table>

            {/* Legend */}
            <div className="flex items-center justify-end gap-3 mt-4 pt-4 border-t border-white/5">
              <span className="text-[10px] text-[var(--fg-muted)]">Retention:</span>
              <div className="flex items-center gap-1">
                <div className="w-6 h-3 rounded bg-violet-500/30" />
                <span className="text-[10px] text-[var(--fg-muted)]">20%</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-6 h-3 rounded bg-violet-500/60" />
                <span className="text-[10px] text-[var(--fg-muted)]">40%</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-6 h-3 rounded bg-violet-500" />
                <span className="text-[10px] text-[var(--fg-muted)]">60%</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-6 h-3 rounded bg-emerald-500/80" />
                <span className="text-[10px] text-[var(--fg-muted)]">80%</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-6 h-3 rounded bg-emerald-500" />
                <span className="text-[10px] text-[var(--fg-muted)]">100%</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default RetentionMatrix;
