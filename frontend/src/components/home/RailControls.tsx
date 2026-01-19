"use client";

import { Pause, Play, ChevronLeft, ChevronRight } from "lucide-react";

interface RailControlsProps {
  onPrev: () => void;
  onNext: () => void;
  onToggleAuto: () => void;
  isAutoRotating: boolean;
  disablePrev?: boolean;
  disableNext?: boolean;
  labels?: {
    prev: string;
    next: string;
    pause: string;
    play: string;
  };
}

export function RailControls({
  onPrev,
  onNext,
  onToggleAuto,
  isAutoRotating,
  disablePrev = false,
  disableNext = false,
  labels,
}: RailControlsProps) {
  const defaultLabels = {
    prev: "Previous items",
    next: "Next items",
    pause: "Pause auto-rotate",
    play: "Play auto-rotate",
  };
  const copy = labels ?? defaultLabels;

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={onPrev}
        disabled={disablePrev}
        className="h-8 w-8 rounded-full border border-[var(--border-muted)] text-[var(--fg-muted)] hover:text-[var(--fg-0)] hover:border-[var(--border-strong)] disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
        aria-label={copy.prev}
      >
        <ChevronLeft className="h-4 w-4" />
      </button>
      <button
        type="button"
        onClick={onToggleAuto}
        aria-pressed={isAutoRotating}
        className="h-8 w-8 rounded-full border border-[var(--border-muted)] text-[var(--fg-muted)] hover:text-[var(--fg-0)] hover:border-[var(--border-strong)] flex items-center justify-center transition-colors"
        aria-label={isAutoRotating ? copy.pause : copy.play}
      >
        {isAutoRotating ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
      </button>
      <button
        type="button"
        onClick={onNext}
        disabled={disableNext}
        className="h-8 w-8 rounded-full border border-[var(--border-muted)] text-[var(--fg-muted)] hover:text-[var(--fg-0)] hover:border-[var(--border-strong)] disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
        aria-label={copy.next}
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
}
