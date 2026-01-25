/**
 * useToolRecommendations - IP-First Coordination Phase 2.5
 *
 * Hook for fetching tool recommendations based on IP/preset context.
 *
 * Features:
 * - Fetch recommendations by IP ID or slug
 * - Cache recommendations
 * - Loading/error state management
 * - Auto-refresh on context change
 */
"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import {
  toolsApi,
  ToolRecommendation,
  ToolRecommendationRequest,
  ToolRecommendationResponse,
  ToolEvidenceResponse,
  ToolDisplayInfo,
} from "@/lib/api-client";

// =============================================================================
// Hook Options
// =============================================================================

interface UseToolRecommendationsOptions {
  /** Auto-fetch on mount */
  autoFetch?: boolean;
  /** Maximum results to fetch */
  maxResults?: number;
}

// =============================================================================
// Hook
// =============================================================================

export function useToolRecommendations(
  options: UseToolRecommendationsOptions = {}
) {
  const { autoFetch: _autoFetch = false, maxResults = 5 } = options;

  const [recommendations, setRecommendations] = useState<ToolRecommendation[]>(
    []
  );
  const [response, setResponse] = useState<ToolRecommendationResponse | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Cache for recommendations by context key
  const cacheRef = useRef<Map<string, ToolRecommendationResponse>>(new Map());

  /**
   * Fetch recommendations with request parameters
   */
  const fetchRecommendations = useCallback(
    async (request: ToolRecommendationRequest) => {
      const cacheKey = JSON.stringify(request);

      // Check cache
      const cached = cacheRef.current.get(cacheKey);
      if (cached) {
        setRecommendations(cached.recommendations);
        setResponse(cached);
        return cached;
      }

      setIsLoading(true);
      setError(null);

      try {
        const res = await toolsApi.recommend({
          ...request,
          max_results: request.max_results || maxResults,
        });

        if (!res.ok || !res.data) {
          throw new Error(res.error?.message || "Failed to fetch recommendations");
        }

        const data = res.data;

        // Cache result
        cacheRef.current.set(cacheKey, data);

        setRecommendations(data.recommendations);
        setResponse(data);
        return data;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to fetch recommendations";
        setError(message);
        setRecommendations([]);
        setResponse(null);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [maxResults]
  );

  /**
   * Fetch recommendations for an IP by slug
   */
  const fetchByIPSlug = useCallback(
    async (
      slug: string,
      options?: { sceneType?: string; dimensionContext?: string }
    ) => {
      setIsLoading(true);
      setError(null);

      try {
        const res = await toolsApi.getIPRecommendations(slug, {
          sceneType: options?.sceneType,
          dimensionContext: options?.dimensionContext,
          maxResults,
        });

        if (!res.ok || !res.data) {
          throw new Error(res.error?.message || "Failed to fetch recommendations");
        }

        const data = res.data;

        setRecommendations(data.recommendations);
        setResponse(data);
        return data;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to fetch recommendations";
        setError(message);
        setRecommendations([]);
        setResponse(null);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [maxResults]
  );

  /**
   * Fetch evidence for a specific tool
   */
  const fetchToolEvidence = useCallback(
    async (toolId: string, ipId?: string) => {
      try {
        const res = await toolsApi.getToolEvidence(toolId, ipId);
        if (!res.ok || !res.data) {
          throw new Error(res.error?.message || "Failed to fetch tool evidence");
        }
        return res.data as ToolEvidenceResponse;
      } catch (err) {
        console.error("Failed to fetch tool evidence:", err);
        return null;
      }
    },
    []
  );

  /**
   * Clear cached recommendations
   */
  const clearCache = useCallback(() => {
    cacheRef.current.clear();
  }, []);

  /**
   * Clear current state
   */
  const clear = useCallback(() => {
    setRecommendations([]);
    setResponse(null);
    setError(null);
  }, []);

  return {
    // State
    recommendations,
    response,
    isLoading,
    error,

    // Computed
    totalCredits: response?.total_estimated_credits || 0,
    workflowSuggested: response?.workflow_suggested || false,
    reasonSummary: response?.reason_summary || "",
    ipContextUsed: response?.ip_context_used || false,
    traceId: response?.trace_id,

    // Actions
    fetchRecommendations,
    fetchByIPSlug,
    fetchToolEvidence,
    clear,
    clearCache,
  };
}

// =============================================================================
// Hook for Tool List
// =============================================================================

interface UseToolListOptions {
  dimension?: string;
  stage?: string;
}

export function useToolList(options: UseToolListOptions = {}) {
  const [tools, setTools] = useState<ToolDisplayInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTools = useCallback(async () => {
    setIsLoading(true);
    setError(null);

      try {
        const res = await toolsApi.listTools({
          dimension: options.dimension,
          stage: options.stage,
        });

        if (!res.ok || !res.data) {
          throw new Error(res.error?.message || "Failed to fetch tools");
        }

        const data = res.data as ToolDisplayInfo[];
        setTools(data);
        return data;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to fetch tools";
      setError(message);
      setTools([]);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [options.dimension, options.stage]);

  // Auto-fetch on mount
  useEffect(() => {
    fetchTools();
  }, [fetchTools]);

  return {
    tools,
    isLoading,
    error,
    fetchTools,
  };
}

// =============================================================================
// Exports
// =============================================================================

export default useToolRecommendations;
