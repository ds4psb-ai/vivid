"use client";

import { SceneSnapshot } from "@/types/agent";
import { formatDateTime } from "@/lib/formatters";

interface SceneCardProps {
  scene: SceneSnapshot;
  variant?: "compact" | "detail";
  isSelected?: boolean;
  onSelect?: (sceneId: string) => void;
}

const extractStyleHighlights = (style?: Record<string, unknown>) => {
  if (!style) return [];
  return Object.entries(style)
    .filter(([, value]) => typeof value === "string" || typeof value === "number")
    .slice(0, 3)
    .map(([key, value]) => `${key}: ${value}`);
};

export default function SceneCard({
  scene,
  variant = "compact",
  isSelected = false,
  onSelect,
}: SceneCardProps) {
  const isCompact = variant === "compact";
  const timestamp = formatDateTime(scene.updatedAt);
  const highlights = extractStyleHighlights(scene.style);
  const containerClasses = `w-full rounded-2xl border px-4 py-3 text-left transition-all ${
    isSelected
      ? "border-sky-400/60 bg-sky-500/10 shadow-[0_0_30px_rgba(56,189,248,0.2)]"
      : "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10"
  }`;

  const content = (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2 text-xs text-slate-500">
        <span className="font-mono">#{scene.sceneId.slice(0, 8)}</span>
        {timestamp && <span>{timestamp}</span>}
      </div>
      <div className="space-y-1">
        <div className={`${isCompact ? "text-sm" : "text-lg"} font-semibold text-slate-100`}>
          {scene.title || "Untitled Scene"}
        </div>
        {scene.summary && (
          <div className={`${isCompact ? "text-xs" : "text-sm"} text-slate-300`}>
            {scene.summary}
          </div>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-slate-500">
        {scene.status && (
          <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1">{scene.status}</span>
        )}
        {scene.source && (
          <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1">
            {scene.source}
          </span>
        )}
      </div>
      {highlights.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {highlights.map((item) => (
            <span
              key={item}
              className="rounded-full border border-white/10 bg-slate-900/40 px-2 py-1 text-[11px] text-slate-300"
            >
              {item}
            </span>
          ))}
        </div>
      )}
    </div>
  );

  if (onSelect) {
    return (
      <button type="button" onClick={() => onSelect(scene.sceneId)} className={containerClasses}>
        {content}
      </button>
    );
  }

  return <div className={containerClasses}>{content}</div>;
}
