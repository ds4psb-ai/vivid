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

// 핵심 앱만 선별 (데모용)
const CORE_APPS: DimensionApp[] = [
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

  const apps = showCore ? CORE_APPS : CORE_APPS;

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
        className={`grid gap-3 ${
          compact
            ? "grid-cols-3 md:grid-cols-6"
            : "grid-cols-2 md:grid-cols-3 lg:grid-cols-6"
        }`}
      >
        {apps.map((app, index) => {
          const Icon = app.icon;

          return (
            <motion.div
              key={app.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Link
                href={app.href}
                className={`group block p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/50 dark:bg-slate-800/30 hover:border-${app.color}-500/50 hover:bg-${app.color}-50/50 dark:hover:bg-${app.color}-900/10 transition-all`}
              >
                <div className="flex flex-col items-center text-center gap-2">
                  {/* Icon with Badge */}
                  <div className="relative">
                    <div
                      className={`w-10 h-10 rounded-lg bg-${app.color}-500/10 flex items-center justify-center group-hover:bg-${app.color}-500/20 transition-colors`}
                    >
                      <Icon className={`w-5 h-5 text-${app.color}-500`} />
                    </div>
                    <span
                      className={`absolute -top-1 -right-1 px-1.5 py-0.5 rounded-full bg-${app.color}-500 text-white text-[8px] font-bold`}
                    >
                      {app.badge}
                    </span>
                  </div>

                  {/* Title */}
                  <div>
                    <p
                      className={`text-xs font-medium text-[var(--fg-0)] group-hover:text-${app.color}-600 dark:group-hover:text-${app.color}-400 transition-colors line-clamp-1`}
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
