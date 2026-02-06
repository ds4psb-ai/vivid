"use client";

import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import type { ThresholdMode } from "../../api/sceneDetect";
import { SceneTimeline } from "./SceneTimeline";

interface DetectionResultsProps {
  detectedTimestamps: string[];
  usedThresholdMode: ThresholdMode;
  uploadedFile: File | null;
  isDownloading: boolean;
  backendVideoDuration: number;
  onTimestampsChange: (timestamps: string[]) => void;
  onReset: () => void;
  onReanalyze: (mode: ThresholdMode) => void;
  onDownloadFrames: () => void;
  previewId: string | null;
}

export function DetectionResults({
  detectedTimestamps,
  usedThresholdMode,
  uploadedFile,
  isDownloading,
  backendVideoDuration,
  onTimestampsChange,
  onReset,
  onReanalyze,
  onDownloadFrames,
  previewId,
}: DetectionResultsProps) {
  const [copied, setCopied] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [localDuration, setLocalDuration] = useState(0);
  const [errorVideoUrl, setErrorVideoUrl] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const rafRef = useRef<number | null>(null);

  const backendUrl = process.env.NEXT_PUBLIC_API_URL || "";
  const serverVideoUrl = previewId
    ? `${backendUrl}/api/v1/scene-detect/preview/${previewId}`
    : null;

  const blobUrl = useMemo(
    () => (uploadedFile ? URL.createObjectURL(uploadedFile) : null),
    [uploadedFile]
  );

  useEffect(() => {
    return () => {
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
  }, [blobUrl]);

  const [failedPreviewId, setFailedPreviewId] = useState<string | null>(null);
  const serverFailed = !!previewId && failedPreviewId === previewId;
  const videoUrl = serverVideoUrl && !serverFailed ? serverVideoUrl : blobUrl;
  const videoError = !!videoUrl && errorVideoUrl === videoUrl;

  const addDebug = useCallback((msg: string) => {
    if (process.env.NODE_ENV !== "production") {
      console.debug(`[VideoDebug] ${msg}`);
    }
  }, []);

  const markServerFailed = useCallback(() => {
    if (previewId) setFailedPreviewId(previewId);
  }, [previewId]);

  const videoDuration = backendVideoDuration > 0 ? backendVideoDuration : localDuration;

  const handleTimeUpdate = useCallback(() => {
    if (rafRef.current) return;
    rafRef.current = requestAnimationFrame(() => {
      if (videoRef.current) {
        setCurrentTime(videoRef.current.currentTime);
      }
      rafRef.current = null;
    });
  }, []);

  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  const handleSeek = useCallback((seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      setCurrentTime(seconds);
    }
  }, []);

  const formatForBuilder1 = () => detectedTimestamps.join("\n");

  const handleCopy = async () => {
    const formatted = formatForBuilder1();
    if (!formatted) return;

    await navigator.clipboard.writeText(formatted);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-3">
        <div className="inline-flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px] text-emerald-500" aria-hidden>
            check_circle
          </span>
          <p className="text-sm font-semibold text-[var(--fg-0)]">
            {detectedTimestamps.length}개 씬
          </p>
          <span className="rounded-full border border-[var(--border-muted)] px-2 py-0.5 text-xs text-[var(--fg-muted)]">
            {usedThresholdMode === "precise" ? "정밀" : "표준"}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {uploadedFile && usedThresholdMode === "standard" && (
            <button
              type="button"
              onClick={() => onReanalyze("precise")}
              className="inline-flex min-h-10 items-center rounded-lg border border-[var(--border-muted)] bg-[var(--surface-1)] px-3 text-xs font-medium text-[var(--fg-0)] hover:bg-[var(--surface-3)]"
            >
              정밀 재분석
            </button>
          )}
          {uploadedFile && usedThresholdMode === "precise" && (
            <button
              type="button"
              onClick={() => onReanalyze("standard")}
              className="inline-flex min-h-10 items-center rounded-lg border border-[var(--border-muted)] bg-[var(--surface-1)] px-3 text-xs font-medium text-[var(--fg-0)] hover:bg-[var(--surface-3)]"
            >
              표준 재분석
            </button>
          )}
          <button
            type="button"
            onClick={onReset}
            className="inline-flex min-h-10 items-center rounded-lg border border-[var(--border-muted)] bg-[var(--surface-1)] px-3 text-xs font-medium text-[var(--fg-muted)] hover:text-[var(--fg-0)]"
          >
            초기화
          </button>
        </div>
      </div>

      {uploadedFile ? (
        <div className="space-y-3">
          <div className="overflow-hidden rounded-xl border border-[var(--border-muted)] bg-black/70">
            {videoError ? (
              <div className="flex flex-col items-center justify-center gap-2 py-10">
                <span className="material-symbols-outlined text-[22px] text-gray-500" aria-hidden>
                  error_outline
                </span>
                <p className="text-sm text-gray-400">비디오를 재생할 수 없습니다</p>
                <button
                  type="button"
                  onClick={() => setErrorVideoUrl(null)}
                  className="rounded-lg border border-white/20 px-3 py-1.5 text-xs text-gray-300 hover:bg-white/10"
                >
                  다시 시도
                </button>
              </div>
            ) : videoUrl ? (
              <video
                key={videoUrl}
                ref={videoRef}
                src={videoUrl || undefined}
                preload="auto"
                controls
                playsInline
                className="max-h-[420px] w-full bg-black object-contain"
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={(e) => {
                  setLocalDuration(e.currentTarget.duration);
                }}
                onError={(e) => {
                  const vid = e.currentTarget;
                  const err = vid.error;
                  const errDetail = err
                    ? `code=${err.code}, msg=${err.message}`
                    : "no error object";
                  addDebug(`VIDEO onError: ${errDetail}`);

                  if (serverVideoUrl && !serverFailed) {
                    markServerFailed();
                  } else {
                    setErrorVideoUrl(videoUrl ?? "__no_url__");
                  }
                }}
              />
            ) : (
              <div className="flex items-center justify-center py-8">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-white/20 border-t-white/60" />
              </div>
            )}
          </div>

          <SceneTimeline
            file={uploadedFile}
            timestamps={detectedTimestamps}
            videoDuration={videoDuration}
            currentTime={currentTime}
            onTimestampsChange={onTimestampsChange}
            onSeek={handleSeek}
          />
        </div>
      ) : (
        <pre className="rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-3 font-mono text-xs text-[var(--fg-muted)]">
          {formatForBuilder1()}
        </pre>
      )}

      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={handleCopy}
          className={`inline-flex min-h-11 items-center justify-center rounded-xl px-4 text-sm font-semibold transition-colors ${
            copied
              ? "bg-emerald-500 text-white"
              : "bg-[var(--fg-0)] text-[var(--bg-0)] hover:opacity-90"
          }`}
        >
          {copied ? "복사됨" : "복사"}
        </button>

        <button
          type="button"
          onClick={onDownloadFrames}
          disabled={isDownloading}
          className={`inline-flex min-h-11 items-center justify-center rounded-xl bg-[var(--color-brand-primary)] px-4 text-sm font-semibold text-white transition-opacity ${
            isDownloading ? "cursor-not-allowed opacity-70" : "hover:opacity-90"
          }`}
        >
          {isDownloading ? "저장 중" : "저장"}
        </button>
      </div>
    </div>
  );
}
