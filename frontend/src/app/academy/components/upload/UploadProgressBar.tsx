"use client";

import type { UploadStatus } from "../../api/sceneDetect";

interface UploadProgressBarProps {
  uploadStatus: UploadStatus;
  uploadProgress: number;
}

export function UploadProgressBar({ uploadStatus, uploadProgress }: UploadProgressBarProps) {
  return (
    <div className="p-8 rounded-2xl bg-black/30 border border-purple-500/30">
      <div className="flex items-center gap-4 mb-4">
        <div className="relative">
          <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center">
            <div className="animate-spin rounded-full h-6 w-6 border-2 border-purple-500 border-t-transparent" />
          </div>
          {uploadStatus === "processing" && (
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-purple-500 rounded-full animate-pulse" />
          )}
        </div>
        <div>
          <p className="text-white font-bold">
            {uploadStatus === "uploading" ? "업로드 중..." : "씬 분석 중..."}
          </p>
          <p className="text-gray-500 text-sm">
            {uploadStatus === "uploading" ? `${uploadProgress}% 완료` : "FFmpeg 처리 중"}
          </p>
        </div>
      </div>
      <div className="h-2 bg-black/50 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 transition-all duration-300"
          style={{ width: uploadStatus === "processing" ? "100%" : `${uploadProgress}%` }}
        />
      </div>
    </div>
  );
}
