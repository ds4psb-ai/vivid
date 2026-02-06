"use client";

import type { UploadStatus } from "../../api/sceneDetect";

interface UploadProgressBarProps {
  uploadStatus: UploadStatus;
  uploadProgress: number;
}

export function UploadProgressBar({ uploadStatus, uploadProgress }: UploadProgressBarProps) {
  return (
    <div className="p-6 rounded-2xl bg-[var(--surface-2)] border border-[var(--border-muted)]">
      <div className="flex items-center gap-4 mb-4">
        <div className="relative">
          <div className="w-12 h-12 rounded-xl bg-[var(--surface-3)] flex items-center justify-center">
            <div className="animate-spin rounded-full h-6 w-6 border-2 border-[var(--color-brand-primary)] border-t-transparent" />
          </div>
          {uploadStatus === "processing" && (
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-[var(--color-brand-primary)] rounded-full animate-pulse" />
          )}
        </div>
        <div>
          <p className="text-[var(--fg-0)] font-bold">
            {uploadStatus === "uploading" ? "업로드" : "분석"}
          </p>
          <p className="text-[var(--fg-muted)] text-sm">
            {uploadStatus === "uploading" ? `${uploadProgress}% 완료` : "영상 분석 중"}
          </p>
        </div>
      </div>
      <div className="h-2 bg-[var(--surface-3)] rounded-full overflow-hidden">
        <div
          className="h-full bg-[var(--color-brand-primary)] transition-all duration-300"
          style={{ width: uploadStatus === "processing" ? "100%" : `${uploadProgress}%` }}
        />
      </div>
    </div>
  );
}
