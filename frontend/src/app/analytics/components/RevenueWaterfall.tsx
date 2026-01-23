"use client";

/**
 * Revenue Waterfall Chart Component (Phase 9: Analytics Dashboard)
 *
 * Visualizes revenue breakdown: Tool Usage → Fork Received → Fork Shared → Platform Fees → Net
 */

import { motion } from "framer-motion";
import {
  Loader2,
  AlertCircle,
  ArrowDown,
  ArrowUp,
  Wallet,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { RevenueWaterfallData } from "@/hooks/useAnalyticsDashboard";

interface RevenueWaterfallProps {
  data: RevenueWaterfallData | null;
  loading: boolean;
  onFetch: (periodDays?: number) => void;
}

const WATERFALL_STEPS = [
  { key: "tool_usage_revenue", label: "Tool Usage", type: "positive" },
  { key: "fork_revenue_received", label: "Fork Received", type: "positive" },
  { key: "fork_revenue_shared", label: "Fork Shared", type: "negative" },
  { key: "platform_fees", label: "Platform Fees", type: "negative" },
  { key: "net_revenue", label: "Net Revenue", type: "total" },
];

function formatCredits(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toLocaleString();
}

function WaterfallBar({
  step,
  value,
  maxValue,
  prevCumulative,
  index,
}: {
  step: typeof WATERFALL_STEPS[0];
  value: number;
  maxValue: number;
  prevCumulative: number;
  index: number;
}) {
  const isPositive = step.type === "positive";
  const isTotal = step.type === "total";
  const isNegative = step.type === "negative";

  const barHeight = Math.max((Math.abs(value) / maxValue) * 150, 8);
  const offsetHeight = (prevCumulative / maxValue) * 150;

  const barColor = isTotal
    ? "bg-violet-500"
    : isPositive
    ? "bg-emerald-500"
    : "bg-red-500/80";

  const Icon = isTotal ? Wallet : isPositive ? ArrowUp : ArrowDown;
  const iconColor = isTotal
    ? "text-violet-400"
    : isPositive
    ? "text-emerald-400"
    : "text-red-400";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
      className="flex flex-col items-center flex-1"
    >
      {/* Value label */}
      <div className={`text-sm font-medium mb-2 ${iconColor}`}>
        {isNegative && value > 0 ? "-" : ""}
        {formatCredits(Math.abs(value))}
      </div>

      {/* Bar container */}
      <div className="relative w-full h-[180px] flex items-end justify-center">
        {/* Connector line for cumulative */}
        {!isTotal && index > 0 && (
          <div
            className="absolute left-0 right-0 border-t border-dashed border-white/20"
            style={{ bottom: `${offsetHeight}px` }}
          />
        )}

        {/* Bar */}
        <div
          className={`w-2/3 rounded-t ${barColor} transition-all relative`}
          style={{
            height: `${barHeight}px`,
            marginBottom: isTotal ? 0 : `${isPositive ? offsetHeight : offsetHeight - barHeight}px`,
          }}
        >
          {/* Glow effect */}
          <div
            className={`absolute inset-0 ${barColor} blur-md opacity-30 rounded-t`}
          />
        </div>
      </div>

      {/* Label */}
      <div className="mt-3 text-center">
        <div className={`flex items-center justify-center gap-1 ${iconColor}`}>
          <Icon className="w-3.5 h-3.5" />
        </div>
        <p className="text-xs text-[var(--fg-muted)] mt-1">{step.label}</p>
      </div>
    </motion.div>
  );
}

function DailyBreakdownMini({ daily }: { daily: RevenueWaterfallData["daily_breakdown"] }) {
  if (!daily || daily.length === 0) return null;

  const maxRevenue = Math.max(...daily.map((d) => d.revenue), 1);

  return (
    <div className="mt-6 pt-4 border-t border-white/5">
      <p className="text-xs text-[var(--fg-muted)] mb-3">Daily Revenue Trend</p>
      <div className="flex items-end gap-0.5 h-12">
        {daily.slice(-14).map((day, idx) => (
          <div
            key={idx}
            className="flex-1 bg-violet-500/40 hover:bg-violet-500/60 rounded-t transition-colors"
            style={{ height: `${(day.revenue / maxRevenue) * 100}%`, minHeight: day.revenue > 0 ? 2 : 0 }}
            title={`${day.date}: ${formatCredits(day.revenue)}`}
          />
        ))}
      </div>
      <div className="flex justify-between text-[10px] text-[var(--fg-muted)] mt-1">
        <span>{daily[Math.max(0, daily.length - 14)]?.date}</span>
        <span>{daily[daily.length - 1]?.date}</span>
      </div>
    </div>
  );
}

export function RevenueWaterfall({ data, loading, onFetch }: RevenueWaterfallProps) {
  if (loading && !data) {
    return (
      <Card className="border border-white/5 bg-[var(--surface-1)]/70">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Wallet className="w-4 h-4 text-violet-400" />
            Revenue Waterfall
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

  if (!data) {
    return (
      <Card className="border border-white/5 bg-[var(--surface-1)]/70">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Wallet className="w-4 h-4 text-violet-400" />
            Revenue Waterfall
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-48 gap-2">
            <AlertCircle className="w-5 h-5 text-[var(--fg-muted)]" />
            <p className="text-sm text-[var(--fg-muted)]">No revenue data available</p>
            <button
              onClick={() => onFetch()}
              className="text-xs text-violet-400 hover:text-violet-300"
            >
              Load data
            </button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Calculate max value for scaling
  const maxValue = Math.max(
    data.total_revenue,
    data.tool_usage_revenue + data.fork_revenue_received,
    1
  );

  const getStepValue = (key: string): number => {
    switch (key) {
      case "tool_usage_revenue": return data.tool_usage_revenue;
      case "fork_revenue_received": return data.fork_revenue_received;
      case "fork_revenue_shared": return data.fork_revenue_shared;
      case "platform_fees": return data.platform_fees;
      case "net_revenue": return data.net_revenue;
      default: return 0;
    }
  };

  // Pre-calculate cumulative values for each step
  const cumulativeValues = WATERFALL_STEPS.reduce<number[]>((acc, step) => {
    const prevCumulative = acc.length > 0 ? acc[acc.length - 1] : 0;
    const value = getStepValue(step.key);
    let newCumulative = prevCumulative;
    if (step.type === "positive") {
      newCumulative = prevCumulative + value;
    } else if (step.type === "negative") {
      newCumulative = prevCumulative - value;
    }
    acc.push(newCumulative);
    return acc;
  }, []);

  return (
    <Card className="border border-white/5 bg-[var(--surface-1)]/70">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base flex items-center gap-2">
          <Wallet className="w-4 h-4 text-violet-400" />
          Revenue Waterfall
        </CardTitle>
        <div className="text-xs text-[var(--fg-muted)]">
          Last {data.period_days} days
        </div>
      </CardHeader>
      <CardContent>
        {/* Waterfall Chart */}
        <div className="flex gap-2">
          {WATERFALL_STEPS.map((step, index) => {
            const value = getStepValue(step.key);
            const prevCumulative = index > 0 ? cumulativeValues[index - 1] : 0;

            return (
              <WaterfallBar
                key={step.key}
                step={step}
                value={value}
                maxValue={maxValue}
                prevCumulative={prevCumulative}
                index={index}
              />
            );
          })}
        </div>

        {/* Summary */}
        <div className="mt-6 grid grid-cols-2 gap-4 pt-4 border-t border-white/5">
          <div>
            <p className="text-xs text-[var(--fg-muted)]">Total Revenue</p>
            <p className="text-lg font-semibold text-[var(--fg-0)]">
              {formatCredits(data.total_revenue)} credits
            </p>
          </div>
          <div>
            <p className="text-xs text-[var(--fg-muted)]">Net Revenue</p>
            <p className="text-lg font-semibold text-emerald-400">
              {formatCredits(data.net_revenue)} credits
            </p>
          </div>
        </div>

        {/* Daily breakdown mini chart */}
        <DailyBreakdownMini daily={data.daily_breakdown} />
      </CardContent>
    </Card>
  );
}

export default RevenueWaterfall;
