"use client";

import { useCallback, useState } from "react";
import {
  parseStateMd,
  type ParsedState,
  calculateOverallCompletion,
  getSceneStats,
  findAnchorScene,
  parsedStateToJson,
} from "@/lib/state-md-parser";
import { api } from "@/lib/api";

interface StateMdImportProps {
  projectId: string;
  onSyncComplete?: () => void;
}

export function StateMdImport({ projectId, onSyncComplete }: StateMdImportProps) {
  const [content, setContent] = useState<string | null>(null);
  const [parsed, setParsed] = useState<ParsedState | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFileRead = useCallback((file: File) => {
    setError(null);
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      try {
        setContent(text);
        const result = parseStateMd(text);
        setParsed(result);
      } catch (err) {
        setError("Failed to parse STATE.md file");
        console.error(err);
      }
    };
    reader.onerror = () => {
      setError("Failed to read file");
    };
    reader.readAsText(file);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragActive(false);

      const file = e.dataTransfer.files[0];
      if (file && (file.name.endsWith(".md") || file.type === "text/markdown")) {
        handleFileRead(file);
      } else {
        setError("Please drop a .md file");
      }
    },
    [handleFileRead]
  );

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragActive(false);
  }, []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        handleFileRead(file);
      }
    },
    [handleFileRead]
  );

  const handleSync = async () => {
    if (!content || !parsed) return;
    setSyncing(true);
    setError(null);
    try {
      await api.syncPromptyState(projectId, parsedStateToJson(parsed));
      onSyncComplete?.();
    } catch (err) {
      setError("Failed to sync state to project");
      console.error(err);
    } finally {
      setSyncing(false);
    }
  };

  const handleReset = () => {
    setContent(null);
    setParsed(null);
    setError(null);
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      {!parsed && (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${
              dragActive
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50"
            }`}
        >
          <input
            type="file"
            accept=".md,text/markdown"
            onChange={handleFileSelect}
            className="hidden"
            id="state-md-input"
          />
          <label htmlFor="state-md-input" className="cursor-pointer">
            <div className="text-4xl mb-2">📄</div>
            <p className="text-muted-foreground">
              STATE.md 파일을 드래그하거나 클릭하세요
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              로컬 프로젝트의 STATE.md 파일을 가져와 동기화합니다
            </p>
          </label>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-destructive/10 text-destructive rounded-lg p-3 text-sm">
          {error}
        </div>
      )}

      {/* Parsed Preview */}
      {parsed && (
        <div className="space-y-4 border border-border rounded-lg p-4">
          {/* Header */}
          <div className="flex justify-between items-start">
            <div>
              <h3 className="font-semibold text-lg">
                {parsed.projectName || "Untitled Project"}
              </h3>
              {parsed.lastUpdated && (
                <p className="text-xs text-muted-foreground">
                  Last Updated: {parsed.lastUpdated}
                </p>
              )}
            </div>
            <button
              onClick={handleReset}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              다시 선택
            </button>
          </div>

          {/* Overall Completion */}
          <div className="flex items-center gap-4">
            <span className="text-2xl font-bold text-primary">
              {calculateOverallCompletion(parsed)}%
            </span>
            <span className="text-muted-foreground">전체 진행률</span>
          </div>

          {/* Stage Progress */}
          {parsed.overallProgress.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Stage Progress</h4>
              {parsed.overallProgress.map((p) => (
                <div key={p.stage} className="flex items-center gap-3">
                  <span className="w-32 text-sm text-muted-foreground">
                    {p.name}
                  </span>
                  <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all"
                      style={{ width: `${p.percent}%` }}
                    />
                  </div>
                  <span className="w-10 text-sm text-right">{p.percent}%</span>
                </div>
              ))}
            </div>
          )}

          {/* Scene Progress Table */}
          {parsed.scenes.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Scene Progress</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-muted-foreground">
                      <th className="py-2 pr-4">Scene</th>
                      <th className="py-2 pr-4">Status</th>
                      <th className="py-2 pr-4">Image</th>
                      <th className="py-2 pr-4">Video</th>
                    </tr>
                  </thead>
                  <tbody>
                    {parsed.scenes.map((s) => (
                      <tr key={s.scene} className="border-b border-border/50">
                        <td className="py-2 pr-4">
                          {s.isAnchor ? (
                            <span className="text-primary font-medium">
                              ⭐ {s.scene} (ANCHOR)
                            </span>
                          ) : (
                            s.scene
                          )}
                        </td>
                        <td className="py-2 pr-4">{s.status}</td>
                        <td className="py-2 pr-4">
                          {s.image ? (
                            <span className="text-green-500">✓</span>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </td>
                        <td className="py-2 pr-4">
                          {s.video ? (
                            <span className="text-green-500">✓</span>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Scene Stats */}
              {(() => {
                const stats = getSceneStats(parsed);
                return (
                  <div className="flex gap-4 text-xs text-muted-foreground">
                    <span>Total: {stats.total}</span>
                    <span className="text-green-500">✅ {stats.completed}</span>
                    <span className="text-yellow-500">🔄 {stats.inProgress}</span>
                    <span>⬜ {stats.pending}</span>
                  </div>
                );
              })()}
            </div>
          )}

          {/* Current Task */}
          {parsed.currentTask && (
            <div className="space-y-1">
              <h4 className="text-sm font-medium">Current Task</h4>
              <p className="text-sm text-muted-foreground bg-muted rounded px-3 py-2">
                {parsed.currentTask}
              </p>
            </div>
          )}

          {/* Blockers */}
          {parsed.blockers.length > 0 && (
            <div className="space-y-1">
              <h4 className="text-sm font-medium text-destructive">
                Blockers ({parsed.blockers.length})
              </h4>
              <ul className="text-sm space-y-1">
                {parsed.blockers.map((b, i) => (
                  <li key={i} className="text-muted-foreground">
                    • {b.issue}: {b.solution}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Sync Button */}
          <button
            onClick={handleSync}
            disabled={syncing}
            className="w-full py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 transition flex items-center justify-center gap-2"
          >
            {syncing ? (
              <>
                <span className="animate-spin">⏳</span>
                <span>Syncing...</span>
              </>
            ) : (
              <>
                <span>🔄</span>
                <span>Sync to Project</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}

export default StateMdImport;
