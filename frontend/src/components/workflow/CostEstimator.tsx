"use client";

/**
 * CostEstimator - Real-time Credit Cost Calculation Component
 *
 * Phase 9: Workflow UX Innovation
 *
 * Provides dynamic cost estimation with:
 * - Provider-aware pricing (VEO, Kling, Suno)
 * - Model-specific costs
 * - Duration-based calculations
 * - Credit sufficiency indicator
 * - Breakdown tooltip
 *
 * 2026 Pattern: "Transparent Pricing, No Surprises"
 */

import { useMemo } from "react";
import { Coins, AlertCircle, Check, Info, TrendingDown, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import type { ProviderId, ProviderModel } from "./hooks/types";

// =============================================================================
// Types
// =============================================================================

export interface CostEstimatorProps {
  /** Selected provider */
  provider: ProviderId;
  /** Selected model (optional, uses default if not provided) */
  model?: string;
  /** Duration in seconds (for video/audio) */
  durationSeconds?: number;
  /** Resolution (for video) */
  resolution?: "720p" | "1080p" | "4k";
  /** Whether user has BYOK (bypasses cost) */
  isBYOK?: boolean;
  /** Show detailed breakdown */
  showBreakdown?: boolean;
  /** Compact display mode */
  compact?: boolean;
  /** Custom className */
  className?: string;
}

export interface CostBreakdown {
  baseCost: number;
  durationCost: number;
  resolutionMultiplier: number;
  totalCost: number;
  discountApplied?: number;
  discountReason?: string;
}

// =============================================================================
// Pricing Data
// =============================================================================

/**
 * Model-based pricing for each provider
 * Source: backend/app/routers/production/providers/*.py
 */
const PROVIDER_PRICING: Record<
  ProviderId,
  {
    models: Record<string, { name: string; baseCredits: number; perSecond?: number }>;
    defaultModel: string;
    type: "fixed" | "duration-based";
  }
> = {
  veo: {
    models: {
      "veo-3.1-generate-preview": { name: "VEO 3.1 Standard", baseCredits: 200 },
      "veo-3.1-fast-generate-preview": { name: "VEO 3.1 Fast", baseCredits: 100 },
    },
    defaultModel: "veo-3.1-generate-preview",
    type: "fixed",
  },
  kling: {
    models: {
      "kling-v3.0": { name: "Kling 3.0", baseCredits: 100, perSecond: 15 },
      "kling-v2.6": { name: "Kling 2.6", baseCredits: 0, perSecond: 10 },
      "kling-v2.5": { name: "Kling 2.5", baseCredits: 0, perSecond: 7 },
    },
    defaultModel: "kling-v2.6",
    type: "duration-based",
  },
  suno: {
    models: {
      "chirp-v4": { name: "Chirp v4", baseCredits: 50 },
      "chirp-v3.5": { name: "Chirp v3.5", baseCredits: 30 },
    },
    defaultModel: "chirp-v4",
    type: "fixed",
  },
  imagen: {
    models: {
      "imagen-3": { name: "Imagen 3", baseCredits: 20 },
    },
    defaultModel: "imagen-3",
    type: "fixed",
  },
};

/**
 * Resolution multipliers for video providers
 */
const RESOLUTION_MULTIPLIERS: Record<string, number> = {
  "720p": 1.0,
  "1080p": 1.4,
  "4k": 2.0,
};

// =============================================================================
// Cost Calculation
// =============================================================================

/**
 * Calculate credit cost breakdown
 */
function calculateCostBreakdown(
  provider: ProviderId,
  model: string | undefined,
  durationSeconds: number,
  resolution: string
): CostBreakdown {
  const pricing = PROVIDER_PRICING[provider];
  if (!pricing) {
    return {
      baseCost: 0,
      durationCost: 0,
      resolutionMultiplier: 1,
      totalCost: 0,
    };
  }

  const selectedModel = model || pricing.defaultModel;
  const modelPricing = pricing.models[selectedModel] || pricing.models[pricing.defaultModel];
  if (!modelPricing) {
    return {
      baseCost: 0,
      durationCost: 0,
      resolutionMultiplier: 1,
      totalCost: 0,
    };
  }

  const baseCost = modelPricing.baseCredits;
  let durationCost = 0;
  let resolutionMultiplier = 1;

  // Duration-based calculation
  if (pricing.type === "duration-based" && modelPricing.perSecond) {
    durationCost = durationSeconds * modelPricing.perSecond;
  }

  // Resolution multiplier (for video providers)
  if (provider === "kling" || provider === "veo") {
    resolutionMultiplier = RESOLUTION_MULTIPLIERS[resolution] || 1;
  }

  // Calculate total
  const subtotal = baseCost + durationCost;
  const totalCost = Math.ceil(subtotal * resolutionMultiplier);

  // Check for discount (VEO Fast mode)
  let discountApplied: number | undefined;
  let discountReason: string | undefined;

  if (provider === "veo" && selectedModel === "veo-3.1-fast-generate-preview") {
    discountApplied = 50;
    discountReason = "Fast 모드 할인";
  }

  return {
    baseCost,
    durationCost,
    resolutionMultiplier,
    totalCost,
    discountApplied,
    discountReason,
  };
}

// =============================================================================
// Sub-Components
// =============================================================================

/**
 * Credit sufficiency indicator
 */
function SufficiencyBadge({
  totalCost,
  currentBalance,
  className,
}: {
  totalCost: number;
  currentBalance: number;
  className?: string;
}) {
  const hasEnough = currentBalance >= totalCost;
  const remaining = currentBalance - totalCost;

  return (
    <div
      className={cn(
        "flex items-center gap-1 px-2 py-1 rounded-lg text-xs",
        hasEnough
          ? "bg-emerald-500/10 text-emerald-400"
          : "bg-red-500/10 text-red-400",
        className
      )}
    >
      {hasEnough ? (
        <>
          <Check className="w-3 h-3" />
          <span>사용 가능</span>
          <span className="text-white/30">({remaining.toLocaleString()} 남음)</span>
        </>
      ) : (
        <>
          <AlertCircle className="w-3 h-3" />
          <span>크레딧 부족</span>
          <span className="text-white/30">({Math.abs(remaining).toLocaleString()} 필요)</span>
        </>
      )}
    </div>
  );
}

/**
 * Discount badge
 */
function DiscountBadge({
  percent,
  reason,
  className,
}: {
  percent: number;
  reason: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium",
        "bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-300",
        className
      )}
    >
      <TrendingDown className="w-3 h-3" />
      <span>{percent}% 할인</span>
      <span className="text-amber-300/60">({reason})</span>
    </div>
  );
}

/**
 * Cost breakdown tooltip/panel
 */
function CostBreakdownPanel({
  breakdown,
  provider,
  model,
  durationSeconds,
  resolution,
  className,
}: {
  breakdown: CostBreakdown;
  provider: ProviderId;
  model: string;
  durationSeconds: number;
  resolution: string;
  className?: string;
}) {
  const pricing = PROVIDER_PRICING[provider];
  const modelPricing = pricing?.models[model];

  return (
    <div
      className={cn(
        "p-3 rounded-lg bg-white/[0.02] border border-white/5 text-xs",
        className
      )}
    >
      <div className="flex items-center gap-2 mb-2 text-white/60">
        <Info className="w-3.5 h-3.5" />
        <span className="font-medium">비용 상세</span>
      </div>

      <div className="space-y-1.5">
        {/* Base cost */}
        <div className="flex justify-between text-white/50">
          <span>기본 비용 ({modelPricing?.name || model})</span>
          <span>{breakdown.baseCost.toLocaleString()}</span>
        </div>

        {/* Duration cost */}
        {breakdown.durationCost > 0 && (
          <div className="flex justify-between text-white/50">
            <span>영상 길이 ({durationSeconds}초)</span>
            <span>+{breakdown.durationCost.toLocaleString()}</span>
          </div>
        )}

        {/* Resolution multiplier */}
        {breakdown.resolutionMultiplier !== 1 && (
          <div className="flex justify-between text-white/50">
            <span>해상도 ({resolution})</span>
            <span>x{breakdown.resolutionMultiplier}</span>
          </div>
        )}

        {/* Discount */}
        {breakdown.discountApplied && (
          <div className="flex justify-between text-amber-400">
            <span>{breakdown.discountReason}</span>
            <span>-{breakdown.discountApplied}%</span>
          </div>
        )}

        {/* Divider */}
        <div className="border-t border-white/10 my-2" />

        {/* Total */}
        <div className="flex justify-between text-white font-medium">
          <span>총 비용</span>
          <span>{breakdown.totalCost.toLocaleString()} 크레딧</span>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

/**
 * CostEstimator - Real-time credit cost estimation
 *
 * @example
 * ```tsx
 * <CostEstimator
 *   provider="veo"
 *   model="veo-3.1-fast-generate-preview"
 *   durationSeconds={5}
 *   resolution="1080p"
 *   showBreakdown
 * />
 * ```
 */
export function CostEstimator({
  provider,
  model,
  durationSeconds = 5,
  resolution = "1080p",
  isBYOK = false,
  showBreakdown = false,
  compact = false,
  className,
}: CostEstimatorProps) {
  const creditCtx = useCreditContextOptional();

  // Calculate cost breakdown
  const breakdown = useMemo(
    () => calculateCostBreakdown(provider, model, durationSeconds, resolution),
    [provider, model, durationSeconds, resolution]
  );

  // Effective model
  const effectiveModel = model || PROVIDER_PRICING[provider]?.defaultModel || "";

  // BYOK mode - no cost
  if (isBYOK) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-violet-500/10 text-violet-400 text-xs">
          <Zap className="w-3.5 h-3.5" />
          <span>BYOK 사용 중</span>
        </div>
        <span className="text-xs text-white/30">크레딧 무료</span>
      </div>
    );
  }

  // Compact mode
  if (compact) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 text-white text-sm">
          <Coins className="w-4 h-4 text-amber-400" />
          <span className="font-medium">{breakdown.totalCost.toLocaleString()}</span>
          <span className="text-white/40">크레딧</span>
        </div>
        {breakdown.discountApplied && (
          <DiscountBadge
            percent={breakdown.discountApplied}
            reason={breakdown.discountReason || ""}
          />
        )}
      </div>
    );
  }

  // Full mode
  return (
    <div className={cn("space-y-3", className)}>
      {/* Main cost display */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
              <Coins className="w-4 h-4 text-amber-400" />
            </div>
            <div>
              <div className="text-lg font-semibold text-white">
                {breakdown.totalCost.toLocaleString()}
                <span className="text-sm font-normal text-white/50 ml-1">크레딧</span>
              </div>
              <div className="text-xs text-white/40">예상 비용</div>
            </div>
          </div>

          {/* Discount badge */}
          {breakdown.discountApplied && (
            <DiscountBadge
              percent={breakdown.discountApplied}
              reason={breakdown.discountReason || ""}
            />
          )}
        </div>

        {/* Sufficiency indicator */}
        {creditCtx && (
          <SufficiencyBadge
            totalCost={breakdown.totalCost}
            currentBalance={creditCtx.balance}
          />
        )}
      </div>

      {/* Breakdown panel */}
      {showBreakdown && (
        <CostBreakdownPanel
          breakdown={breakdown}
          provider={provider}
          model={effectiveModel}
          durationSeconds={durationSeconds}
          resolution={resolution}
        />
      )}
    </div>
  );
}

/**
 * Hook to get cost calculation without UI
 */
export function useCostEstimate(
  provider: ProviderId,
  model?: string,
  durationSeconds: number = 5,
  resolution: string = "1080p"
): CostBreakdown {
  return useMemo(
    () => calculateCostBreakdown(provider, model, durationSeconds, resolution),
    [provider, model, durationSeconds, resolution]
  );
}

export default CostEstimator;
