export type UploadStatus = "idle" | "uploading" | "processing" | "done" | "error";
export type ThresholdMode = "precise" | "standard";

export interface SceneDetectResult {
  timestamps: string[];
  video_duration: number;
  preview_id: string | null;
}

export interface ThumbnailItem {
  timestamp: string;
  data_url: string;
}

export function getThresholdValue(mode: ThresholdMode): number {
  return mode === "precise" ? 0.19 : 0.25;
}

/**
 * Scene detect API using XHR for upload progress tracking
 */
export function uploadVideoForSceneDetect(
  file: File,
  threshold: number,
  onProgress: (progress: number) => void,
  onStatusChange: (status: UploadStatus) => void,
): Promise<SceneDetectResult> {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("video", file);

    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status === 200) {
        const result = JSON.parse(xhr.responseText);
        resolve({
          timestamps: result.timestamps || [],
          video_duration: result.video_duration || 0,
          preview_id: result.preview_id || null,
        });
      } else {
        try {
          const err = JSON.parse(xhr.responseText);
          reject(new Error(err.detail || "서버 오류가 발생했습니다."));
        } catch {
          reject(new Error(`서버 오류 (${xhr.status})`));
        }
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("업로드 중 오류가 발생했습니다."));
    });

    xhr.upload.addEventListener("loadend", () => {
      onStatusChange("processing");
    });

    xhr.open("POST", `${process.env.NEXT_PUBLIC_API_URL || ''}/api/v1/scene-detect/?threshold=${threshold}`);
    xhr.send(formData);
  });
}

/**
 * Download frames as ZIP
 * 첫 번째 감지에서 얻은 타임스탬프를 그대로 전달하여 정확한 프레임 추출
 */
export async function downloadFramesAsZip(
  file: File,
  timestamps: string[],
): Promise<Blob> {
  const formData = new FormData();
  formData.append("video", file);
  formData.append("timestamps", JSON.stringify(timestamps));

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL || ''}/api/v1/scene-detect/extract-frames`,
    { method: "POST", body: formData }
  );

  if (!response.ok) {
    throw new Error("프레임 추출 실패");
  }

  return response.blob();
}

/**
 * Fetch thumbnails from backend (FFmpeg-based, codec-agnostic)
 */
export async function fetchThumbnails(
  file: File,
  timestamps: string[],
): Promise<ThumbnailItem[]> {
  const formData = new FormData();
  formData.append("video", file);
  formData.append("timestamps", JSON.stringify(timestamps));

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL || ''}/api/v1/scene-detect/thumbnails`,
    { method: "POST", body: formData },
  );

  if (!response.ok) {
    throw new Error("썸네일 추출 실패");
  }

  const data = await response.json();
  return data.thumbnails || [];
}
