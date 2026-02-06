"use client";

interface VideoDropzoneProps {
  isDragging: boolean;
  onDragIn: (e: React.DragEvent) => void;
  onDragOut: (e: React.DragEvent) => void;
  onDrag: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export function VideoDropzone({
  isDragging,
  onDragIn,
  onDragOut,
  onDrag,
  onDrop,
  onFileSelect,
}: VideoDropzoneProps) {
  return (
    <div
      onDragEnter={onDragIn}
      onDragLeave={onDragOut}
      onDragOver={onDrag}
      onDrop={onDrop}
      className={`relative cursor-pointer rounded-[var(--academy-radius)] border-2 border-dashed px-6 py-10 text-center transition-colors ${
        isDragging
          ? "border-[var(--color-brand-primary)] bg-[var(--color-brand-primary)]/10"
          : "border-[var(--border-muted)] bg-[var(--surface-2)] hover:border-[var(--color-brand-primary)]/40"
      }`}
      onClick={() => document.getElementById("videoFileInput")?.click()}
    >
      <input
        id="videoFileInput"
        type="file"
        accept="video/*"
        onChange={onFileSelect}
        className="hidden"
      />

      <div className="mx-auto mb-3 inline-flex h-14 w-14 items-center justify-center rounded-full border border-[var(--border-muted)] bg-[var(--surface-1)]">
        <span className="material-symbols-outlined text-[26px] text-[var(--color-brand-primary)]" aria-hidden>
          add
        </span>
      </div>
      <p className="text-base font-semibold text-[var(--fg-0)]">영상 추가</p>
    </div>
  );
}
