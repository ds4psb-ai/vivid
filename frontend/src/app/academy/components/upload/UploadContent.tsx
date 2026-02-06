"use client";

import { useState } from "react";
import { type TabKey } from "../../constants";
import { PageHeader, ContentCard, NextStepButton } from "../shared";
import { useVideoUpload } from "../../hooks/useVideoUpload";
import { VideoDropzone } from "./VideoDropzone";
import { ThresholdSelector } from "./ThresholdSelector";
import { UploadProgressBar } from "./UploadProgressBar";
import { DetectionResults } from "./DetectionResults";

interface UploadContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function UploadContent({ setActiveTab }: UploadContentProps) {
  const [timestampInput, setTimestampInput] = useState("");
  const [copied, setCopied] = useState(false);

  const {
    uploadStatus,
    uploadProgress,
    detectedTimestamps,
    errorMessage,
    uploadedFile,
    thresholdMode,
    usedThresholdMode,
    isDragging,
    isDownloading,
    setDetectedTimestamps,
    setThresholdMode,
    setIsDragging,
    processVideo,
    downloadFrames,
    resetUpload,
  } = useVideoUpload();

  // Parse timestamps from Antigravity output (formats: "00:01.67" or "0:00.00")
  const parseTimestamps = (input: string): string[] => {
    const pattern = /\d{1,2}:\d{2}\.\d{2}/g;
    return input.match(pattern) || [];
  };

  const parsedTimestamps = parseTimestamps(timestampInput);
  const allTimestamps = detectedTimestamps.length > 0 ? detectedTimestamps : parsedTimestamps;

  // Format for Builder1 input - 타임스탬프만
  const formatForBuilder1 = (): string => {
    if (allTimestamps.length === 0) return "";
    return allTimestamps.join('\n');
  };

  const handleCopy = async () => {
    const formatted = formatForBuilder1();
    if (formatted) {
      await navigator.clipboard.writeText(formatted);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Handle drag events
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragIn = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragOut = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      await processVideo(files[0]);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      await processVideo(files[0]);
    }
  };

  const handleReanalyze = async (mode: "precise" | "standard") => {
    if (uploadedFile) {
      setThresholdMode(mode);
      await processVideo(uploadedFile, mode);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="영상 업로드 + 컷 나누기" sub="레퍼런스 영상 다운로드 → 업로드 → 씬 분석" />

      {/* Step 0: 영상 다운로더 - Premium Design */}
      <ContentCard>
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-500 to-red-500 flex items-center justify-center shadow-[0_0_20px_rgba(236,72,153,0.3)]">
            <span className="material-symbols-outlined text-white">download</span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">STEP 0. 레퍼런스 영상 다운로드</h3>
            <p className="text-gray-500 text-xs">오마주할 바이럴 영상을 먼저 다운받으세요</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          {/* YouTube Shorts */}
          <div className="p-4 rounded-xl bg-gradient-to-br from-red-500/10 to-red-600/5 border border-red-500/20">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-red-400 text-lg">play_circle</span>
              <span className="text-red-400 font-bold text-sm">YouTube</span>
            </div>
            <div className="space-y-2">
              <a href="https://savefrom.net" target="_blank" rel="noopener noreferrer" className="block text-xs text-gray-400 hover:text-white transition-colors">savefrom.net</a>
              <a href="https://publer.com/tools/youtube-short-downloader" target="_blank" rel="noopener noreferrer" className="block text-xs text-gray-400 hover:text-white transition-colors">publer.com</a>
            </div>
          </div>

          {/* TikTok */}
          <div className="p-4 rounded-xl bg-gradient-to-br from-pink-500/10 to-pink-600/5 border border-pink-500/20">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-pink-400 text-lg">music_note</span>
              <span className="text-pink-400 font-bold text-sm">TikTok</span>
            </div>
            <div className="space-y-2">
              <a href="https://snaptik.app" target="_blank" rel="noopener noreferrer" className="block text-xs text-gray-400 hover:text-white transition-colors">snaptik.app</a>
              <a href="https://ssstik.io" target="_blank" rel="noopener noreferrer" className="block text-xs text-gray-400 hover:text-white transition-colors">ssstik.io</a>
            </div>
          </div>

          {/* Instagram */}
          <div className="p-4 rounded-xl bg-gradient-to-br from-purple-500/10 to-fuchsia-600/5 border border-purple-500/20">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-purple-400 text-lg">photo_camera</span>
              <span className="text-purple-400 font-bold text-sm">Instagram</span>
            </div>
            <div className="space-y-2">
              <a href="https://snapinsta.to" target="_blank" rel="noopener noreferrer" className="block text-xs text-gray-400 hover:text-white transition-colors">snapinsta.to</a>
              <a href="https://sssinstagram.com/reels-downloader" target="_blank" rel="noopener noreferrer" className="block text-xs text-gray-400 hover:text-white transition-colors">sssinstagram.com</a>
            </div>
          </div>
        </div>

        <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
          <p className="text-amber-300 text-xs flex items-center gap-2">
            <span className="material-symbols-outlined text-sm">lightbulb</span>
            다운받은 영상을 아래 업로드 영역에 드래그하세요
          </p>
        </div>
      </ContentCard>

      {/* Step 1: Scene Detection Upload Section - Premium Design */}
      <ContentCard highlight>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-[0_0_20px_rgba(168,85,247,0.3)]">
            <span className="material-symbols-outlined text-white">movie_filter</span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">STEP 1. 자동 씬 감지</h3>
            <p className="text-gray-500 text-xs">AI 정밀 분석</p>
          </div>
        </div>

        {/* Threshold Mode Selector - Segmented Control */}
        {uploadStatus === "idle" && (
          <ThresholdSelector
            thresholdMode={thresholdMode}
            onModeChange={setThresholdMode}
          />
        )}

        {uploadStatus === "idle" && (
          <VideoDropzone
            isDragging={isDragging}
            onDragIn={handleDragIn}
            onDragOut={handleDragOut}
            onDrag={handleDrag}
            onDrop={handleDrop}
            onFileSelect={handleFileSelect}
          />
        )}

        {(uploadStatus === "uploading" || uploadStatus === "processing") && (
          <UploadProgressBar
            uploadStatus={uploadStatus}
            uploadProgress={uploadProgress}
          />
        )}

        {uploadStatus === "done" && detectedTimestamps.length > 0 && (
          <DetectionResults
            detectedTimestamps={detectedTimestamps}
            usedThresholdMode={usedThresholdMode}
            uploadedFile={uploadedFile}
            isDownloading={isDownloading}
            onTimestampsChange={setDetectedTimestamps}
            onReset={resetUpload}
            onReanalyze={handleReanalyze}
            onDownloadFrames={downloadFrames}
          />
        )}

        {uploadStatus === "error" && (
          <div className="p-6 rounded-xl bg-red-500/10 border border-red-500/30">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-red-500/20 flex items-center justify-center">
                <span className="material-symbols-outlined text-red-400">error</span>
              </div>
              <p className="text-red-400 font-bold">{errorMessage}</p>
            </div>
            <button
              onClick={resetUpload}
              className="w-full py-3 rounded-xl bg-white text-gray-900 text-sm font-bold hover:bg-gray-100 transition-colors"
            >
              다시 시도
            </button>
          </div>
        )}
      </ContentCard>

      {/* Manual Timestamp Helper Section (Fallback) */}
      <ContentCard>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center">
            <span className="material-symbols-outlined text-gray-400 text-sm">keyboard</span>
          </div>
          <div>
            <h3 className="text-white font-bold">타임스탬프 수동 입력</h3>
            <p className="text-gray-500 text-xs">자동 감지가 안 될 때 백업용</p>
          </div>
        </div>

        <textarea
          value={timestampInput}
          onChange={(e) => setTimestampInput(e.target.value)}
          placeholder="예: 00:00.00, 00:01.67, 00:04.56, 00:07.06..."
          className="w-full h-20 p-4 rounded-xl bg-black/50 border border-white/10 text-gray-200 text-sm placeholder-gray-600 focus:border-purple-500/50 focus:outline-none focus:ring-1 focus:ring-purple-500/20 resize-none font-mono"
        />

        {parsedTimestamps.length > 0 && detectedTimestamps.length === 0 && (
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-emerald-400 text-sm font-medium flex items-center gap-2">
                <span className="material-symbols-outlined text-sm">check_circle</span>
                {parsedTimestamps.length}개 씬 감지됨
              </p>
              <button
                onClick={handleCopy}
                className={`px-4 py-2 rounded-lg text-sm font-bold transition-all flex items-center gap-2 ${copied ? 'bg-emerald-500 text-white' : 'bg-white text-gray-900 hover:bg-gray-100'
                  }`}
              >
                <span className="material-symbols-outlined text-sm">{copied ? 'check' : 'content_copy'}</span>
                {copied ? '복사됨!' : '복사'}
              </button>
            </div>
            <div className="p-3 rounded-xl bg-black/30 border border-emerald-500/20">
              <pre className="text-emerald-200 text-xs whitespace-pre-wrap font-mono">
                {formatForBuilder1()}
              </pre>
            </div>
          </div>
        )}
      </ContentCard>

      <NextStepButton onClick={() => setActiveTab("prompt")} label="프롬프트 생성" />
    </div>
  );
}
