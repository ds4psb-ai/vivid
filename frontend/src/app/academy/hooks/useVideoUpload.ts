"use client";

import { useState, useCallback } from "react";
import {
  type UploadStatus,
  type ThresholdMode,
  getThresholdValue,
  uploadVideoForSceneDetect,
  downloadFramesAsZip,
} from "../api/sceneDetect";

interface UseVideoUploadReturn {
  // State
  uploadStatus: UploadStatus;
  uploadProgress: number;
  detectedTimestamps: string[];
  errorMessage: string;
  uploadedFile: File | null;
  thresholdMode: ThresholdMode;
  usedThresholdMode: ThresholdMode;
  isDragging: boolean;

  // Actions
  setThresholdMode: (mode: ThresholdMode) => void;
  setIsDragging: (dragging: boolean) => void;
  processVideo: (file: File) => Promise<void>;
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
  const [thresholdMode, setThresholdMode] = useState<ThresholdMode>("standard");
  const [usedThresholdMode, setUsedThresholdMode] = useState<ThresholdMode>("standard");

  const processVideo = useCallback(async (file: File) => {
    // Validate file type
    if (!file.type.startsWith("video/")) {
      setErrorMessage("영상 파일만 업로드 가능합니다.");
      setUploadStatus("error");
      return;
    }

    // Check file size (max 100MB)
    if (file.size > 100 * 1024 * 1024) {
      setErrorMessage("파일 크기는 100MB 이하만 가능합니다.");
      setUploadStatus("error");
      return;
    }

    setUploadStatus("uploading");
    setUploadProgress(0);
    setErrorMessage("");
    setDetectedTimestamps([]);
    setUploadedFile(file);
    setUsedThresholdMode(thresholdMode);

    const threshold = getThresholdValue(thresholdMode);

    try {
      const result = await uploadVideoForSceneDetect(
        file,
        threshold,
        setUploadProgress,
        setUploadStatus,
      );
      setDetectedTimestamps(result.timestamps);
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

    setUploadStatus("processing");
    setErrorMessage("");

    const threshold = getThresholdValue(usedThresholdMode);

    try {
      const blob = await downloadFramesAsZip(uploadedFile, threshold);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${uploadedFile.name.replace(/\.[^/.]+$/, "")}_scenes.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setUploadStatus("done");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "네트워크 오류");
      setUploadStatus("error");
    }
  }, [uploadedFile, usedThresholdMode]);

  const resetUpload = useCallback(() => {
    setUploadStatus("idle");
    setUploadProgress(0);
    setDetectedTimestamps([]);
    setErrorMessage("");
    setUploadedFile(null);
  }, []);

  return {
    uploadStatus,
    uploadProgress,
    detectedTimestamps,
    errorMessage,
    uploadedFile,
    thresholdMode,
    usedThresholdMode,
    isDragging,
    setThresholdMode,
    setIsDragging,
    processVideo,
    downloadFrames,
    resetUpload,
  };
}
