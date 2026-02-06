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
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-[var(--fg-0)]">MD</h3>
        <label className="cursor-pointer">
          <input
            type="file"
            accept=".md,text/markdown,text/plain"
            onChange={onFileSelect}
            className="hidden"
          />
          <span className="px-3 py-1.5 rounded-lg border border-[var(--border-muted)] bg-[var(--surface-2)] text-[var(--fg-muted)] text-xs font-medium hover:bg-[var(--surface-3)] hover:text-[var(--fg-0)] transition-colors flex items-center gap-2">
            <span className="material-symbols-outlined text-sm">upload_file</span>
            파일 선택
          </span>
        </label>
      </div>
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={`relative rounded-xl transition-all ${isDragging ? 'ring-2 ring-[var(--color-brand-primary)]' : ''}`}
      >
        {isDragging && (
          <div className="absolute inset-0 bg-[var(--color-brand-primary)]/15 rounded-xl flex items-center justify-center z-10 pointer-events-none">
            <span className="text-[var(--color-brand-primary)] font-bold">MD 파일을 여기에 놓으세요</span>
          </div>
        )}
        <textarea
          value={mdInput}
          onChange={(e) => setMdInput(e.target.value)}
          placeholder="MD 붙여넣기"
          className="w-full h-40 p-4 rounded-xl bg-[var(--surface-2)] border border-[var(--border-muted)] text-[var(--fg-0)] text-sm placeholder:text-[var(--fg-muted)] focus:border-[var(--color-brand-primary)]/40 focus:outline-none focus:ring-1 focus:ring-[var(--color-brand-primary)]/20 resize-none font-mono"
        />
      </div>
      {parseResult && (parseResult.hasOhmage || parseResult.hasVariation) && (
        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-emerald-600 dark:text-emerald-400 text-sm flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">check_circle</span>
              완료
            </span>
            <span className="text-[var(--fg-muted)] text-xs">
              O {parseResult.ohmageScenes.length} / V {parseResult.variationScenes.length}
            </span>
          </div>
          {/* 진행도 표시 */}
          {totalPrompts > 0 && (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-[var(--surface-3)] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-600 dark:bg-emerald-500 transition-all duration-300"
                    style={{ width: `${(completedCount / totalPrompts) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-[var(--fg-muted)]">{completedCount}/{totalPrompts}</span>
              </div>
              {completedCount > 0 && (
                <button
                  onClick={onClearProgress}
                  className="text-xs text-[var(--fg-muted)] hover:text-[var(--fg-0)] transition-colors"
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
