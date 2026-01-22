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
import { Sparkles } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { DIMENSION_ICONS, DIMENSION_ITEMS } from "@/lib/dimension-data";

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
// Core Apps (메인페이지 하단 Core Tools)
// =============================================================================
const CORE_APP_IDS = [
  "reference-decoder",
  "abyss-mirror",
  "aesthetic-director",
  "story-architect",
  "video-maker",
  "suno-music",
] as const;

const CORE_APP_OVERRIDES: Record<
  (typeof CORE_APP_IDS)[number],
  Pick<DimensionApp, "badge" | "titleKo" | "titleEn" | "descKo" | "descEn" | "color">
> = {
  "reference-decoder": {
    badge: "4D",
    titleKo: "레퍼런스 해석기",
    titleEn: "Reference Decoder",
    descKo: "4D 분석",
    descEn: "4D Analysis",
    color: "blue",
  },
  "abyss-mirror": {
    badge: "AI",
    titleKo: "심연의 거울",
    titleEn: "Abyss Mirror",
    descKo: "캐릭터 에센스",
    descEn: "Character Essence",
    color: "violet",
  },
  "aesthetic-director": {
    badge: "AD",
    titleKo: "미학디렉터",
    titleEn: "Aesthetic Director",
    descKo: "비주얼 스타일",
    descEn: "Visual Style",
    color: "amber",
  },
  "story-architect": {
    badge: "STORY",
    titleKo: "시나리오 생성기",
    titleEn: "Story Architect",
    descKo: "서사 구조",
    descEn: "Narrative Logic",
    color: "emerald",
  },
  "video-maker": {
    badge: "VEO",
    titleKo: "VEO 비디오",
    titleEn: "VEO Video",
    descKo: "영상 생성",
    descEn: "Video Generation",
    color: "cyan",
  },
  "suno-music": {
    badge: "BGM",
    titleKo: "Suno 음악",
    titleEn: "Suno Music",
    descKo: "BGM & 사운드",
    descEn: "BGM & Sound",
    color: "purple",
  },
};

const CORE_APPS: DimensionApp[] = CORE_APP_IDS.map((id) => {
  const base = DIMENSION_ITEMS.find((item) => item.id === id);
  const overrides = CORE_APP_OVERRIDES[id];
  const icon = base ? DIMENSION_ICONS[base.iconName] ?? Sparkles : Sparkles;

  return {
    id,
    href: base?.href ?? "/dimension",
    icon,
    badge: overrides.badge,
    titleKo: overrides.titleKo,
    titleEn: overrides.titleEn,
    descKo: overrides.descKo,
    descEn: overrides.descEn,
    color: overrides.color,
  };
});

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
    <section className="w-full">
      <div className="mx-auto max-w-6xl px-6 py-10 space-y-6 rounded-3xl border border-white/10 bg-[radial-gradient(circle_at_top,_rgba(255,_255,_255,_0.08),_transparent_60%)] backdrop-blur-2xl shadow-2xl shadow-violet-500/10">
        <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            {showCore && (
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.3em] text-[var(--fg-muted)]">
                <Sparkles className="w-4 h-4 text-violet-400" />
                {ko ? "핵심 도구" : "Core Tools"}
              </div>
            )}
            <h3 className="text-2xl font-semibold text-[var(--fg-0)]">
              {ko ? "차원 앱으로 시작하세요" : "Kick off with Dimension Apps"}
            </h3>
            <p className="text-sm text-[var(--fg-muted)] mt-1 leading-relaxed max-w-2xl">
              {ko
                ? "Flow를 미리 보기 전에 주요 차원 앱을 간결한 카드로 확인하세요. 아이콘, 배지, 설명이 한눈에 들어옵니다."
                : "Preview the key dimension tools in a focused rail before entering the Flow. Icons, badges, and descriptions stay concise."}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/flow"
              className="text-sm font-semibold text-violet-500 hover:text-violet-600 transition-colors"
            >
              {ko ? "전체 보기 →" : "View All →"}
            </Link>
            {!compact && (
              <span className="hidden md:inline text-sm text-[var(--fg-muted)]">
                {ko ? "공간을 넓혀 보세요" : "Explore the workspace"}
              </span>
            )}
          </div>
        </div>

        <div
          className={`grid gap-4 ${compact
            ? "grid-cols-3 sm:grid-cols-4"
            : "grid-cols-2 sm:grid-cols-3 lg:grid-cols-6"
            }`}
        >
          {apps.map((app, index) => {
            const Icon = app.icon;
            const colors = COLOR_CLASSES[app.color as ColorKey];

            return (
              <motion.div
                key={app.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Link
                  href={app.href}
                  className={`group block relative overflow-hidden rounded-2xl border border-white/10 bg-white/30 px-4 py-5 text-center shadow-xl shadow-black/20 transition-all duration-200 hover:border-white/30 hover:bg-white/40`}
                >
                  <div className="flex items-center justify-center">
                    <div className={`w-12 h-12 ${colors.bg} rounded-2xl flex items-center justify-center ${colors.bgHover} transition-colors duration-200`}>
                      <Icon className={`w-6 h-6 ${colors.text}`} />
                    </div>
                  </div>
                  <div className="mt-4 space-y-1">
                    <span
                      className={`inline-flex items-center justify-center rounded-full px-3 py-0.5 text-[10px] font-semibold tracking-wide text-white ${colors.badge}`}
                    >
                      {app.badge}
                    </span>
                    <p className="text-sm font-semibold text-[var(--fg-0)] tracking-tight">
                      {ko ? app.titleKo : app.titleEn}
                    </p>
                    {!compact && (
                      <p className="text-xs text-[var(--fg-muted)] leading-snug">
                        {ko ? app.descKo : app.descEn}
                      </p>
                    )}
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export default DimensionAppRail;
