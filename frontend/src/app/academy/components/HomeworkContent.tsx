"use client";

import { useState } from "react";
import { PageHeader, ContentCard } from "./shared";
import { HOMEWORK_DATA, type LectureKey } from "../content";

export function HomeworkContent() {
  const [selectedLecture, setSelectedLecture] = useState<LectureKey>("3강");
  const data = HOMEWORK_DATA[selectedLecture];

  return (
    <div className="mx-auto w-full max-w-[var(--academy-content-max)] space-y-4">
      <PageHeader title="과제" sub={`${selectedLecture} · ${data.date}`} />

      <div className="grid grid-cols-3 gap-2 rounded-[var(--academy-radius)] border border-[var(--border-muted)] bg-[var(--surface-1)] p-2">
        {(Object.keys(HOMEWORK_DATA) as LectureKey[]).map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => setSelectedLecture(key)}
            className={`min-h-11 rounded-xl border px-3 text-sm font-medium transition-colors ${
              selectedLecture === key
                ? "border-[var(--color-brand-primary)]/40 bg-[var(--color-brand-primary)]/10 text-[var(--color-brand-primary)]"
                : "border-[var(--border-muted)] bg-[var(--surface-2)] text-[var(--fg-muted)] hover:text-[var(--fg-0)]"
            }`}
          >
            {key}
          </button>
        ))}
      </div>

      <ContentCard>
        <h3 className="mb-3 text-base font-semibold text-[var(--fg-0)]">필수</h3>
        <div className="space-y-3">
          {data.tasks.map((task, i) => (
            <div key={i} className="rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-3">
              <p className="mb-2 text-sm font-semibold text-[var(--fg-0)]">{task.title}</p>
              <ul className="space-y-1 text-sm text-[var(--fg-muted)]">
                {task.items.map((item, j) => (
                  <li key={j} className="flex items-start gap-2">
                    <span aria-hidden>•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </ContentCard>

      <ContentCard>
        <h3 className="mb-3 text-base font-semibold text-[var(--fg-0)]">제출</h3>
        <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-3">
          <p className="text-sm font-medium text-[var(--fg-0)]">{data.submission.channel}</p>
          {data.submission.items.length > 0 && (
            <ul className="mt-2 space-y-1 text-sm text-[var(--fg-muted)]">
              {data.submission.items.map((item, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span aria-hidden>•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          )}
          {"note" in data.submission && data.submission.note && (
            <p className="mt-2 text-xs text-[var(--fg-muted)]">{data.submission.note}</p>
          )}
        </div>
      </ContentCard>
    </div>
  );
}
