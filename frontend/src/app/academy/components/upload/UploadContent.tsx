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
    setDetectedTimestamps,
    setThresholdMode,
    setIsDragging,
    processVideo,
    downloadFrames,
    resetUpload,
  } = useVideoUpload();

  const parseTimestamps = (input: string): string[] => {
    const pattern = /\d{1,2}:\d{2}\.\d{2}/g;
    return input.match(pattern) || [];
  };

  const parsedTimestamps = parseTimestamps(timestampInput);
  const allTimestamps =
    detectedTimestamps.length > 0 ? detectedTimestamps : parsedTimestamps;

  const formatForBuilder1 = (): string => {
    if (allTimestamps.length === 0) return "";
    return allTimestamps.join("\n");
  };

  const handleCopy = async () => {
    const formatted = formatForBuilder1();
    if (formatted) {
      await navigator.clipboard.writeText(formatted);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

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
    <div className="mx-auto w-full max-w-[var(--academy-content-max)] space-y-4">
      <PageHeader title="업로드" sub="영상 1개 넣고 씬 추출" />

      <ContentCard>
        <div className="mb-3 flex items-center gap-2">
          <h3 className="text-base font-semibold text-[var(--fg-0)]">다운로드 링크</h3>
          <span className="rounded-full border border-[var(--color-brand-primary)]/35 bg-[var(--color-brand-primary)]/10 px-2 py-0.5 text-[11px] font-semibold text-[var(--color-brand-primary)]">
            필수
          </span>
        </div>
        <div className="grid gap-2 sm:grid-cols-3">
          {VIDEO_DOWNLOAD_SOURCES.map((source) => (
            <div
              key={source.platform}
              className="rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-3"
            >
              <p className="mb-2 text-sm font-semibold text-[var(--fg-0)]">
                {source.platform}
              </p>
              <div className="space-y-1">
                {source.links.map((link) => (
                  <a
                    key={link.href}
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-sm text-[var(--fg-muted)] transition-colors hover:text-[var(--fg-0)]"
                  >
                    {link.label}
                  </a>
                ))}
              </div>
            </div>
          ))}
        </div>
      </ContentCard>

      <ContentCard highlight>
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
          />
        )}

        {uploadStatus === "error" && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
            <p className="text-sm font-medium text-red-700 dark:text-red-300">
              {errorMessage}
            </p>
            <button
              type="button"
              onClick={resetUpload}
              className="mt-3 inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-[var(--fg-0)] px-4 text-sm font-semibold text-[var(--bg-0)] transition-opacity hover:opacity-90"
            >
              다시 시도
            </button>
          </div>
        )}
      </ContentCard>

      <ContentCard>
        <h3 className="mb-3 text-base font-semibold text-[var(--fg-0)]">
          수동 타임스탬프
        </h3>

        <textarea
          value={timestampInput}
          onChange={(e) => setTimestampInput(e.target.value)}
          placeholder="00:00.00"
          className="h-24 w-full resize-none rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-3 font-mono text-sm text-[var(--fg-0)] placeholder:text-[var(--fg-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-primary)]/25"
        />

        {parsedTimestamps.length > 0 && detectedTimestamps.length === 0 && (
          <div className="mt-3 space-y-2">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-[var(--fg-muted)]">
                {parsedTimestamps.length}개 감지
              </p>
              <button
                type="button"
                onClick={handleCopy}
                className={`inline-flex min-h-11 items-center justify-center rounded-xl px-4 text-sm font-semibold transition-colors ${
                  copied
                    ? "bg-emerald-500 text-white"
                    : "bg-[var(--fg-0)] text-[var(--bg-0)]"
                }`}
              >
                {copied ? "복사됨" : "복사"}
              </button>
            </div>
            <pre className="rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-3 text-xs text-[var(--fg-muted)]">
              {formatForBuilder1()}
            </pre>
          </div>
        )}
      </ContentCard>

      <NextStepButton onClick={() => setActiveTab("prompt")} label="다음: 빌더" />
    </div>
  );
}
