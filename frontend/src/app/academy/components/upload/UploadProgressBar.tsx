"use client";

import type { UploadStatus } from "../../api/sceneDetect";

interface UploadProgressBarProps {
  uploadStatus: UploadStatus;
  uploadProgress: number;
}

export function UploadProgressBar({
  uploadStatus,
  uploadProgress,
}: UploadProgressBarProps) {
  const title = uploadStatus === "uploading" ? "업로드" : "분석";
  const progress = uploadStatus === "processing" ? 100 : uploadProgress;

  return (
    <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-4">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-sm font-semibold text-[var(--fg-0)]">{title}</p>
        <p className="text-sm text-[var(--fg-muted)]">{progress}%</p>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-[var(--surface-3)]">
        <div
          className="h-full bg-[var(--color-brand-primary)] transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
