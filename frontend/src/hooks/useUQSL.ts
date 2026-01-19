"use client";

/**
 * useUQSL - Hook for UQSL (Universal Quality Selection Layer) API integration
 *
 * 2026 Best Practice:
 * - SSE streaming for real-time progress
 * - Thompson Sampling feedback integration
 * - Three-way comparison support
 *
 * @see UQSL_SPEC.md
 */

import { useState, useCallback, useRef, useEffect } from "react";
import {
  api,
  type UQSLGenerateCandidatesRequest,
  type UQSLGenerateCandidatesResponse,
  type UQSLThreeWayRequest,
  type UQSLThreeWayResponse,
  type UQSLStreamProgressEvent,
  type UQSLStreamCandidateEvent,
  type UQSLStreamQualityEvent,
  type UQSLStreamSelectionEvent,
  type UQSLStreamCompleteEvent,
  type UQSLStreamErrorEvent,
  type UQSLStreamResultEvent,
  type UQSLStreamRecommendationEvent,
  type UQSLCandidateResult,
  type UQSLQualityScore,
  type UQSLArmStats,
} from "@/lib/api";

// =============================================================================
// Types
// =============================================================================

export interface UseUQSLGenerateState {
  /** Current progress (0-100) */
  progress: number;
  /** Progress message */
  message: string;
  /** Progress stage */
  stage: "idle" | "starting" | "processing" | "finalizing" | "complete" | "error";
  /** Generated candidates (streamed) */
  candidates: UQSLCandidateResult[];
  /** Quality scores (streamed) */
  qualityScores: UQSLQualityScore[];
  /** Recommended candidate index */
  recommendedIdx: number | null;
  /** Selection method used */
  selectionMethod: string | null;
  /** Selection confidence */
  confidence: number | null;
  /** Arms used in generation */
  armsUsed: string[];
  /** Arm statistics */
  armsStats: Record<string, UQSLArmStats>;
  /** Session ID for HITL selection */
  sessionId: string | null;
  /** Error message if any */
  error: string | null;
  /** Whether currently loading */
  isLoading: boolean;
}

export interface UseUQSLThreeWayState {
  /** Current progress (0-100) */
  progress: number;
  /** Progress message */
  message: string;
  /** Progress stage */
  stage: "idle" | "starting" | "processing" | "finalizing" | "complete" | "error";
  /** Result A (Qdrant) */
  resultA: Record<string, unknown> | null;
  /** Result B (NotebookLM) */
  resultB: Record<string, unknown> | null;
  /** Result AB (Ensemble) */
  resultAB: Record<string, unknown> | null;
  /** Recommended option */
  recommended: "a" | "b" | "ab" | null;
  /** Arm statistics */
  armsStats: Record<string, UQSLArmStats>;
  /** Error message if any */
  error: string | null;
  /** Whether currently loading */
  isLoading: boolean;
}

export interface UseUQSLOptions {
  /** Callback when generation completes */
  onComplete?: (response: UQSLGenerateCandidatesResponse) => void;
  /** Callback when three-way comparison completes */
  onThreeWayComplete?: (response: UQSLThreeWayResponse) => void;
  /** Callback when progress updates */
  onProgress?: (progress: number, message: string) => void;
  /** Callback when error occurs */
  onError?: (error: string) => void;
}

// =============================================================================
// Initial States
// =============================================================================

const initialGenerateState: UseUQSLGenerateState = {
  progress: 0,
  message: "",
  stage: "idle",
  candidates: [],
  qualityScores: [],
  recommendedIdx: null,
  selectionMethod: null,
  confidence: null,
  armsUsed: [],
  armsStats: {},
  sessionId: null,
  error: null,
  isLoading: false,
};

const initialThreeWayState: UseUQSLThreeWayState = {
  progress: 0,
  message: "",
  stage: "idle",
  resultA: null,
  resultB: null,
  resultAB: null,
  recommended: null,
  armsStats: {},
  error: null,
  isLoading: false,
};

// =============================================================================
// Hook: useUQSLGenerate
// =============================================================================

export function useUQSLGenerate(options: UseUQSLOptions = {}) {
  const [state, setState] = useState<UseUQSLGenerateState>(initialGenerateState);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    setState(initialGenerateState);
  }, []);

  const generate = useCallback(
    async (request: UQSLGenerateCandidatesRequest) => {
      // Abort any existing request
      if (abortRef.current) {
        abortRef.current.abort();
      }
      abortRef.current = new AbortController();

      // Reset state
      setState({
        ...initialGenerateState,
        isLoading: true,
        stage: "starting",
        message: "UQSL 생성 시작...",
      });

      try {
        const candidates: UQSLCandidateResult[] = [];
        const qualityScores: UQSLQualityScore[] = [];
        let sessionId: string | null = null;

        // Stream events
        for await (const event of api.uqslGenerateCandidatesStream(request)) {
          if (abortRef.current?.signal.aborted) {
            break;
          }

          switch (event.type) {
            case "progress": {
              const progressEvent = event as UQSLStreamProgressEvent;
              setState((prev) => ({
                ...prev,
                progress: progressEvent.percent,
                message: progressEvent.message,
                stage: progressEvent.stage as typeof prev.stage,
              }));
              options.onProgress?.(progressEvent.percent, progressEvent.message);
              break;
            }

            case "candidate": {
              const candidateEvent = event as UQSLStreamCandidateEvent;
              candidates.push({
                idx: candidateEvent.idx,
                content: candidateEvent.content_preview,
                metadata: {},
                latency_ms: 0,
                backend_used: candidateEvent.backend_used,
              });
              setState((prev) => ({
                ...prev,
                candidates: [...candidates],
              }));
              break;
            }

            case "quality": {
              const qualityEvent = event as UQSLStreamQualityEvent;
              qualityScores[qualityEvent.idx] = {
                groundedness: qualityEvent.groundedness,
                relevance: qualityEvent.relevance,
                coherence: qualityEvent.coherence,
                creativity: qualityEvent.creativity,
                safety: qualityEvent.safety,
                weighted_score: qualityEvent.weighted_score,
                total_score: qualityEvent.weighted_score, // Use weighted_score as total_score
              };
              setState((prev) => ({
                ...prev,
                qualityScores: [...qualityScores],
              }));
              break;
            }

            case "selection": {
              const selectionEvent = event as UQSLStreamSelectionEvent;
              setState((prev) => ({
                ...prev,
                recommendedIdx: selectionEvent.selected_idx,
                selectionMethod: selectionEvent.method,
                confidence: selectionEvent.confidence,
                armsUsed: selectionEvent.arms_used,
                armsStats: selectionEvent.arms_stats,
              }));
              break;
            }

            case "complete": {
              const completeEvent = event as UQSLStreamCompleteEvent;
              sessionId = (completeEvent.data as { session_id?: string }).session_id || null;

              // Update candidates with full content from complete event
              const fullCandidates = (completeEvent.data as { candidates?: UQSLCandidateResult[] }).candidates || candidates;

              setState((prev) => ({
                ...prev,
                stage: "complete",
                isLoading: false,
                sessionId,
                candidates: fullCandidates,
              }));

              // Call onComplete callback
              const response: UQSLGenerateCandidatesResponse = {
                session_id: sessionId || "",
                candidates: fullCandidates,
                quality_scores: qualityScores,
                recommended_idx: (completeEvent.data as { recommended_idx?: number }).recommended_idx || 0,
                method: (completeEvent.data as { method?: string }).method || "auto",
              };
              options.onComplete?.(response);
              break;
            }

            case "error": {
              const errorEvent = event as UQSLStreamErrorEvent;
              setState((prev) => ({
                ...prev,
                stage: "error",
                error: errorEvent.error,
                isLoading: false,
              }));
              options.onError?.(errorEvent.error);
              break;
            }
          }
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Unknown error";
        setState((prev) => ({
          ...prev,
          stage: "error",
          error: errorMessage,
          isLoading: false,
        }));
        options.onError?.(errorMessage);
      }
    },
    [options]
  );

  const abort = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
    }
    setState((prev) => ({
      ...prev,
      stage: "idle",
      isLoading: false,
    }));
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortRef.current) {
        abortRef.current.abort();
      }
    };
  }, []);

  return {
    ...state,
    generate,
    abort,
    reset,
  };
}

// =============================================================================
// Hook: useUQSLThreeWay
// =============================================================================

export function useUQSLThreeWay(options: UseUQSLOptions = {}) {
  const [state, setState] = useState<UseUQSLThreeWayState>(initialThreeWayState);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    setState(initialThreeWayState);
  }, []);

  const compare = useCallback(
    async (request: UQSLThreeWayRequest) => {
      // Abort any existing request
      if (abortRef.current) {
        abortRef.current.abort();
      }
      abortRef.current = new AbortController();

      // Reset state
      setState({
        ...initialThreeWayState,
        isLoading: true,
        stage: "starting",
        message: "Ensemble++ 3-way 비교 시작...",
      });

      try {
        let resultA: Record<string, unknown> | null = null;
        let resultB: Record<string, unknown> | null = null;
        let resultAB: Record<string, unknown> | null = null;
        let recommended: "a" | "b" | "ab" | null = null;
        let armsStats: Record<string, UQSLArmStats> = {};

        // Stream events
        for await (const event of api.uqslThreeWayComparisonStream(request)) {
          if (abortRef.current?.signal.aborted) {
            break;
          }

          switch (event.type) {
            case "progress": {
              const progressEvent = event as UQSLStreamProgressEvent;
              setState((prev) => ({
                ...prev,
                progress: progressEvent.percent,
                message: progressEvent.message,
                stage: progressEvent.stage as typeof prev.stage,
              }));
              options.onProgress?.(progressEvent.percent, progressEvent.message);
              break;
            }

            case "result_a":
            case "result_b":
            case "result_ab": {
              const resultEvent = event as UQSLStreamResultEvent;
              if (resultEvent.type === "result_a") {
                resultA = resultEvent.data as unknown as Record<string, unknown>;
                setState((prev) => ({ ...prev, resultA }));
              } else if (resultEvent.type === "result_b") {
                resultB = resultEvent.data as unknown as Record<string, unknown>;
                setState((prev) => ({ ...prev, resultB }));
              } else {
                resultAB = resultEvent.data as unknown as Record<string, unknown>;
                setState((prev) => ({ ...prev, resultAB }));
              }
              break;
            }

            case "recommendation": {
              const recEvent = event as UQSLStreamRecommendationEvent;
              recommended = recEvent.recommended;
              armsStats = recEvent.arms_stats;
              setState((prev) => ({
                ...prev,
                recommended,
                armsStats,
              }));
              break;
            }

            case "complete": {
              setState((prev) => ({
                ...prev,
                stage: "complete",
                isLoading: false,
              }));

              // Call onThreeWayComplete callback
              const response: UQSLThreeWayResponse = {
                results: {
                  a: resultA as unknown as UQSLThreeWayResponse["results"]["a"],
                  b: resultB as unknown as UQSLThreeWayResponse["results"]["b"],
                  ab: resultAB as unknown as UQSLThreeWayResponse["results"]["ab"],
                },
                recommended: recommended || "a",
                arms_stats: armsStats,
              };
              options.onThreeWayComplete?.(response);
              break;
            }

            case "error": {
              const errorEvent = event as UQSLStreamErrorEvent;
              setState((prev) => ({
                ...prev,
                stage: "error",
                error: errorEvent.error,
                isLoading: false,
              }));
              options.onError?.(errorEvent.error);
              break;
            }
          }
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Unknown error";
        setState((prev) => ({
          ...prev,
          stage: "error",
          error: errorMessage,
          isLoading: false,
        }));
        options.onError?.(errorMessage);
      }
    },
    [options]
  );

  const abort = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
    }
    setState((prev) => ({
      ...prev,
      stage: "idle",
      isLoading: false,
    }));
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortRef.current) {
        abortRef.current.abort();
      }
    };
  }, []);

  return {
    ...state,
    compare,
    abort,
    reset,
  };
}

// =============================================================================
// Hook: useUQSLFeedback
// =============================================================================

export function useUQSLFeedback() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitFeedback = useCallback(
    async (selectionId: string, feedback: "positive" | "negative") => {
      setIsSubmitting(true);
      setError(null);

      try {
        const result = await api.uqslSubmitFeedback({
          selection_id: selectionId,
          feedback,
        });
        return result;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Feedback submission failed";
        setError(errorMessage);
        throw err;
      } finally {
        setIsSubmitting(false);
      }
    },
    []
  );

  const selectCandidate = useCallback(
    async (sessionId: string, selectedIdx: number) => {
      setIsSubmitting(true);
      setError(null);

      try {
        const result = await api.uqslSelectBest({
          session_id: sessionId,
          selected_idx: selectedIdx,
        });
        return result;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Selection failed";
        setError(errorMessage);
        throw err;
      } finally {
        setIsSubmitting(false);
      }
    },
    []
  );

  const selectThreeWay = useCallback(
    async (comparisonId: string, selected: "a" | "b" | "ab" | "skip") => {
      setIsSubmitting(true);
      setError(null);

      try {
        const result = await api.uqslSelectThreeWay(comparisonId, selected);
        return result;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Three-way selection failed";
        setError(errorMessage);
        throw err;
      } finally {
        setIsSubmitting(false);
      }
    },
    []
  );

  return {
    isSubmitting,
    error,
    submitFeedback,
    selectCandidate,
    selectThreeWay,
  };
}

// =============================================================================
// Default Export
// =============================================================================

const uqslHooks = {
  useUQSLGenerate,
  useUQSLThreeWay,
  useUQSLFeedback,
};

export default uqslHooks;
