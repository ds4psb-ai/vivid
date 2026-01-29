"use client";

/**
 * SmartProviderSelector - Health-Aware Provider Selection Component
 *
 * Phase 9: Workflow UX Innovation
 *
 * Provides intelligent provider selection with:
 * - Real-time health status indicators
 * - Latency-based recommendations
 * - Capability matching (duration, features)
 * - Automatic best provider suggestion
 *
 * 2026 Pattern: "Smart Defaults, Expert Override"
 */

import { useMemo, useCallback, useState } from "react";
import {
  Video,
  Music2,
  Image as ImageIcon,
  Check,
  AlertTriangle,
  XCircle,
  Zap,
  Clock,
  ChevronDown,
  Sparkles,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useProviderHealth } from "./hooks/useProviderHealth";
import type {
  ProviderId,
  ProviderHealth,
  ProviderHealthStatus,
  ProviderCapabilities,
} from "./hooks/types";

// =============================================================================
// Types
// =============================================================================

export interface SmartProviderSelectorProps {
  /** Currently selected provider */
  value: ProviderId | null;
  /** Callback when provider is selected */
  onChange: (providerId: ProviderId) => void;
  /** Filter by media type */
  mediaType?: "video" | "audio" | "image" | "all";
  /** Minimum required duration (filters out providers that can't support it) */
  minDuration?: number;
  /** Show only healthy providers */
  healthyOnly?: boolean;
  /** Show recommendation badge on best provider */
  showRecommendation?: boolean;
  /** Compact display mode */
  compact?: boolean;
  /** Disabled state */
  disabled?: boolean;
  /** Custom className */
  className?: string;
}

/** Provider display configuration */
interface ProviderDisplayConfig {
  id: ProviderId;
  name: string;
  description: string;
  icon: LucideIcon;
  colorClass: string;
  bgClass: string;
}

// =============================================================================
// Constants
// =============================================================================

const PROVIDER_CONFIGS: Record<ProviderId, ProviderDisplayConfig> = {
  veo: {
    id: "veo",
    name: "VEO 3.1",
    description: "Google AI 고품질 비디오",
    icon: Video,
    colorClass: "text-emerald-400",
    bgClass: "bg-emerald-500/10",
  },
  kling: {
    id: "kling",
    name: "Kling 2.6",
    description: "시네마틱 비디오 & 립싱크",
    icon: Video,
    colorClass: "text-orange-400",
    bgClass: "bg-orange-500/10",
  },
  suno: {
    id: "suno",
    name: "Suno AI",
    description: "AI 음악 생성",
    icon: Music2,
    colorClass: "text-pink-400",
    bgClass: "bg-pink-500/10",
  },
  imagen: {
    id: "imagen",
    name: "Imagen 3",
    description: "Google AI 이미지 생성",
    icon: ImageIcon,
    colorClass: "text-blue-400",
    bgClass: "bg-blue-500/10",
  },
};

const STATUS_CONFIGS: Record<
  ProviderHealthStatus,
  { icon: LucideIcon; color: string; label: string }
> = {
  healthy: { icon: Check, color: "text-emerald-400", label: "정상" },
  degraded: { icon: AlertTriangle, color: "text-amber-400", label: "지연" },
  unhealthy: { icon: XCircle, color: "text-red-400", label: "오류" },
  unknown: { icon: Clock, color: "text-white/40", label: "확인 중" },
};

// =============================================================================
// Sub-Components
// =============================================================================

/**
 * Health status indicator badge
 */
function HealthBadge({
  status,
  latencyMs,
  compact = false,
}: {
  status: ProviderHealthStatus;
  latencyMs: number | null;
  compact?: boolean;
}) {
  const config = STATUS_CONFIGS[status];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "flex items-center gap-1 text-xs",
        config.color,
        compact ? "gap-0.5" : "gap-1"
      )}
    >
      <Icon className={cn("flex-shrink-0", compact ? "w-3 h-3" : "w-3.5 h-3.5")} />
      {!compact && (
        <>
          <span>{config.label}</span>
          {latencyMs !== null && status !== "unhealthy" && (
            <span className="text-white/30">({latencyMs}ms)</span>
          )}
        </>
      )}
    </div>
  );
}

/**
 * Recommendation badge for best provider
 */
function RecommendationBadge({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium",
        "bg-gradient-to-r from-cyan-500/20 to-violet-500/20 text-cyan-300",
        className
      )}
    >
      <Sparkles className="w-3 h-3" />
      <span>추천</span>
    </div>
  );
}

/**
 * Capability tags for provider features
 */
function CapabilityTags({
  capabilities,
  compact = false,
}: {
  capabilities: ProviderCapabilities;
  compact?: boolean;
}) {
  const tags: string[] = [];

  if (capabilities.maxDuration > 0) {
    tags.push(`최대 ${capabilities.maxDuration}초`);
  }
  if (capabilities.referenceImages) {
    tags.push("참조 이미지");
  }
  if (capabilities.lipSync) {
    tags.push("립싱크");
  }
  if (capabilities.frameControl) {
    tags.push("프레임 제어");
  }
  if (capabilities.audioSupport) {
    tags.push("오디오");
  }

  if (compact) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-1 mt-1">
      {tags.slice(0, 3).map((tag) => (
        <span
          key={tag}
          className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-white/40"
        >
          {tag}
        </span>
      ))}
      {tags.length > 3 && (
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-white/30">
          +{tags.length - 3}
        </span>
      )}
    </div>
  );
}

/**
 * Single provider option card
 */
function ProviderOption({
  provider,
  health,
  isSelected,
  isRecommended,
  isDisabled,
  compact,
  onClick,
}: {
  provider: ProviderDisplayConfig;
  health: ProviderHealth;
  isSelected: boolean;
  isRecommended: boolean;
  isDisabled: boolean;
  compact: boolean;
  onClick: () => void;
}) {
  const Icon = provider.icon;

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isDisabled}
      className={cn(
        "relative w-full text-left transition-all rounded-xl border",
        compact ? "p-2" : "p-3",
        isSelected
          ? "bg-white/10 border-white/20"
          : "bg-white/[0.02] border-white/5 hover:bg-white/[0.05] hover:border-white/10",
        isDisabled && "opacity-50 cursor-not-allowed"
      )}
    >
      {/* Recommendation badge */}
      {isRecommended && !isSelected && (
        <RecommendationBadge className="absolute -top-2 -right-2" />
      )}

      <div className="flex items-start gap-3">
        {/* Icon */}
        <div
          className={cn(
            "flex-shrink-0 rounded-lg flex items-center justify-center",
            provider.bgClass,
            compact ? "w-8 h-8" : "w-10 h-10"
          )}
        >
          <Icon className={cn(provider.colorClass, compact ? "w-4 h-4" : "w-5 h-5")} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "font-medium",
                  compact ? "text-sm" : "text-sm",
                  isSelected ? "text-white" : "text-white/80"
                )}
              >
                {provider.name}
              </span>
              {isSelected && (
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              )}
            </div>
            <HealthBadge
              status={health.status}
              latencyMs={health.latencyMs}
              compact={compact}
            />
          </div>

          {!compact && (
            <>
              <p className="text-xs text-white/40 mt-0.5">{provider.description}</p>
              <CapabilityTags capabilities={health.capabilities} compact={compact} />
            </>
          )}
        </div>
      </div>
    </button>
  );
}

// =============================================================================
// Main Component
// =============================================================================

/**
 * SmartProviderSelector - Health-aware provider selection
 *
 * @example
 * ```tsx
 * const [provider, setProvider] = useState<ProviderId>("veo");
 *
 * <SmartProviderSelector
 *   value={provider}
 *   onChange={setProvider}
 *   mediaType="video"
 *   minDuration={10}
 *   showRecommendation
 * />
 * ```
 */
export function SmartProviderSelector({
  value,
  onChange,
  mediaType = "all",
  minDuration,
  healthyOnly = false,
  showRecommendation = true,
  compact = false,
  disabled = false,
  className,
}: SmartProviderSelectorProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const {
    providers: healthData,
    isUsable,
    bestVideoProvider,
    bestAudioProvider,
  } = useProviderHealth();

  // Filter providers by media type and capabilities
  const availableProviders = useMemo(() => {
    const allProviders = Object.keys(PROVIDER_CONFIGS) as ProviderId[];

    return allProviders.filter((id) => {
      const health = healthData[id];
      if (!health) return false;

      // Filter by media type
      if (mediaType !== "all" && health.capabilities.mediaType !== mediaType) {
        return false;
      }

      // Filter by health status
      if (healthyOnly && !isUsable(id)) {
        return false;
      }

      // Filter by minimum duration
      if (minDuration && health.capabilities.maxDuration < minDuration) {
        return false;
      }

      return true;
    });
  }, [healthData, mediaType, healthyOnly, minDuration, isUsable]);

  // Determine recommended provider
  const recommendedProvider = useMemo((): ProviderId | null => {
    if (!showRecommendation) return null;

    if (mediaType === "video" || mediaType === "all") {
      return bestVideoProvider;
    }
    if (mediaType === "audio") {
      return bestAudioProvider;
    }

    return availableProviders[0] || null;
  }, [showRecommendation, mediaType, bestVideoProvider, bestAudioProvider, availableProviders]);

  // Handle provider selection
  const handleSelect = useCallback(
    (providerId: ProviderId) => {
      onChange(providerId);
      setIsExpanded(false);
    },
    [onChange]
  );

  // Currently selected provider config
  const selectedConfig = value ? PROVIDER_CONFIGS[value] : null;
  const selectedHealth = value ? healthData[value] : null;

  // Compact dropdown mode
  if (compact) {
    return (
      <div className={cn("relative", className)}>
        {/* Selected / Trigger */}
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          disabled={disabled}
          className={cn(
            "w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg",
            "bg-white/[0.02] border border-white/10 hover:bg-white/[0.05]",
            "transition-colors",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        >
          <div className="flex items-center gap-2">
            {selectedConfig ? (
              <>
                <selectedConfig.icon
                  className={cn("w-4 h-4", selectedConfig.colorClass)}
                />
                <span className="text-sm text-white">{selectedConfig.name}</span>
              </>
            ) : (
              <span className="text-sm text-white/50">Provider 선택</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {selectedHealth && (
              <HealthBadge
                status={selectedHealth.status}
                latencyMs={selectedHealth.latencyMs}
                compact
              />
            )}
            <ChevronDown
              className={cn(
                "w-4 h-4 text-white/40 transition-transform",
                isExpanded && "rotate-180"
              )}
            />
          </div>
        </button>

        {/* Dropdown */}
        {isExpanded && (
          <div className="absolute z-50 top-full left-0 right-0 mt-1 p-1 rounded-lg bg-[#0F0F1A] border border-white/10 shadow-xl">
            {availableProviders.map((id) => {
              const config = PROVIDER_CONFIGS[id];
              const health = healthData[id];
              if (!config || !health) return null;

              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => handleSelect(id)}
                  className={cn(
                    "w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg",
                    "hover:bg-white/5 transition-colors",
                    value === id && "bg-white/10"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <config.icon className={cn("w-4 h-4", config.colorClass)} />
                    <span className="text-sm text-white">{config.name}</span>
                    {id === recommendedProvider && id !== value && (
                      <Sparkles className="w-3 h-3 text-cyan-400" />
                    )}
                  </div>
                  <HealthBadge status={health.status} latencyMs={health.latencyMs} compact />
                </button>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  // Full card grid mode
  return (
    <div className={cn("space-y-2", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <label className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1">
          Provider 선택
        </label>
        {recommendedProvider && (
          <div className="flex items-center gap-1 text-xs text-cyan-400">
            <Zap className="w-3 h-3" />
            <span>추천: {PROVIDER_CONFIGS[recommendedProvider]?.name}</span>
          </div>
        )}
      </div>

      {/* Provider Grid */}
      <div className="grid grid-cols-1 gap-2">
        {availableProviders.map((id) => {
          const config = PROVIDER_CONFIGS[id];
          const health = healthData[id];
          if (!config || !health) return null;

          const isDisabled = disabled || (healthyOnly && !isUsable(id));

          return (
            <ProviderOption
              key={id}
              provider={config}
              health={health}
              isSelected={value === id}
              isRecommended={id === recommendedProvider}
              isDisabled={isDisabled}
              compact={false}
              onClick={() => handleSelect(id)}
            />
          );
        })}
      </div>

      {/* Empty state */}
      {availableProviders.length === 0 && (
        <div className="text-center py-6 text-white/40 text-sm">
          사용 가능한 Provider가 없습니다.
        </div>
      )}
    </div>
  );
}

export default SmartProviderSelector;
