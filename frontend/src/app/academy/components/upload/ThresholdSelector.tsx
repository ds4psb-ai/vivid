"use client";

import type { ThresholdMode } from "../../api/sceneDetect";

interface ThresholdSelectorProps {
  thresholdMode: ThresholdMode;
  onModeChange: (mode: ThresholdMode) => void;
}

export function ThresholdSelector({
  thresholdMode,
  onModeChange,
}: ThresholdSelectorProps) {
  return (
    <div className="mb-4">
      <div className="grid grid-cols-2 gap-2 rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-1">
        <button
          type="button"
          onClick={() => onModeChange("standard")}
          className={`min-h-11 rounded-lg px-3 text-sm font-medium transition-colors ${
            thresholdMode === "standard"
              ? "bg-[var(--color-brand-primary)] text-white"
              : "text-[var(--fg-muted)] hover:text-[var(--fg-0)]"
          }`}
        >
          표준
        </button>
        <button
          type="button"
          onClick={() => onModeChange("precise")}
          className={`min-h-11 rounded-lg px-3 text-sm font-medium transition-colors ${
            thresholdMode === "precise"
              ? "bg-[var(--color-brand-primary)] text-white"
              : "text-[var(--fg-muted)] hover:text-[var(--fg-0)]"
          }`}
        >
          정밀
        </button>
      </div>
    </div>
  );
}
