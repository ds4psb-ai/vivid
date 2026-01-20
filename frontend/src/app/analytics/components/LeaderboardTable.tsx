"use client";

/**
 * Leaderboard Table Component (Phase 9: Analytics Dashboard)
 *
 * Displays ranking table with change indicators and live updates.
 */

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Loader2,
  AlertCircle,
  Trophy,
  TrendingUp,
  TrendingDown,
  Minus,
  Medal,
  Crown,
  Wifi,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LeaderboardData, LeaderboardEntry } from "@/hooks/useAnalyticsDashboard";

interface LeaderboardTableProps {
  data: LeaderboardData | null;
  loading: boolean;
  onFetch: (type: string, period?: string) => void;
}

const LEADERBOARD_TYPES = [
  { value: "revenue", label: "Revenue" },
  { value: "executions", label: "Executions" },
  { value: "engagement", label: "Engagement" },
  { value: "rating", label: "Rating" },
];

const PERIOD_OPTIONS = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

function getRankIcon(rank: number) {
  switch (rank) {
    case 1:
      return <Crown className="w-4 h-4 text-yellow-400" />;
    case 2:
      return <Medal className="w-4 h-4 text-gray-300" />;
    case 3:
      return <Medal className="w-4 h-4 text-amber-600" />;
    default:
      return (
        <span className="w-4 h-4 flex items-center justify-center text-xs text-[var(--fg-muted)]">
          {rank}
        </span>
      );
  }
}

function DeltaIndicator({ delta }: { delta: number | null }) {
  if (delta === null || delta === 0) {
    return <Minus className="w-3 h-3 text-gray-500" />;
  }

  if (delta > 0) {
    return (
      <div className="flex items-center gap-0.5 text-emerald-400">
        <TrendingUp className="w-3 h-3" />
        <span className="text-[10px]">+{delta}</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-0.5 text-red-400">
      <TrendingDown className="w-3 h-3" />
      <span className="text-[10px]">{delta}</span>
    </div>
  );
}

function formatScore(score: number, type: string): string {
  if (type === "revenue") {
    if (score >= 1_000_000) return `${(score / 1_000_000).toFixed(1)}M`;
    if (score >= 1_000) return `${(score / 1_000).toFixed(1)}K`;
    return score.toLocaleString();
  }
  if (type === "rating") {
    return score.toFixed(2);
  }
  if (type === "engagement") {
    return score.toFixed(1);
  }
  return score.toLocaleString();
}

function LeaderboardRow({
  entry,
  type,
  index,
}: {
  entry: LeaderboardEntry;
  type: string;
  index: number;
}) {
  const isTopThree = entry.rank <= 3;

  return (
    <motion.tr
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: index * 0.03 }}
      className={`group border-b border-white/5 last:border-0 ${
        isTopThree ? "bg-violet-500/5" : ""
      } hover:bg-white/5 transition-colors`}
    >
      {/* Rank */}
      <td className="py-3 pl-4">
        <div className="flex items-center gap-2">
          {getRankIcon(entry.rank)}
          <DeltaIndicator delta={entry.delta} />
        </div>
      </td>

      {/* User */}
      <td className="py-3">
        <div className="flex items-center gap-2">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
              isTopThree
                ? "bg-violet-500/30 text-violet-300"
                : "bg-white/10 text-[var(--fg-subtle)]"
            }`}
          >
            {(entry.display_name || entry.user_id).charAt(0).toUpperCase()}
          </div>
          <div>
            <p
              className={`text-sm font-medium ${
                isTopThree ? "text-[var(--fg-0)]" : "text-[var(--fg-subtle)]"
              }`}
            >
              {entry.display_name || "Anonymous"}
            </p>
            <p className="text-[10px] text-[var(--fg-muted)] truncate max-w-[120px]">
              {entry.user_id.slice(0, 8)}...
            </p>
          </div>
        </div>
      </td>

      {/* Score */}
      <td className="py-3 pr-4 text-right">
        <p
          className={`text-sm font-semibold ${
            isTopThree ? "text-violet-400" : "text-[var(--fg-0)]"
          }`}
        >
          {formatScore(entry.score, type)}
        </p>
        <p className="text-[10px] text-[var(--fg-muted)]">
          {type === "revenue" ? "credits" : type}
        </p>
      </td>
    </motion.tr>
  );
}

export function LeaderboardTable({ data, loading, onFetch }: LeaderboardTableProps) {
  const [leaderboardType, setLeaderboardType] = useState("revenue");
  const [period, setPeriod] = useState("weekly");

  const handleFetch = () => {
    onFetch(leaderboardType, period);
  };

  if (loading && !data) {
    return (
      <Card className="border border-white/5 bg-[var(--surface-1)]/70">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Trophy className="w-4 h-4 text-yellow-400" />
            Leaderboard
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
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-base flex items-center gap-2">
          <Trophy className="w-4 h-4 text-yellow-400" />
          Leaderboard
        </CardTitle>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <select
            value={leaderboardType}
            onChange={(e) => setLeaderboardType(e.target.value)}
            className="text-xs bg-[var(--surface-2)] border border-white/10 rounded-lg px-2 py-1 text-[var(--fg-0)]"
          >
            {LEADERBOARD_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="text-xs bg-[var(--surface-2)] border border-white/10 rounded-lg px-2 py-1 text-[var(--fg-0)]"
          >
            {PERIOD_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
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

      <CardContent className="p-0">
        {!data ? (
          <div className="flex flex-col items-center justify-center h-48 gap-2">
            <AlertCircle className="w-5 h-5 text-[var(--fg-muted)]" />
            <p className="text-sm text-[var(--fg-muted)]">
              Select type and period, then click Load
            </p>
          </div>
        ) : data.entries.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 gap-2">
            <Trophy className="w-5 h-5 text-[var(--fg-muted)]" />
            <p className="text-sm text-[var(--fg-muted)]">No rankings yet</p>
          </div>
        ) : (
          <div>
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10 text-left">
                  <th className="py-2 pl-4 text-xs text-[var(--fg-muted)] font-medium w-20">
                    Rank
                  </th>
                  <th className="py-2 text-xs text-[var(--fg-muted)] font-medium">
                    User
                  </th>
                  <th className="py-2 pr-4 text-xs text-[var(--fg-muted)] font-medium text-right">
                    Score
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.entries.map((entry, index) => (
                  <LeaderboardRow
                    key={entry.user_id}
                    entry={entry}
                    type={data.leaderboard_type}
                    index={index}
                  />
                ))}
              </tbody>
            </table>

            {/* Footer */}
            <div className="flex items-center justify-between px-4 py-3 border-t border-white/5 text-xs text-[var(--fg-muted)]">
              <div className="flex items-center gap-2">
                <span className="capitalize">{data.scope}</span>
                <span>•</span>
                <span>{data.period}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Wifi className="w-3 h-3 text-emerald-400" />
                <span>Updated: {new Date(data.updated_at).toLocaleTimeString()}</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default LeaderboardTable;
