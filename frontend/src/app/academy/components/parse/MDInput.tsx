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
        <h3 className="text-lg font-bold text-white">📋 MD 결과물</h3>
        <label className="cursor-pointer">
          <input
            type="file"
            accept=".md,text/markdown,text/plain"
            onChange={onFileSelect}
            className="hidden"
          />
          <span className="px-3 py-1.5 rounded-lg bg-white/10 text-gray-300 text-xs font-medium hover:bg-white/20 transition-colors flex items-center gap-2">
            <span className="material-symbols-outlined text-sm">upload_file</span>
            파일 선택
          </span>
        </label>
      </div>
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={`relative rounded-xl transition-all ${isDragging ? 'ring-2 ring-purple-500' : ''}`}
      >
        {isDragging && (
          <div className="absolute inset-0 bg-purple-500/20 rounded-xl flex items-center justify-center z-10 pointer-events-none">
            <span className="text-purple-300 font-bold">MD 파일을 여기에 놓으세요</span>
          </div>
        )}
        <textarea
          value={mdInput}
          onChange={(e) => setMdInput(e.target.value)}
          placeholder="통합빌더에서 다운로드한 MD 파일을 드래그하거나 내용을 붙여넣으세요..."
          className="w-full h-40 p-4 rounded-xl bg-black/50 border border-purple-500/30 text-gray-200 text-sm placeholder-gray-600 focus:border-purple-500/50 focus:outline-none focus:ring-1 focus:ring-purple-500/20 resize-none font-mono"
        />
      </div>
      {parseResult && (parseResult.hasOhmage || parseResult.hasVariation) && (
        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-emerald-400 text-sm flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">check_circle</span>
              파싱 완료!
            </span>
            <span className="text-gray-500 text-xs">
              오마주 {parseResult.ohmageScenes.length}개 / 변주 {parseResult.variationScenes.length}개
            </span>
          </div>
          {/* 진행도 표시 */}
          {totalPrompts > 0 && (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 transition-all duration-300"
                    style={{ width: `${(completedCount / totalPrompts) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-400">{completedCount}/{totalPrompts}</span>
              </div>
              {completedCount > 0 && (
                <button
                  onClick={onClearProgress}
                  className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
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
