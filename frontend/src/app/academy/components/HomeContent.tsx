"use client";

import { TOOL_LINKS, type TabKey } from "../constants";

interface HomeContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function HomeContent({ setActiveTab }: HomeContentProps) {
  const workflowSteps = [
    { key: "upload" as TabKey, num: 1, label: "업로드", icon: "cloud_upload" },
    { key: "prompt" as TabKey, num: 2, label: "프롬프트", icon: "auto_awesome" },
    { key: "parse" as TabKey, num: 3, label: "파싱", icon: "content_copy" },
    { key: "tools" as TabKey, num: 4, label: "툴", icon: "build" },
    { key: "homework" as TabKey, num: 5, label: "과제", icon: "assignment_turned_in" },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="rounded-3xl border border-[var(--border-muted)] bg-[var(--surface-1)] p-6 md:p-8">
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
              <div className="text-[var(--fg-0)] font-bold text-sm">{step.label}</div>
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
            <p className="text-[var(--fg-0)] font-bold">통합빌더</p>
          </a>
          <button
            onClick={() => setActiveTab("vibe")}
            className="p-5 rounded-xl border border-[var(--border-muted)] bg-[var(--surface-1)] hover:border-[var(--color-brand-primary)]/40 transition-all text-center"
          >
            <span className="material-symbols-outlined text-[var(--color-brand-primary)] text-3xl mb-2 block">
              psychology
            </span>
            <p className="text-[var(--fg-0)] font-bold">바이브</p>
          </button>
        </div>
      </div>
    </div>
  );
}
