"use client";

import { useState, useCallback } from "react";
import {
  type UploadStatus,
  type ThresholdMode,
  getThresholdValue,
  uploadVideoForSceneDetect,
  downloadFramesAsZip,
} from "../api/sceneDetect";

const MAX_UPLOAD_SIZE_BYTES = 1024 * 1024 * 1024; // 1GB

interface UseVideoUploadReturn {
  // State
  uploadStatus: UploadStatus;
  uploadProgress: number;
  detectedTimestamps: string[];
  errorMessage: string;
  uploadedFile: File | null;
  videoDuration: number;
  thresholdMode: ThresholdMode;
  usedThresholdMode: ThresholdMode;
  isDragging: boolean;
  isDownloading: boolean;
  previewId: string | null;
  previewError: string | null;

  // Actions
  setDetectedTimestamps: (ts: string[]) => void;
  setThresholdMode: (mode: ThresholdMode) => void;
  setIsDragging: (dragging: boolean) => void;
  processVideo: (file: File, modeOverride?: ThresholdMode) => Promise<void>;
  downloadFrames: () => Promise<void>;
  resetUpload: () => void;
}

export function useVideoUpload(): UseVideoUploadReturn {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>("idle");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [detectedTimestamps, setDetectedTimestamps] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [videoDuration, setVideoDuration] = useState(0);
  const [thresholdMode, setThresholdMode] = useState<ThresholdMode>("standard");
  const [usedThresholdMode, setUsedThresholdMode] = useState<ThresholdMode>("standard");
  const [isDownloading, setIsDownloading] = useState(false);
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);

  const processVideo = useCallback(async (file: File, modeOverride?: ThresholdMode) => {
    // Validate file type
    if (!file.type.startsWith("video/")) {
      setErrorMessage("영상 파일만 업로드 가능합니다.");
      setUploadStatus("error");
      return;
    }

    // Check file size (max 1GB)
    if (file.size > MAX_UPLOAD_SIZE_BYTES) {
      setErrorMessage("파일 크기는 1GB 이하만 가능합니다.");
      setUploadStatus("error");
      return;
    }

    const mode = modeOverride || thresholdMode;

    setUploadStatus("uploading");
    setUploadProgress(0);
    setErrorMessage("");
    setDetectedTimestamps([]);
    setUploadedFile(file);
    setUsedThresholdMode(mode);
    setPreviewId(null);
    setPreviewError(null);

    const threshold = getThresholdValue(mode);

    try {
      const result = await uploadVideoForSceneDetect(
        file,
        threshold,
        setUploadProgress,
        setUploadStatus,
      );
      setDetectedTimestamps(result.timestamps);
      setVideoDuration(result.video_duration || 0);
      setPreviewId(result.preview_id);
      setPreviewError(result.preview_error);
      setUploadStatus("done");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "네트워크 오류가 발생했습니다.");
      setUploadStatus("error");
    }
  }, [thresholdMode]);

  const downloadFrames = useCallback(async () => {
    if (!uploadedFile) {
      setErrorMessage("먼저 영상을 업로드해주세요.");
      return;
    }

    if (detectedTimestamps.length === 0) {
      setErrorMessage("먼저 씬 감지를 실행해주세요.");
      return;
    }

    setIsDownloading(true);
    setErrorMessage("");

    try {
      const blob = await downloadFramesAsZip(uploadedFile, detectedTimestamps);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${uploadedFile.name.replace(/\.[^/.]+$/, "")}_scenes.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "네트워크 오류");
      setUploadStatus("error");
    } finally {
      setIsDownloading(false);
    }
  }, [uploadedFile, detectedTimestamps]);

  const resetUpload = useCallback(() => {
    setUploadStatus("idle");
    setUploadProgress(0);
    setDetectedTimestamps([]);
    setErrorMessage("");
    setUploadedFile(null);
    setVideoDuration(0);
    setPreviewId(null);
    setPreviewError(null);
  }, []);

  return {
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
  };
}
