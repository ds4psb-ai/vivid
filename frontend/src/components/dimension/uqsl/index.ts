/**
 * UQSL (Universal Quality Selection Layer) Components
 *
 * @see UQSL_SPEC.md - Universal Quality Selection Layer Specification
 *
 * Components:
 * - ABComparisonCard: 2-way A/B comparison for HITL selection
 * - ThreeWayComparison: Ensemble++ 3-way comparison (NeurIPS 2025)
 * - QualityScorecard: Quality score visualization (5 dimensions)
 * - FeedbackButtons: Enhanced with UQSL feedback modes
 */

// Re-export from parent directory (UQSL components are colocated with Dimension components)
export {
  default as ABComparisonCard,
  CandidateCard,
  type CandidateData,
  type ABComparisonCardProps,
} from "../ABComparisonCard";

export {
  default as ThreeWayComparison,
  CompactThreeWay,
  type ThreeWayCandidateData,
  type ThreeWaySelection,
  type ThreeWayComparisonProps,
} from "../ThreeWayComparison";

export {
  default as QualityScorecard,
  QualityBadge,
  QualityDot,
  type QualityScores,
  type QualityScorecardProps,
} from "../QualityScorecard";

// Types for external use
export type {
  UQSLQualityScore,
  UQSLCandidateResult,
  UQSLGenerateCandidatesRequest,
  UQSLGenerateCandidatesResponse,
  UQSLSelectBestRequest,
  UQSLFeedbackRequest,
  UQSLThreeWayCandidateData,
  UQSLThreeWayRequest,
  UQSLThreeWayResponse,
  UQSLQualityMetrics,
} from "@/lib/api";
