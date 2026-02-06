"use client";

import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import type { ThresholdMode } from "../../api/sceneDetect";
import { SceneTimeline } from "./SceneTimeline";
import { parseTimestampToSeconds } from "../../hooks/useFrameExtractor";

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
  const [compareIndex, setCompareIndex] = useState<number | null>(null);
  const [capturedFrame, setCapturedFrame] = useState<string | null>(null);
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

  const captureVideoFrame = useCallback((): string | null => {
    const video = videoRef.current;
    if (!video || video.readyState < 2) return null;

    const canvas = document.createElement("canvas");
    canvas.width = 320;
    canvas.height = 180;

    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    const scale = Math.min(320 / video.videoWidth, 180 / video.videoHeight);
    const w = video.videoWidth * scale;
    const h = video.videoHeight * scale;

    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, 320, 180);
    ctx.drawImage(video, (320 - w) / 2, (180 - h) / 2, w, h);

    return canvas.toDataURL("image/jpeg", 0.8);
  }, []);

  const handleCompare = useCallback(
    (index: number | null) => {
      if (index === null) {
        setCompareIndex(null);
        setCapturedFrame(null);
        return;
      }

      setCompareIndex(index);
      const ts = detectedTimestamps[index];

      if (ts && videoRef.current) {
        const seconds = parseTimestampToSeconds(ts);
        videoRef.current.currentTime = seconds;
        setCurrentTime(seconds);

        const onSeeked = () => {
          videoRef.current?.removeEventListener("seeked", onSeeked);
          setCapturedFrame(captureVideoFrame());
        };

        videoRef.current.addEventListener("seeked", onSeeked);
      }
    },
    [detectedTimestamps, captureVideoFrame]
  );

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
            compareIndex={compareIndex}
            onCompare={handleCompare}
          />

          {compareIndex !== null && detectedTimestamps[compareIndex] && (
            <ComparePanel
              compareIndex={compareIndex}
              timestamp={detectedTimestamps[compareIndex]}
              capturedFrame={capturedFrame}
              onClose={() => {
                setCompareIndex(null);
                setCapturedFrame(null);
              }}
            />
          )}
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

function ComparePanel({
  compareIndex,
  timestamp,
  capturedFrame,
  onClose,
}: {
  compareIndex: number;
  timestamp: string;
  capturedFrame: string | null;
  onClose: () => void;
}) {
  return (
    <div className="space-y-3 rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-[var(--fg-0)]">
          Scene {compareIndex + 1} · {timestamp}
        </p>
        <button
          type="button"
          onClick={onClose}
          className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-[var(--border-muted)] text-[var(--fg-muted)] hover:text-[var(--fg-0)]"
        >
          <span className="material-symbols-outlined text-[16px]" aria-hidden>
            close
          </span>
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <p className="text-xs text-[var(--fg-muted)]">Video</p>
          <div className="flex aspect-video items-center justify-center overflow-hidden rounded-lg border border-[var(--border-muted)] bg-black/50">
            {capturedFrame ? (
              <img src={capturedFrame} alt="Video frame" className="h-full w-full object-contain" />
            ) : (
              <span className="text-xs text-gray-400">캡처 중</span>
            )}
          </div>
        </div>

        <div className="space-y-1">
          <p className="text-xs text-[var(--fg-muted)]">Extracted</p>
          <div className="flex aspect-video items-center justify-center overflow-hidden rounded-lg border border-[var(--border-muted)] bg-black/50">
            <CompareThumb timestamp={timestamp} />
          </div>
        </div>
      </div>
    </div>
  );
}

function CompareThumb({ timestamp }: { timestamp: string }) {
  const thumbUrl = useMemo(() => {
    if (typeof document === "undefined") return null;
    const imgs = document.querySelectorAll<HTMLImageElement>("img[alt^='Scene ']");
    for (const img of imgs) {
      const card = img.closest("[class*='flex-shrink-0']");
      if (card) {
        const tsText = card.querySelector(".font-mono")?.textContent;
        if (tsText?.trim() === timestamp) return img.src;
      }
    }
    return null;
  }, [timestamp]);

  if (thumbUrl) {
    return <img src={thumbUrl} alt="Extracted thumbnail" className="h-full w-full object-contain" />;
  }

  return <span className="text-xs text-gray-400">썸네일 없음</span>;
}
