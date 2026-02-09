"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowUpRight, Loader2, Sparkles } from "lucide-react";

const SUGGESTIONS = [
  "캐릭터 쇼츠 기획",
  "브랜드 영상 콘셉트",
  "유튜브 시리즈 포맷",
];

const TARGET_OPTIONS = [
  { key: "dna-lab", label: "DNA Lab" },
  { key: "flow", label: "Flow" },
  { key: "story-engine", label: "Story Engine" },
] as const;

type TargetKey = (typeof TARGET_OPTIONS)[number]["key"];

const TARGET_CTA_LABEL: Record<TargetKey, string> = {
  "dna-lab": "DNA Lab에서 시작",
  flow: "Flow에서 시작",
  "story-engine": "Story Engine에서 시작",
};

export function StudioIntentInput() {
  const router = useRouter();
  const [intent, setIntent] = useState("");
  const [target, setTarget] = useState<TargetKey>("dna-lab");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const buttonLabel = TARGET_CTA_LABEL[target];

  const submitIntent = useCallback(() => {
    const trimmed = intent.trim();
    if (!trimmed || isSubmitting) return;
    setIsSubmitting(true);
    const query = `intent=${encodeURIComponent(trimmed)}`;
    const path =
      target === "dna-lab"
        ? `/dna-lab?${query}`
        : target === "flow"
          ? `/flow?${query}`
          : `/story-engine?${query}`;
    router.push(path);
    // Fallback to prevent sticky loading UI when navigation is interrupted.
    window.setTimeout(() => setIsSubmitting(false), 1500);
  }, [intent, isSubmitting, router, target]);

  return (
    <section className="relative rounded-[20px] p-[1px] bg-gradient-to-r from-sky-400/70 via-amber-300/60 to-sky-400/70 animate-gradient-x">
      <div className="rounded-[20px] border border-[var(--border-muted)]/80 bg-[var(--surface-1)]/85 p-4 backdrop-blur-sm sm:p-5">
        <div className="mb-3 flex items-center justify-between gap-2">
          <p className="text-sm font-semibold text-[var(--fg-0)]">무엇을 만들고 싶나요?</p>
          <Sparkles className="h-4 w-4 text-[var(--accent)]" aria-hidden="true" />
        </div>

        <div className="mb-3 inline-flex rounded-lg border border-[var(--border-muted)] bg-[var(--bg-1)]/70 p-1">
          {TARGET_OPTIONS.map((item) => {
            const active = target === item.key;
            return (
              <button
                key={item.key}
                type="button"
                onClick={() => setTarget(item.key)}
                className={`rounded-md px-2.5 py-1 text-xs font-medium transition ${
                  active
                    ? "bg-[var(--accent)] text-slate-950"
                    : "text-[var(--fg-muted)] hover:text-[var(--fg-0)]"
                }`}
              >
                {item.label}
              </button>
            );
          })}
        </div>

        <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-1)]/70 p-3">
          <textarea
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
            disabled={isSubmitting}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submitIntent();
              }
            }}
            rows={3}
            placeholder="예: 캐릭터 일관성 유지되는 30초 브랜디드 티저"
            className="w-full resize-none bg-transparent text-sm text-[var(--fg-0)] outline-none placeholder:text-[var(--fg-subtle)]"
            aria-label="스튜디오 의도 입력"
          />
          <p className="mt-2 text-[11px] text-[var(--fg-subtle)]">
            Enter로 실행, Shift + Enter 줄바꿈
          </p>
          <div className="mt-3 flex items-center justify-between gap-2">
            <div className="flex flex-wrap gap-1.5">
              {SUGGESTIONS.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setIntent(item)}
                  className="rounded-full border border-[var(--border-muted)] px-2.5 py-1 text-xs text-[var(--fg-muted)] transition hover:border-[var(--accent)]/60 hover:text-[var(--fg-0)]"
                >
                  {item}
                </button>
              ))}
            </div>
            <button
              type="button"
              onClick={submitIntent}
              disabled={isSubmitting || !intent.trim()}
              className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--accent)] px-3 py-1.5 text-xs font-semibold text-slate-950 transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                  이동 중...
                </>
              ) : (
                <>
                  {buttonLabel}
                  <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

export default StudioIntentInput;
