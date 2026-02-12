"use client";

import { ArrowDown } from "lucide-react";
import type { SceneAnalysisResult } from "../ADStudioPanel";

// =============================================================================
// TYPES
// =============================================================================

interface TransitionConnectorProps {
  fromScene: SceneAnalysisResult;
  toScene: SceneAnalysisResult;
}

// =============================================================================
// COMPONENT
// =============================================================================

export default function TransitionConnector({
  fromScene,
  toScene,
}: TransitionConnectorProps) {
  const transitionLabel =
    toScene.sequence_context?.transition_in ||
    fromScene.sequence_context?.transition_out_setup;

  return (
    <div className="flex items-center justify-center py-1">
      <div className="flex items-center gap-2">
        <div className="w-px h-4 bg-slate-200 dark:bg-white/10" />
        <ArrowDown className="w-3.5 h-3.5 text-slate-400 dark:text-zinc-600" />
        {transitionLabel && (
          <span className="text-[10px] text-slate-400 dark:text-zinc-600 font-medium px-2 py-0.5 bg-slate-50 dark:bg-white/[0.02] rounded-full border border-slate-200 dark:border-white/5">
            {transitionLabel}
          </span>
        )}
        <div className="w-px h-4 bg-slate-200 dark:bg-white/10" />
      </div>
    </div>
  );
}
