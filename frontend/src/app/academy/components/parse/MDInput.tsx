"use client";

import type { Builder2ParseResult } from "@/lib/builder2-md-parser";
import { ContentCard } from "../shared";

interface MDInputProps {
  mdInput: string;
  setMdInput: (input: string) => void;
  parseResult: Builder2ParseResult | null;
  isDragging: boolean;
  totalPrompts: number;
  completedCount: number;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onClearProgress: () => void;
}

export function MDInput({
  mdInput,
  setMdInput,
  parseResult,
  isDragging,
  totalPrompts,
  completedCount,
  onDragOver,
  onDragLeave,
  onDrop,
  onFileSelect,
  onClearProgress,
}: MDInputProps) {
  return (
    <ContentCard highlight>
      <div className="mb-3 flex items-center justify-between gap-3">
        <h3 className="text-base font-semibold text-[var(--fg-0)]">MD</h3>
        <label className="cursor-pointer">
          <input
            type="file"
            accept=".md,text/markdown,text/plain"
            onChange={onFileSelect}
            className="hidden"
          />
          <span className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-[var(--border-muted)] bg-[var(--surface-2)] px-3 text-xs font-medium text-[var(--fg-0)] transition-colors hover:bg-[var(--surface-3)]">
            <span className="material-symbols-outlined text-[16px]" aria-hidden>
              add
            </span>
            파일
          </span>
        </label>
      </div>

      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={`relative rounded-xl ${isDragging ? "ring-2 ring-[var(--color-brand-primary)]/40" : ""}`}
      >
        {isDragging && (
          <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center rounded-xl bg-[var(--color-brand-primary)]/10 text-sm font-medium text-[var(--color-brand-primary)]">
            여기에 드롭
          </div>
        )}
        <textarea
          value={mdInput}
          onChange={(e) => setMdInput(e.target.value)}
          placeholder="MD 붙여넣기 또는 드래그 앤 드롭"
          className="h-44 w-full resize-none rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-3 font-mono text-sm text-[var(--fg-0)] placeholder:text-[var(--fg-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-primary)]/25"
        />
      </div>

      {parseResult && (parseResult.hasOhmage || parseResult.hasVariation) && (
        <div className="mt-3 flex items-center justify-between gap-3 text-sm">
          <p className="text-[var(--fg-muted)]">
            O {parseResult.ohmageScenes.length} / V {parseResult.variationScenes.length}
          </p>
          {totalPrompts > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-[var(--fg-muted)]">
                {completedCount}/{totalPrompts}
              </span>
              {completedCount > 0 && (
                <button
                  type="button"
                  onClick={onClearProgress}
                  className="text-xs text-[var(--fg-muted)] underline-offset-2 hover:underline"
                >
                  초기화
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </ContentCard>
  );
}
