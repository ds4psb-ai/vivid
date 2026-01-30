"use client";

/**
 * DisclosureLevelToggle - Progressive Disclosure 3-Level Toggle
 *
 * Phase 2-1: 패널 콘텐츠 복잡도 조절을 위한 토글 컴포넌트
 * - basic: 필수 입력만 (간편 모드)
 * - intermediate: 스타일/거장 선택 추가 (기본값)
 * - advanced: 모든 옵션 표시 (전문가 모드)
 *
 * 2026 Pattern: "Progressive Complexity"
 */

import { useCallback } from "react";
import { Circle, Layers, Sliders } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  type DisclosureLevel,
  DISCLOSURE_LEVELS,
  getDisclosureLevelConfig,
} from "./types";

// =============================================================================
// Types
// =============================================================================

export interface DisclosureLevelToggleProps {
  /** Current disclosure level */
  value: DisclosureLevel;
  /** Callback when level changes */
  onChange: (level: DisclosureLevel) => void;
  /** Use Korean labels (default: true) */
  isKorean?: boolean;
  /** Compact mode for mobile */
  compact?: boolean;
  /** Additional className */
  className?: string;
}

// =============================================================================
// Icon mapping
// =============================================================================

const LEVEL_ICONS: Record<DisclosureLevel, typeof Circle> = {
  basic: Circle,
  intermediate: Layers,
  advanced: Sliders,
};

// =============================================================================
// Component
// =============================================================================

export function DisclosureLevelToggle({
  value,
  onChange,
  isKorean = true,
  compact = false,
  className,
}: DisclosureLevelToggleProps) {
  const handleClick = useCallback(
    (level: DisclosureLevel) => {
      if (level !== value) {
        onChange(level);
      }
    },
    [value, onChange]
  );

  const currentConfig = getDisclosureLevelConfig(value);

  // Compact mode: single dropdown-style button
  if (compact) {
    return (
      <div className={cn("relative group", className)}>
        <button
          className="flex items-center gap-1.5 px-2 py-1 text-xs bg-white/5 hover:bg-white/10 rounded-md transition-colors"
          title={isKorean ? currentConfig.description : currentConfig.descriptionEn}
        >
          {(() => {
            const Icon = LEVEL_ICONS[value];
            return <Icon className="w-3.5 h-3.5 text-white/60" />;
          })()}
          <span className="text-white/70">
            {isKorean ? currentConfig.label : currentConfig.labelEn}
          </span>
        </button>

        {/* Dropdown on hover */}
        <div className="absolute top-full left-0 mt-1 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
          <div className="bg-[var(--surface-2)] border border-white/10 rounded-lg shadow-xl p-1 min-w-[120px]">
            {DISCLOSURE_LEVELS.map((level) => {
              const Icon = LEVEL_ICONS[level.value];
              const isActive = level.value === value;

              return (
                <button
                  key={level.value}
                  onClick={() => handleClick(level.value)}
                  className={cn(
                    "w-full flex items-center gap-2 px-2 py-1.5 rounded text-xs transition-colors",
                    isActive
                      ? "bg-blue-500/20 text-blue-400"
                      : "text-white/60 hover:bg-white/10 hover:text-white/80"
                  )}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{isKorean ? level.label : level.labelEn}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // Full mode: 3-button toggle group
  return (
    <div
      className={cn(
        "flex items-center gap-1 p-1 bg-white/5 rounded-lg",
        className
      )}
    >
      {DISCLOSURE_LEVELS.map((level) => {
        const Icon = LEVEL_ICONS[level.value];
        const isActive = level.value === value;

        return (
          <button
            key={level.value}
            onClick={() => handleClick(level.value)}
            title={isKorean ? level.description : level.descriptionEn}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all",
              isActive
                ? "bg-blue-500 text-white shadow-md"
                : "text-white/60 hover:bg-white/10 hover:text-white/80"
            )}
          >
            <Icon className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">
              {isKorean ? level.label : level.labelEn}
            </span>
          </button>
        );
      })}
    </div>
  );
}

/**
 * Minimal inline toggle for tight spaces
 */
export function DisclosureLevelToggleInline({
  value,
  onChange,
  className,
}: Pick<DisclosureLevelToggleProps, "value" | "onChange" | "className">) {
  // Cycle through levels on click
  const handleCycle = useCallback(() => {
    const currentIndex = DISCLOSURE_LEVELS.findIndex((l) => l.value === value);
    const nextIndex = (currentIndex + 1) % DISCLOSURE_LEVELS.length;
    onChange(DISCLOSURE_LEVELS[nextIndex].value);
  }, [value, onChange]);

  const Icon = LEVEL_ICONS[value];
  const config = getDisclosureLevelConfig(value);

  return (
    <button
      onClick={handleCycle}
      title={`${config.label} - ${config.description}`}
      className={cn(
        "flex items-center gap-1 px-2 py-1 rounded text-xs text-white/60 hover:text-white/80 hover:bg-white/10 transition-colors",
        className
      )}
    >
      <Icon className="w-3.5 h-3.5" />
    </button>
  );
}
