"use client";

import { useState } from "react";
import { PageHeader, ContentCard } from "./shared";
import { HOMEWORK_DATA, type LectureKey } from "../content";

export function HomeworkContent() {
  const [selectedLecture, setSelectedLecture] = useState<LectureKey>("3강");
  const data = HOMEWORK_DATA[selectedLecture];

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="과제 안내" sub={`${selectedLecture} 예정: ${data.date}`} />

      <div className="flex items-center gap-2 bg-[var(--surface-2)] rounded-xl p-1.5">
        {(Object.keys(HOMEWORK_DATA) as LectureKey[]).map((key) => (
          <button
            key={key}
            onClick={() => setSelectedLecture(key)}
            className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              selectedLecture === key
                ? "bg-[var(--color-brand-primary)] text-white"
                : "text-[var(--fg-muted)] hover:text-[var(--fg-0)] hover:bg-[var(--surface-1)]"
            }`}
          >
            {key}
          </button>
        ))}
      </div>

      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-4">필수 과제</h3>
        <div className="space-y-4">
          {data.tasks.map((task, i) => (
            <div key={i} className="p-4 rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)]">
              <p className="font-bold mb-2">{task.title}</p>
              <ul className="text-[var(--fg-muted)] text-sm space-y-1">
                {task.items.map((item, j) => (
                  <li key={j}>
                    {"highlight" in task && task.highlight && item.includes(task.highlight) ? (
                      <>
                        {item.split(task.highlight)[0]}
                        <span className="font-bold text-purple-600">{task.highlight}</span>
                        {item.split(task.highlight)[1]}
                      </>
                    ) : (
                      item
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </ContentCard>

      <ContentCard>
        <h3 className="text-lg font-bold text-[var(--fg-0)] mb-4">제출 방법</h3>
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
          <p className="text-emerald-700 dark:text-emerald-300 font-medium mb-2">{data.submission.channel}</p>
          {data.submission.items.length > 0 && (
            <ul className="text-emerald-700/80 dark:text-emerald-200/80 text-sm space-y-1">
              {data.submission.items.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          )}
        </div>
        {"note" in data.submission && data.submission.note && (
          <p className="text-[var(--fg-muted)] text-xs mt-3">{data.submission.note}</p>
        )}
      </ContentCard>
    </div>
  );
}
