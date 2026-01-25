"use client";

/**
 * Funnel Chart Component (Phase 9: Analytics Dashboard)
 *
 * Visualizes conversion funnel with drop-off analysis.
 */

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Loader2,
  AlertCircle,
  Filter,
  ChevronDown,
  AlertTriangle,
  Clock,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { FunnelAnalysis, FunnelStep } from "@/hooks/useAnalyticsDashboard";

interface FunnelChartProps {
  data: FunnelAnalysis | null;
  loading: boolean;
  onFetch: (name: string, startDate: string, endDate: string) => void;
}

const FUNNEL_PRESETS = [
  { name: "signup_to_first_tool", label: "Signup → First Tool" },
  { name: "tool_discovery_to_execution", label: "Discovery → Execution" },
  { name: "free_to_paid", label: "Free → Paid Conversion" },
];

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`;
  return `${(ms / 3600000).toFixed(1)}h`;
}

function FunnelStepBar({
  step,
  maxUsers,
  isBottleneck,
  index,
}: {
  step: FunnelStep;
  maxUsers: number;
  isBottleneck: boolean;
  index: number;
}) {
  const widthPercent = (step.users_entered / maxUsers) * 100;
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
      className="relative"
    >
      {/* Step container */}
      <div
        className={`relative cursor-pointer transition-all ${
          expanded ? "mb-4" : ""
        }`}
        onClick={() => setExpanded(!expanded)}
      >
        {/* Bar */}
        <div
          className="relative h-12 rounded-lg overflow-hidden"
          style={{ width: `${widthPercent}%`, minWidth: "120px" }}
        >
          {/* Background */}
          <div
            className={`absolute inset-0 ${
              isBottleneck
                ? "bg-gradient-to-r from-orange-500/80 to-orange-600/80"
                : "bg-gradient-to-r from-violet-500/80 to-violet-600/80"
            }`}
          />

          {/* Completion portion */}
          <div
            className={`absolute inset-y-0 left-0 ${
              isBottleneck ? "bg-orange-400" : "bg-violet-400"
            }`}
            style={{ width: `${step.conversion_rate * 100}%` }}
          />

          {/* Content */}
          <div className="relative flex items-center justify-between h-full px-4">
            <div className="flex items-center gap-2">
              {isBottleneck && (
                <AlertTriangle className="w-4 h-4 text-orange-200" />
              )}
              <span className="text-sm font-medium text-white truncate">
                {step.step_name}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-white/80">
                {step.users_entered.toLocaleString()} users
              </span>
              <ChevronDown
                className={`w-4 h-4 text-white/60 transition-transform ${
                  expanded ? "rotate-180" : ""
                }`}
              />
            </div>
          </div>
        </div>

        {/* Arrow connecting to next step */}
        {step.drop_off_rate > 0 && (
          <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full px-2">
            <div className="text-xs text-red-400">
              -{(step.drop_off_rate * 100).toFixed(1)}%
            </div>
          </div>
        )}
      </div>

      {/* Expanded details */}
      {expanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="ml-4 pl-4 border-l-2 border-white/10 space-y-2"
        >
          <div className="grid grid-cols-3 gap-4 text-xs">
            <div>
              <p className="text-[var(--fg-muted)]">Completed</p>
              <p className="text-[var(--fg-0)] font-medium">
                {step.users_completed.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-[var(--fg-muted)]">Conversion</p>
              <p className="text-emerald-400 font-medium">
                {(step.conversion_rate * 100).toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-[var(--fg-muted)]">Avg Time</p>
              <p className="text-[var(--fg-0)] font-medium flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatDuration(step.avg_time_in_step_ms)}
              </p>
            </div>
          </div>

          {step.top_drop_off_reasons.length > 0 && (
            <div className="pt-2">
              <p className="text-xs text-[var(--fg-muted)] mb-1">
                Top Drop-off Reasons
              </p>
              <div className="space-y-1">
                {step.top_drop_off_reasons.slice(0, 3).map((reason, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-xs"
                  >
                    <span className="text-[var(--fg-subtle)]">
                      {reason.reason}
                    </span>
                    <span className="text-red-400">{reason.count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}

export function FunnelChart({ data, loading, onFetch }: FunnelChartProps) {
  const [selectedFunnel, setSelectedFunnel] = useState(FUNNEL_PRESETS[0].name);

  const handleFetch = () => {
    const endDate = new Date().toISOString().split("T")[0];
    const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split("T")[0];
    onFetch(selectedFunnel, startDate, endDate);
  };

  if (loading && !data) {
    return (
      <Card className="border border-white/5 bg-[var(--surface-1)]/70">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Filter className="w-4 h-4 text-violet-400" />
            Funnel Analysis
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

  return (
    <Card className="border border-white/5 bg-[var(--surface-1)]/70">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base flex items-center gap-2">
          <Filter className="w-4 h-4 text-violet-400" />
          Funnel Analysis
        </CardTitle>

        {/* Funnel selector */}
        <div className="flex items-center gap-2">
          <select
            value={selectedFunnel}
            onChange={(e) => setSelectedFunnel(e.target.value)}
            className="text-xs bg-[var(--surface-2)] border border-white/10 rounded-lg px-2 py-1 text-[var(--fg-0)]"
          >
            {FUNNEL_PRESETS.map((preset) => (
              <option key={preset.name} value={preset.name}>
                {preset.label}
              </option>
            ))}
          </select>
          <button
            onClick={handleFetch}
            className="text-xs bg-violet-600/90 hover:bg-violet-600 text-white px-3 py-1 rounded-lg transition-colors"
          >
            Analyze
          </button>
        </div>
      </CardHeader>

      <CardContent>
        {!data ? (
          <div className="flex flex-col items-center justify-center h-48 gap-2">
            <AlertCircle className="w-5 h-5 text-[var(--fg-muted)]" />
            <p className="text-sm text-[var(--fg-muted)]">
              Select a funnel and click Analyze
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Summary stats */}
            <div className="grid grid-cols-3 gap-4 p-4 bg-[var(--surface-2)]/50 rounded-lg">
              <div className="text-center">
                <p className="text-xs text-[var(--fg-muted)]">Total Started</p>
                <p className="text-lg font-semibold text-[var(--fg-0)]">
                  {data.total_users_started.toLocaleString()}
                </p>
              </div>
              <div className="text-center">
                <p className="text-xs text-[var(--fg-muted)]">Completed</p>
                <p className="text-lg font-semibold text-emerald-400">
                  {data.total_users_completed.toLocaleString()}
                </p>
              </div>
              <div className="text-center">
                <p className="text-xs text-[var(--fg-muted)]">Overall Rate</p>
                <p className="text-lg font-semibold text-violet-400">
                  {(data.overall_conversion_rate * 100).toFixed(1)}%
                </p>
              </div>
            </div>

            {/* Funnel steps */}
            <div className="space-y-3">
              {data.steps.map((step, index) => (
                <FunnelStepBar
                  key={step.step_name}
                  step={step}
                  maxUsers={data.total_users_started}
                  isBottleneck={step.step_name === data.bottleneck_step}
                  index={index}
                />
              ))}
            </div>

            {/* Bottleneck alert */}
            {data.bottleneck_step && (
              <div className="flex items-center gap-2 p-3 bg-orange-500/10 border border-orange-500/20 rounded-lg">
                <AlertTriangle className="w-4 h-4 text-orange-400" />
                <p className="text-xs text-orange-200">
                  <span className="font-medium">Bottleneck detected:</span>{" "}
                  {data.bottleneck_step} has the highest drop-off rate
                </p>
              </div>
            )}

            {/* Period info */}
            <div className="text-xs text-[var(--fg-muted)] text-right">
              {data.period_start} → {data.period_end}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default FunnelChart;
