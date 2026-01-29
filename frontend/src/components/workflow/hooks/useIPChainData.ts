"use client";

/**
 * useIPChainData - IP Data + Chain Data Integration Hook
 *
 * Connects IP catalog data with the Chain Data system for project-based workflows.
 * Enables automatic initialization of chain data from IP worldbuilding.
 *
 * Features:
 * - IP data fetching (backend API or demo fallback)
 * - Session persistence per IP (via DimensionChainContext)
 * - IP-based suggested defaults extraction
 * - Phase 2 MissingDataBanner integration
 *
 * @example
 * ```tsx
 * function DNALabContent({ ipSlug }: { ipSlug: string | null }) {
 *   const {
 *     ipData,
 *     ipLoading,
 *     hasMissingData,
 *     missingKeys,
 *     ipDefaults,
 *     applySuggestion,
 *     goToSource,
 *   } = useIPChainData({
 *     ipSlug,
 *     requiredKeys: ["vpe", "ad"],
 *   });
 *
 *   if (hasMissingData) {
 *     return (
 *       <MissingDataBanner
 *         missingKeys={missingKeys}
 *         onGoToSource={goToSource}
 *         suggestedDefaults={ipDefaults}
 *         onApplySuggestion={applySuggestion}
 *       />
 *     );
 *   }
 *   // ...
 * }
 * ```
 */

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";
import { useRequiredChainData } from "./useRequiredChainData";
import { getConfidenceLevel } from "../types";
import type { SuggestedDefault } from "../types";
import type {
  SyntheticIPDetail,
  IPWorldbuilding,
  UseIPChainDataOptions,
  UseIPChainDataResult,
} from "./types";

// Demo IP data fallback (imported dynamically to avoid circular deps)
import { getDemoIPData, isDemoIP } from "@/lib/demo-ip-overrides";

// =============================================================================
// IP Defaults Extraction
// =============================================================================

/**
 * Extract suggested defaults from IP worldbuilding data
 *
 * Maps IP.worldbuilding fields to chain data keys with confidence scores.
 * Used by MissingDataBanner to offer one-click initialization.
 */
function extractIPDefaults(
  ipData: SyntheticIPDetail
): Record<string, SuggestedDefault> {
  const defaults: Record<string, SuggestedDefault> = {};
  const wb = ipData.worldbuilding as IPWorldbuilding;

  if (!wb || typeof wb !== "object") return defaults;

  const ipRef = `db:ip_catalog:${ipData.slug}`;

  // VPE (Video Prompt Engineering) defaults from thematic_elements
  if (wb.thematic_elements) {
    const te = wb.thematic_elements;
    const hasCore = !!te.core;
    const hasMotifs = te.motifs && te.motifs.length > 0;
    const hasThemes = te.themes && te.themes.length > 0;

    if (hasCore || hasMotifs || hasThemes) {
      // Calculate confidence based on data completeness
      let confidence = 50; // Base
      if (hasCore) confidence += 15;
      if (hasMotifs) confidence += 10;
      if (hasThemes) confidence += 10;
      confidence = Math.min(confidence, 85);

      defaults.vpe = {
        value: {
          thematicCore: te.core || "",
          visualMotifs: te.motifs || [],
          themes: te.themes || [],
        },
        confidence,
        confidenceLevel: getConfidenceLevel(confidence),
        evidenceSources: [ipRef],
        summary: `IP "${ipData.name_ko}" 세계관의 테마 요소 기반`,
      };
    }
  }

  // AD (Aesthetic Director) defaults from visual_style
  if (wb.visual_style) {
    const vs = wb.visual_style;
    const hasColors = vs.colors && vs.colors.length > 0;
    const hasLighting = !!vs.lighting;
    const hasMood = !!vs.mood;
    const hasCinematography = !!vs.cinematography;

    if (hasColors || hasLighting || hasMood || hasCinematography) {
      let confidence = 45;
      if (hasColors) confidence += 15;
      if (hasLighting) confidence += 10;
      if (hasMood) confidence += 8;
      if (hasCinematography) confidence += 12;
      confidence = Math.min(confidence, 85);

      defaults.ad = {
        value: {
          colorPalette: vs.colors || [],
          lightingStyle: vs.lighting || "",
          mood: vs.mood || "",
          cinematographyStyle: vs.cinematography || "",
        },
        confidence,
        confidenceLevel: getConfidenceLevel(confidence),
        evidenceSources: [ipRef],
        summary: `IP "${ipData.name_ko}" 비주얼 스타일 기반`,
      };
    }
  }

  // Mirror (Abyss Mirror) defaults from characters
  if (wb.characters && Array.isArray(wb.characters) && wb.characters.length > 0) {
    const chars = wb.characters;
    const avgTraits =
      chars.reduce((sum, c) => sum + (c.traits?.length || 0), 0) / chars.length;

    let confidence = 40;
    confidence += Math.min(chars.length * 10, 25); // More chars = more confidence
    confidence += Math.min(avgTraits * 5, 15); // More traits = more confidence
    confidence = Math.min(confidence, 80);

    defaults.mirror = {
      value: {
        characters: chars.map((c) => ({
          name: c.name,
          role: c.role,
          traits: c.traits,
        })),
      },
      confidence,
      confidenceLevel: getConfidenceLevel(confidence),
      evidenceSources: [ipRef],
      summary: `IP "${ipData.name_ko}"의 ${chars.length}명 캐릭터 데이터 기반`,
    };
  }

  // Story defaults from setting/logline
  if (wb.setting || wb.logline) {
    let confidence = 35;
    if (wb.setting) confidence += 20;
    if (wb.logline) confidence += 25;
    if (wb.mood) confidence += 10;
    confidence = Math.min(confidence, 85);

    defaults.story = {
      value: {
        setting: wb.setting || "",
        logline: wb.logline || "",
        mood: wb.mood || "",
      },
      confidence,
      confidenceLevel: getConfidenceLevel(confidence),
      evidenceSources: [ipRef],
      summary: `IP "${ipData.name_ko}" 세계관 설정 기반`,
    };
  }

  return defaults;
}

// =============================================================================
// Hook Implementation
// =============================================================================

export function useIPChainData<T extends Record<string, unknown> = Record<string, unknown>>({
  ipSlug,
  requiredKeys = [],
  autoFetchIP = true,
  autoRestoreSession = true,
}: UseIPChainDataOptions): UseIPChainDataResult<T> {
  // IP data state
  const [ipData, setIPData] = useState<SyntheticIPDetail | null>(null);
  const [ipLoading, setIPLoading] = useState(false);
  const [ipError, setIPError] = useState<Error | null>(null);
  const [sessionRestored, setSessionRestored] = useState(false);
  const [hasExistingSession, setHasExistingSession] = useState(false);

  // Prevent duplicate fetches/restores
  const fetchedRef = useRef<string | null>(null);
  const restoredRef = useRef<string | null>(null);

  // DimensionChainContext (IP session storage)
  const chainCtx = useDimensionChainOptional();

  // Chain data (reuse existing hook)
  const chainResult = useRequiredChainData<T>(requiredKeys);

  // Check for existing session on mount
  useEffect(() => {
    if (!ipSlug || typeof window === "undefined") return;
    if (chainCtx?.hasSessionData(ipSlug)) {
      setHasExistingSession(true);
    }
  }, [ipSlug, chainCtx]);

  // Restore session from storage (once per IP)
  useEffect(() => {
    if (!ipSlug || !autoRestoreSession || !chainCtx) return;
    if (restoredRef.current === ipSlug) return;

    if (chainCtx.hasSessionData(ipSlug)) {
      const restored = chainCtx.loadFromSession(ipSlug);
      if (restored) {
        console.log(`[useIPChainData] Restored session for IP: ${ipSlug}`);
        setSessionRestored(true);
      }
    }
    restoredRef.current = ipSlug;
  }, [ipSlug, autoRestoreSession, chainCtx]);

  // Fetch IP data
  useEffect(() => {
    if (!ipSlug || !autoFetchIP) return;
    if (fetchedRef.current === ipSlug) return;

    fetchedRef.current = ipSlug;
    setIPLoading(true);
    setIPError(null);

    // Check for demo IP first (no backend needed)
    if (isDemoIP(ipSlug)) {
      const demoData = getDemoIPData(ipSlug);
      if (demoData) {
        setIPData(demoData.ipDetail as SyntheticIPDetail);
        setIPLoading(false);
        // Add IP to evidence refs
        chainCtx?.appendEvidenceRefs([`db:ip_catalog:${ipSlug}`]);
        return;
      }
    }

    // Fetch from backend
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "";
    fetch(`${apiUrl}/api/v1/ip/catalog/${ipSlug}`)
      .then((res) => {
        if (!res.ok) {
          // Fallback to demo data
          const demoData = getDemoIPData(ipSlug);
          if (demoData) {
            setIPData(demoData.ipDetail as SyntheticIPDetail);
            return null;
          }
          throw new Error(`IP not found: ${ipSlug}`);
        }
        return res.json();
      })
      .then((data) => {
        if (data) {
          setIPData(data);
          // Add IP to evidence refs
          chainCtx?.appendEvidenceRefs([`db:ip_catalog:${ipSlug}`]);
        }
      })
      .catch((err) => {
        console.error("[useIPChainData] IP fetch error:", err);
        setIPError(err);
      })
      .finally(() => {
        setIPLoading(false);
      });
  }, [ipSlug, autoFetchIP, chainCtx]);

  // Extract IP-based defaults
  const ipDefaults = useMemo(() => {
    if (!ipData) return {};
    return extractIPDefaults(ipData);
  }, [ipData]);

  // Restore from IP session
  const restoreFromIP = useCallback((): boolean => {
    if (!ipSlug || !chainCtx) return false;
    const restored = chainCtx.loadFromSession(ipSlug);
    if (restored) {
      setSessionRestored(true);
    }
    return restored;
  }, [ipSlug, chainCtx]);

  // Save to IP session
  const saveToIP = useCallback(() => {
    if (!ipSlug || !chainCtx) return;
    chainCtx.syncToSession(ipSlug);
  }, [ipSlug, chainCtx]);

  // Apply suggested default to chain data
  const applySuggestion = useCallback(
    (key: string, value: unknown) => {
      if (!chainCtx) {
        console.warn("[useIPChainData] No chain context available");
        return;
      }

      const evidenceRef = ipSlug ? `db:ip_catalog:${ipSlug}` : undefined;
      const evidenceRefs = evidenceRef ? [evidenceRef] : [];

      chainCtx.setChainData(
        key,
        value as Record<string, unknown>,
        `IP "${ipData?.name_ko || ipSlug}" 기반 자동 추론`,
        evidenceRefs
      );

      // Also save to session for persistence
      if (ipSlug) {
        // Small delay to ensure chain data is updated
        setTimeout(() => chainCtx.syncToSession(ipSlug), 50);
      }
    },
    [chainCtx, ipSlug, ipData?.name_ko]
  );

  // Initialize from IP (manual trigger)
  const initializeFromIP = useCallback(async () => {
    if (!ipSlug) return;

    // 1. Try to restore session
    if (chainCtx?.hasSessionData(ipSlug)) {
      chainCtx.loadFromSession(ipSlug);
      setSessionRestored(true);
    }

    // 2. If no session and autoFetchIP was disabled, fetch now
    if (!ipData && !autoFetchIP) {
      setIPLoading(true);
      try {
        // Demo check
        if (isDemoIP(ipSlug)) {
          const demoData = getDemoIPData(ipSlug);
          if (demoData) {
            setIPData(demoData.ipDetail as SyntheticIPDetail);
            chainCtx?.appendEvidenceRefs([`db:ip_catalog:${ipSlug}`]);
            return;
          }
        }

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "";
        const res = await fetch(`${apiUrl}/api/v1/ip/catalog/${ipSlug}`);
        if (res.ok) {
          const data = await res.json();
          setIPData(data);
          chainCtx?.appendEvidenceRefs([`db:ip_catalog:${ipSlug}`]);
        }
      } catch (err) {
        console.error("[useIPChainData] Manual fetch error:", err);
        setIPError(err as Error);
      } finally {
        setIPLoading(false);
      }
    }
  }, [ipSlug, chainCtx, ipData, autoFetchIP]);

  // Add evidence ref
  const addEvidenceRef = useCallback(
    (ref: string) => {
      chainCtx?.appendEvidenceRefs([ref]);
    },
    [chainCtx]
  );

  return {
    // IP State
    ipSlug,
    ipData,
    ipLoading,
    ipError,

    // Chain Data
    chainData: chainResult.data as T | null,
    hasMissingData: chainResult.hasMissingData,
    missingKeys: chainResult.missingKeys,
    partialData: chainResult.partialData as Partial<T>,

    // IP Defaults (Phase 2)
    ipDefaults,

    // Actions
    initializeFromIP,
    saveToIP,
    restoreFromIP,
    applySuggestion,
    goToSource: chainResult.goToSource,

    // Evidence
    evidenceRefs: chainCtx?.accumulatedEvidenceRefs ?? [],
    addEvidenceRef,

    // Session Status
    sessionRestored,
    hasExistingSession,
  };
}

export default useIPChainData;
