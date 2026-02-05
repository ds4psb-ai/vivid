"use client";

import { useState } from "react";
import { ContentCard } from "../shared";

export function ImageAttachmentGuide() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <ContentCard>
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <span className="text-2xl">🖼️</span>
          <h3 className="text-lg font-bold text-white">이미지 첨부 워크플로우 가이드</h3>
        </div>
        <span className={`material-symbols-outlined text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
          expand_more
        </span>
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-4">
          {/* STEP 1: 프레임 추출 */}
          <div className="p-4 rounded-lg bg-slate-800 border border-slate-700">
            <h4 className="font-bold text-white mb-2">STEP 1: 프레임 추출</h4>
            <ol className="text-sm text-gray-300 space-y-2 ml-4 list-decimal">
              <li>
                위 "프레임 다운로드" 버튼으로 영상에서 자동 추출된 프레임 다운로드
              </li>
              <li>
                ZIP 압축 해제하면{' '}
                <code className="px-2 py-1 bg-black/40 rounded font-mono text-blue-300">frame_01_00-00.00.jpg</code>,{' '}
                <code className="px-2 py-1 bg-black/40 rounded font-mono text-blue-300 ml-1">frame_02_00-01.67.jpg</code>{' '}
                등 파일 생성
              </li>
              <li>이 파일들이 각 씬의 "구도 레퍼런스"로 사용됩니다</li>
            </ol>
          </div>

          {/* STEP 2: 앵커 이미지 생성 */}
          <div className="p-4 rounded-lg bg-slate-800 border border-slate-700">
            <h4 className="font-bold text-white mb-2">STEP 2: 앵커 이미지 생성 (최우선)</h4>
            <div className="text-sm text-gray-300 space-y-2">
              <p>
                <strong className="text-amber-300">⚠️ 앵커부터 생성:</strong>{' '}
                캐릭터 일관성을 위해 반드시 먼저 생성
              </p>
              <ol className="ml-4 list-decimal space-y-1">
                <li>
                  아래 "앵커 이미지 먼저 생성" 섹션에서 해당 씬의 프레임 파일 확인
                </li>
                <li>
                  NanoBanana Pro 또는 Midjourney에서 프롬프트 복사 + 프레임 첨부
                </li>
                <li>
                  생성된 이미지를{' '}
                  <code className="px-2 py-1 bg-black/40 rounded font-mono text-green-300 ml-1">anchor_male.jpg</code> /{' '}
                  <code className="px-2 py-1 bg-black/40 rounded font-mono text-green-300 ml-1">anchor_female.jpg</code>로 저장
                </li>
              </ol>
            </div>
          </div>

          {/* STEP 3: 씬별 이미지 생성 */}
          <div className="p-4 rounded-lg bg-slate-800 border border-slate-700">
            <h4 className="font-bold text-white mb-2">STEP 3: 씬별 이미지 생성</h4>
            <div className="text-sm text-gray-300 space-y-2">
              <p>각 씬마다 다음 이미지 첨부:</p>
              <ul className="ml-4 list-disc space-y-1">
                <li>
                  <strong className="text-blue-300">Image 1 (구도):</strong> 해당 씬의 frame 파일
                </li>
                <li>
                  <strong className="text-green-300">Image 2 (캐릭터):</strong> STEP 2에서 생성한 anchor 파일
                </li>
              </ul>
              <p className="mt-2 text-xs text-gray-400">
                💡 각 씬 카드의 "이미지 첨부 가이드" 섹션에서 정확한 파일명 확인
              </p>
            </div>
          </div>

          {/* STEP 4: 모션 생성 */}
          <div className="p-4 rounded-lg bg-slate-800 border border-slate-700">
            <h4 className="font-bold text-white mb-2">STEP 4: 모션 생성</h4>
            <div className="text-sm text-gray-300 space-y-2">
              <ul className="ml-4 list-disc space-y-1">
                <li>
                  <strong>Kling 3.0:</strong> STEP 3에서 생성한 이미지 첨부
                </li>
                <li>
                  <strong>Veo 3.1:</strong> 씬 프레임 + 앵커 이미지 (최대 3개) 첨부
                </li>
              </ul>
            </div>
          </div>

          {/* 파일명 규칙 요약 */}
          <div className="p-4 rounded-lg bg-slate-800 border border-slate-700">
            <h4 className="font-bold text-white mb-2">📁 파일명 규칙 요약</h4>
            <div className="text-sm space-y-2">
              <div className="flex items-start gap-2">
                <span className="text-blue-300">•</span>
                <div>
                  <strong className="text-blue-200">씬 프레임:</strong>{' '}
                  <code className="ml-2 px-2 py-1 bg-black/40 rounded font-mono text-xs text-blue-300">
                    frame_01_00-00.00.jpg
                  </code>
                  <span className="ml-2 text-gray-400">(영상에서 자동 추출)</span>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-green-300">•</span>
                <div>
                  <strong className="text-green-200">앵커 이미지:</strong>{' '}
                  <code className="ml-2 px-2 py-1 bg-black/40 rounded font-mono text-xs text-green-300">
                    anchor_male.jpg
                  </code>
                  <span className="ml-2 text-gray-400">(생성 후 저장)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </ContentCard>
  );
}
