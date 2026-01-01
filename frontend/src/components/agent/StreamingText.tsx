"use client";

import { useMemo } from "react";
import { canUseClipboard, copyToClipboard } from "@/lib/clipboard";

interface Segment {
  type: "text" | "code";
  value: string;
  lang?: string;
}

const parseSegments = (content: string): Segment[] => {
  const segments: Segment[] = [];
  const fenceRegex = /```(\w+)?\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = fenceRegex.exec(content))) {
    if (match.index > lastIndex) {
      segments.push({
        type: "text",
        value: content.slice(lastIndex, match.index),
      });
    }
    segments.push({
      type: "code",
      lang: match[1],
      value: match[2].replace(/\n$/, ""),
    });
    lastIndex = fenceRegex.lastIndex;
  }
  if (lastIndex < content.length) {
    segments.push({
      type: "text",
      value: content.slice(lastIndex),
    });
  }
  return segments;
};

export default function StreamingText({ content, className }: { content: string; className?: string }) {
  const segments = useMemo(() => parseSegments(content), [content]);
  const canCopy = canUseClipboard();

  return (
    <div className={`space-y-3 ${className ?? ""}`}>
      {segments.map((segment, index) => {
        if (!segment.value) return null;
        if (segment.type === "code") {
          return (
            <div
              key={`${segment.type}-${index}`}
              className="rounded-xl border border-white/10 bg-slate-950/70 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.02)]"
            >
              <div className="flex items-center justify-between px-3 py-2 text-[10px] uppercase tracking-[0.2em] text-slate-400">
                <span>{segment.lang || "code"}</span>
                {canCopy && (
                  <button
                    type="button"
                    onClick={() => copyToClipboard(segment.value)}
                    className="rounded-full border border-white/10 px-2 py-1 text-[10px] text-slate-300 hover:border-white/20 hover:text-white"
                  >
                    Copy
                  </button>
                )}
              </div>
              <pre className="overflow-x-auto px-3 pb-3 text-xs text-slate-200">
                <code>{segment.value}</code>
              </pre>
            </div>
          );
        }
        return (
          <p key={`${segment.type}-${index}`} className="whitespace-pre-wrap text-sm leading-relaxed text-slate-100">
            {segment.value}
          </p>
        );
      })}
    </div>
  );
}
