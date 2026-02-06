"use client";

import { TOOL_LINKS, type TabKey } from "../constants";

interface HomeContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function HomeContent({ setActiveTab }: HomeContentProps) {
  const workflowSteps = [
    { key: "upload" as TabKey, num: 1, label: "업로드", icon: "cloud_upload" },
    { key: "prompt" as TabKey, num: 2, label: "빌더", icon: "auto_awesome" },
    { key: "parse" as TabKey, num: 3, label: "파싱", icon: "content_copy" },
    { key: "tools" as TabKey, num: 4, label: "툴", icon: "build" },
    { key: "homework" as TabKey, num: 5, label: "과제", icon: "assignment_turned_in" },
  ];

  return (
    <div className="mx-auto w-full max-w-[var(--academy-content-max)] space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <a
          href={TOOL_LINKS.builder}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex min-h-12 items-center justify-between rounded-[var(--academy-radius)] border border-[var(--border-muted)] bg-[var(--surface-1)] px-4 text-sm font-semibold text-[var(--fg-0)] transition-colors hover:bg-[var(--surface-2)]"
        >
          <span className="inline-flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px] text-[var(--color-brand-primary)]" aria-hidden>
              add
            </span>
            통합빌더
          </span>
          <span className="material-symbols-outlined text-[18px] text-[var(--fg-muted)]" aria-hidden>
            north_east
          </span>
        </a>

        <button
          type="button"
          onClick={() => setActiveTab("vibe")}
          className="inline-flex min-h-12 items-center justify-between rounded-[var(--academy-radius)] border border-[var(--border-muted)] bg-[var(--surface-1)] px-4 text-sm font-semibold text-[var(--fg-0)] transition-colors hover:bg-[var(--surface-2)]"
        >
          <span className="inline-flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px] text-[var(--color-brand-primary)]" aria-hidden>
              add
            </span>
            바이브
          </span>
          <span className="material-symbols-outlined text-[18px] text-[var(--fg-muted)]" aria-hidden>
            arrow_forward
          </span>
        </button>
      </div>

      <div className="rounded-[var(--academy-radius)] border border-[var(--border-muted)] bg-[var(--surface-1)] p-3">
        <div className="grid gap-2 sm:grid-cols-5">
          {workflowSteps.map((step) => (
            <button
              key={step.num}
              type="button"
              onClick={() => setActiveTab(step.key)}
              className="inline-flex min-h-11 items-center justify-between rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] px-3 text-sm font-medium text-[var(--fg-0)] transition-colors hover:bg-[var(--surface-3)]"
            >
              <span className="inline-flex items-center gap-2">
                <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[var(--color-brand-primary)]/12 text-xs font-semibold text-[var(--color-brand-primary)]">
                  {step.num}
                </span>
                {step.label}
              </span>
              <span className="material-symbols-outlined text-[16px] text-[var(--fg-muted)]" aria-hidden>
                {step.icon}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
