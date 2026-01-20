"use client";

import { useCallback, useEffect, useState } from "react";
import { useSSEStream } from "./useSSEStream";

// =============================================================================
// Types
// =============================================================================

export interface KPIValue {
  key: string;
  value: number;
  unit: string;
  trend: "up" | "down" | "neutral";
  delta_pct: number | null;
  updated_at: string;
}

export interface DashboardKPIs {
  total_revenue: KPIValue;
  active_users: KPIValue;
  tool_executions: KPIValue;
  avg_engagement_score: KPIValue;
  conversion_rate: KPIValue;
  period_days: number;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  display_name: string | null;
  score: number;
  delta: number | null;
}

export interface LeaderboardData {
  leaderboard_type: string;
  scope: string;
  period: string;
  period_date: string;
  entries: LeaderboardEntry[];
  updated_at: string;
}

export interface RevenueWaterfallData {
  period_days: number;
  total_revenue: number;
  tool_usage_revenue: number;
  fork_revenue_received: number;
  fork_revenue_shared: number;
  platform_fees: number;
  net_revenue: number;
  daily_breakdown: Array<{
    date: string;
    revenue: number;
    executions: number;
  }>;
}

export interface FunnelStep {
  step_name: string;
  step_order: number;
  users_entered: number;
  users_completed: number;
  conversion_rate: number;
  drop_off_rate: number;
  avg_time_in_step_ms: number;
  top_drop_off_reasons: Array<{ reason: string; count: number }>;
}

export interface FunnelAnalysis {
  funnel_name: string;
  period_start: string;
  period_end: string;
  total_users_started: number;
  total_users_completed: number;
  overall_conversion_rate: number;
  steps: FunnelStep[];
  bottleneck_step: string | null;
}

export interface CohortRow {
  cohort_date: string;
  cohort_size: number;
  retention_rates: number[];
  revenue_per_user: number[];
}

export interface RetentionCohortsData {
  cohort_type: string;
  period_type: string;
  periods: number;
  cohorts: CohortRow[];
}

export interface EngagementScore {
  user_id: string;
  total_score: number;
  tier: string;
  recency_score: number;
  frequency_score: number;
  monetary_score: number;
  depth_score: number;
  last_activity: string | null;
}

export interface TopTool {
  tool_key: string;
  revenue: number;
  executions: number;
  avg_rating: number | null;
}

// =============================================================================
// API Functions
// =============================================================================

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function fetchAPI<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

// =============================================================================
// Hook
// =============================================================================

interface UseAnalyticsDashboardOptions {
  /** Enable real-time KPI streaming (default: true) */
  enableStreaming?: boolean;
  /** Dashboard refresh interval in ms (default: 60000) */
  refreshInterval?: number;
  /** Period for analytics data (default: 30) */
  periodDays?: number;
}

interface UseAnalyticsDashboardReturn {
  // KPI data
  kpis: DashboardKPIs | null;
  kpisLoading: boolean;
  kpisError: Error | null;
  refreshKPIs: () => Promise<void>;

  // Leaderboard data
  leaderboard: LeaderboardData | null;
  leaderboardLoading: boolean;
  fetchLeaderboard: (type: string, period?: string) => Promise<void>;

  // Revenue waterfall
  waterfall: RevenueWaterfallData | null;
  waterfallLoading: boolean;
  fetchWaterfall: (periodDays?: number) => Promise<void>;

  // Funnel analysis
  funnel: FunnelAnalysis | null;
  funnelLoading: boolean;
  fetchFunnel: (name: string, startDate: string, endDate: string) => Promise<void>;

  // Retention cohorts
  cohorts: RetentionCohortsData | null;
  cohortsLoading: boolean;
  fetchCohorts: (type?: string, periodType?: string) => Promise<void>;

  // Engagement score
  engagement: EngagementScore | null;
  engagementLoading: boolean;
  fetchEngagement: () => Promise<void>;

  // Top tools
  topTools: TopTool[] | null;
  topToolsLoading: boolean;
  fetchTopTools: (periodDays?: number, limit?: number) => Promise<void>;

  // SSE connection status
  isStreamConnected: boolean;
}

/**
 * Hook for managing analytics dashboard state and data fetching.
 *
 * @example
 * ```tsx
 * const {
 *   kpis,
 *   leaderboard,
 *   waterfall,
 *   isStreamConnected,
 *   fetchLeaderboard,
 * } = useAnalyticsDashboard({ enableStreaming: true });
 * ```
 */
export function useAnalyticsDashboard(
  options: UseAnalyticsDashboardOptions = {}
): UseAnalyticsDashboardReturn {
  const {
    enableStreaming = true,
    refreshInterval = 60000,
    periodDays = 30,
  } = options;

  // KPI state
  const [kpis, setKPIs] = useState<DashboardKPIs | null>(null);
  const [kpisLoading, setKPIsLoading] = useState(true);
  const [kpisError, setKPIsError] = useState<Error | null>(null);

  // Leaderboard state
  const [leaderboard, setLeaderboard] = useState<LeaderboardData | null>(null);
  const [leaderboardLoading, setLeaderboardLoading] = useState(false);

  // Waterfall state
  const [waterfall, setWaterfall] = useState<RevenueWaterfallData | null>(null);
  const [waterfallLoading, setWaterfallLoading] = useState(false);

  // Funnel state
  const [funnel, setFunnel] = useState<FunnelAnalysis | null>(null);
  const [funnelLoading, setFunnelLoading] = useState(false);

  // Cohorts state
  const [cohorts, setCohorts] = useState<RetentionCohortsData | null>(null);
  const [cohortsLoading, setCohortsLoading] = useState(false);

  // Engagement state
  const [engagement, setEngagement] = useState<EngagementScore | null>(null);
  const [engagementLoading, setEngagementLoading] = useState(false);

  // Top tools state
  const [topTools, setTopTools] = useState<TopTool[] | null>(null);
  const [topToolsLoading, setTopToolsLoading] = useState(false);

  // SSE stream for real-time KPIs
  const { data: streamData, isConnected: isStreamConnected } = useSSEStream<{
    total_revenue: number;
    total_executions: number;
    timestamp: string;
  }>(
    enableStreaming ? `/api/v1/analytics/stream/kpis` : "",
    { reconnect: true }
  );

  // Update KPIs from stream data
  useEffect(() => {
    if (streamData && kpis) {
      setKPIs((prev) =>
        prev
          ? {
              ...prev,
              total_revenue: {
                ...prev.total_revenue,
                value: streamData.total_revenue,
                updated_at: streamData.timestamp,
              },
              tool_executions: {
                ...prev.tool_executions,
                value: streamData.total_executions,
                updated_at: streamData.timestamp,
              },
            }
          : prev
      );
    }
  }, [streamData]);

  // Fetch KPIs
  const refreshKPIs = useCallback(async () => {
    setKPIsLoading(true);
    setKPIsError(null);
    try {
      const data = await fetchAPI<DashboardKPIs>(
        `/api/v1/analytics/kpis?period_days=${periodDays}`
      );
      setKPIs(data);
    } catch (err) {
      setKPIsError(err instanceof Error ? err : new Error("Failed to fetch KPIs"));
    } finally {
      setKPIsLoading(false);
    }
  }, [periodDays]);

  // Fetch leaderboard
  const fetchLeaderboard = useCallback(
    async (type: string, period: string = "weekly") => {
      setLeaderboardLoading(true);
      try {
        const data = await fetchAPI<LeaderboardData>(
          `/api/v1/analytics/leaderboard/${type}?period=${period}`
        );
        setLeaderboard(data);
      } catch (err) {
        console.error("Failed to fetch leaderboard:", err);
      } finally {
        setLeaderboardLoading(false);
      }
    },
    []
  );

  // Fetch waterfall
  const fetchWaterfall = useCallback(async (days: number = periodDays) => {
    setWaterfallLoading(true);
    try {
      const data = await fetchAPI<RevenueWaterfallData>(
        `/api/v1/analytics/revenue/waterfall?period_days=${days}`
      );
      setWaterfall(data);
    } catch (err) {
      console.error("Failed to fetch waterfall:", err);
    } finally {
      setWaterfallLoading(false);
    }
  }, [periodDays]);

  // Fetch funnel
  const fetchFunnel = useCallback(
    async (name: string, startDate: string, endDate: string) => {
      setFunnelLoading(true);
      try {
        const data = await fetchAPI<FunnelAnalysis>(
          `/api/v1/analytics/funnel/${name}?start_date=${startDate}&end_date=${endDate}`
        );
        setFunnel(data);
      } catch (err) {
        console.error("Failed to fetch funnel:", err);
      } finally {
        setFunnelLoading(false);
      }
    },
    []
  );

  // Fetch cohorts
  const fetchCohorts = useCallback(
    async (type: string = "first_tool", periodType: string = "weekly") => {
      setCohortsLoading(true);
      try {
        const data = await fetchAPI<RetentionCohortsData>(
          `/api/v1/analytics/retention/cohorts?cohort_type=${type}&period_type=${periodType}`
        );
        setCohorts(data);
      } catch (err) {
        console.error("Failed to fetch cohorts:", err);
      } finally {
        setCohortsLoading(false);
      }
    },
    []
  );

  // Fetch engagement
  const fetchEngagement = useCallback(async () => {
    setEngagementLoading(true);
    try {
      const data = await fetchAPI<EngagementScore>(
        `/api/v1/analytics/engagement/score`
      );
      setEngagement(data);
    } catch (err) {
      console.error("Failed to fetch engagement:", err);
    } finally {
      setEngagementLoading(false);
    }
  }, []);

  // Fetch top tools
  const fetchTopTools = useCallback(
    async (days: number = periodDays, limit: number = 10) => {
      setTopToolsLoading(true);
      try {
        const data = await fetchAPI<TopTool[]>(
          `/api/v1/analytics/top-tools?period_days=${days}&limit=${limit}`
        );
        setTopTools(data);
      } catch (err) {
        console.error("Failed to fetch top tools:", err);
      } finally {
        setTopToolsLoading(false);
      }
    },
    [periodDays]
  );

  // Initial fetch
  useEffect(() => {
    refreshKPIs();
  }, [refreshKPIs]);

  // Periodic refresh
  useEffect(() => {
    if (!enableStreaming && refreshInterval > 0) {
      const interval = setInterval(refreshKPIs, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [enableStreaming, refreshInterval, refreshKPIs]);

  return {
    kpis,
    kpisLoading,
    kpisError,
    refreshKPIs,
    leaderboard,
    leaderboardLoading,
    fetchLeaderboard,
    waterfall,
    waterfallLoading,
    fetchWaterfall,
    funnel,
    funnelLoading,
    fetchFunnel,
    cohorts,
    cohortsLoading,
    fetchCohorts,
    engagement,
    engagementLoading,
    fetchEngagement,
    topTools,
    topToolsLoading,
    fetchTopTools,
    isStreamConnected,
  };
}

export default useAnalyticsDashboard;
