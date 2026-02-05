"use client";

import type { ThresholdMode } from "../../api/sceneDetect";

interface ThresholdSelectorProps {
  thresholdMode: ThresholdMode;
  onModeChange: (mode: ThresholdMode) => void;
}

export function ThresholdSelector({ thresholdMode, onModeChange }: ThresholdSelectorProps) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-3">
        <span className="material-symbols-outlined text-purple-400 text-sm">tune</span>
        <span className="text-gray-400 text-sm font-medium">감지 모드 선택</span>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {/* 표준 모드 (기본) */}
        <button
          onClick={() => onModeChange("standard")}
          className={`relative p-4 rounded-xl border-2 transition-all text-left group ${
            thresholdMode === "standard"
              ? "border-emerald-500 bg-emerald-500/10"
              : "border-white/10 hover:border-emerald-500/30 hover:bg-emerald-500/5"
          }`}
        >
          {thresholdMode === "standard" && (
            <div className="absolute top-2 right-2">
              <span className="material-symbols-outlined text-emerald-400 text-lg">check_circle</span>
            </div>
          )}
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xl">🎯</span>
            <span className={`font-bold ${thresholdMode === "standard" ? "text-emerald-400" : "text-white"}`}>
              표준 모드
            </span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-medium">추천</span>
          </div>
          <p className="text-gray-400 text-xs leading-relaxed">
            트랜지션 효과는 무시<br/>
            <span className="text-gray-500">일반 영상 · 페이드/디졸브 있는 영상</span>
          </p>
        </button>

        {/* 정밀 모드 */}
        <button
          onClick={() => onModeChange("precise")}
          className={`relative p-4 rounded-xl border-2 transition-all text-left group ${
            thresholdMode === "precise"
              ? "border-purple-500 bg-purple-500/10"
              : "border-white/10 hover:border-purple-500/30 hover:bg-purple-500/5"
          }`}
        >
          {thresholdMode === "precise" && (
            <div className="absolute top-2 right-2">
              <span className="material-symbols-outlined text-purple-400 text-lg">check_circle</span>
            </div>
          )}
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xl">⚡</span>
            <span className={`font-bold ${thresholdMode === "precise" ? "text-purple-400" : "text-white"}`}>
              정밀 모드
            </span>
          </div>
          <p className="text-gray-400 text-xs leading-relaxed">
            빠른 컷도 놓치지 않고 감지<br/>
            <span className="text-gray-500">빠른 편집 · 많은 장면 전환</span>
          </p>
        </button>
      </div>
      <p className="mt-3 text-gray-500 text-xs flex items-center gap-1.5">
        <span className="material-symbols-outlined text-sm">info</span>
        잘 모르겠다면 <span className="text-emerald-400 font-medium">표준 모드</span>로 시작하세요
      </p>
    </div>
  );
}
