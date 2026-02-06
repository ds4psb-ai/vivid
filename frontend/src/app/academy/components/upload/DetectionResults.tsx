"use client";

import { useState, useRef, useEffect, useCallback } from "react";
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
}: DetectionResultsProps) {
  const [copied, setCopied] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [localDuration, setLocalDuration] = useState(0);
  const [videoError, setVideoError] = useState(false);
  const [compareIndex, setCompareIndex] = useState<number | null>(null);
  const [capturedFrame, setCapturedFrame] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const rafRef = useRef<number | null>(null);

  // useState+useEffect: cleanup only runs when uploadedFile changes, avoiding
  // the useMemo race where revokeObjectURL fires while <video> is still loading.
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  useEffect(() => {
    if (!uploadedFile) {
      setVideoUrl(null);
      return;
    }
    const url = URL.createObjectURL(uploadedFile);
    setVideoUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [uploadedFile]);

  // Reset video error whenever the URL changes (e.g. re-upload or re-analyze)
  useEffect(() => {
    setVideoError(false);
  }, [videoUrl]);

  // Force browser to start loading blob URL (Safari/iOS require explicit load())
  useEffect(() => {
    const video = videoRef.current;
    if (video && videoUrl) {
      video.load();
    }
  }, [videoUrl]);

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
              <p className="text-emerald-400 font-bold">
                {detectedTimestamps.length}개 씬 감지 완료!
              </p>
              <p className="text-emerald-400/60 text-xs flex items-center gap-1.5 mt-0.5">
                {usedThresholdMode === "precise" ? "⚡ 정밀 모드" : "🎯 표준 모드"}로 분석됨
              </p>
            </div>
          </div>
          <button
            onClick={onReset}
            className="px-3 py-1.5 rounded-lg text-gray-400 text-sm hover:text-white hover:bg-white/5 transition-all"
          >
            다시 업로드
          </button>
        </div>

        {/* Re-analyze with different mode */}
        {uploadedFile && usedThresholdMode === "standard" && (
          <button
            onClick={() => onReanalyze("precise")}
            className="w-full py-3 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-300 text-sm font-medium hover:bg-purple-500/20 hover:border-purple-500/50 transition-all flex items-center justify-center gap-2"
          >
            <span className="material-symbols-outlined text-base">search</span>
            혹시 놓친 씬이 있나요? ⚡ 정밀 모드로 다시 분석해보기
          </button>
        )}
        {uploadedFile && usedThresholdMode === "precise" && (
          <button
            onClick={() => onReanalyze("standard")}
            className="w-full py-2.5 rounded-lg bg-white/5 border border-white/10 text-gray-300 text-sm font-medium hover:bg-white/10 hover:border-white/20 transition-all flex items-center justify-center gap-2"
          >
            <span className="material-symbols-outlined text-base">refresh</span>
            씬이 너무 많나요? 🎯 표준 모드로 다시 분석해보기
          </button>
        )}
      </div>

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
                  onClick={() => setVideoError(false)}
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
                onLoadedMetadata={(e) => setLocalDuration(e.currentTarget.duration)}
                onError={(e) => {
                  console.error("[video] playback error:", e.currentTarget.error?.code, e.currentTarget.error?.message);
                  setVideoError(true);
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
              : "bg-white text-gray-900 hover:bg-gray-100 shadow-[0_4px_20px_rgba(255,255,255,0.1)]"
          }`}
        >
          <span className="material-symbols-outlined text-lg">
            {copied ? "check" : "content_copy"}
          </span>
          {copied ? "복사됨!" : "Builder1 입력용 복사"}
        </button>
        <button
          onClick={onDownloadFrames}
          disabled={isDownloading}
          className={`py-4 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white transition-all flex items-center justify-center gap-2 shadow-[0_4px_20px_rgba(168,85,247,0.3)] ${isDownloading ? "opacity-70 cursor-not-allowed" : "hover:from-purple-700 hover:to-indigo-700"}`}
        >
          {isDownloading ? (
            <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
          ) : (
            <span className="material-symbols-outlined text-lg">download</span>
          )}
          <div className="flex flex-col items-start">
            <span className="font-bold text-sm">
              {isDownloading ? "프레임 추출 중..." : "프레임 이미지 다운로드"}
            </span>
            <span className="text-xs text-purple-100">
              {isDownloading ? "잠시만 기다려주세요" : "ZIP으로 frame_01.jpg, frame_02.jpg... 추출"}
            </span>
          </div>
        </button>
      </div>

      {/* Download info */}
      <div className="mt-4 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
        <p className="text-xs text-blue-200">
          💡 다운로드 후 압축 해제하면 씬별 프레임 이미지를 얻을 수 있습니다. 이 이미지들이 각
          프롬프트의 &quot;구도 레퍼런스&quot;로 사용됩니다.
        </p>
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
            Scene {compareIndex + 1} 비교 ({timestamp})
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

      <p className="text-xs text-cyan-400/60 text-center">
        이 컷 포인트가 정확한가요? 타임라인에서 +/- 버튼으로 미세 조정하세요.
      </p>
    </div>
  );
}

/** Renders the extracted thumbnail for a timestamp by reading from SceneTimeline's frame cache via DOM */
function CompareThumb({ timestamp }: { timestamp: string }) {
  // Find the thumbnail from already-rendered SceneTimeline img elements
  const [thumbUrl, setThumbUrl] = useState<string | null>(null);

  useEffect(() => {
    // SceneTimeline renders thumbnails as <img alt="Scene N">, find by walking the DOM
    const imgs = document.querySelectorAll<HTMLImageElement>("img[alt^='Scene ']");
    // Match by finding the card that contains this timestamp
    for (const img of imgs) {
      const card = img.closest("[class*='flex-shrink-0']");
      if (card) {
        const tsText = card.querySelector(".font-mono")?.textContent;
        if (tsText?.trim() === timestamp) {
          setThumbUrl(img.src);
          return;
        }
      }
    }
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
