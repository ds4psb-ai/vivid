"use client";

import React, { useEffect, useRef, useCallback, useState } from "react";
import {
  useFrameExtractor,
  parseTimestampToSeconds,
  formatSecondsToTimestamp,
} from "../../hooks/useFrameExtractor";

interface SceneTimelineProps {
  file: File;
  timestamps: string[];
  videoDuration: number;
  currentTime: number;
  onTimestampsChange: (ts: string[]) => void;
  onSeek: (seconds: number) => void;
}

function SceneTimelineInner({
  file,
  timestamps,
  videoDuration,
  currentTime,
  onTimestampsChange,
  onSeek,
}: SceneTimelineProps) {
  const { frames, isExtracting, extractionError, extractAll, updateSingleFrame, removeFrame, insertFrame } =
    useFrameExtractor();
  const scrollRef = useRef<HTMLDivElement>(null);
  const activeRef = useRef<HTMLDivElement>(null);
  const debounceTimers = useRef<Map<number, ReturnType<typeof setTimeout>>>(new Map());
  const [pendingExtracts, setPendingExtracts] = useState<Set<number>>(new Set());
  const skipNextExtractRef = useRef(false);

  // Extract all frames when timestamps change (skip if local +/- change)
  useEffect(() => {
    if (file && timestamps.length > 0) {
      if (skipNextExtractRef.current) {
        skipNextExtractRef.current = false;
        return;
      }
      extractAll(file, timestamps);
    }
  }, [file, timestamps, extractAll]);

  // Find active scene index based on currentTime
  const activeIndex = (() => {
    if (timestamps.length === 0) return -1;
    const seconds = timestamps.map(parseTimestampToSeconds);
    for (let i = seconds.length - 1; i >= 0; i--) {
      if (currentTime >= seconds[i] - 0.05) return i;
    }
    return 0;
  })();

  // Auto-scroll to active card
  useEffect(() => {
    if (activeRef.current) {
      activeRef.current.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
    }
  }, [activeIndex]);

  const adjustTimestamp = useCallback(
    (index: number, delta: number) => {
      const currentSec = parseTimestampToSeconds(timestamps[index]);
      let newSec = Math.round((currentSec + delta) * 100) / 100;

      // Clamp: not below 0
      newSec = Math.max(0, newSec);
      // Clamp: not above duration
      if (videoDuration > 0) newSec = Math.min(videoDuration, newSec);

      // Prevent overlap with adjacent scenes (min 0.1s gap)
      if (index > 0) {
        const prevSec = parseTimestampToSeconds(timestamps[index - 1]);
        newSec = Math.max(prevSec + 0.1, newSec);
      }
      if (index < timestamps.length - 1) {
        const nextSec = parseTimestampToSeconds(timestamps[index + 1]);
        newSec = Math.min(nextSec - 0.1, newSec);
      }

      const newTs = formatSecondsToTimestamp(newSec);
      const updated = [...timestamps];
      updated[index] = newTs;

      skipNextExtractRef.current = true;
      onTimestampsChange(updated);

      // Mark pending extract
      setPendingExtracts((prev) => new Set(prev).add(index));

      // Debounce single-frame re-extraction
      const existing = debounceTimers.current.get(index);
      if (existing) clearTimeout(existing);
      debounceTimers.current.set(
        index,
        setTimeout(async () => {
          await updateSingleFrame(file, index, newTs);
          setPendingExtracts((prev) => {
            const next = new Set(prev);
            next.delete(index);
            return next;
          });
          debounceTimers.current.delete(index);
        }, 300),
      );
    },
    [timestamps, videoDuration, onTimestampsChange, file, updateSingleFrame],
  );

  const deleteScene = useCallback(
    (index: number) => {
      if (timestamps.length <= 1) return;
      const updated = timestamps.filter((_, i) => i !== index);
      skipNextExtractRef.current = true;
      onTimestampsChange(updated);
      removeFrame(index);
    },
    [timestamps, onTimestampsChange, removeFrame],
  );

  const addScene = useCallback(() => {
    const newTs = formatSecondsToTimestamp(currentTime);
    const newSec = currentTime;

    // Check for duplicate (within 0.05s)
    const hasDuplicate = timestamps.some((ts) => {
      const sec = parseTimestampToSeconds(ts);
      return Math.abs(sec - newSec) < 0.05;
    });
    if (hasDuplicate) return;

    // Sorted insert
    const seconds = timestamps.map(parseTimestampToSeconds);
    let insertIdx = seconds.findIndex((s) => s > newSec);
    if (insertIdx === -1) insertIdx = timestamps.length;

    const updated = [...timestamps];
    updated.splice(insertIdx, 0, newTs);
    skipNextExtractRef.current = true;
    onTimestampsChange(updated);
    insertFrame(file, insertIdx, newTs);
  }, [timestamps, currentTime, onTimestampsChange, file, insertFrame]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-[var(--fg-muted)] font-medium">타임라인</p>
        <div className="flex items-center gap-2">
          {extractionError && (
            <button
              onClick={() => extractAll(file, timestamps)}
              className="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-700 dark:text-amber-300 text-xs font-medium hover:bg-amber-500/20 transition-all flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-sm">refresh</span>
              재시도
            </button>
          )}
          <button
            onClick={addScene}
            className="w-8 h-8 rounded-lg bg-[var(--color-brand-primary)] text-white hover:opacity-90 transition-all flex items-center justify-center"
            title="씬 추가"
            aria-label="씬 추가"
          >
            <span className="material-symbols-outlined text-sm">add</span>
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent"
      >
        {timestamps.map((ts, i) => {
          const isActive = i === activeIndex;
          const frame = frames[i];
          const isPending = pendingExtracts.has(i);
          const showSkeleton = !extractionError && (isExtracting || isPending || !frame);
          const showError = extractionError && !frame;

          return (
            <div
              key={`${i}-${ts}`}
              ref={isActive ? activeRef : undefined}
              className={`flex-shrink-0 w-[260px] rounded-xl overflow-hidden border transition-all cursor-pointer ${
                isActive
                  ? "border-purple-500 ring-2 ring-purple-500/40 bg-purple-500/10"
                  : "border-white/10 bg-white/5 hover:border-white/20"
              }`}
              onClick={() => onSeek(parseTimestampToSeconds(ts))}
            >
              {/* Thumbnail */}
              <div className="relative w-full aspect-video bg-black/50">
                {showError ? (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-800/50 gap-1">
                    <span className="material-symbols-outlined text-gray-500 text-sm">broken_image</span>
                    <span className="text-[9px] text-gray-500">로드 실패</span>
                  </div>
                ) : showSkeleton ? (
                  <div className="absolute inset-0 flex items-center justify-center bg-gray-800/50">
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-purple-400 border-t-transparent" />
                  </div>
                ) : (
                  <img
                    src={frame.thumbnailUrl}
                    alt={`Scene ${i + 1}`}
                    className="w-full h-full object-cover"
                  />
                )}
                {/* Scene number badge */}
                <div className="absolute top-1 left-1 px-1.5 py-0.5 rounded bg-black/60 text-[10px] text-white font-medium">
                  {i + 1}
                </div>
              </div>

              {/* Info + controls */}
              <div className="p-2 space-y-1.5">
                <p className="text-center text-xs font-mono text-gray-300">{ts}</p>
                <div className="flex items-center justify-center gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      adjustTimestamp(i, -0.1);
                    }}
                    className="w-7 h-7 rounded-md bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-all flex items-center justify-center text-xs font-bold"
                    title="-0.1s"
                  >
                    -
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      adjustTimestamp(i, 0.1);
                    }}
                    className="w-7 h-7 rounded-md bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-all flex items-center justify-center text-xs font-bold"
                    title="+0.1s"
                  >
                    +
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteScene(i);
                    }}
                    disabled={timestamps.length <= 1}
                    className={`w-7 h-7 rounded-md flex items-center justify-center transition-all ${
                      timestamps.length <= 1
                        ? "bg-white/5 text-gray-600 cursor-not-allowed"
                        : "bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300"
                    }`}
                    title="삭제"
                  >
                    <span className="material-symbols-outlined text-sm">close</span>
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export const SceneTimeline = React.memo(SceneTimelineInner);
