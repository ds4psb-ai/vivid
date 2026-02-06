"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { fetchThumbnails } from "../api/sceneDetect";

export interface FrameData {
  timestamp: string;
  seconds: number;
  thumbnailUrl: string;
}

interface UseFrameExtractorReturn {
  frames: FrameData[];
  isExtracting: boolean;
  extractionError: string | null;
  extractAll: (file: File, timestamps: string[]) => Promise<void>;
  extractSingle: (file: File, seconds: number) => Promise<string>;
}

/** "00:01.67" → 1.67 */
export function parseTimestampToSeconds(ts: string): number {
  const match = ts.match(/^(\d{1,2}):(\d{2})\.(\d{2})$/);
  if (!match) return 0;
  const [, min, sec, cs] = match;
  return Number(min) * 60 + Number(sec) + Number(cs) / 100;
}

/** 1.67 → "00:01.67" */
export function formatSecondsToTimestamp(seconds: number): string {
  const clamped = Math.max(0, seconds);
  const min = Math.floor(clamped / 60);
  const sec = clamped % 60;
  const wholeSec = Math.floor(sec);
  const cs = Math.round((sec - wholeSec) * 100);
  return `${String(min).padStart(2, "0")}:${String(wholeSec).padStart(2, "0")}.${String(cs).padStart(2, "0")}`;
}

const THUMB_W = 320;
const THUMB_H = 180;

export function useFrameExtractor(): UseFrameExtractorReturn {
  const [frames, setFrames] = useState<FrameData[]>([]);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  const cacheRef = useRef<Map<string, string>>(new Map());
  const videoUrlRef = useRef<string | null>(null);

  // Cleanup object URL on unmount
  useEffect(() => {
    return () => {
      if (videoUrlRef.current) {
        URL.revokeObjectURL(videoUrlRef.current);
        videoUrlRef.current = null;
      }
    };
  }, []);

  const extractFrame = useCallback(
    (video: HTMLVideoElement, canvas: HTMLCanvasElement, seconds: number): Promise<string> => {
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error("Frame extract timeout")), 15000);

        const onSeeked = () => {
          video.removeEventListener("seeked", onSeeked);
          clearTimeout(timeout);

          const ctx = canvas.getContext("2d");
          if (!ctx) {
            reject(new Error("Canvas context unavailable"));
            return;
          }

          // Fit video to thumbnail while preserving aspect ratio
          const scale = Math.min(THUMB_W / video.videoWidth, THUMB_H / video.videoHeight);
          const w = video.videoWidth * scale;
          const h = video.videoHeight * scale;
          canvas.width = THUMB_W;
          canvas.height = THUMB_H;
          ctx.fillStyle = "#000";
          ctx.fillRect(0, 0, THUMB_W, THUMB_H);
          ctx.drawImage(video, (THUMB_W - w) / 2, (THUMB_H - h) / 2, w, h);

          resolve(canvas.toDataURL("image/jpeg", 0.7));
        };

        video.addEventListener("seeked", onSeeked);
        video.currentTime = seconds;
      });
    },
    [],
  );

  const createVideoElement = useCallback((file: File): Promise<HTMLVideoElement> => {
    return new Promise((resolve, reject) => {
      const video = document.createElement("video");
      video.muted = true;
      video.playsInline = true;
      video.preload = "auto";

      // Reuse or create object URL
      if (!videoUrlRef.current) {
        videoUrlRef.current = URL.createObjectURL(file);
      }
      video.src = videoUrlRef.current;

      const onLoaded = () => {
        video.removeEventListener("loadeddata", onLoaded);
        video.removeEventListener("error", onError);
        resolve(video);
      };
      const onError = () => {
        video.removeEventListener("loadeddata", onLoaded);
        video.removeEventListener("error", onError);
        reject(new Error("Video load failed"));
      };

      video.addEventListener("loadeddata", onLoaded);
      video.addEventListener("error", onError);
    });
  }, []);

  const extractAll = useCallback(
    async (file: File, timestamps: string[]) => {
      setIsExtracting(true);
      setExtractionError(null);

      // 1) Try backend FFmpeg extraction first
      try {
        const thumbnails = await fetchThumbnails(file, timestamps);
        if (thumbnails.length > 0) {
          const results: FrameData[] = thumbnails.map((t) => ({
            timestamp: t.timestamp,
            seconds: parseTimestampToSeconds(t.timestamp),
            thumbnailUrl: t.data_url,
          }));
          // Update cache
          for (const t of thumbnails) {
            cacheRef.current.set(t.timestamp, t.data_url);
          }
          setFrames(results);
          setIsExtracting(false);
          return;
        }
      } catch (backendErr) {
        console.warn("Backend thumbnail extraction failed, falling back to canvas:", backendErr);
      }

      // 2) Fallback: client-side canvas extraction
      try {
        const video = await createVideoElement(file);
        const canvas = document.createElement("canvas");

        const results: FrameData[] = [];

        for (const ts of timestamps) {
          const seconds = parseTimestampToSeconds(ts);
          const cacheKey = ts;

          // Use cache if available
          let thumbnailUrl = cacheRef.current.get(cacheKey);
          if (!thumbnailUrl) {
            thumbnailUrl = await extractFrame(video, canvas, seconds);
            cacheRef.current.set(cacheKey, thumbnailUrl);
          }

          results.push({ timestamp: ts, seconds, thumbnailUrl });
        }

        setFrames(results);
      } catch (err) {
        console.error("Frame extraction failed:", err);
        setExtractionError(
          err instanceof Error ? err.message : "썸네일을 불러올 수 없습니다",
        );
      } finally {
        setIsExtracting(false);
      }
    },
    [createVideoElement, extractFrame],
  );

  const extractSingle = useCallback(
    async (file: File, seconds: number): Promise<string> => {
      const ts = formatSecondsToTimestamp(seconds);
      const cached = cacheRef.current.get(ts);
      if (cached) return cached;

      const video = await createVideoElement(file);
      const canvas = document.createElement("canvas");
      const dataUrl = await extractFrame(video, canvas, seconds);
      cacheRef.current.set(ts, dataUrl);
      return dataUrl;
    },
    [createVideoElement, extractFrame],
  );

  return { frames, isExtracting, extractionError, extractAll, extractSingle };
}
