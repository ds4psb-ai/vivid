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
      className={`relative border-2 border-dashed rounded-2xl p-10 text-center transition-all cursor-pointer group ${isDragging
        ? "border-[var(--color-brand-primary)] bg-[var(--color-brand-primary)]/10"
        : "border-[var(--border-muted)] hover:border-[var(--color-brand-primary)]/50 hover:bg-[var(--color-brand-primary)]/5"
        }`}
      onClick={() => document.getElementById("videoFileInput")?.click()}
    >
      <div className="absolute inset-0 rounded-2xl bg-[var(--color-brand-primary)]/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

      <input
        id="videoFileInput"
        type="file"
        accept="video/*"
        onChange={onFileSelect}
        className="hidden"
      />
      <div className="relative z-10">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[var(--surface-2)] border border-[var(--border-muted)] flex items-center justify-center group-hover:scale-110 transition-transform">
          <span className="material-symbols-outlined text-4xl text-[var(--color-brand-primary)]">
            cloud_upload
          </span>
        </div>
        <p className="text-[var(--fg-0)] font-bold text-lg">파일 업로드</p>
      </div>
    </div>
  );
}
