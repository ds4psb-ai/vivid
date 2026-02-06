"use client";

import type {
  Builder2Scene,
  AnchorInfo,
  ParseWarning,
  SceneRefInfo,
} from "@/lib/builder2-md-parser";
import { ContentCard } from "../shared";
import { AnchorHint } from "./AnchorHint";

const PROMPT_COLORS: Record<string, string> = {
  nanoBanana: "text-orange-500",
  midjourney: "text-violet-500",
  kling: "text-cyan-500",
  veo: "text-red-500",
};

interface SceneCardProps {
  scene: Builder2Scene;
  copiedStates: Record<string, boolean>;
  completedPrompts: Set<string>;
  onCopy: (key: string, text: string) => void;
  anchors: AnchorInfo[];
  warnings?: ParseWarning[];
}

const WARNING_COLORS: Record<ParseWarning["type"], string> = {
  lazy_pattern: "text-red-700 dark:text-red-300 bg-red-500/10 border-red-500/25",
  missing_param: "text-yellow-700 dark:text-yellow-200 bg-yellow-500/10 border-yellow-500/25",
  missing_prompt: "text-orange-700 dark:text-orange-200 bg-orange-500/10 border-orange-500/25",
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
  ].filter((item) => item.prompt);

  const faceType: SceneRefInfo["face"] | undefined = scene.refInfo?.face;

  const relevantAnchors = (() => {
    if (scene.isAnchor) return [];
    if (faceType === "NONE") return [];
    if (faceType === "BOTH") {
      return anchors.filter((a) => a.key === "MALE" || a.key === "FEMALE");
    }
    if (faceType === "MALE_ANCHOR") return anchors.filter((a) => a.key === "MALE");
    if (faceType === "FEMALE_ANCHOR") return anchors.filter((a) => a.key === "FEMALE");
    if (scene.anchorRefs && scene.anchorRefs.length > 0) {
      return anchors.filter((a) => scene.anchorRefs.includes(a.key));
    }
    return [];
  })();

  const attachmentNames = scene.isAnchor
    ? [
        `anchor_${
          scene.refInfo?.face === "FEMALE_ANCHOR" ? "female" : "male"
        }.jpg`,
      ]
    : [
        scene.frameFile,
        ...relevantAnchors.map((anchor) => `anchor_${anchor.key.toLowerCase()}.jpg`),
      ];

  return (
    <ContentCard>
      <div className="mb-3 flex items-start gap-3">
        <span
          className={`inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold ${
            scene.isAnchor
              ? "bg-amber-500/20 text-amber-700 dark:text-amber-300"
              : "bg-[var(--color-brand-primary)]/12 text-[var(--color-brand-primary)]"
          }`}
        >
          {scene.sceneNum}
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="truncate text-sm font-semibold text-[var(--fg-0)]">
              {scene.title || `Scene ${scene.sceneNum}`}
            </h3>
            {scene.isAnchor && (
              <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-700 dark:text-amber-300">
                ANCHOR
              </span>
            )}
            {scene.isAnchor && <AnchorHint />}
          </div>

          {scene.beatTimestamp && (
            <p className="mt-1 text-xs text-[var(--fg-muted)]">{scene.beatTimestamp}</p>
          )}
        </div>
      </div>

      {attachmentNames.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {attachmentNames.map((name) => (
            <code
              key={name}
              className="rounded-lg border border-[var(--border-muted)] bg-[var(--surface-2)] px-2 py-1 text-xs text-[var(--fg-0)]"
            >
              {name}
            </code>
          ))}
        </div>
      )}

      {warnings.length > 0 && (
        <div className="mb-3 space-y-1">
          {warnings.map((warning, i) => (
            <div
              key={i}
              className={`rounded-lg border px-3 py-1.5 text-xs ${WARNING_COLORS[warning.type]}`}
            >
              {warning.message}
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {promptItems.map((item) => {
          const copyKey = `${scene.sceneNum}-${item.key}`;
          const isCopied = copiedStates[copyKey];
          const isCompleted = completedPrompts.has(copyKey);

          return (
            <div key={item.key} className={isCompleted ? "opacity-60" : ""}>
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className={`text-xs font-semibold ${PROMPT_COLORS[item.key]}`}>
                  {item.label}
                </span>
                <button
                  type="button"
                  onClick={() => onCopy(copyKey, item.prompt)}
                  className={`inline-flex min-h-8 items-center justify-center rounded-md px-2 text-xs font-medium transition-colors ${
                    isCopied
                      ? "bg-emerald-500 text-white"
                      : "bg-[var(--fg-0)] text-[var(--bg-0)] hover:opacity-90"
                  }`}
                >
                  {isCopied ? "완료" : isCompleted ? "재복사" : "복사"}
                </button>
              </div>
              <div className="max-h-24 overflow-y-auto rounded-lg border border-[var(--border-muted)] bg-[var(--surface-2)] p-2">
                <p className="whitespace-pre-wrap break-all font-mono text-xs text-[var(--fg-muted)]">
                  {item.prompt.slice(0, 220)}
                  {item.prompt.length > 220 ? "..." : ""}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </ContentCard>
  );
}
