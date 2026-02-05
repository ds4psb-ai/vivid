"use client";

import type { Builder2Scene, AnchorInfo } from "@/lib/builder2-md-parser";
import { ContentCard } from "../shared";

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
}

export function SceneCard({
  scene,
  copiedStates,
  completedPrompts,
  onCopy,
  anchors,
}: SceneCardProps) {
  const promptItems = [
    { key: "nanoBanana", label: "NanoBanana", prompt: scene.imagePrompts.nanoBanana },
    { key: "midjourney", label: "Midjourney", prompt: scene.imagePrompts.midjourney },
    { key: "kling", label: "Kling", prompt: scene.motionPrompts.kling },
    { key: "veo", label: "Veo", prompt: scene.motionPrompts.veo },
  ].filter(item => item.prompt);

  // Get relevant anchor refs for this scene (non-anchor scenes with anchorRefs)
  const relevantAnchors = !scene.isAnchor && scene.anchorRefs && scene.anchorRefs.length > 0
    ? anchors.filter(a => scene.anchorRefs.includes(a.key))
    : [];

  return (
    <ContentCard>
      <div className="flex items-center gap-3 mb-4">
        <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${scene.isAnchor
          ? "bg-amber-500/20 text-amber-400"
          : "bg-purple-500/20 text-purple-400"
          }`}>
          {scene.sceneNum}
        </span>
        <div>
          <h3 className="text-white font-bold">{scene.title || `Scene ${scene.sceneNum}`}</h3>
          {scene.beatTimestamp && (
            <p className="text-gray-500 text-xs">{scene.beatTimestamp}</p>
          )}
        </div>
        {scene.isAnchor && (
          <span className="ml-auto px-2 py-1 rounded text-xs font-bold bg-amber-500/20 text-amber-400">
            ANCHOR
          </span>
        )}
      </div>

      {/* 앵커 씬 특별 가이드 */}
      {scene.isAnchor && (
        <div className="mb-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
          <p className="text-xs font-bold text-amber-200 mb-2">⭐ 이 씬은 앵커 씬입니다</p>
          <div className="text-xs text-amber-100 space-y-1">
            <div>• 이 씬의 이미지가 다른 씬에서 캐릭터 레퍼런스로 사용됩니다</div>
            <div>• --oref 파라미터 없이 먼저 생성하세요</div>
            <div>
              • 생성 후{' '}
              <code className="ml-1 px-2 py-1 bg-black/40 rounded text-green-300 font-mono">
                anchor_male.jpg
              </code>{' '}
              (또는 anchor_female.jpg)로 저장
            </div>
          </div>
        </div>
      )}

      {/* 이미지 첨부 가이드 (비앵커 씬) */}
      {!scene.isAnchor && (
        <div className="mb-4 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
          <p className="text-xs font-bold text-blue-200 mb-2">📎 이미지 첨부 가이드:</p>

          {/* Image 1: COMPOSITION (씬 프레임) */}
          <div className="mb-2">
            <span className="text-xs text-blue-300">Image 1 (구도):</span>
            <code className="ml-2 px-2 py-1 bg-black/40 rounded text-blue-200 font-mono text-xs">
              {scene.frameFile}
            </code>
          </div>

          {/* Image 2: CHARACTER FACE (앵커 이미지들) */}
          {relevantAnchors.length > 0 && (
            <div className="mb-2">
              <span className="text-xs text-blue-300">Image 2 (캐릭터):</span>
              {relevantAnchors.map((anchor) => (
                <code
                  key={anchor.key}
                  className="ml-2 px-2 py-1 bg-black/40 rounded text-green-200 font-mono text-xs"
                >
                  anchor_{anchor.key.toLowerCase()}.jpg
                </code>
              ))}
            </div>
          )}

          {/* 도구별 첨부 방법 */}
          <div className="mt-2 text-xs text-blue-100 space-y-1">
            <div>• <strong>NanoBanana Pro</strong>: 두 이미지 모두 드래그앤드롭</div>
            <div>• <strong>Midjourney</strong>: Discord에 업로드 → --oref에 앵커 URL 사용</div>
            <div>• <strong>Kling/Veo</strong>: 생성된 이미지 또는 {scene.frameFile} 첨부</div>
          </div>
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
                      ? "bg-gray-700 text-gray-400 hover:bg-gray-600"
                      : "bg-white text-gray-900 hover:bg-gray-100"
                    }`}
                >
                  {isCopied ? "✓" : isCompleted ? "재복사" : "복사"}
                </button>
              </div>
              <div className={`p-2 rounded-lg bg-black/30 border max-h-20 overflow-y-auto ${isCompleted ? 'border-emerald-500/30' : 'border-white/10'}`}>
                <p className="text-gray-300 text-xs font-mono whitespace-pre-wrap break-all">
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
