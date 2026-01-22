/**
 * Custom Hooks Index
 */

export { useSSEStream } from "./useSSEStream";
export type { SSEEvent } from "./useSSEStream";

export { useAnalyticsDashboard } from "./useAnalyticsDashboard";
export type {
  KPIValue,
  DashboardKPIs,
  LeaderboardEntry,
  LeaderboardData,
  RevenueWaterfallData,
  FunnelStep,
  FunnelAnalysis,
  CohortRow,
  RetentionCohortsData,
  EngagementScore,
  TopTool,
} from "./useAnalyticsDashboard";

export {
  useCardMotion,
  CARD_HOVER_TRANSITION,
  CARD_HOVER_STATE,
  CARD_MOTION_PROPS,
} from "./useCardMotion";
export type { CardMotionPreset, CardMotionConfig, CardMotionResult } from "./useCardMotion";
