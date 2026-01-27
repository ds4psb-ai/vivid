"use client";

/**
 * MegaMenu - Netflix 2026 Style Mega Menu
 *
 * Three-column grid layout showcasing Mega Apps:
 * - DNA Lab (DNA 연구실): Auteur DNA extraction
 * - Story Engine (스토리 엔진): Story composition & prompts
 * - Production Bridge (프로덕션 브릿지): Media generation
 *
 * Features:
 * - Glass morphism with backdrop blur
 * - Framer Motion animations
 * - Responsive (collapses on tablet/mobile)
 * - Keyboard accessible
 */

import React from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, Sparkles } from "lucide-react";
import {
  MEGA_APPS,
  DIMENSION_ITEMS,
  getDimensionIcon,
  type DimensionItemData,
} from "@/lib/dimension-data";

// =============================================================================
// TYPES
// =============================================================================

interface MegaMenuProps {
  isOpen: boolean;
  onClose: () => void;
}

interface MegaMenuSectionProps {
  appKey: string;
  title: string;
  icon: string;
  description: string;
  items: DimensionItemData[];
  href: string;
}

// =============================================================================
// MEGA MENU SECTION
// =============================================================================

function MegaMenuSection({
  appKey,
  title,
  icon,
  description,
  items,
  href,
}: MegaMenuSectionProps) {
  // Get color class based on mega app
  const getColorClass = () => {
    switch (appKey) {
      case "dna-lab":
        return "text-emerald-400 group-hover/section:text-emerald-300";
      case "story-engine":
        return "text-amber-400 group-hover/section:text-amber-300";
      case "production":
        return "text-blue-400 group-hover/section:text-blue-300";
      default:
        return "text-violet-400";
    }
  };

  const getBgClass = () => {
    switch (appKey) {
      case "dna-lab":
        return "hover:bg-emerald-500/10";
      case "story-engine":
        return "hover:bg-amber-500/10";
      case "production":
        return "hover:bg-blue-500/10";
      default:
        return "hover:bg-violet-500/10";
    }
  };

  return (
    <div className="group/section">
      {/* Section Header */}
      <Link
        href={href}
        className={`flex items-center gap-2 mb-3 pb-2 border-b border-[var(--glass-border)] ${getBgClass()} rounded-lg px-2 py-1.5 -mx-2 transition-all duration-200`}
      >
        <span className="text-xl">{icon}</span>
        <div className="flex-1 min-w-0">
          <h3 className={`text-sm font-semibold ${getColorClass()} transition-colors`}>
            {title}
          </h3>
          <p className="text-[11px] text-[var(--fg-muted)] truncate">
            {description}
          </p>
        </div>
        <ChevronRight className="w-4 h-4 text-[var(--fg-muted)] group-hover/section:translate-x-0.5 transition-transform" />
      </Link>

      {/* Items List */}
      <div className="space-y-0.5">
        {items.map((item) => {
          const Icon = getDimensionIcon(item.iconName);
          return (
            <Link
              key={item.id}
              href={item.href}
              className="group/item flex items-center gap-2.5 px-2 py-2 rounded-lg
                         hover:bg-[var(--surface-2)] dark:hover:bg-white/[0.04]
                         transition-all duration-150"
            >
              <div className="w-7 h-7 rounded-md bg-[var(--surface-2)] dark:bg-white/[0.06]
                              flex items-center justify-center shrink-0
                              group-hover/item:scale-105 transition-transform">
                <Icon className="w-4 h-4 text-[var(--fg-muted)]" />
              </div>
              <div className="flex-1 min-w-0">
                <span className="text-sm text-[var(--fg-0)] dark:text-white font-medium
                               group-hover/item:text-[var(--color-brand-primary)] transition-colors">
                  {item.titleKo}
                </span>
                <p className="text-[11px] text-[var(--fg-muted)] truncate">
                  {item.descKo}
                </p>
              </div>
              {item.isNew && (
                <span className="px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider
                               bg-[var(--color-brand-primary)]/20 text-[var(--color-brand-primary)]
                               rounded-full shrink-0">
                  NEW
                </span>
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );
}

// =============================================================================
// RECOMMENDED WORKFLOW
// =============================================================================

function RecommendedWorkflow() {
  const workflow = [
    { name: "레퍼런스 해석기", href: "/dimension/reference-decoder" },
    { name: "스토리보드", href: "/dimension/storyboard" },
    { name: "비디오 메이커", href: "/dimension/video-maker" },
  ];

  return (
    <div className="flex items-center gap-2 text-sm">
      <Sparkles className="w-4 h-4 text-[var(--color-brand-primary)]" />
      <span className="text-[var(--fg-muted)] font-medium">추천:</span>
      <div className="flex items-center gap-1.5">
        {workflow.map((step, idx) => (
          <React.Fragment key={step.href}>
            <Link
              href={step.href}
              className="text-[var(--fg-0)] dark:text-white hover:text-[var(--color-brand-primary)] transition-colors"
            >
              {step.name}
            </Link>
            {idx < workflow.length - 1 && (
              <ChevronRight className="w-3 h-3 text-[var(--fg-muted)]" />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

// =============================================================================
// MEGA MENU MAIN COMPONENT
// =============================================================================

// Explicit item mappings for each mega app section
const DNA_LAB_ITEMS = [
  "abyss-mirror",      // 심연의 거울
  "reference-decoder", // 레퍼런스 해석기
  "aesthetic-director",// 미학 디렉터
  "quality-director",  // 퀄리티 디렉터
];

const STORY_ENGINE_ITEMS = [
  "story-architect",     // 시나리오 생성기
  "storyboard-sketch",   // 스토리보드 스케치
  "prompt-generator",    // 프롬프트 생성기
  "platform-translator", // 플랫폼 번역기
];

const PRODUCTION_ITEMS = [
  "visual-realizer", // 비주얼 리얼라이저
  "video-maker",     // 비디오 메이커
  "kling-video",     // Kling 2.6
  "suno-music",      // Suno 음악
  "sound-crafter",   // 사운드 크래프터
];

export function MegaMenu({ isOpen, onClose }: MegaMenuProps) {
  // Get items by explicit ID list
  const getItemsById = (ids: string[]): DimensionItemData[] => {
    return ids
      .map((id) => DIMENSION_ITEMS.find((item) => item.id === id))
      .filter((item): item is DimensionItemData => item !== undefined);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 bg-black/20 dark:bg-black/40 z-40"
            onClick={onClose}
          />

          {/* Menu Panel */}
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="absolute top-full left-0 right-0 mt-2 z-50
                       bg-[var(--surface-1)] dark:bg-[rgba(22,22,24,0.95)]
                       backdrop-blur-xl
                       border border-[var(--glass-border)]
                       rounded-2xl shadow-2xl
                       p-6 max-w-5xl mx-auto"
            role="menu"
            aria-label="도구 메뉴"
          >
            {/* 3-Column Grid for Mega Apps */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
              {/* DNA Lab */}
              <MegaMenuSection
                appKey="dna-lab"
                title={MEGA_APPS["dna-lab"].nameKo}
                icon={MEGA_APPS["dna-lab"].icon}
                description={MEGA_APPS["dna-lab"].descriptionKo}
                href={MEGA_APPS["dna-lab"].href}
                items={getItemsById(DNA_LAB_ITEMS)}
              />

              {/* Story Engine */}
              <MegaMenuSection
                appKey="story-engine"
                title={MEGA_APPS["story-engine"].nameKo}
                icon={MEGA_APPS["story-engine"].icon}
                description={MEGA_APPS["story-engine"].descriptionKo}
                href={MEGA_APPS["story-engine"].href}
                items={getItemsById(STORY_ENGINE_ITEMS)}
              />

              {/* Production Bridge */}
              <MegaMenuSection
                appKey="production"
                title={MEGA_APPS["production"].nameKo}
                icon={MEGA_APPS["production"].icon}
                description={MEGA_APPS["production"].descriptionKo}
                href={MEGA_APPS["production"].href}
                items={getItemsById(PRODUCTION_ITEMS)}
              />
            </div>

            {/* Recommended Workflow */}
            <div className="mt-6 pt-4 border-t border-[var(--glass-border)]">
              <RecommendedWorkflow />
            </div>

            {/* Quick Link to All Tools */}
            <div className="mt-4 flex justify-end">
              <Link
                href="/dimension"
                className="text-xs text-[var(--fg-muted)] hover:text-[var(--color-brand-primary)]
                         transition-colors flex items-center gap-1"
              >
                모든 도구 보기
                <ChevronRight className="w-3 h-3" />
              </Link>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

export default MegaMenu;
