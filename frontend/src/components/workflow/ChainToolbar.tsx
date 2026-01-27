"use client";

/**
 * ChainToolbar - Save/Load UI for chain sessions
 *
 * Provides:
 * - Save button with status indicator
 * - Load dropdown with recent sessions
 * - Share URL copy
 * - Clear/reset button
 *
 * P7+ Chain UX Enhancement
 */

import { useState, useCallback, useEffect } from "react";
import { useChainPersistence } from "@/hooks/useChainPersistence";
import { useDimensionChain } from "@/contexts/DimensionChainContext";
import { ConflictResolutionModal } from "./ConflictResolutionModal";
import type { ChainSessionListItem } from "@/lib/api";

interface ChainToolbarProps {
  /** Position variant */
  position?: "header" | "sidebar" | "floating";
  /** Whether to show session history dropdown */
  showHistory?: boolean;
  /** IP slug for project association */
  ipSlug?: string;
  /** Compact mode (icons only) */
  compact?: boolean;
}

export function ChainToolbar({
  position = "header",
  showHistory = true,
  ipSlug,
  compact = false,
}: ChainToolbarProps) {
  const chain = useDimensionChain();
  const {
    sessionId,
    version,
    isSaving,
    lastSaved,
    isDirty,
    conflictState,
    syncStatus,
    saveToServer,
    loadFromServer,
    createNewSession,
    listSessions,
    resolveConflict,
    clearConflict,
  } = useChainPersistence({ ipSlug });

  const [sessions, setSessions] = useState<ChainSessionListItem[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Load sessions list
  const loadSessions = useCallback(async () => {
    setIsLoading(true);
    try {
      const list = await listSessions();
      setSessions(list);
    } finally {
      setIsLoading(false);
    }
  }, [listSessions]);

  // Handle save
  const handleSave = useCallback(async () => {
    if (!sessionId) {
      // Create new session first
      await createNewSession();
    }
    await saveToServer();
  }, [sessionId, createNewSession, saveToServer]);

  // Handle load session
  const handleLoadSession = useCallback(
    async (loadSessionId: string) => {
      setShowDropdown(false);
      await loadFromServer(loadSessionId);
    },
    [loadFromServer]
  );

  // Handle share
  const handleShare = useCallback(() => {
    if (!sessionId) return;

    const url = new URL(window.location.href);
    url.searchParams.set("chain", sessionId);

    navigator.clipboard.writeText(url.toString());
    // TODO: Show toast notification
  }, [sessionId]);

  // Handle clear
  const handleClear = useCallback(() => {
    chain.clearChain();
  }, [chain]);

  // Status icon based on sync status
  const statusIcon = (() => {
    switch (syncStatus) {
      case "syncing":
        return (
          <svg className="w-4 h-4 animate-spin text-blue-400" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        );
      case "synced":
        return (
          <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case "error":
        return (
          <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      case "conflict":
        return (
          <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        );
      default:
        return isDirty ? (
          <svg className="w-4 h-4 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01" />
          </svg>
        ) : null;
    }
  })();

  // Container classes based on position
  const containerClasses = {
    header: "flex items-center gap-2",
    sidebar: "flex flex-col gap-2",
    floating: "fixed bottom-4 right-4 flex items-center gap-2 bg-zinc-900/95 backdrop-blur-sm border border-zinc-700 rounded-lg p-2 shadow-lg",
  };

  return (
    <>
      <div className={containerClasses[position]}>
        {/* Save button */}
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-sm text-zinc-300 transition-colors disabled:opacity-50"
          title={lastSaved ? `Last saved: ${lastSaved.toLocaleTimeString()}` : "Save to cloud"}
        >
          {isSaving ? (
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
            </svg>
          )}
          {!compact && <span>{isSaving ? "저장 중..." : "저장"}</span>}
          {statusIcon}
        </button>

        {/* Load dropdown */}
        {showHistory && (
          <div className="relative">
            <button
              onClick={() => {
                setShowDropdown(!showDropdown);
                if (!showDropdown) loadSessions();
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-sm text-zinc-300 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              {!compact && <span>불러오기</span>}
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {showDropdown && (
              <div className="absolute top-full mt-1 right-0 w-64 bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl z-50">
                <div className="p-2 border-b border-zinc-800">
                  <span className="text-xs text-zinc-500">최근 세션</span>
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {isLoading ? (
                    <div className="p-4 text-center text-sm text-zinc-500">
                      로딩 중...
                    </div>
                  ) : sessions.length === 0 ? (
                    <div className="p-4 text-center text-sm text-zinc-500">
                      저장된 세션이 없습니다
                    </div>
                  ) : (
                    sessions.map((session) => (
                      <button
                        key={session.id}
                        onClick={() => handleLoadSession(session.id)}
                        className="w-full px-3 py-2 text-left hover:bg-zinc-800 transition-colors"
                      >
                        <div className="text-sm text-white truncate">
                          {session.title || "Untitled"}
                        </div>
                        <div className="text-xs text-zinc-500 flex items-center gap-2">
                          <span>{session.mega_app || "General"}</span>
                          <span>·</span>
                          <span>{session.dimension_count} dimensions</span>
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Share button */}
        {sessionId && (
          <button
            onClick={handleShare}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-sm text-zinc-300 transition-colors"
            title="Copy share URL"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
            {!compact && <span>공유</span>}
          </button>
        )}

        {/* Clear button */}
        <button
          onClick={handleClear}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-zinc-800 hover:bg-red-900/50 border border-zinc-700 hover:border-red-800 text-sm text-zinc-300 hover:text-red-300 transition-colors"
          title="Clear all chain data"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          {!compact && <span>초기화</span>}
        </button>
      </div>

      {/* Conflict resolution modal */}
      <ConflictResolutionModal
        isOpen={syncStatus === "conflict"}
        conflict={conflictState}
        onResolve={resolveConflict}
        onClose={clearConflict}
      />
    </>
  );
}
