"use client";

/**
 * useRequiredChainData - Smart Data Injection Hook
 *
 * Automatically injects required chain data into components.
 * Detects missing data and provides navigation to source steps.
 *
 * 2026 Pattern: "Declare, Don't Fetch"
 * - Component declares what it needs
 * - Hook provides data + missing detection + navigation
 */

import { useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";
import { CHAIN_DATA_SOURCE_MAP } from "../workflow-configs";
import type { MegaAppId } from "../types";

export interface UseRequiredChainDataResult<T> {
  /** The required data (null if any missing) */
  data: T | null;
  /** Loading state */
  isLoading: boolean;
  /** Keys that are missing */
  missingKeys: string[];
  /** Whether any required data is missing */
  hasMissingData: boolean;
  /** Navigate to the source step for a missing key */
  goToSource: (key: string) => void;
  /** Get source info for a key */
  getSourceInfo: (key: string) => { app: MegaAppId; step: string; label: string } | null;
  /** Partial data (even when some keys missing) */
  partialData: Partial<T>;
}

export interface UseRequiredChainDataOptions {
  /** Show console warning when data missing */
  warnOnMissing?: boolean;
  /** Allow partial data usage */
  allowPartial?: boolean;
}

/**
 * Hook for smart data injection with missing data detection
 *
 * @example
 * ```tsx
 * function StoryArchitectPanel() {
 *   const { data, hasMissingData, missingKeys, goToSource } = useRequiredChainData<{
 *     vpe: VPEOutput;
 *     ad: AestheticDirectorOutput;
 *   }>(["vpe", "ad"]);
 *
 *   if (hasMissingData) {
 *     return <MissingDataBanner missingKeys={missingKeys} onGoToSource={goToSource} />;
 *   }
 *
 *   return <Editor logicVector={data.vpe.logicVector} aesthetics={data.ad} />;
 * }
 * ```
 */
export function useRequiredChainData<T extends Record<string, unknown>>(
  requiredKeys: string[],
  options: UseRequiredChainDataOptions = {}
): UseRequiredChainDataResult<T> {
  const { warnOnMissing = false, allowPartial = false } = options;
  const router = useRouter();
  const chainCtx = useDimensionChainOptional();

  // Calculate missing keys
  const missingKeys = useMemo(() => {
    if (!chainCtx?.chainData) return requiredKeys;
    return requiredKeys.filter((key) => !chainCtx.chainData[key]);
  }, [chainCtx?.chainData, requiredKeys]);

  // Build partial data (available keys only)
  const partialData = useMemo(() => {
    if (!chainCtx?.chainData) return {} as Partial<T>;
    const partial: Partial<T> = {};
    for (const key of requiredKeys) {
      const chainEntry = chainCtx.chainData[key];
      if (chainEntry?.output) {
        (partial as Record<string, unknown>)[key] = chainEntry.output;
      }
    }
    return partial;
  }, [chainCtx?.chainData, requiredKeys]);

  // Build complete data (null if any missing)
  const data = useMemo(() => {
    if (missingKeys.length > 0) {
      if (warnOnMissing) {
        console.warn(
          `[useRequiredChainData] Missing required data: ${missingKeys.join(", ")}`
        );
      }
      return null;
    }
    return partialData as T;
  }, [missingKeys, partialData, warnOnMissing]);

  // Get source info for a key
  const getSourceInfo = useCallback((key: string) => {
    return CHAIN_DATA_SOURCE_MAP[key] || null;
  }, []);

  // Navigate to source step for a missing key
  const goToSource = useCallback(
    (key: string) => {
      const source = CHAIN_DATA_SOURCE_MAP[key];
      if (!source) {
        console.warn(`[useRequiredChainData] No source mapping for key: ${key}`);
        return;
      }

      // Build URL with step parameter
      const stepParam = source.app === "dna-lab" ? "step" : "step";
      const url = `/${source.app}?${stepParam}=${source.step}`;
      router.push(url);
    },
    [router]
  );

  return {
    data,
    isLoading: false, // Chain data is synchronous
    missingKeys,
    hasMissingData: missingKeys.length > 0,
    goToSource,
    getSourceInfo,
    partialData,
  };
}

/**
 * Hook variant that returns data even when partial
 * Useful for optional enhancements
 */
export function useOptionalChainData<T extends Record<string, unknown>>(
  keys: string[]
): {
  data: Partial<T>;
  availableKeys: string[];
  missingKeys: string[];
} {
  const chainCtx = useDimensionChainOptional();

  const availableKeys = useMemo(() => {
    if (!chainCtx?.chainData) return [];
    return keys.filter((key) => !!chainCtx.chainData[key]);
  }, [chainCtx?.chainData, keys]);

  const missingKeys = useMemo(() => {
    return keys.filter((key) => !availableKeys.includes(key));
  }, [keys, availableKeys]);

  const data = useMemo(() => {
    if (!chainCtx?.chainData) return {} as Partial<T>;
    const result: Partial<T> = {};
    for (const key of availableKeys) {
      const chainEntry = chainCtx.chainData[key];
      if (chainEntry?.output) {
        (result as Record<string, unknown>)[key] = chainEntry.output;
      }
    }
    return result;
  }, [chainCtx?.chainData, availableKeys]);

  return { data, availableKeys, missingKeys };
}
