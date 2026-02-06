"use client";

import { TOOL_LINKS, type TabKey } from "../constants";

interface HomeContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function HomeContent({ setActiveTab }: HomeContentProps) {
  const workflowSteps = [
    { key: "upload" as TabKey, num: 1, label: "영상 업로드", icon: "cloud_upload", sub: "레퍼런스 준비 + 씬 감지" },
    { key: "prompt" as TabKey, num: 2, label: "프롬프트 생성", icon: "auto_awesome", sub: "오마주/변주 생성" },
    { key: "parse" as TabKey, num: 3, label: "파싱 + 복사", icon: "content_copy", sub: "씬별 프롬프트 추출" },
    { key: "tools" as TabKey, num: 4, label: "외부 툴 실행", icon: "build", sub: "이미지/영상 생성" },
    { key: "homework" as TabKey, num: 5, label: "과제 제출", icon: "assignment_turned_in", sub: "결과물 업로드" },
  ];

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mt-4 mb-8">
        <div className="inline-block px-4 py-1 rounded-full bg-[var(--color-brand-primary)]/10 border border-[var(--color-brand-primary)]/20 mb-4">
          <span className="text-[10px] font-bold text-[var(--color-brand-primary)] tracking-[0.2em] font-mono uppercase">
            Workflow
          </span>
        </div>
        <h2 className="text-3xl md:text-4xl font-black mb-4 tracking-tight text-[var(--fg-0)]">
          AI 영상 제작 5단계
        </h2>
        <p className="text-[var(--fg-muted)] text-base max-w-2xl mx-auto leading-relaxed">
          필요한 순서만 빠르게 따라가도록 구성했습니다.
          각 단계에서 다음 행동 하나만 보여줍니다.
        </p>
      </div>

      <div className="rounded-3xl border border-[var(--border-muted)] bg-[var(--surface-1)] p-6 md:p-8 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {workflowSteps.map((step) => (
            <button
              key={step.num}
              onClick={() => setActiveTab(step.key)}
              className="group p-4 rounded-2xl border border-[var(--border-muted)] bg-[var(--surface-2)] hover:border-[var(--color-brand-primary)]/40 hover:bg-[var(--surface-1)] transition-all text-left"
            >
              <div className="w-10 h-10 mb-3 rounded-xl bg-[var(--color-brand-primary)]/10 flex items-center justify-center">
                <span className="material-symbols-outlined text-xl text-[var(--color-brand-primary)]">
                  {step.icon}
                </span>
              </div>
              <div className="text-[10px] font-mono text-[var(--fg-muted)] mb-1">
                STEP {step.num}
              </div>
              <div className="text-[var(--fg-0)] font-bold text-sm mb-1">{step.label}</div>
              <div className="text-[var(--fg-muted)] text-xs leading-relaxed">{step.sub}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="max-w-2xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <a
            href={TOOL_LINKS.builder}
            target="_blank"
            rel="noopener noreferrer"
            className="p-5 rounded-xl border border-[var(--border-muted)] bg-[var(--surface-1)] hover:border-[var(--color-brand-primary)]/40 transition-all text-center"
          >
            <span className="material-symbols-outlined text-[var(--color-brand-primary)] text-3xl mb-2 block">
              movie_filter
            </span>
            <p className="text-[var(--fg-0)] font-bold">통합빌더 실행</p>
            <p className="text-[var(--fg-muted)] text-xs mt-1">프롬프트 생성기로 바로 이동</p>
          </a>
          <button
            onClick={() => setActiveTab("vibe")}
            className="p-5 rounded-xl border border-[var(--border-muted)] bg-[var(--surface-1)] hover:border-[var(--color-brand-primary)]/40 transition-all text-center"
          >
            <span className="material-symbols-outlined text-[var(--color-brand-primary)] text-3xl mb-2 block">
              psychology
            </span>
            <p className="text-[var(--fg-0)] font-bold">바이브 철학관</p>
            <p className="text-[var(--fg-muted)] text-xs mt-1">선택 기능: 변주 개인화</p>
          </button>
        </div>
      </div>
    </div>
  );
}
