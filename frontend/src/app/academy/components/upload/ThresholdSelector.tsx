"use client";

import type { ThresholdMode } from "../../api/sceneDetect";

interface ThresholdSelectorProps {
  thresholdMode: ThresholdMode;
  onModeChange: (mode: ThresholdMode) => void;
}

export function ThresholdSelector({ thresholdMode, onModeChange }: ThresholdSelectorProps) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-3">
        <span className="material-symbols-outlined text-[var(--color-brand-primary)] text-sm">tune</span>
        <span className="text-[var(--fg-muted)] text-sm font-medium">모드</span>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => onModeChange("standard")}
          className={`relative p-4 rounded-xl border-2 transition-all text-left group ${
            thresholdMode === "standard"
              ? "border-emerald-500 bg-emerald-500/10"
              : "border-[var(--border-muted)] bg-[var(--surface-2)] hover:border-emerald-500/30"
          }`}
        >
          {thresholdMode === "standard" && (
            <div className="absolute top-2 right-2">
              <span className="material-symbols-outlined text-emerald-400 text-lg">check_circle</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <span className="text-xl">🎯</span>
            <span className={`font-bold ${thresholdMode === "standard" ? "text-emerald-600 dark:text-emerald-400" : "text-[var(--fg-0)]"}`}>
              표준
            </span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 font-medium">기본</span>
          </div>
        </button>

        <button
          onClick={() => onModeChange("precise")}
          className={`relative p-4 rounded-xl border-2 transition-all text-left group ${
            thresholdMode === "precise"
              ? "border-[var(--color-brand-primary)] bg-[var(--color-brand-primary)]/10"
              : "border-[var(--border-muted)] bg-[var(--surface-2)] hover:border-[var(--color-brand-primary)]/30"
          }`}
        >
          {thresholdMode === "precise" && (
            <div className="absolute top-2 right-2">
              <span className="material-symbols-outlined text-[var(--color-brand-primary)] text-lg">check_circle</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <span className="text-xl">⚡</span>
            <span className={`font-bold ${thresholdMode === "precise" ? "text-[var(--color-brand-primary)]" : "text-[var(--fg-0)]"}`}>
              정밀
            </span>
          </div>
        </button>
      </div>
    </div>
  );
}
