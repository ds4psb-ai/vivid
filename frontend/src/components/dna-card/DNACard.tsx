"use client";

import { useState, useRef, useCallback } from "react";
import { AnimatePresence } from "framer-motion";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { DNACard as DNACardType } from "@/types/dna-card";
import { DNA_CARD_CONFIG } from "./constants";
import { DNACardPreview } from "./DNACardPreview";
import { useIsMobile } from "@/hooks/useMediaQuery";
import { useDNACardContext } from "@/stores/dnaCardContextStore";

interface DNACardProps {
  card: DNACardType;
  onClick?: (card: DNACardType) => void;
  showPreviewOnHover?: boolean;
}

export function DNACard({
  card,
  onClick,
  showPreviewOnHover = true,
}: DNACardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const cardRef = useRef<HTMLAnchorElement>(null);
  const [anchorRect, setAnchorRect] = useState<DOMRect | null>(null);
  const config = DNA_CARD_CONFIG[card.type];
  const Icon = config.icon;

  // Responsive: Side Panel on desktop, page navigation on mobile
  const isMobile = useIsMobile();
  const openSidePanel = useDNACardContext((s) => s.openSidePanel);

  const handleCardClick = useCallback(
    (e: React.MouseEvent) => {
      // If custom onClick is provided, use it
      if (onClick) {
        e.preventDefault();
        onClick(card);
        return;
      }

      // Desktop: open Side Panel instead of navigating
      if (!isMobile) {
        e.preventDefault();
        openSidePanel(card);
      }
      // Mobile: let the Link navigate normally
    },
    [onClick, isMobile, openSidePanel, card]
  );

  const href = `/${card.megaAppEntry.app}?tab=${card.megaAppEntry.tab}${
    card.megaAppEntry.preloadParams
      ? `&${new URLSearchParams(card.megaAppEntry.preloadParams).toString()}`
      : ""
  }`;

  const handleMouseEnter = () => {
    setIsHovered(true);
    // P0: 위치 계산을 위한 rect 저장
    if (cardRef.current) {
      setAnchorRect(cardRef.current.getBoundingClientRect());
    }
  };

  return (
    <div
      className="relative"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* 기본 카드 (Collapsed State) - P1: 반응형 */}
      <Link
        ref={cardRef}
        href={href}
        onClick={handleCardClick}
        className={cn(
          "block overflow-hidden",
          // P1: 반응형 크기
          "w-44 rounded-xl", // 모바일
          "md:w-52 md:rounded-2xl", // 태블릿
          "lg:w-56", // 데스크톱
          "bg-[var(--surface-1)] border border-[var(--border-muted)]",
          "hover:border-[var(--border-strong)] hover:-translate-y-1",
          "transition-all duration-300"
        )}
        style={
          {
            "--card-hue": card.hue ?? config.hue,
          } as React.CSSProperties
        }
      >
        {/* 썸네일 */}
        <div className="relative h-32 bg-black/20 overflow-hidden">
          {card.thumbnailUrl ? (
            <img
              src={card.thumbnailUrl}
              alt={card.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-800 to-gray-900">
              <Icon className="w-12 h-12 text-white/20" />
            </div>
          )}

          {/* 타입 배지 */}
          <div className="absolute top-2 left-2 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-sm">
            <span className="text-[10px] font-medium text-white/80 flex items-center gap-1">
              <Icon className="w-3 h-3" />
              {config.label}
            </span>
          </div>

          {/* NEW/HOT 배지 */}
          {card.badgeText && (
            <div
              className="absolute top-2 right-2 px-2 py-0.5 rounded-full text-[10px] font-bold text-white"
              style={{
                backgroundColor:
                  card.badgeColor ??
                  `oklch(0.7 0.2 ${card.hue ?? config.hue})`,
              }}
            >
              {card.badgeText}
            </div>
          )}

          {/* 하단 그라데이션 */}
          <div className="absolute inset-x-0 bottom-0 h-12 bg-gradient-to-t from-black/60 to-transparent" />
        </div>

        {/* 정보 */}
        <div className="p-4 space-y-2">
          <h3 className="font-bold text-[var(--fg-default)] truncate">
            {card.name}
          </h3>
          <p className="text-xs text-[var(--fg-muted)] line-clamp-2">
            {card.description}
          </p>

          {/* CTA */}
          <div className="flex items-center justify-between pt-2">
            <span className="text-[10px] text-[var(--fg-muted)]">
              {config.megaApp === "dna-lab" ? "DNA Lab" : "Story Engine"}
            </span>
            <ArrowRight className="w-4 h-4 text-[var(--fg-muted)]" />
          </div>
        </div>
      </Link>

      {/* 호버 프리뷰 (Expanded State) - P0: anchorRect 전달 */}
      <AnimatePresence>
        {showPreviewOnHover && isHovered && (
          <DNACardPreview card={card} anchorRect={anchorRect} />
        )}
      </AnimatePresence>
    </div>
  );
}
