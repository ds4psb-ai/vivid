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
 *
 * Phase 1-2: VPE + AD merged into "analysis"
 * Legacy "vpe" | "ad" maintained for backend compatibility
 */
export type PipelineStepId = "analysis" | "mirror" | "qc";

/**
 * Legacy step identifiers for backend API compatibility
 * The backend still expects "vpe", "ad" as separate steps
 */
export type LegacyPipelineStepId = "vpe" | "ad" | "mirror" | "qc";

/**
 * Step execution status
 * Uses LegacyPipelineStepId for backend API response compatibility
 */
export interface StepExecutionStatus {
  step: LegacyPipelineStepId;
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
 * Backend returns legacy keys (vpe, ad) which are merged into "analysis" for frontend
 */
export interface PipelineResult {
  success: boolean;
  trace_id: string;
  status: "completed" | "partial" | "failed";
  /** Legacy: VPE output from backend */
  vpe?: Record<string, unknown>;
  /** Legacy: AD output from backend */
  ad?: Record<string, unknown>;
  /** Merged analysis output (vpe + ad) for frontend consumption */
  analysis?: Record<string, unknown>;
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
  /** Steps to run (default: all). Uses frontend step IDs */
  steps?: PipelineStepId[];
  /** Video URI for analysis (VPE) */
  video_uri?: string;
  /** Creative concept for analysis (AD) */
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

/**
 * Convert frontend step IDs to backend legacy step IDs
 * "analysis" → ["vpe", "ad"]
 */
function toBackendSteps(frontendSteps: PipelineStepId[]): LegacyPipelineStepId[] {
  const backendSteps: LegacyPipelineStepId[] = [];
  for (const step of frontendSteps) {
    if (step === "analysis") {
      backendSteps.push("vpe", "ad");
    } else {
      backendSteps.push(step);
    }
  }
  return backendSteps;
}

/** Default frontend steps */
const DEFAULT_STEPS: PipelineStepId[] = ["analysis", "mirror", "qc"];

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
      const frontendSteps = options.steps || DEFAULT_STEPS;
      const backendSteps = toBackendSteps(frontendSteps);

      setState({
        ...initialState,
        isRunning: true,
        progress: 5,
        steps: backendSteps.map((step) => ({
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
            // Send legacy step IDs to backend
            steps: backendSteps,
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
        // Merge vpe + ad into unified "analysis" key for frontend consumption
        if (chain) {
          // Store unified analysis output (vpe + ad merged)
          if (result.vpe || result.ad) {
            const analysisOutput = {
              logicVector: result.vpe || {},
              aestheticGuidelines: result.ad || {},
              analysisTimestamp: Date.now(),
            };
            chain.setChainData(
              "analysis",
              { output: analysisOutput },
              "통합 분석 완료",
              result.evidence_refs.filter((ref) => ref.includes("vpe") || ref.includes("ad"))
            );
            // Also set on result for getStepResult compatibility
            result.analysis = analysisOutput;
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
   * Supports both frontend (analysis) and legacy (vpe, ad) step IDs
   */
  const getStepResult = useCallback(
    (stepId: PipelineStepId | LegacyPipelineStepId): Record<string, unknown> | undefined => {
      if (!state.result) return undefined;
      // For "analysis", return the merged result
      if (stepId === "analysis") {
        return state.result.analysis as Record<string, unknown> | undefined;
      }
      return state.result[stepId as keyof PipelineResult] as Record<string, unknown> | undefined;
    },
    [state.result]
  );

  /**
   * Check if a specific step completed successfully
   * For "analysis", checks both vpe and ad completion
   */
  const isStepCompleted = useCallback(
    (stepId: PipelineStepId | LegacyPipelineStepId): boolean => {
      if (stepId === "analysis") {
        // Analysis is complete when both vpe and ad are complete
        const vpeStatus = state.steps.find((s) => s.step === "vpe");
        const adStatus = state.steps.find((s) => s.step === "ad");
        return vpeStatus?.status === "completed" && adStatus?.status === "completed";
      }
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
