"use client";

import { useState, useCallback } from "react";
import { useResultExport } from "../DimensionPanelLayout";
import { ChevronDown, Copy, Check } from "lucide-react";
import type { SceneAnalysisResult, TechniqueTag } from "../ADStudioPanel";

// =============================================================================
// TECHNIQUE BADGE COLORS
// =============================================================================

const TECHNIQUE_COLORS: Record<string, string> = {
  composition: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
  camera_movement: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
  camera_angle: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
  lighting: "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/20",
  color: "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20",
  editing_rhythm: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20",
};

const TECHNIQUE_LABELS: Record<string, string> = {
  composition: "구도",
  camera_movement: "카메라 무브",
  camera_angle: "카메라 앵글",
  lighting: "조명",
  color: "색감",
  editing_rhythm: "편집 리듬",
};

// =============================================================================
// COMPONENT
// =============================================================================

interface SceneCardProps {
  scene: SceneAnalysisResult;
  index: number;
}

export default function SceneCard({ scene, index }: SceneCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [copiedEngine, setCopiedEngine] = useState<string | null>(null);
  const { copyToClipboard } = useResultExport();

  const handleCopyPrompt = useCallback((engine: string, prompt: string) => {
    copyToClipboard(prompt);
    setCopiedEngine(engine);
    setTimeout(() => setCopiedEngine(null), 2000);
  }, [copyToClipboard]);

  const techniques = scene.techniques;
  const allTags: { category: string; tag: TechniqueTag }[] = [];
  for (const [category, tags] of Object.entries(techniques)) {
    if (Array.isArray(tags)) {
      for (const tag of tags) {
        allTags.push({ category, tag });
      }
    }
  }

  return (
    <div className="bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 rounded-2xl overflow-hidden transition-all hover:border-amber-500/30 dark:hover:border-amber-500/20">
      {/* Scene Header */}
      <div className="px-5 py-4 flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center text-sm font-bold">
              {scene.scene_number}
            </span>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white/90 truncate">
              Scene {scene.scene_number}
            </h3>
          </div>
          <p className="text-sm text-slate-600 dark:text-zinc-400 leading-relaxed">
            {scene.description}
          </p>
          {scene.description_en && (
            <p className="text-xs text-slate-400 dark:text-zinc-500 mt-1 italic">
              {scene.description_en}
            </p>
          )}
        </div>
      </div>

      {/* Technique Tags */}
      {allTags.length > 0 && (
        <div className="px-5 pb-3 flex flex-wrap gap-1.5">
          {allTags.map(({ category, tag }) => (
            <span
              key={tag.technique_id}
              className={`inline-flex items-center px-2 py-0.5 text-[10px] font-medium rounded-md border ${
                TECHNIQUE_COLORS[category] || "bg-slate-100 text-slate-600 border-slate-200"
              }`}
              title={`${TECHNIQUE_LABELS[category] || category}: ${tag.description_ko}`}
            >
              {tag.name_ko}
            </span>
          ))}
        </div>
      )}

      {/* Prompt Copy Buttons */}
      <div className="px-5 pb-4 grid grid-cols-2 gap-2">
        {scene.prompts.kling_3_0 && (
          <button
            onClick={() => handleCopyPrompt("kling", scene.prompts.kling_3_0)}
            className="flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 hover:bg-amber-500/20 transition-colors border border-amber-500/20"
          >
            {copiedEngine === "kling" ? (
              <><Check className="w-3.5 h-3.5" /> 복사됨!</>
            ) : (
              <><Copy className="w-3.5 h-3.5" /> Kling 3.0</>
            )}
          </button>
        )}
        {scene.prompts.seedance_2_0 && (
          <button
            onClick={() => handleCopyPrompt("seedance", scene.prompts.seedance_2_0)}
            className="flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg bg-violet-500/10 text-violet-600 dark:text-violet-400 hover:bg-violet-500/20 transition-colors border border-violet-500/20"
          >
            {copiedEngine === "seedance" ? (
              <><Check className="w-3.5 h-3.5" /> 복사됨!</>
            ) : (
              <><Copy className="w-3.5 h-3.5" /> Seedance 2.0</>
            )}
          </button>
        )}
      </div>

      {/* Expandable Sequence Context */}
      <div className="border-t border-slate-100 dark:border-white/5">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full px-5 py-2.5 flex items-center justify-between text-xs text-slate-500 dark:text-zinc-500 hover:text-slate-700 dark:hover:text-zinc-300 transition-colors"
        >
          <span>시퀀스 컨텍스트</span>
          <ChevronDown
            className={`w-3.5 h-3.5 transition-transform ${expanded ? "rotate-180" : ""}`}
          />
        </button>

        {expanded && (
          <div className="px-5 pb-4 space-y-2 animate-in fade-in slide-in-from-top-1 duration-200">
            {scene.sequence_context.transition_in && (
              <ContextRow label="전환 IN" value={scene.sequence_context.transition_in} />
            )}
            <ContextRow label="감정 포지션" value={scene.sequence_context.emotional_position} />
            <ContextRow label="카메라 거리" value={scene.sequence_context.camera_distance_flow} />
            {scene.sequence_context.transition_out_setup && (
              <ContextRow label="전환 OUT" value={scene.sequence_context.transition_out_setup} />
            )}
            {scene.sequence_context.previous_exit && (
              <ContextRow label="이전 장면 종료" value={scene.sequence_context.previous_exit} />
            )}

            {/* Full Prompt Preview */}
            <div className="mt-3 space-y-2">
              {scene.prompts.kling_3_0 && (
                <div className="p-3 bg-amber-500/5 rounded-lg border border-amber-500/10">
                  <p className="text-[10px] font-bold text-amber-500 uppercase tracking-widest mb-1">
                    Kling 3.0 <span className="text-amber-500/50">({scene.prompts.kling_3_0.split(' ').length}w)</span>
                  </p>
                  <p className="text-xs text-slate-600 dark:text-zinc-400 leading-relaxed whitespace-pre-wrap">{scene.prompts.kling_3_0}</p>
                </div>
              )}
              {scene.prompts.seedance_2_0 && (
                <div className="p-3 bg-violet-500/5 rounded-lg border border-violet-500/10">
                  <p className="text-[10px] font-bold text-violet-500 uppercase tracking-widest mb-1">
                    Seedance 2.0 <span className="text-violet-500/50">({scene.prompts.seedance_2_0.split(' ').length}w)</span>
                  </p>
                  <p className="text-xs text-slate-600 dark:text-zinc-400 leading-relaxed whitespace-pre-wrap">{scene.prompts.seedance_2_0}</p>
                </div>
              )}
            </div>

            {/* Continuity Anchors */}
            {scene.continuity_anchors && (
              <div className="mt-2 p-2 bg-slate-500/5 rounded-lg">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">연속성 앵커</p>
                {scene.continuity_anchors.character && (
                  <p className="text-xs text-slate-500">{scene.continuity_anchors.character}</p>
                )}
                {scene.continuity_anchors.style && (
                  <p className="text-xs text-slate-400 italic">{scene.continuity_anchors.style}</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// HELPER
// =============================================================================

function ContextRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start gap-2">
      <span className="flex-shrink-0 text-[10px] font-bold text-slate-400 dark:text-zinc-600 uppercase tracking-wider w-20">
        {label}
      </span>
      <span className="text-xs text-slate-600 dark:text-zinc-400">{value}</span>
    </div>
  );
}
