"use client";

/**
 * Top Tools Table Component (Phase 9: Analytics Dashboard)
 *
 * Displays top performing tools by revenue and executions.
 */

import { motion } from "framer-motion";
import {
  Loader2,
  AlertCircle,
  Wrench,
  DollarSign,
  Zap,
  Star,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TopTool } from "@/hooks/useAnalyticsDashboard";

interface TopToolsTableProps {
  data: TopTool[] | null;
  loading: boolean;
  onFetch: (periodDays?: number, limit?: number) => void;
}

function formatCredits(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toLocaleString();
}

function ToolRow({ tool, index, maxRevenue }: { tool: TopTool; index: number; maxRevenue: number }) {
  const revenuePercent = (tool.revenue / maxRevenue) * 100;

  return (
    <motion.tr
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: index * 0.05 }}
      className="group border-b border-white/5 last:border-0 hover:bg-white/5 transition-colors"
    >
      {/* Rank */}
      <td className="py-3 pl-4">
        <span className="text-sm font-medium text-[var(--fg-muted)]">
          #{index + 1}
        </span>
      </td>

      {/* Tool */}
      <td className="py-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-violet-500/20 flex items-center justify-center">
            <Wrench className="w-4 h-4 text-violet-400" />
          </div>
          <span className="text-sm font-medium text-[var(--fg-0)]">
            {tool.tool_key}
          </span>
        </div>
      </td>

      {/* Revenue with bar */}
      <td className="py-3 px-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <DollarSign className="w-3 h-3 text-emerald-400" />
            <span className="text-sm font-medium text-emerald-400">
              {formatCredits(tool.revenue)}
            </span>
          </div>
          <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-500/60 rounded-full transition-all"
              style={{ width: `${revenuePercent}%` }}
            />
          </div>
        </div>
      </td>

      {/* Executions */}
      <td className="py-3">
        <div className="flex items-center gap-1.5">
          <Zap className="w-3 h-3 text-blue-400" />
          <span className="text-sm text-[var(--fg-subtle)]">
            {tool.executions.toLocaleString()}
          </span>
        </div>
      </td>

      {/* Rating */}
      <td className="py-3 pr-4">
        {tool.avg_rating !== null ? (
          <div className="flex items-center gap-1.5">
            <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
            <span className="text-sm text-[var(--fg-subtle)]">
              {tool.avg_rating.toFixed(1)}
            </span>
          </div>
        ) : (
          <span className="text-xs text-[var(--fg-muted)]">-</span>
        )}
      </td>
    </motion.tr>
  );
}

export function TopToolsTable({ data, loading, onFetch }: TopToolsTableProps) {
  if (loading && !data) {
    return (
      <Card className="border border-white/5 bg-[var(--surface-1)]/70">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Wrench className="w-4 h-4 text-violet-400" />
            Top Tools
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

  const maxRevenue = data ? Math.max(...data.map((t) => t.revenue), 1) : 1;

  return (
    <Card className="border border-white/5 bg-[var(--surface-1)]/70">
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-base flex items-center gap-2">
          <Wrench className="w-4 h-4 text-violet-400" />
          Top Tools
        </CardTitle>
        <button
          onClick={() => onFetch()}
          className="text-xs text-violet-400 hover:text-violet-300 transition-colors"
        >
          Refresh
        </button>
      </CardHeader>

      <CardContent className="p-0">
        {!data || data.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 gap-2">
            <AlertCircle className="w-5 h-5 text-[var(--fg-muted)]" />
            <p className="text-sm text-[var(--fg-muted)]">No tool data available</p>
            <button
              onClick={() => onFetch()}
              className="text-xs text-violet-400 hover:text-violet-300"
            >
              Load data
            </button>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10 text-left">
                <th className="py-2 pl-4 text-xs text-[var(--fg-muted)] font-medium w-12">
                  #
                </th>
                <th className="py-2 text-xs text-[var(--fg-muted)] font-medium">
                  Tool
                </th>
                <th className="py-2 px-4 text-xs text-[var(--fg-muted)] font-medium">
                  Revenue
                </th>
                <th className="py-2 text-xs text-[var(--fg-muted)] font-medium">
                  Runs
                </th>
                <th className="py-2 pr-4 text-xs text-[var(--fg-muted)] font-medium">
                  Rating
                </th>
              </tr>
            </thead>
            <tbody>
              {data.map((tool, index) => (
                <ToolRow
                  key={tool.tool_key}
                  tool={tool}
                  index={index}
                  maxRevenue={maxRevenue}
                />
              ))}
            </tbody>
          </table>
        )}
      </CardContent>
    </Card>
  );
}

export default TopToolsTable;
