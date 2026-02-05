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
        ? "border-purple-500 bg-purple-500/10"
        : "border-white/20 hover:border-purple-500/50 hover:bg-purple-500/5"
        }`}
      onClick={() => document.getElementById("videoFileInput")?.click()}
    >
      {/* Glow effect on hover */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

      <input
        id="videoFileInput"
        type="file"
        accept="video/*"
        onChange={onFileSelect}
        className="hidden"
      />
      <div className="relative z-10">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-purple-500/20 to-indigo-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
          <span className="material-symbols-outlined text-4xl text-purple-400">
            cloud_upload
          </span>
        </div>
        <p className="text-white font-bold text-lg mb-1">영상 파일을 드래그하거나 클릭</p>
        <p className="text-gray-500 text-sm">MP4, MOV, WebM 지원 • 최대 100MB</p>
      </div>
    </div>
  );
}
