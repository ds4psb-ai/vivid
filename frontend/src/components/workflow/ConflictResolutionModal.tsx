"use client";

/**
 * ConflictResolutionModal - Handle version conflicts in chain sessions
 *
 * When two clients update the same session, the server detects the conflict
 * via optimistic locking. This modal lets the user choose which version to keep.
 *
 * P7+ Chain UX Enhancement
 */

import { useCallback } from "react";

interface ConflictData {
  serverVersion: number;
  localVersion: number;
}

interface ConflictResolutionModalProps {
  isOpen: boolean;
  conflict: ConflictData | null;
  onResolve: (strategy: "keep_local" | "use_server") => Promise<void>;
  onClose: () => void;
}

export function ConflictResolutionModal({
  isOpen,
  conflict,
  onResolve,
  onClose,
}: ConflictResolutionModalProps) {
  const handleKeepLocal = useCallback(async () => {
    await onResolve("keep_local");
  }, [onResolve]);

  const handleUseServer = useCallback(async () => {
    await onResolve("use_server");
  }, [onResolve]);

  if (!isOpen || !conflict) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center">
            <svg
              className="w-5 h-5 text-amber-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">동기화 충돌</h3>
            <p className="text-sm text-zinc-400">
              다른 곳에서 변경사항이 발생했습니다
            </p>
          </div>
        </div>

        {/* Version Info */}
        <div className="bg-zinc-800/50 rounded-lg p-4 mb-4 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-zinc-400">내 버전</span>
            <span className="text-white font-mono">v{conflict.localVersion}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-zinc-400">서버 버전</span>
            <span className="text-white font-mono">v{conflict.serverVersion}</span>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-zinc-400 mb-6">
          작업 중 다른 기기나 탭에서 변경사항이 저장되었습니다.
          어떤 버전을 유지하시겠습니까?
        </p>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={handleUseServer}
            className="flex-1 px-4 py-2.5 rounded-lg border border-zinc-700 text-zinc-300 hover:bg-zinc-800 transition-colors text-sm font-medium"
          >
            서버 버전 사용
            <span className="block text-xs text-zinc-500 mt-0.5">
              내 변경사항 폐기
            </span>
          </button>
          <button
            onClick={handleKeepLocal}
            className="flex-1 px-4 py-2.5 rounded-lg bg-blue-600 text-white hover:bg-blue-500 transition-colors text-sm font-medium"
          >
            내 버전 유지
            <span className="block text-xs text-blue-200/70 mt-0.5">
              서버에 덮어쓰기
            </span>
          </button>
        </div>

        {/* Close button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 p-1 text-zinc-500 hover:text-zinc-300 transition-colors"
          aria-label="충돌 해결 모달 닫기"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}
