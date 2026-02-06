"use client";

import type { Builder2Scene, AnchorInfo, ParseWarning, SceneRefInfo } from "@/lib/builder2-md-parser";
import { ContentCard } from "../shared";
import { AnchorHint } from "./AnchorHint";

const PROMPT_COLORS: Record<string, string> = {
  nanoBanana: "text-orange-400",
  midjourney: "text-violet-400",
  kling: "text-cyan-400",
  veo: "text-red-400",
};

interface SceneCardProps {
  scene: Builder2Scene;
  copiedStates: Record<string, boolean>;
  completedPrompts: Set<string>;
  onCopy: (key: string, text: string) => void;
  anchors: AnchorInfo[];
  warnings?: ParseWarning[];
}

const WARNING_COLORS: Record<ParseWarning['type'], string> = {
  lazy_pattern: 'text-red-400 bg-red-500/10 border-red-500/20',
  missing_param: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  missing_prompt: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
};

const WARNING_ICONS: Record<ParseWarning['type'], string> = {
  lazy_pattern: 'LAZY',
  missing_param: 'PARAM',
  missing_prompt: 'EMPTY',
};

export function SceneCard({
  scene,
  copiedStates,
  completedPrompts,
  onCopy,
  anchors,
  warnings = [],
}: SceneCardProps) {
  const promptItems = [
    { key: "nanoBanana", label: "NanoBanana", prompt: scene.imagePrompts.nanoBanana },
    { key: "midjourney", label: "Midjourney", prompt: scene.imagePrompts.midjourney },
    { key: "kling", label: "Kling", prompt: scene.motionPrompts.kling },
    { key: "veo", label: "Veo", prompt: scene.motionPrompts.veo },
  ].filter(item => item.prompt);

  // Determine face type from refInfo or fall back to anchorRefs
  const faceType: SceneRefInfo['face'] | undefined = scene.refInfo?.face;

  // Get relevant anchor refs for this scene
  // refInfo takes priority, then fall back to anchorRefs
  const relevantAnchors = (() => {
    if (scene.isAnchor) return [];
    if (faceType === 'NONE') return [];
    if (faceType === 'BOTH') return anchors.filter(a => a.key === 'MALE' || a.key === 'FEMALE');
    if (faceType === 'MALE_ANCHOR') return anchors.filter(a => a.key === 'MALE');
    if (faceType === 'FEMALE_ANCHOR') return anchors.filter(a => a.key === 'FEMALE');
    // Legacy fallback: use anchorRefs
    if (scene.anchorRefs && scene.anchorRefs.length > 0) {
      return anchors.filter(a => scene.anchorRefs.includes(a.key));
    }
    return [];
  })();

  return (
    <ContentCard>
      <div className="flex items-center gap-3 mb-4">
        <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${scene.isAnchor
          ? "bg-amber-500/20 text-amber-400"
          : "bg-[var(--color-brand-primary)]/15 text-[var(--color-brand-primary)]"
          }`}>
          {scene.sceneNum}
        </span>
        <div>
          <h3 className="text-[var(--fg-0)] font-bold">{scene.title || `Scene ${scene.sceneNum}`}</h3>
          {scene.beatTimestamp && (
            <p className="text-[var(--fg-muted)] text-xs">{scene.beatTimestamp}</p>
          )}
        </div>
        <div className="ml-auto flex items-center gap-2">
          {warnings.length > 0 && (
            <span className="px-2 py-1 rounded text-xs font-bold bg-yellow-500/20 text-yellow-700 dark:text-yellow-300">
              {warnings.length} warning{warnings.length > 1 ? 's' : ''}
            </span>
          )}
          {scene.isAnchor && (
            <span className="px-2 py-1 rounded text-xs font-bold bg-amber-500/20 text-amber-400">
              ANCHOR
            </span>
          )}
        </div>
      </div>

      {/* 앵커 씬 특별 가이드 */}
      {scene.isAnchor && (
        <div className="mb-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
          <div className="flex items-center gap-2 mb-1">
            <p className="text-xs font-bold text-amber-700 dark:text-amber-200">앵커</p>
            <AnchorHint />
          </div>
          <p className="text-xs text-amber-800 dark:text-amber-100">
            <code className="ml-1 rounded bg-amber-200/40 dark:bg-amber-900/40 px-2 py-1 font-mono text-emerald-700 dark:text-emerald-300">
              anchor_{scene.refInfo?.face === "FEMALE_ANCHOR" ? "female" : "male"}.jpg
            </code>
            저장
          </p>
        </div>
      )}

      {/* 이미지 첨부 가이드 (비앵커 씬) */}
      {!scene.isAnchor && (
        <div className="mb-4 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
          <p className="text-xs font-bold text-blue-700 dark:text-blue-200 mb-2">첨부</p>

          {/* Image 1: COMPOSITION (씬 프레임) */}
          <div className="mb-2">
            <div className="flex items-start gap-2">
              <span className="text-xs text-blue-700 dark:text-blue-300 shrink-0">Image 1:</span>
              <code className="px-2 py-1 rounded bg-blue-100 dark:bg-blue-900/40 text-blue-900 dark:text-blue-100 font-mono text-xs">
                {scene.frameFile}
              </code>
            </div>
          </div>

          {/* Image 2: CHARACTER FACE (앵커 이미지들) */}
          {relevantAnchors.length > 0 && (
            <div className="mb-2">
              <div className="flex items-start gap-2">
                <span className="text-xs text-blue-700 dark:text-blue-300 shrink-0">Image 2:</span>
                <div className="flex flex-wrap gap-1">
                  {relevantAnchors.map((anchor) => (
                    <code
                      key={anchor.key}
                      className="px-2 py-1 rounded bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-200 font-mono text-xs"
                    >
                      anchor_{anchor.key.toLowerCase()}.jpg
                    </code>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="mb-4 space-y-1">
          {warnings.map((w, i) => (
            <div
              key={i}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs ${WARNING_COLORS[w.type]}`}
            >
              <span className="font-mono font-bold text-[10px] px-1.5 py-0.5 rounded bg-[var(--surface-3)]">
                {WARNING_ICONS[w.type]}
              </span>
              <span>{w.message}</span>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        {promptItems.map((item) => {
          const copyKey = `${scene.sceneNum}-${item.key}`;
          const isCopied = copiedStates[copyKey];
          const isCompleted = completedPrompts.has(copyKey);

          return (
            <div key={item.key} className={`space-y-2 ${isCompleted ? 'opacity-50' : ''}`}>
              <div className="flex items-center justify-between">
                <span className={`text-xs font-bold ${PROMPT_COLORS[item.key]}`}>
                  {isCompleted && <span className="mr-1">✓</span>}
                  {item.label}
                </span>
                <button
                  onClick={() => onCopy(copyKey, item.prompt)}
                  className={`px-2 py-1 rounded text-xs font-bold transition-all ${isCopied
                    ? "bg-emerald-500 text-white"
                    : isCompleted
                      ? "bg-[var(--surface-3)] text-[var(--fg-muted)] hover:opacity-90"
                      : "bg-[var(--fg-0)] text-[var(--bg-0)] hover:opacity-90"
                    }`}
                >
                  {isCopied ? "✓" : isCompleted ? "재복사" : "복사"}
                </button>
              </div>
              <div className={`p-2 rounded-lg bg-[var(--surface-2)] border max-h-20 overflow-y-auto ${isCompleted ? 'border-emerald-500/30' : 'border-[var(--border-muted)]'}`}>
                <p className="text-[var(--fg-muted)] text-xs font-mono whitespace-pre-wrap break-all">
                  {item.prompt.slice(0, 200)}{item.prompt.length > 200 ? "..." : ""}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </ContentCard>
  );
}
