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
  previewError: string | null;
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
  previewError,
}: DetectionResultsProps) {
  const [copied, setCopied] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [localDuration, setLocalDuration] = useState(0);
  const [errorVideoUrl, setErrorVideoUrl] = useState<string | null>(null);
  const [compareIndex, setCompareIndex] = useState<number | null>(null);
  const [capturedFrame, setCapturedFrame] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const rafRef = useRef<number | null>(null);

  // 서버 트랜스코딩 preview URL (백엔드 직접 — Range 지원 + CORS OK)
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || '';
  const serverVideoUrl = previewId
    ? `${backendUrl}/api/v1/scene-detect/preview/${previewId}`
    : null;

  const blobUrl = useMemo(
    () => (uploadedFile ? URL.createObjectURL(uploadedFile) : null),
    [uploadedFile],
  );

  useEffect(() => {
    return () => {
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
  }, [blobUrl]);

  // 서버 preview 실패 시 blob fallback
  const [failedPreviewId, setFailedPreviewId] = useState<string | null>(null);
  const serverFailed = !!previewId && failedPreviewId === previewId;
  const videoUrl = (serverVideoUrl && !serverFailed) ? serverVideoUrl : blobUrl;
  const videoError = !!videoUrl && errorVideoUrl === videoUrl;
  const addDebug = useCallback((msg: string) => {
    console.log(`[VideoDebug] ${msg}`);
  }, []);

  const markServerFailed = useCallback(() => {
    if (previewId) setFailedPreviewId(previewId);
  }, [previewId]);

  // Log URL resolution
  useEffect(() => {
    addDebug(`URL resolved → serverUrl=${serverVideoUrl ?? "null"}, blobUrl=${blobUrl ? "blob:..." : "null"}, serverFailed=${serverFailed}, using=${videoUrl?.slice(0, 60) ?? "null"}`);
  }, [videoUrl, serverVideoUrl, blobUrl, serverFailed, addDebug]);

  // Pre-flight check: fetch server URL to detect 404/errors early
  useEffect(() => {
    if (!serverVideoUrl || serverFailed) return;
    addDebug(`Preflight HEAD ${serverVideoUrl}`);
    fetch(serverVideoUrl, { method: "HEAD" })
      .then(res => {
        addDebug(`Preflight result: ${res.status} ${res.statusText}, content-type=${res.headers.get("content-type")}, content-length=${res.headers.get("content-length")}`);
        if (!res.ok) {
          addDebug(`Server preview not OK (${res.status}), falling back to blob`);
          markServerFailed();
        }
      })
      .catch(err => {
        addDebug(`Preflight fetch error: ${err.message}`);
        markServerFailed();
      });
  }, [serverVideoUrl, serverFailed, addDebug, markServerFailed]);

  // Use backend duration if available, otherwise fall back to local <video> metadata
  const videoDuration = backendVideoDuration > 0 ? backendVideoDuration : localDuration;

  // Throttled timeupdate via rAF
  const handleTimeUpdate = useCallback(() => {
    if (rafRef.current) return;
    rafRef.current = requestAnimationFrame(() => {
      if (videoRef.current) {
        setCurrentTime(videoRef.current.currentTime);
      }
      rafRef.current = null;
    });
  }, []);

  // Cleanup rAF on unmount
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

  // Capture current video frame to canvas dataURL
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

  // Handle compare button
  const handleCompare = useCallback((index: number | null) => {
    if (index === null) {
      setCompareIndex(null);
      setCapturedFrame(null);
      return;
    }
    setCompareIndex(index);
    // Seek to the timestamp, then capture after a short delay for the seek to complete
    const ts = detectedTimestamps[index];
    if (ts && videoRef.current) {
      const seconds = parseTimestampToSeconds(ts);
      videoRef.current.currentTime = seconds;
      setCurrentTime(seconds);
      // Capture frame after seek completes
      const onSeeked = () => {
        videoRef.current?.removeEventListener("seeked", onSeeked);
        setCapturedFrame(captureVideoFrame());
      };
      videoRef.current.addEventListener("seeked", onSeeked);
    }
  }, [detectedTimestamps, captureVideoFrame]);

  // Format for Builder1 input
  const formatForBuilder1 = (): string => {
    if (detectedTimestamps.length === 0) return "";
    return detectedTimestamps.join("\n");
  };

  const handleCopy = async () => {
    const formatted = formatForBuilder1();
    if (formatted) {
      await navigator.clipboard.writeText(formatted);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-5">
      {/* Success header */}
      <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center">
              <span className="material-symbols-outlined text-emerald-400">check_circle</span>
            </div>
            <div>
              <p className="text-emerald-700 dark:text-emerald-300 font-bold">
                {detectedTimestamps.length}개 감지
              </p>
              <p className="text-emerald-800/80 dark:text-emerald-300/80 text-xs mt-0.5">
                {usedThresholdMode === "precise" ? "정밀" : "표준"}
              </p>
            </div>
          </div>
          <button
            onClick={onReset}
            className="px-3 py-1.5 rounded-lg text-[var(--fg-muted)] text-sm hover:text-[var(--fg-0)] hover:bg-[var(--surface-2)] transition-all"
          >
            초기화
          </button>
        </div>

        {/* Re-analyze with different mode */}
        {uploadedFile && usedThresholdMode === "standard" && (
          <button
            onClick={() => onReanalyze("precise")}
            className="w-full py-2.5 rounded-lg bg-[var(--color-brand-primary)]/10 border border-[var(--color-brand-primary)]/30 text-[var(--color-brand-primary)] text-sm font-medium hover:bg-[var(--color-brand-primary)]/20 transition-all flex items-center justify-center gap-2"
          >
            <span className="material-symbols-outlined text-base">search</span>
            정밀 재분석
          </button>
        )}
        {uploadedFile && usedThresholdMode === "precise" && (
          <button
            onClick={() => onReanalyze("standard")}
            className="w-full py-2.5 rounded-lg bg-[var(--surface-2)] border border-[var(--border-muted)] text-[var(--fg-muted)] text-sm font-medium hover:bg-[var(--surface-3)] hover:text-[var(--fg-0)] transition-all flex items-center justify-center gap-2"
          >
            <span className="material-symbols-outlined text-base">refresh</span>
            표준 재분석
          </button>
        )}
      </div>

      {/* Preview transcode error warning */}
      {previewError && !previewId && (
        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
          <div className="flex items-start gap-2">
            <span className="material-symbols-outlined text-amber-400 text-lg mt-0.5">warning</span>
            <div className="min-w-0">
              <p className="text-amber-300 text-xs font-bold">서버 영상 변환 실패</p>
              <p className="text-amber-300/70 text-[10px] mt-1">일부 브라우저에서 재생이 안 될 수 있습니다</p>
              {process.env.NODE_ENV !== "production" && (
                <details className="mt-1">
                  <summary className="text-amber-300/50 text-[10px] cursor-pointer">진단 상세</summary>
                  <pre className="text-amber-300/40 text-[9px] mt-1 whitespace-pre-wrap break-all font-mono">{previewError}</pre>
                </details>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Video player + Scene Timeline */}
      {uploadedFile ? (
        <div className="space-y-4">
          {/* Video player */}
          <div className="rounded-xl overflow-hidden bg-black/30 border border-white/10">
            {videoError ? (
              <div className="flex flex-col items-center justify-center gap-3 py-8">
                <span className="material-symbols-outlined text-2xl text-gray-500">error_outline</span>
                <p className="text-gray-400 text-sm">비디오를 재생할 수 없습니다</p>
                <button
                  onClick={() => setErrorVideoUrl(null)}
                  className="px-4 py-2 rounded-lg bg-white/10 text-sm text-gray-300 hover:bg-white/20 transition-all"
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
                className="w-full max-h-[400px] object-contain bg-black"
                onTimeUpdate={handleTimeUpdate}
                onLoadStart={() => addDebug(`loadstart: ${videoUrl?.slice(0, 60)}`)}
                onLoadedMetadata={(e) => {
                  setLocalDuration(e.currentTarget.duration);
                  addDebug(`loadedmetadata: duration=${e.currentTarget.duration}, videoW=${e.currentTarget.videoWidth}x${e.currentTarget.videoHeight}`);
                }}
                onCanPlay={() => addDebug("canplay: video ready to play")}
                onError={(e) => {
                  const vid = e.currentTarget;
                  const err = vid.error;
                  const errDetail = err
                    ? `code=${err.code} (${["","ABORTED","NETWORK","DECODE","SRC_NOT_SUPPORTED"][err.code] ?? "?"}), msg=${err.message}`
                    : "no error object";
                  addDebug(`VIDEO onError: ${errDetail}, src=${vid.src?.slice(0, 80)}, networkState=${vid.networkState}, readyState=${vid.readyState}`);
                  if (serverVideoUrl && !serverFailed) {
                    addDebug("→ Falling back to blob URL");
                    markServerFailed();
                  } else {
                    addDebug("→ Final failure (both server & blob failed)");
                    setErrorVideoUrl(videoUrl ?? "__no_url__");
                  }
                }}
              />
            ) : (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-2 border-white/20 border-t-white/60" />
              </div>
            )}
          </div>

          {/* Scene timeline - always rendered */}
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

          {/* Side-by-side comparison panel */}
          {compareIndex !== null && detectedTimestamps[compareIndex] && (
            <ComparePanel
              compareIndex={compareIndex}
              timestamp={detectedTimestamps[compareIndex]}
              capturedFrame={capturedFrame}
              onClose={() => { setCompareIndex(null); setCapturedFrame(null); }}
            />
          )}
        </div>
      ) : (
        /* Fallback: text list when no file */
        <div className="p-4 rounded-xl bg-black/30 border border-emerald-500/20 overflow-hidden">
          <pre className="text-emerald-200 text-xs whitespace-pre-wrap font-mono leading-relaxed">
            {formatForBuilder1()}
          </pre>
        </div>
      )}

      {/* Action buttons */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={handleCopy}
          className={`py-4 rounded-xl text-sm font-bold transition-all flex items-center justify-center gap-2 ${
            copied
              ? "bg-emerald-500 text-white shadow-[0_0_20px_rgba(52,211,153,0.3)]"
              : "bg-[var(--fg-0)] text-[var(--bg-0)] hover:opacity-90"
          }`}
        >
          <span className="material-symbols-outlined text-lg">
            {copied ? "check" : "content_copy"}
          </span>
          {copied ? "복사됨" : "복사"}
        </button>
        <button
          onClick={onDownloadFrames}
          disabled={isDownloading}
          className={`py-4 rounded-xl bg-[var(--color-brand-primary)] text-white transition-all flex items-center justify-center gap-2 ${isDownloading ? "opacity-70 cursor-not-allowed" : "hover:opacity-90"}`}
        >
          {isDownloading ? (
            <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
          ) : (
            <span className="material-symbols-outlined text-lg">download</span>
          )}
          <span className="font-bold text-sm">{isDownloading ? "추출 중" : "프레임"}</span>
        </button>
      </div>
    </div>
  );
}

/* ──────────────── Compare Panel ──────────────── */

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
    <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/5 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-cyan-400 text-lg">compare</span>
          <p className="text-sm font-bold text-cyan-300">
            Scene {compareIndex + 1} ({timestamp})
          </p>
        </div>
        <button
          onClick={onClose}
          className="w-7 h-7 rounded-md bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-all flex items-center justify-center"
        >
          <span className="material-symbols-outlined text-sm">close</span>
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Video Frame (canvas capture) */}
        <div className="space-y-2">
          <p className="text-[10px] font-mono text-gray-500 uppercase tracking-wider text-center">
            Video Frame
          </p>
          <div className="rounded-lg overflow-hidden bg-black/50 border border-white/10 aspect-video flex items-center justify-center">
            {capturedFrame ? (
              <img src={capturedFrame} alt="Video frame" className="w-full h-full object-contain" />
            ) : (
              <div className="flex flex-col items-center gap-1 text-gray-500">
                <span className="material-symbols-outlined text-xl">videocam</span>
                <span className="text-[10px]">캡처 중...</span>
              </div>
            )}
          </div>
        </div>

        {/* Extracted Thumbnail */}
        <div className="space-y-2">
          <p className="text-[10px] font-mono text-gray-500 uppercase tracking-wider text-center">
            Extracted Thumbnail
          </p>
          <div className="rounded-lg overflow-hidden bg-black/50 border border-white/10 aspect-video flex items-center justify-center">
            <CompareThumb timestamp={timestamp} />
          </div>
        </div>
      </div>
    </div>
  );
}

/** Renders the extracted thumbnail for a timestamp by reading from SceneTimeline's frame cache via DOM */
function CompareThumb({ timestamp }: { timestamp: string }) {
  const thumbUrl = useMemo(() => {
    if (typeof document === "undefined") return null;
    const imgs = document.querySelectorAll<HTMLImageElement>("img[alt^='Scene ']");
    for (const img of imgs) {
      const card = img.closest("[class*='flex-shrink-0']");
      if (card) {
        const tsText = card.querySelector(".font-mono")?.textContent;
        if (tsText?.trim() === timestamp) {
          return img.src;
        }
      }
    }
    return null;
  }, [timestamp]);

  if (thumbUrl) {
    return <img src={thumbUrl} alt="Extracted thumbnail" className="w-full h-full object-contain" />;
  }

  return (
    <div className="flex flex-col items-center gap-1 text-gray-500">
      <span className="material-symbols-outlined text-xl">image</span>
      <span className="text-[10px]">썸네일 없음</span>
    </div>
  );
}
