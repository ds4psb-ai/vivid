"use client";

import type { AnchorInfo } from "@/lib/builder2-md-parser";
import { ContentCard } from "../shared";

interface AnchorGuidePanelProps {
  anchors: AnchorInfo[];
}

export function AnchorGuidePanel({ anchors }: AnchorGuidePanelProps) {
  if (anchors.length === 0) return null;

  return (
    <ContentCard>
      <div className="flex items-center gap-2 mb-4">
        <span className="text-2xl">⭐</span>
        <h3 className="text-lg font-bold text-white">앵커 이미지 먼저 생성</h3>
      </div>

      {/* 워크플로우 안내 추가 */}
      <div className="mb-4 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
        <p className="text-sm text-blue-200">
          💡 앵커 이미지는 캐릭터 일관성을 위해 <strong>반드시 먼저</strong> 생성하세요.
        </p>
      </div>

      <div className="space-y-3">
        {anchors.map(anchor => (
          <div key={anchor.key} className="p-4 rounded-lg bg-slate-800 border border-slate-700 mb-3">
            {/* 기본 정보 */}
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">{anchor.emoji}</span>
              <div>
                <h4 className="font-bold text-white">{anchor.key} ANCHOR</h4>
                <p className="text-sm text-gray-400">Scene {String(anchor.sceneNum).padStart(2, '0')}: {anchor.title}</p>
              </div>
            </div>

            {/* 이미지 첨부 가이드 추가 */}
            <div className="mt-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
              <p className="text-xs font-bold text-amber-200 mb-2">📎 이미지 첨부 가이드:</p>
              <ol className="text-xs text-amber-100 space-y-1 ml-4 list-decimal">
                <li>
                  영상에서 프레임 추출:{' '}
                  <code className="ml-2 px-2 py-1 bg-black/40 rounded text-amber-300 font-mono">
                    {anchor.frameFile}
                  </code>
                </li>
                <li>NanoBanana Pro: 위 프레임을 레퍼런스로 첨부</li>
                <li>Midjourney: 위 프레임을 Discord에 업로드</li>
                <li>
                  생성된 이미지를 저장:{' '}
                  <code className="ml-2 px-2 py-1 bg-black/40 rounded text-green-300 font-mono">
                    anchor_{anchor.key.toLowerCase()}.jpg
                  </code>
                </li>
              </ol>
            </div>

            {/* 캐릭터 설명 */}
            <div className="mt-3 text-sm">
              <span className="text-gray-400">👤 캐릭터:</span>
              <span className="ml-2 text-white">{anchor.character}</span>
            </div>
          </div>
        ))}
      </div>

      {/* 다음 단계 안내 */}
      <div className="mt-4 p-3 rounded-lg bg-green-500/10 border border-green-500/20">
        <p className="text-sm text-green-200">
          ✅ 앵커 이미지 생성 완료 후 아래 씬별 프롬프트로 진행하세요.
        </p>
      </div>
    </ContentCard>
  );
}
