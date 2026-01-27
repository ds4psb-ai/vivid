"use client";

/**
 * ChainDataBadge - Display chain data injection status
 *
 * Shows:
 * - Loading state when fetching upstream data
 * - "Data from X" when upstream data is available
 * - Hover tooltip with details
 *
 * P7+ Chain UX Enhancement
 */

import { useMemo } from "react";
import { useDimensionChain, DIMENSION_DISPLAY_NAMES } from "@/contexts/DimensionChainContext";

interface ChainDataBadgeProps {
  /** Current dimension key */
  dimensionKey: string;
  /** Whether data is being loaded */
  isLoading?: boolean;
  /** Compact mode (small badge) */
  compact?: boolean;
  /** Show tooltip on hover */
  showTooltip?: boolean;
}

export function ChainDataBadge({
  dimensionKey,
  isLoading = false,
  compact = false,
  showTooltip = true,
}: ChainDataBadgeProps) {
  const chain = useDimensionChain();

  // Get input data for this dimension
  const inputData = useMemo(
    () => chain.getInputData(dimensionKey),
    [chain, dimensionKey]
  );

  // Get upstream dimension names that have data
  const upstreamSources = useMemo(() => {
    return Object.keys(inputData).map((key) => ({
      key,
      name: DIMENSION_DISPLAY_NAMES[key] || key,
      hasData: !!inputData[key],
      timestamp: inputData[key]?.timestamp,
    }));
  }, [inputData]);

  const hasUpstreamData = upstreamSources.some((s) => s.hasData);

  // Nothing to show if no upstream and not loading
  if (!isLoading && !hasUpstreamData) {
    return null;
  }

  // Loading state
  if (isLoading) {
    return (
      <div
        className={`inline-flex items-center gap-1.5 ${
          compact ? "px-2 py-0.5" : "px-3 py-1"
        } rounded-full bg-blue-500/10 border border-blue-500/20`}
      >
        <svg
          className="w-3 h-3 animate-spin text-blue-400"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
        <span className={`text-blue-300 ${compact ? "text-xs" : "text-sm"}`}>
          데이터 로딩 중...
        </span>
      </div>
    );
  }

  // Has upstream data
  const sourcesWithData = upstreamSources.filter((s) => s.hasData);
  const sourceNames = sourcesWithData.map((s) => s.name).join(", ");

  return (
    <div className="relative group">
      <div
        className={`inline-flex items-center gap-1.5 ${
          compact ? "px-2 py-0.5" : "px-3 py-1"
        } rounded-full bg-green-500/10 border border-green-500/20`}
      >
        <svg
          className="w-3 h-3 text-green-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 10V3L4 14h7v7l9-11h-7z"
          />
        </svg>
        <span className={`text-green-300 ${compact ? "text-xs" : "text-sm"}`}>
          {compact
            ? `${sourcesWithData.length}개 연결`
            : `${sourceNames}에서 데이터 수신`}
        </span>
      </div>

      {/* Tooltip */}
      {showTooltip && (
        <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-50">
          <div className="bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl p-3 min-w-48">
            <div className="text-xs font-medium text-zinc-400 mb-2">
              연결된 체인 데이터
            </div>
            <div className="space-y-2">
              {sourcesWithData.map((source) => (
                <div key={source.key} className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-400" />
                  <div>
                    <div className="text-sm text-white">{source.name}</div>
                    {source.timestamp && (
                      <div className="text-xs text-zinc-500">
                        {new Date(source.timestamp).toLocaleTimeString()}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
