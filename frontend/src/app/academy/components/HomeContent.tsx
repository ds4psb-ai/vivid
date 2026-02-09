"use client";

import type { LucideIcon } from "lucide-react";
import {
  ArrowUpRight,
  Brain,
  ClipboardCheck,
  ClipboardCopy,
  Lock,
  Sparkles,
  Upload,
  Wrench,
} from "lucide-react";
import { TOOL_LINKS, type TabKey } from "../constants";

interface HomeContentProps {
  setActiveTab: (tab: TabKey) => void;
  hasAccess: boolean;
}

interface WorkflowStep {
  key: TabKey;
  num: number;
  label: string;
  icon: LucideIcon;
}

export function HomeContent({ setActiveTab, hasAccess }: HomeContentProps) {
  const workflowSteps: WorkflowStep[] = [
    { key: "upload", num: 1, label: "업로드", icon: Upload },
    { key: "prompt", num: 2, label: "프롬프터", icon: Sparkles },
    { key: "parse", num: 3, label: "파싱", icon: ClipboardCopy },
    { key: "tools", num: 4, label: "툴", icon: Wrench },
    { key: "homework", num: 5, label: "과제", icon: ClipboardCheck },
  ];

  return (
    <div className="mx-auto w-full max-w-[var(--academy-content-max)] space-y-5">
      <div className="grid gap-3 md:grid-cols-3">
        {hasAccess ? (
          <a
            href={TOOL_LINKS.builder}
            target="_blank"
            rel="noopener noreferrer"
            className="group relative overflow-hidden rounded-2xl border border-[var(--border-muted)] bg-[linear-gradient(135deg,rgba(199,135,58,0.14)_0%,rgba(199,135,58,0.03)_45%,transparent_100%)] p-5 md:col-span-2"
          >
            <div className="flex min-h-[156px] flex-col justify-between">
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-[var(--color-brand-primary)]/35 bg-[var(--surface-1)] text-[var(--color-brand-primary)]">
                <Sparkles className="h-4 w-4" />
              </span>

              <div className="flex items-end justify-between gap-3">
                <div>
                  <p className="text-[11px] font-semibold tracking-wide text-[var(--fg-muted)]">
                    QUICK START
                  </p>
                  <h3 className="text-2xl font-semibold tracking-tight text-[var(--fg-0)]">
                    프롬프터
                  </h3>
                </div>
                <span className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-[var(--border-muted)] bg-[var(--surface-1)] text-[var(--fg-0)] transition-transform group-hover:translate-x-0.5">
                  <ArrowUpRight className="h-4 w-4" />
                </span>
              </div>
            </div>
          </a>
        ) : (
          <div className="relative overflow-hidden rounded-2xl border border-[var(--border-muted)] bg-[linear-gradient(135deg,rgba(199,135,58,0.14)_0%,rgba(199,135,58,0.03)_45%,transparent_100%)] p-5 md:col-span-2">
            <div className="flex min-h-[156px] flex-col justify-between">
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-[var(--color-brand-primary)]/35 bg-[var(--surface-1)] text-[var(--color-brand-primary)]">
                <Sparkles className="h-4 w-4" />
              </span>

              <div className="flex items-end justify-between gap-3">
                <div>
                  <p className="text-[11px] font-semibold tracking-wide text-[var(--fg-muted)]">
                    QUICK START
                  </p>
                  <h3 className="text-2xl font-semibold tracking-tight text-[var(--fg-0)]">
                    프롬프터
                  </h3>
                </div>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--border-muted)] bg-[var(--surface-1)] px-3 py-1.5 text-xs text-[var(--fg-muted)]">
                  <Lock className="h-3 w-3" />
                  수강 후 이용
                </span>
              </div>
            </div>
          </div>
        )}

        {hasAccess ? (
          <a
            href={TOOL_LINKS.vibe}
            target="_blank"
            rel="noopener noreferrer"
            className="group relative overflow-hidden rounded-2xl border border-[var(--border-muted)] bg-[linear-gradient(145deg,rgba(199,135,58,0.11)_0%,rgba(255,255,255,0)_60%)] p-5 text-left"
          >
            <div className="flex min-h-[156px] flex-col justify-between">
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-[var(--color-brand-primary)]/35 bg-[var(--surface-1)] text-[var(--color-brand-primary)]">
                <Brain className="h-4 w-4" />
              </span>

              <div className="flex items-end justify-between gap-3">
                <h3 className="text-xl font-semibold tracking-tight text-[var(--fg-0)]">
                  철학관
                </h3>
                <span className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-[var(--border-muted)] bg-[var(--surface-1)] text-[var(--fg-0)] transition-transform group-hover:translate-x-0.5">
                  <ArrowUpRight className="h-4 w-4" />
                </span>
              </div>
            </div>
          </a>
        ) : (
          <div className="relative overflow-hidden rounded-2xl border border-[var(--border-muted)] bg-[linear-gradient(145deg,rgba(199,135,58,0.11)_0%,rgba(255,255,255,0)_60%)] p-5 text-left">
            <div className="flex min-h-[156px] flex-col justify-between">
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-[var(--color-brand-primary)]/35 bg-[var(--surface-1)] text-[var(--color-brand-primary)]">
                <Brain className="h-4 w-4" />
              </span>

              <div className="flex items-end justify-between gap-3">
                <h3 className="text-xl font-semibold tracking-tight text-[var(--fg-0)]">
                  철학관
                </h3>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--border-muted)] bg-[var(--surface-1)] px-3 py-1.5 text-xs text-[var(--fg-muted)]">
                  <Lock className="h-3 w-3" />
                  수강 후 이용
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      <section className="rounded-2xl border border-[var(--border-muted)] bg-[var(--surface-1)] p-3 md:p-4">
        <div className="mb-2 flex items-center justify-between px-1">
          <h3 className="text-sm font-semibold text-[var(--fg-0)]">워크플로우</h3>
          <span className="text-xs text-[var(--fg-muted)]">1 → 5</span>
        </div>

        <div className="space-y-2">
          {workflowSteps.map((step) => {
            const StepIcon = step.icon;

            return (
              <button
                key={step.num}
                type="button"
                onClick={() => setActiveTab(step.key)}
                className="group inline-flex min-h-[52px] w-full items-center gap-3 rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] px-3 text-left transition-colors hover:bg-[var(--surface-3)]"
              >
                <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-[var(--color-brand-primary)]/12 text-xs font-semibold text-[var(--color-brand-primary)]">
                  {step.num}
                </span>
                <span className="flex-1 text-sm font-semibold text-[var(--fg-0)]">
                  {step.label}
                </span>
                <StepIcon className="h-4 w-4 text-[var(--fg-muted)]" />
              </button>
            );
          })}
        </div>
      </section>

      {!hasAccess && (
        <section className="rounded-2xl border border-[var(--border-muted)] bg-[var(--surface-1)] p-4 md:p-5">
          <a
            href="https://cafe.naver.com/antacademy1/5150"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex min-h-11 items-center rounded-xl bg-[var(--color-brand-primary)] px-5 text-sm font-semibold text-white transition-opacity hover:opacity-90"
          >
            수강 신청하기
          </a>
          <p className="mt-3 text-sm text-[var(--fg-muted)]">
            이미 결제하셨나요?{" "}
            <a
              href="mailto:ted.taeeun.kim@gmail.com"
              className="font-medium text-[var(--color-brand-primary)] hover:underline"
            >
              문의하기
            </a>
          </p>
        </section>
      )}
    </div>
  );
}
