"use client";

/**
 * DNAContextBanner - DNA 카드 컨텍스트 로드 알림 배너
 *
 * DNA 카드에서 메가앱으로 진입했을 때 패널 상단에 표시되는 배너입니다.
 * 로드된 DNA 정보와 해제 버튼을 제공합니다.
 *
 * @example
 * ```tsx
 * <DNAContextBanner
 *   cardType="master"
 *   cardName="강주노"
 *   onDismiss={handleDismiss}
 * />
 * ```
 */

import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles, Palette, Film, User } from "lucide-react";
import { DNA_CARD_CONFIG } from "./constants";
import type { DNACardType } from "@/types/dna-card";

interface DNAContextBannerProps {
  /** 카드 타입 */
  cardType: DNACardType;
  /** 카드 이름 (거장명, 작품명, 캐릭터명) */
  cardName: string;
  /** 해제 버튼 클릭 시 */
  onDismiss: () => void;
  /** 추가 정보 (선택) */
  additionalInfo?: string;
  /** 클래스명 오버라이드 */
  className?: string;
}

export function DNAContextBanner({
  cardType,
  cardName,
  onDismiss,
  additionalInfo,
  className = "",
}: DNAContextBannerProps) {
  const config = DNA_CARD_CONFIG[cardType];

  // 타입별 아이콘
  const IconComponent =
    cardType === "master"
      ? Palette
      : cardType === "masterpiece"
        ? Film
        : User;

  // 타입별 그라데이션 색상
  const gradientColors: Record<DNACardType, string> = {
    master: "from-amber-500/10 to-orange-500/10 border-amber-500/20",
    masterpiece: "from-emerald-500/10 to-teal-500/10 border-emerald-500/20",
    character: "from-violet-500/10 to-purple-500/10 border-violet-500/20",
  };

  const textColors: Record<DNACardType, string> = {
    master: "text-amber-500",
    masterpiece: "text-emerald-500",
    character: "text-violet-500",
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.2 }}
        className={`p-3 rounded-lg bg-gradient-to-r ${gradientColors[cardType]} border ${className}`}
      >
        <div className="flex items-center justify-between">
          {/* 아이콘 + 텍스트 */}
          <div className="flex items-center gap-2">
            <div
              className={`p-1.5 rounded-md bg-white/10 ${textColors[cardType]}`}
            >
              <IconComponent className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm text-white/90 font-medium flex items-center gap-1.5">
                <Sparkles className={`w-3 h-3 ${textColors[cardType]}`} />
                <strong>{cardName}</strong>의 {config.label}가 로드되었습니다
              </span>
              {additionalInfo && (
                <span className="text-xs text-white/50 mt-0.5">
                  {additionalInfo}
                </span>
              )}
            </div>
          </div>

          {/* 해제 버튼 */}
          <button
            onClick={onDismiss}
            className="p-1.5 hover:bg-white/10 rounded-md transition-colors"
            aria-label="DNA 컨텍스트 해제"
          >
            <X className="w-4 h-4 text-white/60 hover:text-white/90" />
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

/**
 * DNAContextBannerCompact - 컴팩트 버전 (인라인 표시용)
 */
interface DNAContextBannerCompactProps {
  cardType: DNACardType;
  cardName: string;
  onDismiss: () => void;
}

export function DNAContextBannerCompact({
  cardType,
  cardName,
  onDismiss,
}: DNAContextBannerCompactProps) {
  const config = DNA_CARD_CONFIG[cardType];

  const badgeColors: Record<DNACardType, string> = {
    master: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    masterpiece: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    character: "bg-violet-500/20 text-violet-400 border-violet-500/30",
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border ${badgeColors[cardType]}`}
    >
      <Sparkles className="w-3 h-3" />
      <span className="text-xs font-medium">
        {cardName} {config.label}
      </span>
      <button
        onClick={onDismiss}
        className="p-0.5 hover:bg-white/10 rounded-full"
      >
        <X className="w-3 h-3" />
      </button>
    </motion.div>
  );
}
