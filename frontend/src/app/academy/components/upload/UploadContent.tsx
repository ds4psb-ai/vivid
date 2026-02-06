"use client";

import { useState } from "react";
import { type TabKey } from "../../constants";
import { PageHeader, ContentCard, NextStepButton } from "../shared";
import { useVideoUpload } from "../../hooks/useVideoUpload";
import { VideoDropzone } from "./VideoDropzone";
import { ThresholdSelector } from "./ThresholdSelector";
import { UploadProgressBar } from "./UploadProgressBar";
import { DetectionResults } from "./DetectionResults";
import { VIDEO_DOWNLOAD_SOURCES } from "../../content";

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
    videoDuration,
    thresholdMode,
    usedThresholdMode,
    isDragging,
    isDownloading,
    previewId,
    previewError,
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
      <PageHeader title="업로드" />

      <ContentCard>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-[var(--surface-2)] border border-[var(--border-muted)] flex items-center justify-center">
            <span className="material-symbols-outlined text-[var(--color-brand-primary)]">download</span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-[var(--fg-0)]">STEP 0. 레퍼런스 영상 다운로드</h3>
          </div>
        </div>

        <details className="rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-4">
          <summary className="cursor-pointer text-sm font-semibold text-[var(--fg-0)]">
            다운로드 링크
          </summary>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
            {VIDEO_DOWNLOAD_SOURCES.map((source) => (
              <div
                key={source.platform}
                className={`p-4 rounded-xl bg-gradient-to-br border ${source.colorClass}`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="material-symbols-outlined text-lg" aria-hidden>{source.icon}</span>
                  <span className="font-bold text-sm">{source.platform}</span>
                </div>
                <div className="space-y-1.5">
                  {source.links.map((link) => (
                    <a
                      key={link.href}
                      href={link.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-xs text-[var(--fg-muted)] hover:text-[var(--fg-0)] transition-colors"
                    >
                      {link.label}
                    </a>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </details>
      </ContentCard>

      <ContentCard highlight>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-[var(--color-brand-primary)] text-white flex items-center justify-center">
            <span className="material-symbols-outlined text-white">movie_filter</span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-[var(--fg-0)]">STEP 1. 자동 씬 감지</h3>
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
            backendVideoDuration={videoDuration}
            onTimestampsChange={setDetectedTimestamps}
            onReset={resetUpload}
            onReanalyze={handleReanalyze}
            onDownloadFrames={downloadFrames}
            previewId={previewId}
            previewError={previewError}
          />
        )}

        {uploadStatus === "error" && (
          <div className="p-6 rounded-xl bg-red-500/10 border border-red-500/30">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-red-500/20 flex items-center justify-center">
                <span className="material-symbols-outlined text-red-400">error</span>
              </div>
              <p className="text-red-700 dark:text-red-400 font-bold">{errorMessage}</p>
            </div>
            <button
              onClick={resetUpload}
              className="w-full py-3 rounded-xl bg-[var(--fg-0)] text-[var(--bg-0)] text-sm font-bold hover:opacity-90 transition-colors"
            >
              다시 시도
            </button>
          </div>
        )}
      </ContentCard>

      <ContentCard>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-[var(--surface-2)] border border-[var(--border-muted)] flex items-center justify-center">
            <span className="material-symbols-outlined text-[var(--fg-muted)] text-sm">keyboard</span>
          </div>
          <div>
            <h3 className="text-[var(--fg-0)] font-bold">타임스탬프 수동 입력</h3>
          </div>
        </div>

        <textarea
          value={timestampInput}
          onChange={(e) => setTimestampInput(e.target.value)}
          placeholder="00:00.00, 00:01.67 ..."
          className="w-full h-20 p-4 rounded-xl bg-[var(--surface-2)] border border-[var(--border-muted)] text-[var(--fg-0)] text-sm placeholder:text-[var(--fg-muted)] focus:border-[var(--color-brand-primary)]/50 focus:outline-none focus:ring-1 focus:ring-[var(--color-brand-primary)]/20 resize-none font-mono"
        />

        {parsedTimestamps.length > 0 && detectedTimestamps.length === 0 && (
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-emerald-700 dark:text-emerald-400 text-sm font-medium flex items-center gap-2">
                <span className="material-symbols-outlined text-sm">check_circle</span>
                {parsedTimestamps.length}개 씬 감지됨
              </p>
              <button
                onClick={handleCopy}
                className={`px-4 py-2 rounded-lg text-sm font-bold transition-all flex items-center gap-2 ${copied ? 'bg-emerald-500 text-white' : 'bg-[var(--fg-0)] text-[var(--bg-0)] hover:opacity-90'
                  }`}
              >
                <span className="material-symbols-outlined text-sm">{copied ? 'check' : 'content_copy'}</span>
                {copied ? '복사됨!' : '복사'}
              </button>
            </div>
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
              <pre className="text-emerald-700 dark:text-emerald-200 text-xs whitespace-pre-wrap font-mono">
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
