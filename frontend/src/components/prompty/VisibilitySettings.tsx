"use client";

import { useState } from "react";

type Visibility = "private" | "prompts-only" | "full";

interface VisibilitySettingsProps {
  value: Visibility;
  onChange: (value: Visibility) => void;
  disabled?: boolean;
}

const VISIBILITY_OPTIONS = [
  {
    value: "private" as const,
    label: "비공개",
    description: "나만 볼 수 있음",
    icon: "🔒",
  },
  {
    value: "prompts-only" as const,
    label: "프롬프트 비공개",
    description: "결과물/점수만 공개, 프롬프트는 Fork 시 공개",
    icon: "👀",
  },
  {
    value: "full" as const,
    label: "전체 공개",
    description: "모든 것 공개",
    icon: "🌍",
  },
];

/**
 * VisibilitySettings - 3-level visibility selector
 *
 * - private: only owner can see
 * - prompts-only: results/scores public, prompts visible after fork
 * - full: everything public
 */
export function VisibilitySettings({
  value,
  onChange,
  disabled = false,
}: VisibilitySettingsProps) {
  return (
    <div className="space-y-3">
      <label className="text-sm font-medium">공개 범위</label>
      <div className="space-y-2">
        {VISIBILITY_OPTIONS.map((option) => (
          <label
            key={option.value}
            className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition ${
              value === option.value
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50"
            } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
          >
            <input
              type="radio"
              name="visibility"
              value={option.value}
              checked={value === option.value}
              onChange={() => !disabled && onChange(option.value)}
              disabled={disabled}
              className="mt-1"
            />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span>{option.icon}</span>
                <span className="font-medium">{option.label}</span>
              </div>
              <p className="text-sm text-muted-foreground mt-0.5">
                {option.description}
              </p>
            </div>
          </label>
        ))}
      </div>
    </div>
  );
}

/**
 * Compact visibility badge for display
 */
export function VisibilityBadge({ visibility }: { visibility: Visibility }) {
  const option = VISIBILITY_OPTIONS.find((o) => o.value === visibility);
  if (!option || visibility === "private") return null;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${
        visibility === "full"
          ? "bg-blue-500/10 text-blue-500"
          : "bg-gray-500/10 text-gray-500"
      }`}
    >
      <span>{option.icon}</span>
      <span>{option.label}</span>
    </span>
  );
}

/**
 * Quick toggle for visibility (inline use)
 */
export function VisibilityToggle({
  value,
  onChange,
  disabled = false,
}: VisibilitySettingsProps) {
  const [isOpen, setIsOpen] = useState(false);
  const currentOption = VISIBILITY_OPTIONS.find((o) => o.value === value);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm transition ${
          disabled
            ? "opacity-50 cursor-not-allowed"
            : "hover:border-primary/50 cursor-pointer"
        }`}
      >
        <span>{currentOption?.icon}</span>
        <span>{currentOption?.label}</span>
        <span className="text-muted-foreground">▾</span>
      </button>

      {isOpen && !disabled && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full left-0 mt-1 w-64 bg-card border border-border rounded-lg shadow-lg z-20">
            {VISIBILITY_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => {
                  onChange(option.value);
                  setIsOpen(false);
                }}
                className={`w-full flex items-start gap-3 p-3 text-left hover:bg-accent transition ${
                  value === option.value ? "bg-primary/5" : ""
                }`}
              >
                <span className="text-lg">{option.icon}</span>
                <div>
                  <p className="font-medium text-sm">{option.label}</p>
                  <p className="text-xs text-muted-foreground">
                    {option.description}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default VisibilitySettings;
