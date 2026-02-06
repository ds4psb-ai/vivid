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
          <span className="material-symbols-outlined text-[var(--color-brand-primary)]">imagesmode</span>
          <h3 className="text-lg font-bold text-[var(--fg-0)]">이미지 첨부 워크플로우</h3>
        </div>
        <span className={`material-symbols-outlined text-[var(--fg-muted)] transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
          expand_more
        </span>
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-4">
          <div className="p-4 rounded-lg border border-[var(--border-muted)] bg-[var(--surface-2)]">
            <h4 className="font-bold text-[var(--fg-0)] mb-2">STEP 1. 프레임 추출</h4>
            <p className="text-sm text-[var(--fg-muted)]">
              `프레임 다운로드`로 ZIP을 받고, `frame_01_00-00.00.jpg` 형식 파일을 사용합니다.
            </p>
          </div>

          <div className="p-4 rounded-lg border border-amber-500/30 bg-amber-500/10">
            <h4 className="font-bold text-amber-700 dark:text-amber-200 mb-2">STEP 2. 앵커 우선 생성</h4>
            <p className="text-sm text-amber-800 dark:text-amber-100">
              앵커 컷을 먼저 만든 뒤 `anchor_male.jpg`, `anchor_female.jpg`로 저장합니다.
            </p>
          </div>

          <div className="p-4 rounded-lg border border-[var(--border-muted)] bg-[var(--surface-2)]">
            <h4 className="font-bold text-[var(--fg-0)] mb-2">STEP 3. 씬 이미지 생성</h4>
            <ul className="text-sm text-[var(--fg-muted)] ml-4 list-disc space-y-1">
              <li>Image 1: 해당 씬의 `frame_XX...jpg`</li>
              <li>Image 2: 앵커 파일(`anchor_*.jpg`)</li>
            </ul>
          </div>

          <div className="p-4 rounded-lg border border-[var(--border-muted)] bg-[var(--surface-2)]">
            <h4 className="font-bold text-[var(--fg-0)] mb-2">STEP 4. 모션 생성</h4>
            <p className="text-sm text-[var(--fg-muted)]">
              Kling/Veo에서 STEP 3 이미지를 첨부해 최종 영상을 생성합니다.
            </p>
          </div>

          <div className="p-4 rounded-lg border border-[var(--border-muted)] bg-[var(--surface-2)]">
            <h4 className="font-bold text-[var(--fg-0)] mb-2">파일명 규칙</h4>
            <p className="text-sm text-[var(--fg-muted)]">
              씬 프레임: <code className="rounded bg-[var(--surface-3)] px-2 py-1 font-mono">frame_01_00-00.00.jpg</code>
            </p>
            <p className="text-sm text-[var(--fg-muted)] mt-2">
              앵커 이미지: <code className="rounded bg-[var(--surface-3)] px-2 py-1 font-mono">anchor_male.jpg</code>
            </p>
          </div>
        </div>
      )}
    </ContentCard>
  );
}
