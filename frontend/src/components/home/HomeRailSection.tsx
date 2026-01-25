"use client";
/* eslint-disable @next/next/no-img-element */

import React, { useRef, useState, useEffect, useCallback, TouchEvent } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ChevronLeft, ChevronRight, Pause, Play } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface RailItem {
  id: string;
  slug: string;
  name_ko: string;
  name_en: string;
  thumbnail_url?: string | null;
  license_status: string;
  preset_count: number;
}

interface HomeRailSectionProps {
  sectionId: string;
  titleKo: string;
  titleEn: string;
  items: RailItem[];
  hasMore?: boolean;
  onSeeMore?: () => void;
  onItemClick?: (item: RailItem) => void;
  autoPlayInterval?: number;
  visibleItems?: number;
  renderItem?: (item: RailItem, index: number) => React.ReactNode;
}

export default function HomeRailSection({
  sectionId: _sectionId,
  titleKo,
  titleEn,
  items,
  hasMore = false,
  onSeeMore,
  onItemClick,
  autoPlayInterval = 0,
  visibleItems = 5,
  renderItem,
}: HomeRailSectionProps) {
  const { language } = useLanguage();
  const title = language === "ko" ? titleKo : titleEn;

  const scrollRef = useRef<HTMLDivElement>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(autoPlayInterval > 0);
  const [announcement, setAnnouncement] = useState("");

  const shouldReduceMotion = useReducedMotion();
  const effectiveAutoPlay = shouldReduceMotion ? 0 : autoPlayInterval;

  const itemWidth = 192;
  const gap = 16;
  const maxIndex = Math.max(0, items.length - visibleItems);

  const scrollToIndex = useCallback(
    (index: number) => {
      if (scrollRef.current) {
        const clampedIndex = Math.max(0, Math.min(index, maxIndex));
        const scrollPosition = clampedIndex * (itemWidth + gap);
        scrollRef.current.scrollTo({
          left: scrollPosition,
          behavior: shouldReduceMotion ? "auto" : "smooth",
        });
        setCurrentIndex(clampedIndex);

        const visibleCount = Math.min(visibleItems, items.length - clampedIndex);
        const announcementText =
          language === "ko"
            ? clampedIndex + 1 + "번째부터 " + visibleCount + "개 항목 표시 중"
            : "Showing items " + (clampedIndex + 1) + " to " + (clampedIndex + visibleCount);
        setAnnouncement(announcementText);
      }
    },
    [maxIndex, itemWidth, gap, shouldReduceMotion, visibleItems, items.length, language]
  );

  const handlePrev = useCallback(() => {
    scrollToIndex(currentIndex - visibleItems);
  }, [currentIndex, visibleItems, scrollToIndex]);

  const handleNext = useCallback(() => {
    scrollToIndex(currentIndex + visibleItems);
  }, [currentIndex, visibleItems, scrollToIndex]);

  const togglePlay = useCallback(() => {
    setIsPlaying((prev) => !prev);
  }, []);

  useEffect(() => {
    if (!isPlaying || effectiveAutoPlay <= 0) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => {
        const next = prev + 1;
        if (next > maxIndex) {
          scrollToIndex(0);
          return 0;
        }
        scrollToIndex(next);
        return next;
      });
    }, effectiveAutoPlay);

    return () => clearInterval(interval);
  }, [isPlaying, effectiveAutoPlay, maxIndex, scrollToIndex]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case "ArrowLeft":
          e.preventDefault();
          handlePrev();
          break;
        case "ArrowRight":
          e.preventDefault();
          handleNext();
          break;
        case " ":
          if (autoPlayInterval > 0) {
            e.preventDefault();
            togglePlay();
          }
          break;
      }
    },
    [handlePrev, handleNext, autoPlayInterval, togglePlay]
  );

  const handleMouseEnter = useCallback(() => {
    if (autoPlayInterval > 0) setIsPlaying(false);
  }, [autoPlayInterval]);

  const handleMouseLeave = useCallback(() => {
    if (autoPlayInterval > 0) setIsPlaying(true);
  }, [autoPlayInterval]);

  // Touch swipe support for mobile accessibility (WCAG 2.2)
  const touchStartRef = useRef<number | null>(null);
  const touchEndRef = useRef<number | null>(null);
  const minSwipeDistance = 50;

  const handleTouchStart = useCallback((e: TouchEvent<HTMLDivElement>) => {
    touchStartRef.current = e.targetTouches[0].clientX;
    // Pause autoplay during touch
    if (autoPlayInterval > 0) setIsPlaying(false);
  }, [autoPlayInterval]);

  const handleTouchMove = useCallback((e: TouchEvent<HTMLDivElement>) => {
    touchEndRef.current = e.targetTouches[0].clientX;
  }, []);

  const handleTouchEnd = useCallback(() => {
    if (!touchStartRef.current || !touchEndRef.current) return;

    const distance = touchStartRef.current - touchEndRef.current;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;

    if (isLeftSwipe) {
      handleNext();
    } else if (isRightSwipe) {
      handlePrev();
    }

    touchStartRef.current = null;
    touchEndRef.current = null;

    // Resume autoplay after touch
    if (autoPlayInterval > 0) setIsPlaying(true);
  }, [handleNext, handlePrev, autoPlayInterval]);

  if (items.length === 0) return null;

  return (
    <section
      aria-roledescription="carousel"
      aria-label={title}
      className="relative mb-8"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div role="status" aria-live="polite" aria-atomic="true" className="sr-only">
        {announcement}
      </div>

      <div className="flex items-center justify-between mb-4 px-4">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">{title}</h2>
        <div className="flex items-center gap-2">
          {autoPlayInterval > 0 && (
            <button
              onClick={togglePlay}
              aria-label={isPlaying ? "Pause auto-rotation" : "Start auto-rotation"}
              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              {isPlaying ? (
                <Pause className="w-4 h-4 text-slate-600 dark:text-slate-400" />
              ) : (
                <Play className="w-4 h-4 text-slate-600 dark:text-slate-400" />
              )}
            </button>
          )}

          <div className="flex items-center gap-1">
            <button
              onClick={handlePrev}
              disabled={currentIndex === 0}
              aria-label={language === "ko" ? "이전" : "Previous"}
              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-5 h-5 text-slate-600 dark:text-slate-400" />
            </button>
            <button
              onClick={handleNext}
              disabled={currentIndex >= maxIndex}
              aria-label={language === "ko" ? "다음" : "Next"}
              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-5 h-5 text-slate-600 dark:text-slate-400" />
            </button>
          </div>

          {hasMore && onSeeMore && (
            <button
              onClick={onSeeMore}
              className="text-sm font-medium text-violet-600 dark:text-violet-400 hover:underline ml-2"
            >
              {language === "ko" ? "더보기 →" : "See more →"}
            </button>
          )}
        </div>
      </div>

      <div
        ref={scrollRef}
        role="group"
        aria-label={title}
        tabIndex={0}
        onKeyDown={handleKeyDown}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        className="flex gap-4 overflow-x-auto scrollbar-none px-4 scroll-smooth focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 focus-visible:ring-offset-2 rounded-lg touch-pan-y"
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        {items.map((item, index) => {
          const isVisible = index >= currentIndex && index < currentIndex + visibleItems;
          const itemName = language === "ko" ? item.name_ko : item.name_en;

          return (
            <motion.div
              key={item.id}
              role="group"
              aria-roledescription="slide"
              aria-label={(index + 1) + " / " + items.length + ": " + itemName}
              aria-hidden={!isVisible}
              tabIndex={isVisible ? 0 : -1}
              initial={false}
              animate={shouldReduceMotion ? {} : { opacity: isVisible ? 1 : 0.5, scale: isVisible ? 1 : 0.95 }}
              className="flex-shrink-0"
            >
              {renderItem ? renderItem(item, index) : <DefaultRailCard item={item} onClick={() => onItemClick?.(item)} />}
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}

function DefaultRailCard({ item, onClick }: { item: RailItem; onClick?: () => void }) {
  const { language } = useLanguage();
  const name = language === "ko" ? item.name_ko : item.name_en;

  return (
    <button onClick={onClick} className="w-48 group focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 rounded-xl">
      <div className="relative w-48 h-64 rounded-xl overflow-hidden bg-slate-100 dark:bg-slate-800 mb-2">
        {item.thumbnail_url ? (
          <img src={item.thumbnail_url} alt={name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-4xl">🎬</div>
        )}
        {item.license_status !== "allowed" && (
          <div className="absolute top-2 right-2">
            <span className={"text-xs px-2 py-1 rounded-full " + (item.license_status === "restricted" ? "bg-yellow-500/90 text-black" : "bg-red-500/90 text-white")}>
              {item.license_status === "restricted" ? "제한" : "불가"}
            </span>
          </div>
        )}
      </div>
      <h3 className="text-sm font-medium text-slate-900 dark:text-white truncate group-hover:text-violet-600 dark:group-hover:text-violet-400 transition-colors">{name}</h3>
      <p className="text-xs text-slate-500 dark:text-slate-400">{language === "ko" ? item.preset_count + "개 프리셋" : item.preset_count + " presets"}</p>
    </button>
  );
}
