"use client";

import type { TabKey } from "../../constants";
import { ContentCard, PageHeader } from "../shared";
import { FAQ_ITEMS, IMAGE_TOOLS, VIDEO_TOOLS } from "./toolsData";

interface ToolsContentProps {
  setActiveTab: (tab: TabKey) => void;
}

const TOOL_TIPS: Record<string, string[]> = {
  nanobanana: [
    "Gemini 접속 후 이미지 생성 모델 선택",
    "파싱 탭에서 복사한 프롬프트 입력",
    "생성 결과 중 기준 컷부터 저장",
  ],
  midjourney: [
    "웹 또는 Discord에서 /imagine 실행",
    "앵커 이미지 URL로 일관성 유지",
    "세로 숏폼은 --ar 9:16 권장",
  ],
  kling: [
    "Image to Video 모드 선택",
    "이미지 업로드 후 프롬프트 입력",
    "Duration/Camera 설정 후 생성",
  ],
  veo: [
    "Flow 또는 AI Studio Veo 탭 진입",
    "복사한 프롬프트 붙여넣기",
    "대사/효과음 필요 씬 우선 적용",
  ],
};

export function ToolsContent({ setActiveTab }: ToolsContentProps) {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <PageHeader title="외부 툴" sub="복사한 프롬프트를 도구별로 실행하세요" />

      <ContentCard highlight>
        <p className="text-sm text-[var(--fg-muted)]">
          권장 순서: `파싱 + 복사` → `이미지 생성` → `영상 생성` → `과제 제출`
        </p>
      </ContentCard>

      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-4">이미지 생성</h3>
        <div className="space-y-3">
          {IMAGE_TOOLS.map((tool) => (
            <div
              key={tool.id}
              className="rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-4"
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="font-semibold text-[var(--fg-0)]">{tool.title}</p>
                  <p className="text-xs text-[var(--fg-muted)]">{tool.badge}</p>
                </div>
                <a
                  href={tool.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded-lg bg-[var(--fg-0)] text-[var(--bg-0)] px-3 py-1.5 text-xs font-semibold hover:opacity-90 transition-all"
                >
                  열기
                </a>
              </div>
              <ul className="mt-3 space-y-1 text-sm text-[var(--fg-muted)]">
                {(TOOL_TIPS[tool.id] || []).map((tip) => (
                  <li key={tip}>- {tip}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </ContentCard>

      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-4">영상 생성</h3>
        <div className="space-y-3">
          {VIDEO_TOOLS.map((tool) => (
            <div
              key={tool.id}
              className="rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-4"
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="font-semibold text-[var(--fg-0)]">{tool.title}</p>
                  <p className="text-xs text-[var(--fg-muted)]">{tool.badge}</p>
                </div>
                <a
                  href={tool.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded-lg bg-[var(--fg-0)] text-[var(--bg-0)] px-3 py-1.5 text-xs font-semibold hover:opacity-90 transition-all"
                >
                  열기
                </a>
              </div>
              <ul className="mt-3 space-y-1 text-sm text-[var(--fg-muted)]">
                {(TOOL_TIPS[tool.id] || []).map((tip) => (
                  <li key={tip}>- {tip}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </ContentCard>

      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-4">운영 팁</h3>
        <ul className="space-y-2 text-sm text-[var(--fg-muted)]">
          <li>- 캐릭터 고정이 중요하면 Kling 우선</li>
          <li>- 대사/효과음이 중요하면 Veo 우선</li>
          <li>- 생성 결과는 씬 번호 순으로 저장</li>
        </ul>
      </ContentCard>

      <details className="rounded-2xl border border-[var(--border-muted)] bg-[var(--surface-1)] p-4">
        <summary className="cursor-pointer text-sm font-semibold text-[var(--fg-0)]">
          FAQ 보기
        </summary>
        <div className="mt-3 space-y-3">
          {FAQ_ITEMS.map((faq) => (
            <div key={faq.id} className="rounded-lg border border-[var(--border-muted)] bg-[var(--surface-2)] p-3">
              <p className="text-sm font-semibold text-[var(--fg-0)]">{faq.question}</p>
              <p className="text-sm text-[var(--fg-muted)] mt-1 whitespace-pre-line">{faq.answer}</p>
            </div>
          ))}
        </div>
      </details>

      <div className="text-center py-4">
        <button
          onClick={() => setActiveTab("homework")}
          className="px-6 py-3 rounded-xl bg-[var(--fg-0)] text-[var(--bg-0)] font-bold hover:opacity-90 transition-all inline-flex items-center gap-2"
        >
          <span className="material-symbols-outlined">assignment</span>
          과제 확인하기
        </button>
      </div>
    </div>
  );
}
