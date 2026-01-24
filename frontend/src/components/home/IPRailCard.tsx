"use client";

import { useState, useRef, useCallback, useEffect, useMemo } from "react";
import Image from "next/image";
import { ShieldCheck, ShieldAlert, ShieldX, Play, Eye, Flame, Sparkles, Volume2, VolumeX } from "lucide-react";

type LicenseStatus = "allowed" | "restricted" | "prohibited";

interface IPRailCardProps {
  title: string;
  subtitle?: string;
  thumbnailUrl?: string;
  previewVideoUrl?: string;
  genres?: string[];
  licenseStatus?: LicenseStatus;
  viewCount?: string;
  isHot?: boolean;
  isNew?: boolean;
  /** Aspect ratio for card thumbnail: "9:16" (vertical) or "16:9" (horizontal) */
  aspectRatio?: "9:16" | "16:9";
}

const STATUS_STYLES: Record<LicenseStatus, { label: string; icon: typeof ShieldCheck; className: string }> = {
  allowed: {
    label: "허용",
    icon: ShieldCheck,
    className: "text-emerald-400 border-emerald-400/30 bg-emerald-500/10",
  },
  restricted: {
    label: "제한",
    icon: ShieldAlert,
    className: "text-amber-400 border-amber-400/30 bg-amber-500/10",
  },
  prohibited: {
    label: "금지",
    icon: ShieldX,
    className: "text-rose-400 border-rose-400/30 bg-rose-500/10",
  },
};

export function IPRailCard({
  title,
  subtitle,
  thumbnailUrl,
  previewVideoUrl,
  genres,
  licenseStatus = "allowed",
  viewCount,
  isHot,
  isNew,
  aspectRatio = "16:9",
}: IPRailCardProps) {
  const status = STATUS_STYLES[licenseStatus];
  const StatusIcon = status.icon;
  const videoRef = useRef<HTMLVideoElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [videoLoaded, setVideoLoaded] = useState(false);
  const [isMuted, setIsMuted] = useState(true); // 기본 muted 상태
  const [tiltStyle, setTiltStyle] = useState({ transform: '' });

  // 세로 영상(9:16)은 더 높은 카드, 가로 영상(16:9)은 기본 높이
  const isVertical = aspectRatio === "9:16";
  const thumbnailHeightClass = isVertical ? "h-72" : "h-44";

  // 3D Tilt effect handler
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;

    setTiltStyle({
      transform: `perspective(1000px) rotateY(${x * 8}deg) rotateX(${y * -8}deg) scale(1.02)`
    });
  }, []);

  const handleMouseEnter = useCallback(() => {
    setIsHovered(true);
    if (videoRef.current && previewVideoUrl) {
      videoRef.current.currentTime = 0;
      videoRef.current.play().catch(() => { });
    }
  }, [previewVideoUrl]);

  const handleMouseLeave = useCallback(() => {
    setIsHovered(false);
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
    // 마우스 나가면 다시 muted로 초기화
    setIsMuted(true);
    // Reset 3D tilt
    setTiltStyle({ transform: 'perspective(1000px) rotateY(0) rotateX(0) scale(1)' });
  }, []);

  // Mute 상태 동기화
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.muted = isMuted;
    }
  }, [isMuted, videoLoaded]);

  // Mute 토글 핸들러 - 강력한 이벤 전파 방지
  const handleMuteToggle = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    e.nativeEvent.stopImmediatePropagation(); // 부모로의 모든 이벤트 차단
    setIsMuted((prev) => !prev);
  }, []);

  return (
    <div
      ref={cardRef}
      className="group h-full overflow-hidden bg-[var(--ip-card-bg)] border border-[var(--ip-card-border)] hover:border-[var(--ip-card-border-hover)] hover:bg-[var(--ip-card-bg-hover)] shadow-[var(--ip-card-shadow)] hover:shadow-[var(--ip-card-shadow-hover)] rounded-[var(--ip-card-radius)] transition-all duration-200 ease-out"
      style={tiltStyle}
      onMouseEnter={handleMouseEnter}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* 썸네일/비디오 영역 - aspectRatio에 따라 높이 조정 */}
      <div className={`relative ${thumbnailHeightClass} w-full bg-gradient-to-br from-slate-900 to-slate-800 overflow-hidden`}>
        {/* 정적 썸네일 */}
        {thumbnailUrl && (
          <Image
            src={thumbnailUrl}
            alt={title}
            fill
            sizes="(max-width: 1024px) 220px, 220px"
            className={`object-cover transition-opacity duration-300 ${isHovered && previewVideoUrl && videoLoaded ? 'opacity-0' : 'opacity-100'}`}
          />
        )}

        {/* 비디오 프리뷰 */}
        {previewVideoUrl && (
          <video
            ref={videoRef}
            src={previewVideoUrl}
            muted={isMuted}
            loop
            playsInline
            preload="metadata"
            onLoadedData={() => setVideoLoaded(true)}
            className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-300 ${isHovered && videoLoaded ? 'opacity-100' : 'opacity-0'}`}
          />
        )}

        {/* 플레이 오버레이 - 호버 전에만 표시 */}
        {!isHovered && previewVideoUrl && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="w-12 h-12 rounded-full bg-white/90 flex items-center justify-center shadow-lg">
              <Play className="w-5 h-5 text-slate-900 ml-0.5" />
            </div>
          </div>
        )}

        {/* Mute/Unmute 토글 버튼 - 호버 중일 때 중간 좌측에 표시 */}
        {isHovered && previewVideoUrl && videoLoaded && (
          <button
            onClick={handleMuteToggle}
            className="absolute left-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/60 backdrop-blur-sm flex items-center justify-center text-white hover:bg-black/80 transition-all z-10 shadow-lg"
            aria-label={isMuted ? "Unmute" : "Mute"}
          >
            {isMuted ? (
              <VolumeX className="w-5 h-5" />
            ) : (
              <Volume2 className="w-5 h-5" />
            )}
          </button>
        )}

        {/* 상단 배지들 */}
        <div className="absolute top-2 left-2 flex items-center gap-1.5">
          {isHot && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-gradient-to-r from-rose-500 to-orange-500 text-white text-[10px] font-bold shadow-lg">
              <Flame className="w-3 h-3" />
              HOT
            </span>
          )}
          {isNew && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-gradient-to-r from-violet-500 to-blue-500 text-white text-[10px] font-bold shadow-lg">
              <Sparkles className="w-3 h-3" />
              NEW
            </span>
          )}
        </div>

        {/* 조회수 배지 */}
        {viewCount && (
          <div className="absolute bottom-2 left-2 flex items-center gap-1 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-sm text-white text-[10px] font-medium">
            <Eye className="w-3 h-3" />
            {viewCount}
          </div>
        )}

        {/* 라이선스 상태 배지 */}
        {licenseStatus !== "allowed" && (
          <div className="absolute top-2 right-2">
            <span
              className={`flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold backdrop-blur-sm ${status.className}`}
            >
              <StatusIcon className="h-3 w-3" />
              {status.label}
            </span>
          </div>
        )}

        {/* 하단 그라데이션 */}
        <div className="absolute bottom-0 left-0 right-0 h-16" style={{ background: 'var(--ip-card-gradient)' }} />
      </div>

      {/* 정보 영역 */}
      <div className="p-3 space-y-2">
        <div>
          <p className="text-sm font-bold text-[var(--fg-default)] line-clamp-1 group-hover:text-[var(--fg-primary)] transition-[var(--transition-color)]">{title}</p>
          {subtitle && (
            <p className="text-[11px] text-[var(--fg-muted)] line-clamp-1 mt-0.5">{subtitle}</p>
          )}
        </div>

        {genres && genres.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {genres.slice(0, 3).map((genre) => (
              <span
                key={genre}
                className="rounded-full bg-[var(--bg-primary-subtle)] px-2 py-0.5 text-[10px] text-[var(--fg-primary)] font-medium"
              >
                {genre}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
