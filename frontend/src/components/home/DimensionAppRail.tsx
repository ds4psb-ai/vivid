"use client";

/**
 * Dimension App Rail Component
 *
 * 핵심 차원 앱을 한 줄로 표시하는 컴팩트한 레일 컴포넌트입니다.
 * 투자자 데모용 메인 페이지 하단에 사용됩니다.
 */

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Brain,
  Search,
  Layers,
  Image as ImageIcon,
  Video,
  Palette,
  Sparkles,
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface DimensionApp {
  id: string;
  href: string;
  icon: React.ElementType;
  badge: string;
  titleKo: string;
  titleEn: string;
  descKo: string;
  descEn: string;
  color: string;
}

// =============================================================================
// Color Classes Map (Tailwind can't generate dynamic classes at runtime)
// =============================================================================
type ColorKey = "violet" | "blue" | "emerald" | "amber" | "rose" | "cyan" | "purple" | "orange";

const COLOR_CLASSES: Record<ColorKey, {
  border: string;
  bg: string;
  bgHover: string;
  text: string;
  badge: string;
  textHover: string;
}> = {
  violet: {
    border: "hover:border-violet-500/50",
    bg: "bg-violet-500/10",
    bgHover: "group-hover:bg-violet-500/20",
    text: "text-violet-500",
    badge: "bg-violet-500",
    textHover: "group-hover:text-violet-600 dark:group-hover:text-violet-400",
  },
  blue: {
    border: "hover:border-blue-500/50",
    bg: "bg-blue-500/10",
    bgHover: "group-hover:bg-blue-500/20",
    text: "text-blue-500",
    badge: "bg-blue-500",
    textHover: "group-hover:text-blue-600 dark:group-hover:text-blue-400",
  },
  emerald: {
    border: "hover:border-emerald-500/50",
    bg: "bg-emerald-500/10",
    bgHover: "group-hover:bg-emerald-500/20",
    text: "text-emerald-500",
    badge: "bg-emerald-500",
    textHover: "group-hover:text-emerald-600 dark:group-hover:text-emerald-400",
  },
  amber: {
    border: "hover:border-amber-500/50",
    bg: "bg-amber-500/10",
    bgHover: "group-hover:bg-amber-500/20",
    text: "text-amber-500",
    badge: "bg-amber-500",
    textHover: "group-hover:text-amber-600 dark:group-hover:text-amber-400",
  },
  rose: {
    border: "hover:border-rose-500/50",
    bg: "bg-rose-500/10",
    bgHover: "group-hover:bg-rose-500/20",
    text: "text-rose-500",
    badge: "bg-rose-500",
    textHover: "group-hover:text-rose-600 dark:group-hover:text-rose-400",
  },
  cyan: {
    border: "hover:border-cyan-500/50",
    bg: "bg-cyan-500/10",
    bgHover: "group-hover:bg-cyan-500/20",
    text: "text-cyan-500",
    badge: "bg-cyan-500",
    textHover: "group-hover:text-cyan-600 dark:group-hover:text-cyan-400",
  },
  purple: {
    border: "hover:border-purple-500/50",
    bg: "bg-purple-500/10",
    bgHover: "group-hover:bg-purple-500/20",
    text: "text-purple-500",
    badge: "bg-purple-500",
    textHover: "group-hover:text-purple-600 dark:group-hover:text-purple-400",
  },
  orange: {
    border: "hover:border-orange-500/50",
    bg: "bg-orange-500/10",
    bgHover: "group-hover:bg-orange-500/20",
    text: "text-orange-500",
    badge: "bg-orange-500",
    textHover: "group-hover:text-orange-600 dark:group-hover:text-orange-400",
  },
};

// =============================================================================
// Core Apps (데모용 핵심 앱 8개)
// =============================================================================
const CORE_APPS: DimensionApp[] = [
  {
    id: "reference-decoder",
    href: "/dimension/reference-decoder",
    icon: Search,
    badge: "4D",
    titleKo: "레퍼런스 분석",
    titleEn: "Reference Decoder",
    descKo: "영상 분석",
    descEn: "Video Analysis",
    color: "blue",
  },
  {
    id: "abyss-mirror",
    href: "/dimension/abyss",
    icon: Brain,
    badge: "AI",
    titleKo: "심연의 거울",
    titleEn: "Abyss Mirror",
    descKo: "창작 DNA 분석",
    descEn: "Creative DNA",
    color: "violet",
  },
  {
    id: "aesthetic-director",
    href: "/dimension/aesthetic",
    icon: Palette,
    badge: "AD",
    titleKo: "미학디렉터",
    titleEn: "Aesthetic Director",
    descKo: "거장 스타일",
    descEn: "Master Styles",
    color: "amber",
  },
  {
    id: "story-architect",
    href: "/dimension/story-architect",
    icon: Layers,
    badge: "2D",
    titleKo: "스토리 생성",
    titleEn: "Story Architect",
    descKo: "시나리오 작성",
    descEn: "Scenario Writing",
    color: "emerald",
  },
  {
    id: "visual-realizer",
    href: "/dimension/visual-realizer",
    icon: ImageIcon,
    badge: "3D",
    titleKo: "비주얼 생성",
    titleEn: "Visual Realizer",
    descKo: "키프레임 생성",
    descEn: "Key Frames",
    color: "rose",
  },
  {
    id: "suno",
    href: "/dimension/suno",
    icon: Sparkles,
    badge: "BGM",
    titleKo: "음악 생성",
    titleEn: "Suno Music",
    descKo: "Suno V5 BGM",
    descEn: "Suno V5 BGM",
    color: "purple",
  },
  {
    id: "video-maker",
    href: "/dimension/video-maker",
    icon: Video,
    badge: "VEO",
    titleKo: "비디오 메이커",
    titleEn: "Video Maker",
    descKo: "Veo 3.1 영상",
    descEn: "Veo 3.1 Video",
    color: "cyan",
  },
  {
    id: "kling",
    href: "/dimension/kling",
    icon: Video,
    badge: "KLING",
    titleKo: "Kling 영상",
    titleEn: "Kling Video",
    descKo: "Kling 2.6 영상",
    descEn: "Kling 2.6 Video",
    color: "orange",
  },
];

interface DimensionAppRailProps {
  /** 컴팩트 모드 (작은 크기) */
  compact?: boolean;
  /** 핵심 앱만 표시 */
  showCore?: boolean;
}

export function DimensionAppRail({
  compact = false,
  showCore = true,
}: DimensionAppRailProps) {
  const { language } = useLanguage();
  const ko = language === "ko";

  const apps = CORE_APPS;

  return (
    <div className="w-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-violet-500" />
          <h3 className="text-lg font-semibold text-[var(--fg-0)]">
            {ko ? "차원 도구" : "Dimension Tools"}
          </h3>
        </div>
        <Link
          href="/flow"
          className="text-sm text-violet-500 hover:text-violet-600 transition-colors"
        >
          {ko ? "전체 보기 →" : "View All →"}
        </Link>
      </div>

      {/* App Grid */}
      <div
        className={`grid gap-3 ${compact
          ? "grid-cols-3 md:grid-cols-6"
          : "grid-cols-2 md:grid-cols-3 lg:grid-cols-6"
          }`}
      >
        {apps.map((app, index) => {
          const Icon = app.icon;
          const colors = COLOR_CLASSES[app.color as ColorKey];

          return (
            <motion.div
              key={app.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Link
                href={app.href}
                className={`group block p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/50 dark:bg-slate-800/30 ${colors.border} hover:bg-opacity-50 transition-all`}
              >
                <div className="flex flex-col items-center text-center gap-2">
                  {/* Icon with Badge */}
                  <div className="relative">
                    <div
                      className={`w-10 h-10 rounded-lg ${colors.bg} flex items-center justify-center ${colors.bgHover} transition-colors`}
                    >
                      <Icon className={`w-5 h-5 ${colors.text}`} />
                    </div>
                    <span
                      className={`absolute -top-1 -right-1 px-1.5 py-0.5 rounded-full ${colors.badge} text-white text-[8px] font-bold`}
                    >
                      {app.badge}
                    </span>
                  </div>

                  {/* Title */}
                  <div>
                    <p
                      className={`text-xs font-medium text-[var(--fg-0)] ${colors.textHover} transition-colors line-clamp-1`}
                    >
                      {ko ? app.titleKo : app.titleEn}
                    </p>
                    {!compact && (
                      <p className="text-[10px] text-[var(--fg-muted)] mt-0.5 line-clamp-1">
                        {ko ? app.descKo : app.descEn}
                      </p>
                    )}
                  </div>
                </div>
              </Link>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

export default DimensionAppRail;
