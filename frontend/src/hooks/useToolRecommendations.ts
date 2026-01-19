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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

// =============================================================================
// Types
// =============================================================================

export type ConfidenceLevel = "high" | "medium" | "low";

export interface ToolRecommendation {
  tool_id: string;
  display_name: string;
  dimension: string;
  confidence: number;
  confidence_level: ConfidenceLevel;
  reason_codes: string[];
  evidence_refs: string[];
  estimated_credits: number;
  priority: number;
  description?: string;
}

export interface ToolRecommendationResponse {
  recommendations: ToolRecommendation[];
  total_estimated_credits: number;
  workflow_suggested: boolean;
  reason_summary: string;
  ip_context_used: boolean;
  trace_id?: string;
}

export interface ToolRecommendationRequest {
  ip_id?: string;
  preset_id?: string;
  scene_type?: string;
  user_history?: string[];
  dimension_context?: string;
  max_results?: number;
}

export interface ToolEvidenceResponse {
  tool_id: string;
  evidence_refs: string[];
  datasets_used: string[];
  reason_codes: string[];
  confidence: number;
  confidence_level: ConfidenceLevel;
}

export interface ToolDisplayInfo {
  tool_id: string;
  display_name_ko: string;
  display_name_en: string;
  dimension: string;
  description_ko: string;
  description_en: string;
  icon: string;
  base_credits: number;
}

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
  const { autoFetch = false, maxResults = 5 } = options;

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
        const res = await fetch(`${API_BASE}/api/v1/tools/recommend`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...request,
            max_results: request.max_results || maxResults,
          }),
        });

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }

        const data = (await res.json()) as ToolRecommendationResponse;

        // Cache result
        cacheRef.current.set(cacheKey, data);

        setRecommendations(data.recommendations);
        setResponse(data);
        return data;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to fetch recommendations";
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
        const params = new URLSearchParams();
        if (options?.sceneType) params.set("scene_type", options.sceneType);
        if (options?.dimensionContext) {
          params.set("dimension_context", options.dimensionContext);
        }

        const url = `${API_BASE}/api/v1/tools/ip/${encodeURIComponent(slug)}/recommendations${
          params.toString() ? `?${params.toString()}` : ""
        }`;

        const res = await fetch(url);

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }

        const data = (await res.json()) as ToolRecommendationResponse;

        setRecommendations(data.recommendations);
        setResponse(data);
        return data;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to fetch recommendations";
        setError(message);
        setRecommendations([]);
        setResponse(null);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  /**
   * Fetch evidence for a specific tool
   */
  const fetchToolEvidence = useCallback(
    async (toolId: string, ipId?: string) => {
      try {
        const params = new URLSearchParams();
        if (ipId) params.set("ip_id", ipId);

        const url = `${API_BASE}/api/v1/tools/${encodeURIComponent(toolId)}/evidence${
          params.toString() ? `?${params.toString()}` : ""
        }`;

        const res = await fetch(url);

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }

        return (await res.json()) as ToolEvidenceResponse;
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
      const params = new URLSearchParams();
      if (options.dimension) params.set("dimension", options.dimension);
      if (options.stage) params.set("stage", options.stage);

      const url = `${API_BASE}/api/v1/tools/list${
        params.toString() ? `?${params.toString()}` : ""
      }`;

      const res = await fetch(url);

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = (await res.json()) as ToolDisplayInfo[];
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
