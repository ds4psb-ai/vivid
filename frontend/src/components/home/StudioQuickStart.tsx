"use client";

import Link from "next/link";
import { Rocket, Workflow, Sparkles } from "lucide-react";

export function StudioQuickStart() {
  return (
    <section className="rounded-2xl border border-[var(--border-muted)] bg-[var(--surface-1)]/70 p-5 backdrop-blur-sm sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-[var(--fg-subtle)]">
            Quick Start
          </p>
          <h2 className="mt-1 text-xl font-semibold text-[var(--fg-0)] sm:text-2xl">
            빠른 시작
          </h2>
          <p className="mt-2 text-sm text-[var(--fg-muted)]">
            지금 가장 많이 쓰는 제작 흐름으로 바로 들어가세요.
          </p>
        </div>
        <Sparkles className="h-5 w-5 text-[var(--accent)]" aria-hidden="true" />
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        {/* Primary CTA */}
        <Link
          href="/dna-lab"
          className="inline-flex items-center gap-2 rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-slate-950 transition hover:opacity-90"
        >
          <Rocket className="h-4 w-4" aria-hidden="true" />
          지금 바로 시작
        </Link>
        {/* Secondary CTA */}
        <Link
          href="/flow"
          className="inline-flex items-center gap-2 rounded-lg border border-[var(--border-muted)] px-4 py-2 text-sm font-medium text-[var(--fg-muted)] transition hover:border-[var(--accent)]/60 hover:text-[var(--fg-0)]"
        >
          <Workflow className="h-4 w-4" aria-hidden="true" />
          워크플로우 둘러보기
        </Link>
      </div>
    </section>
  );
}

export default StudioQuickStart;
