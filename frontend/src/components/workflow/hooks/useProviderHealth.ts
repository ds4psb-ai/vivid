"use client";

/**
 * useProviderHealth - Production Provider Health Monitoring Hook
 *
 * Phase 8: Workflow UX Innovation
 *
 * Provides real-time health monitoring for Production providers (VEO, Kling, Suno).
 * Enables smart provider selection based on availability and latency.
 *
 * Features:
 * - Periodic health checks with configurable interval
 * - Circuit breaker tracking for failover
 * - Latency-based provider ranking
 * - Capability introspection
 *
 * 2026 Pattern: "Health-Aware Provider Selection"
 */

import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import type {
  ProviderId,
  ProviderHealth,
  ProviderHealthStatus,
  ProviderCapabilities,
  ProviderModel,
  UseProviderHealthOptions,
  UseProviderHealthResult,
  ProviderListResponse,
  CircuitBreakerState,
} from "./types";

// =============================================================================
// Constants
// =============================================================================

/** Default refresh interval: 60 seconds */
const DEFAULT_REFRESH_INTERVAL = 60_000;

/** Circuit breaker reset timeout: 30 seconds */
const CIRCUIT_BREAKER_RESET_TIMEOUT = 30_000;

/** Failure threshold to open circuit breaker */
const CIRCUIT_BREAKER_THRESHOLD = 3;

/** All known provider IDs */
const ALL_PROVIDERS: ProviderId[] = ["veo", "kling", "suno", "imagen"];

/** Provider display names */
const PROVIDER_NAMES: Record<ProviderId, string> = {
  veo: "VEO 3.1",
  kling: "Kling 2.6",
  suno: "Suno AI",
  imagen: "Imagen 3",
};

/** Default capabilities per provider (fallback when API unavailable) */
const DEFAULT_CAPABILITIES: Record<ProviderId, ProviderCapabilities> = {
  veo: {
    maxDuration: 8,
    minDuration: 1,
    aspectRatios: ["16:9", "9:16", "1:1"],
    referenceImages: true,
    maxReferenceImages: 3,
    frameControl: true,
    audioSupport: true,
    mediaType: "video",
  },
  kling: {
    maxDuration: 120,
    minDuration: 1,
    aspectRatios: ["16:9", "9:16", "1:1", "4:3", "3:4"],
    referenceImages: true,
    maxReferenceImages: 1,
    lipSync: true,
    mediaType: "video",
  },
  suno: {
    maxDuration: 180,
    minDuration: 30,
    aspectRatios: [],
    mediaType: "audio",
  },
  imagen: {
    maxDuration: 0,
    aspectRatios: ["16:9", "9:16", "1:1", "4:3", "3:4"],
    mediaType: "image",
  },
};

/** Default models per provider */
const DEFAULT_MODELS: Record<ProviderId, ProviderModel[]> = {
  veo: [
    { id: "veo-3.1-generate-preview", name: "VEO 3.1", creditsPerUnit: 200, unit: "second", isDefault: true },
    { id: "veo-3.1-fast-generate-preview", name: "VEO 3.1 Fast", creditsPerUnit: 60, unit: "second" },
  ],
  kling: [
    { id: "kling-v3.0", name: "Kling 3.0", creditsPerUnit: 300, unit: "second", isDefault: true },
    { id: "kling-v2.6", name: "Kling 2.6", creditsPerUnit: 200, unit: "second" },
    { id: "kling-v2.5", name: "Kling 2.5", creditsPerUnit: 150, unit: "second" },
  ],
  suno: [
    { id: "chirp-v4", name: "Chirp v4", creditsPerUnit: 50, unit: "song", isDefault: true },
    { id: "chirp-v3.5", name: "Chirp v3.5", creditsPerUnit: 30, unit: "song" },
  ],
  imagen: [
    { id: "imagen-3", name: "Imagen 3", creditsPerUnit: 20, unit: "image", isDefault: true },
  ],
};

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Create initial health state for a provider
 */
function createInitialHealth(providerId: ProviderId): ProviderHealth {
  return {
    provider: providerId,
    displayName: PROVIDER_NAMES[providerId],
    status: "unknown",
    latencyMs: null,
    lastChecked: null,
    models: DEFAULT_MODELS[providerId],
    capabilities: DEFAULT_CAPABILITIES[providerId],
  };
}

/**
 * Create initial state for all providers
 */
function createInitialState(providerIds: ProviderId[]): Record<ProviderId, ProviderHealth> {
  const state: Partial<Record<ProviderId, ProviderHealth>> = {};
  for (const id of providerIds) {
    state[id] = createInitialHealth(id);
  }
  return state as Record<ProviderId, ProviderHealth>;
}

/**
 * Determine circuit breaker state based on failure count
 */
function getCircuitBreakerState(
  failureCount: number,
  lastFailure: number | null,
  resetTimeout: number
): CircuitBreakerState {
  if (failureCount >= CIRCUIT_BREAKER_THRESHOLD) {
    // Check if reset timeout has passed
    if (lastFailure && Date.now() - lastFailure > resetTimeout) {
      return "half-open";
    }
    return "open";
  }
  return "closed";
}

// =============================================================================
// Main Hook
// =============================================================================

/**
 * useProviderHealth - Monitor Production provider health
 *
 * @example
 * ```tsx
 * const {
 *   providers,
 *   isLoading,
 *   healthyProviders,
 *   bestVideoProvider,
 *   getStatus,
 *   refresh,
 * } = useProviderHealth({
 *   refreshInterval: 30000,
 *   enableCircuitBreaker: true,
 * });
 *
 * // Check if VEO is usable
 * if (isUsable("veo")) {
 *   // Proceed with VEO generation
 * }
 *
 * // Get best provider for video
 * const provider = bestVideoProvider || "veo";
 * ```
 */
export function useProviderHealth(
  options: UseProviderHealthOptions = {}
): UseProviderHealthResult {
  const {
    providers: targetProviders = ALL_PROVIDERS,
    refreshInterval = DEFAULT_REFRESH_INTERVAL,
    enableCircuitBreaker = true,
    fetchOnMount = true,
  } = options;

  // State
  const [healthState, setHealthState] = useState<Record<ProviderId, ProviderHealth>>(
    () => createInitialState(targetProviders)
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);

  // Refs for interval management
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  // ==========================================================================
  // Fetch Provider List
  // ==========================================================================

  /**
   * Fetch available providers from backend
   */
  const fetchProviderList = useCallback(async (): Promise<string[]> => {
    try {
      const response = await fetch("/api/production/providers");
      if (!response.ok) {
        throw new Error(`Failed to fetch providers: ${response.status}`);
      }
      const data: ProviderListResponse = await response.json();
      return data.providers;
    } catch (err) {
      console.warn("[useProviderHealth] Failed to fetch provider list:", err);
      // Return target providers as fallback
      return targetProviders;
    }
  }, [targetProviders]);

  // ==========================================================================
  // Health Check Logic
  // ==========================================================================

  /**
   * Check health for a single provider
   */
  const checkProviderHealth = useCallback(
    async (providerId: ProviderId): Promise<ProviderHealth> => {
      const startTime = Date.now();
      const currentHealth = healthState[providerId] || createInitialHealth(providerId);

      try {
        // Check if provider is available via /api/production/health
        const response = await fetch("/api/production/health", {
          method: "GET",
          signal: AbortSignal.timeout(5000), // 5s timeout
        });

        const latencyMs = Date.now() - startTime;

        if (!response.ok) {
          throw new Error(`Health check failed: ${response.status}`);
        }

        const healthData = await response.json();

        // Determine status based on response
        let status: ProviderHealthStatus = "healthy";
        if (healthData.status === "degraded") {
          status = "degraded";
        } else if (healthData.status !== "healthy") {
          status = "unhealthy";
        }

        // Check if this specific provider is listed
        const availableProviders = healthData.providers || [];
        if (!availableProviders.includes(providerId)) {
          status = "unhealthy";
        }

        // Update circuit breaker (success resets failure count)
        const circuitBreaker = enableCircuitBreaker
          ? {
              state: "closed" as CircuitBreakerState,
              failureCount: 0,
              lastFailure: null,
              resetTimeout: CIRCUIT_BREAKER_RESET_TIMEOUT,
            }
          : undefined;

        return {
          ...currentHealth,
          status,
          latencyMs,
          lastChecked: Date.now(),
          circuitBreaker,
          errorMessage: undefined,
        };
      } catch (err) {
        const latencyMs = Date.now() - startTime;
        const errorMessage = err instanceof Error ? err.message : "Unknown error";

        // Update circuit breaker (failure increments count)
        const prevCircuitBreaker = currentHealth.circuitBreaker;
        const newFailureCount = (prevCircuitBreaker?.failureCount || 0) + 1;
        const circuitBreaker = enableCircuitBreaker
          ? {
              state: getCircuitBreakerState(
                newFailureCount,
                Date.now(),
                CIRCUIT_BREAKER_RESET_TIMEOUT
              ),
              failureCount: newFailureCount,
              lastFailure: Date.now(),
              resetTimeout: CIRCUIT_BREAKER_RESET_TIMEOUT,
            }
          : undefined;

        return {
          ...currentHealth,
          status: "unhealthy",
          latencyMs,
          lastChecked: Date.now(),
          circuitBreaker,
          errorMessage,
        };
      }
    },
    [healthState, enableCircuitBreaker]
  );

  /**
   * Refresh health for all providers
   */
  const refresh = useCallback(async () => {
    if (!mountedRef.current) return;

    setIsLoading(true);
    setError(null);

    try {
      // Fetch provider list first
      const availableProviders = await fetchProviderList();

      // Check health for each target provider
      const healthChecks = await Promise.all(
        targetProviders.map(async (providerId) => {
          // If provider not in available list, mark as unknown
          if (!availableProviders.includes(providerId)) {
            const currentHealth = healthState[providerId] || createInitialHealth(providerId);
            return {
              ...currentHealth,
              status: providerId === "imagen" ? "unknown" : "unhealthy",
              lastChecked: Date.now(),
              errorMessage: "Provider not available",
            } as ProviderHealth;
          }
          return checkProviderHealth(providerId);
        })
      );

      if (!mountedRef.current) return;

      // Update state with all health results
      const newHealthState = { ...healthState };
      for (const health of healthChecks) {
        newHealthState[health.provider] = health;
      }

      setHealthState(newHealthState);
      setLastUpdated(Date.now());
    } catch (err) {
      if (!mountedRef.current) return;
      setError(err instanceof Error ? err : new Error("Failed to refresh health"));
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [targetProviders, fetchProviderList, checkProviderHealth, healthState]);

  /**
   * Check health for a specific provider
   */
  const checkProvider = useCallback(
    async (providerId: ProviderId) => {
      if (!mountedRef.current) return;

      const health = await checkProviderHealth(providerId);

      if (!mountedRef.current) return;

      setHealthState((prev) => ({
        ...prev,
        [providerId]: health,
      }));
    },
    [checkProviderHealth]
  );

  /**
   * Reset circuit breaker for a provider
   */
  const resetCircuitBreaker = useCallback((providerId: ProviderId) => {
    setHealthState((prev) => {
      const current = prev[providerId];
      if (!current) return prev;

      return {
        ...prev,
        [providerId]: {
          ...current,
          circuitBreaker: current.circuitBreaker
            ? {
                ...current.circuitBreaker,
                state: "half-open",
                failureCount: 0,
              }
            : undefined,
        },
      };
    });
  }, []);

  // ==========================================================================
  // Quick Accessors
  // ==========================================================================

  const getStatus = useCallback(
    (providerId: ProviderId): ProviderHealthStatus => {
      return healthState[providerId]?.status || "unknown";
    },
    [healthState]
  );

  const isUsable = useCallback(
    (providerId: ProviderId): boolean => {
      const status = healthState[providerId]?.status;
      return status === "healthy" || status === "degraded";
    },
    [healthState]
  );

  const getLatency = useCallback(
    (providerId: ProviderId): number | null => {
      return healthState[providerId]?.latencyMs ?? null;
    },
    [healthState]
  );

  const getModels = useCallback(
    (providerId: ProviderId): ProviderModel[] => {
      return healthState[providerId]?.models || DEFAULT_MODELS[providerId] || [];
    },
    [healthState]
  );

  const getCapabilities = useCallback(
    (providerId: ProviderId): ProviderCapabilities | null => {
      return healthState[providerId]?.capabilities || DEFAULT_CAPABILITIES[providerId] || null;
    },
    [healthState]
  );

  // ==========================================================================
  // Derived State
  // ==========================================================================

  const healthyProviders = useMemo(
    () =>
      targetProviders.filter((id) => healthState[id]?.status === "healthy"),
    [targetProviders, healthState]
  );

  const degradedProviders = useMemo(
    () =>
      targetProviders.filter((id) => healthState[id]?.status === "degraded"),
    [targetProviders, healthState]
  );

  const unhealthyProviders = useMemo(
    () =>
      targetProviders.filter((id) => healthState[id]?.status === "unhealthy"),
    [targetProviders, healthState]
  );

  const bestVideoProvider = useMemo((): ProviderId | null => {
    // Filter to video providers that are usable
    const videoProviders = targetProviders.filter((id) => {
      const health = healthState[id];
      return (
        health &&
        health.capabilities.mediaType === "video" &&
        (health.status === "healthy" || health.status === "degraded")
      );
    });

    if (videoProviders.length === 0) return null;

    // Sort by latency (lowest first), then by status (healthy before degraded)
    return videoProviders.sort((a, b) => {
      const healthA = healthState[a];
      const healthB = healthState[b];

      // Prefer healthy over degraded
      if (healthA?.status !== healthB?.status) {
        return healthA?.status === "healthy" ? -1 : 1;
      }

      // Sort by latency
      const latencyA = healthA?.latencyMs ?? Infinity;
      const latencyB = healthB?.latencyMs ?? Infinity;
      return latencyA - latencyB;
    })[0];
  }, [targetProviders, healthState]);

  const bestAudioProvider = useMemo((): ProviderId | null => {
    // Filter to audio providers that are usable
    const audioProviders = targetProviders.filter((id) => {
      const health = healthState[id];
      return (
        health &&
        health.capabilities.mediaType === "audio" &&
        (health.status === "healthy" || health.status === "degraded")
      );
    });

    if (audioProviders.length === 0) return null;

    // Sort by latency
    return audioProviders.sort((a, b) => {
      const latencyA = healthState[a]?.latencyMs ?? Infinity;
      const latencyB = healthState[b]?.latencyMs ?? Infinity;
      return latencyA - latencyB;
    })[0];
  }, [targetProviders, healthState]);

  // ==========================================================================
  // Effects
  // ==========================================================================

  // Initial fetch on mount
  useEffect(() => {
    if (fetchOnMount) {
      refresh();
    }

    return () => {
      mountedRef.current = false;
    };
    // Only run on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Set up refresh interval
  useEffect(() => {
    if (refreshInterval > 0) {
      intervalRef.current = setInterval(() => {
        refresh();
      }, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [refreshInterval, refresh]);

  // ==========================================================================
  // Return
  // ==========================================================================

  return {
    // Health State
    providers: healthState,
    isLoading,
    error,
    lastUpdated,

    // Quick Accessors
    getStatus,
    isUsable,
    getLatency,
    getModels,
    getCapabilities,

    // Derived State
    healthyProviders,
    degradedProviders,
    unhealthyProviders,
    bestVideoProvider,
    bestAudioProvider,

    // Actions
    refresh,
    checkProvider,
    resetCircuitBreaker,
  };
}
