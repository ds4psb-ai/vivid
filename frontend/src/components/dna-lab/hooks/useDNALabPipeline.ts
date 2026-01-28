"use client";

/**
 * useDNALabPipeline - Unified Pipeline Execution Hook
 *
 * Provides a unified interface to run the entire DNA Lab pipeline
 * through the /run-pipeline endpoint.
 *
 * 2026 Trends Implementation:
 * - Single API call for multi-step pipeline
 * - Progress tracking with SSE support
 * - Saga pattern with automatic compensation
 */

import { useState, useCallback } from "react";
import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";

/**
 * Pipeline step identifiers
 */
export type PipelineStepId = "vpe" | "ad" | "mirror" | "qc";

/**
 * Step execution status
 */
export interface StepExecutionStatus {
  step: PipelineStepId;
  status: "pending" | "running" | "completed" | "failed";
  duration_ms?: number;
  credits_used?: number;
  error?: string;
}

/**
 * Pipeline execution state
 */
export interface PipelineState {
  isRunning: boolean;
  currentStep: PipelineStepId | null;
  progress: number;
  steps: StepExecutionStatus[];
  error: string | null;
  result: PipelineResult | null;
}

/**
 * Pipeline result from backend
 */
export interface PipelineResult {
  success: boolean;
  trace_id: string;
  status: "completed" | "partial" | "failed";
  vpe?: Record<string, unknown>;
  ad?: Record<string, unknown>;
  mirror?: Record<string, unknown>;
  qc?: Record<string, unknown>;
  evidence_refs: string[];
  steps: StepExecutionStatus[];
  credits_used: number;
  processing_time_ms: number;
  errors: Record<string, string>;
}

/**
 * Pipeline execution options
 */
export interface PipelineOptions {
  /** Steps to run (default: all) */
  steps?: PipelineStepId[];
  /** Video URI for VPE */
  video_uri?: string;
  /** Creative concept for AD */
  concept?: string;
  /** Auteur key for style matching */
  auteur_key?: string;
  /** Context for Mirror analysis */
  persona_context?: Record<string, unknown>;
  /** Content for QC analysis */
  quality_content?: string;
  /** IP ID for context-aware QC */
  ip_id?: string;
  /** Whether to sync to Qdrant (default: true) */
  store_to_qdrant?: boolean;
  /** Stop on first failure (default: false) */
  fail_fast?: boolean;
}

const initialState: PipelineState = {
  isRunning: false,
  currentStep: null,
  progress: 0,
  steps: [],
  error: null,
  result: null,
};

/**
 * DNA Lab Pipeline Hook
 *
 * Manages execution of the unified DNA Lab pipeline with
 * automatic chain data integration.
 */
export function useDNALabPipeline() {
  const [state, setState] = useState<PipelineState>(initialState);
  const chain = useDimensionChainOptional();

  /**
   * Run the pipeline with given options
   */
  const runPipeline = useCallback(
    async (options: PipelineOptions) => {
      setState({
        ...initialState,
        isRunning: true,
        progress: 5,
        steps: (options.steps || ["vpe", "ad", "mirror", "qc"]).map((step) => ({
          step,
          status: "pending",
        })),
      });

      try {
        const response = await fetch("/api/dna-lab/run-pipeline", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            steps: options.steps || ["vpe", "ad", "mirror", "qc"],
            video_uri: options.video_uri,
            concept: options.concept,
            auteur_key: options.auteur_key,
            persona_context: options.persona_context,
            quality_content: options.quality_content,
            ip_id: options.ip_id,
            store_to_qdrant: options.store_to_qdrant ?? true,
            fail_fast: options.fail_fast ?? false,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.detail?.message || errorData.message || `HTTP ${response.status}`
          );
        }

        const result: PipelineResult = await response.json();

        // Update chain context with results
        if (chain) {
          if (result.vpe) {
            chain.setChainData(
              "vpe",
              { output: result.vpe },
              "VPE 분석 완료",
              result.evidence_refs.filter((ref) => ref.includes("vpe"))
            );
          }
          if (result.ad) {
            chain.setChainData(
              "aesthetic-director",
              { output: result.ad },
              "미학 분석 완료",
              result.evidence_refs.filter((ref) => ref.includes("ad"))
            );
          }
          if (result.mirror) {
            chain.setChainData(
              "abyss-mirror",
              { output: result.mirror },
              "페르소나 분석 완료",
              result.evidence_refs.filter((ref) => ref.includes("mirror"))
            );
          }
          if (result.qc) {
            chain.setChainData(
              "quality-director",
              { output: result.qc },
              "품질 검증 완료",
              result.evidence_refs.filter((ref) => ref.includes("qc"))
            );
          }
        }

        setState({
          isRunning: false,
          currentStep: null,
          progress: 100,
          steps: result.steps,
          error: result.success ? null : Object.values(result.errors).join(", "),
          result,
        });

        return result;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "파이프라인 실행 실패";

        setState({
          isRunning: false,
          currentStep: null,
          progress: 0,
          steps: [],
          error: errorMessage,
          result: null,
        });

        throw error;
      }
    },
    [chain]
  );

  /**
   * Reset pipeline state
   */
  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  /**
   * Get result for a specific step
   */
  const getStepResult = useCallback(
    (stepId: PipelineStepId): Record<string, unknown> | undefined => {
      if (!state.result) return undefined;
      return state.result[stepId] as Record<string, unknown> | undefined;
    },
    [state.result]
  );

  /**
   * Check if a specific step completed successfully
   */
  const isStepCompleted = useCallback(
    (stepId: PipelineStepId): boolean => {
      const stepStatus = state.steps.find((s) => s.step === stepId);
      return stepStatus?.status === "completed";
    },
    [state.steps]
  );

  /**
   * Get total credits used
   */
  const creditsUsed = state.result?.credits_used ?? 0;

  /**
   * Get total processing time
   */
  const processingTimeMs = state.result?.processing_time_ms ?? 0;

  return {
    // State
    ...state,

    // Actions
    runPipeline,
    reset,

    // Helpers
    getStepResult,
    isStepCompleted,
    creditsUsed,
    processingTimeMs,
  };
}

export default useDNALabPipeline;
