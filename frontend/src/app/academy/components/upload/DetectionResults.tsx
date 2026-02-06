"use client";

import { useState, useRef, useMemo, useEffect, useCallback } from "react";
import type { ThresholdMode } from "../../api/sceneDetect";
import { SceneTimeline } from "./SceneTimeline";

interface DetectionResultsProps {
  detectedTimestamps: string[];
  usedThresholdMode: ThresholdMode;
  uploadedFile: File | null;
  isDownloading: boolean;
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
  onTimestampsChange,
  onReset,
  onReanalyze,
  onDownloadFrames,
}: DetectionResultsProps) {
  const [copied, setCopied] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [videoDuration, setVideoDuration] = useState(0);
  const [videoError, setVideoError] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const rafRef = useRef<number | null>(null);

  const videoUrl = useMemo(
    () => (uploadedFile ? URL.createObjectURL(uploadedFile) : null),
    [uploadedFile],
  );

  // Cleanup object URL on unmount
  useEffect(() => {
    return () => {
      if (videoUrl) URL.revokeObjectURL(videoUrl);
    };
  }, [videoUrl]);

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
      {uploadedFile && videoUrl && !videoError ? (
        <div className="space-y-4">
          {/* Video player */}
          <div className="rounded-xl overflow-hidden bg-black/30 border border-white/10">
            <video
              ref={videoRef}
              src={videoUrl}
              controls
              playsInline
              className="w-full"
              onTimeUpdate={handleTimeUpdate}
              onLoadedMetadata={(e) => setVideoDuration(e.currentTarget.duration)}
              onError={() => setVideoError(true)}
            />
          </div>

          {/* Scene timeline */}
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
        /* Fallback: text list when video fails */
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
