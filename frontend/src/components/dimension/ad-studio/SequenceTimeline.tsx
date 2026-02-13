"use client";

import { useMemo } from "react";
import type { SceneAnalysisResult, EmotionalBeat } from "../ADStudioPanel";

// =============================================================================
// TYPES
// =============================================================================

interface SequenceTimelineProps {
  scenes: SceneAnalysisResult[];
  emotionalArc: EmotionalBeat[];
  continuityScore?: number;
  onSceneClick: (index: number) => void;
}

// =============================================================================
// COMPONENT
// =============================================================================

export default function SequenceTimeline({
  scenes,
  emotionalArc,
  continuityScore,
  onSceneClick,
}: SequenceTimelineProps) {
  // Build SVG path for emotional intensity curve
  const { pathD, maxIntensity } = useMemo(() => {
    if (!emotionalArc || emotionalArc.length === 0) {
      return { pathD: "", maxIntensity: 1 };
    }

    const maxVal = Math.max(...emotionalArc.map((b) => b.intensity), 1);
    const width = scenes.length * 120;
    const height = 48;
    const padding = 10;

    const points = emotionalArc.map((beat, i) => {
      const x = padding + ((beat.scene_number - 1) / Math.max(scenes.length - 1, 1)) * (width - padding * 2);
      const y = height - padding - ((beat.intensity / maxVal) * (height - padding * 2));
      return { x, y };
    });

    if (points.length < 2) return { pathD: "", maxIntensity: maxVal };

    // Smooth curve via cubic bezier
    let d = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
      const prev = points[i - 1];
      const curr = points[i];
      const cpx = (prev.x + curr.x) / 2;
      d += ` C ${cpx} ${prev.y}, ${cpx} ${curr.y}, ${curr.x} ${curr.y}`;
    }

    return { pathD: d, maxIntensity: maxVal };
  }, [emotionalArc, scenes.length]);

  if (scenes.length === 0) return null;

  const svgWidth = scenes.length * 120;
  const continuityPercent = typeof continuityScore === "number"
    ? Math.round(Math.max(0, Math.min(continuityScore, 1)) * 100)
    : null;
  const continuityToneClass =
    continuityPercent === null
      ? ""
      : continuityPercent >= 80
        ? "text-emerald-500"
        : continuityPercent >= 60
          ? "text-amber-500"
          : "text-rose-500";

  return (
    <div className="bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 rounded-2xl p-4 overflow-hidden">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest">
          시퀀스 타임라인
        </span>
        {emotionalArc.length > 0 && (
          <span className="text-[10px] text-amber-500 font-medium">
            감정 강도 커브
          </span>
        )}
        {continuityPercent !== null && (
          <span className={`text-[10px] font-semibold ${continuityToneClass}`}>
            연속성 점수 {continuityPercent}%
          </span>
        )}
      </div>

      {/* Scrollable timeline */}
      <div className="overflow-x-auto pb-2 -mx-1 px-1 custom-scrollbar">
        <div className="relative" style={{ minWidth: `${svgWidth}px`, height: "100px" }}>
          {/* SVG Emotional Curve */}
          {pathD && (
            <svg
              className="absolute inset-0 pointer-events-none"
              viewBox={`0 0 ${svgWidth} 48`}
              preserveAspectRatio="none"
              style={{ width: `${svgWidth}px`, height: "48px" }}
            >
              <defs>
                <linearGradient id="emotionGrad" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="rgb(59, 130, 246)" stopOpacity="0.6" />
                  <stop offset="50%" stopColor="rgb(245, 158, 11)" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="rgb(239, 68, 68)" stopOpacity="0.6" />
                </linearGradient>
              </defs>
              <path
                d={pathD}
                fill="none"
                stroke="url(#emotionGrad)"
                strokeWidth="2"
                strokeLinecap="round"
              />
              {/* Dots on the curve */}
              {emotionalArc.map((beat, i) => {
                const x = 10 + ((beat.scene_number - 1) / Math.max(scenes.length - 1, 1)) * (svgWidth - 20);
                const y = 48 - 10 - ((beat.intensity / maxIntensity) * 28);
                return (
                  <circle
                    key={i}
                    cx={x}
                    cy={y}
                    r="3"
                    fill="rgb(245, 158, 11)"
                    stroke="white"
                    strokeWidth="1"
                    className="opacity-80"
                  />
                );
              })}
            </svg>
          )}

          {/* Scene Blocks */}
          <div className="absolute bottom-0 left-0 right-0 flex">
            {scenes.map((scene, idx) => {
              const beat = emotionalArc.find((b) => b.scene_number === scene.scene_number);
              const transition = scene.sequence_context?.transition_out_setup;

              return (
                <div key={scene.scene_number} className="flex items-end" style={{ width: "120px" }}>
                  <button
                    onClick={() => onSceneClick(idx)}
                    className="flex-1 mx-1 group"
                  >
                    <div className="bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 hover:border-amber-500/40 rounded-lg px-2 py-2 transition-all cursor-pointer">
                      <div className="text-xs font-bold text-amber-600 dark:text-amber-400">
                        S{scene.scene_number}
                      </div>
                      {beat && (
                        <div className="text-[9px] text-slate-500 dark:text-zinc-500 truncate mt-0.5">
                          {beat.emotion}
                        </div>
                      )}
                    </div>
                    {/* Transition label */}
                    {transition && idx < scenes.length - 1 && (
                      <div className="absolute -right-3 top-1/2 -translate-y-1/2 z-10">
                        <span className="text-[8px] text-slate-400 dark:text-zinc-600 bg-white dark:bg-zinc-900 px-1 rounded whitespace-nowrap">
                          {transition.length > 12 ? transition.slice(0, 12) + "..." : transition}
                        </span>
                      </div>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
