"use client";

/**
 * Variations Grid Section
 *
 * Netflix-style card grid for IP workflow variations
 * - Visual, Video, Story, Audio, Interactive categories
 * - Version badges
 * - Hover effects with scale and shadow
 * - "Start Workflow" CTA
 */

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Brush,
  Video,
  BookOpen,
  Headphones,
  Gamepad2,
  Plus,
  ArrowRight,
  Filter,
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

export interface VariationCard {
  id: string;
  slug: string;
  nameKo: string;
  nameEn: string;
  descriptionKo: string;
  descriptionEn: string;
  thumbnailUrl?: string;
  category: "visual" | "video" | "story" | "audio" | "interactive";
  version?: string;
  isNew?: boolean;
  isBeta?: boolean;
  href: string;
}

interface VariationsGridProps {
  variations: VariationCard[];
  ipSlug?: string;
}

const CATEGORY_CONFIG = {
  visual: {
    icon: Brush,
    label: "Visual",
    labelKo: "비주얼",
    color: "text-pink-400",
    bgColor: "bg-pink-500/10",
  },
  video: {
    icon: Video,
    label: "Video",
    labelKo: "영상",
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
  },
  story: {
    icon: BookOpen,
    label: "Story",
    labelKo: "스토리",
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10",
  },
  audio: {
    icon: Headphones,
    label: "Audio",
    labelKo: "오디오",
    color: "text-green-400",
    bgColor: "bg-green-500/10",
  },
  interactive: {
    icon: Gamepad2,
    label: "Interactive",
    labelKo: "인터랙티브",
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
  },
};

function VariationCardItem({ card }: { card: VariationCard }) {
  const { language } = useLanguage();
  const ko = language === "ko";
  const categoryConfig = CATEGORY_CONFIG[card.category];
  const CategoryIcon = categoryConfig.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="group relative bg-white dark:bg-gray-800 rounded-2xl overflow-hidden border border-gray-100 dark:border-gray-700 shadow-sm hover:shadow-xl hover:shadow-violet-500/10 transition-all duration-300 transform hover:-translate-y-1"
    >
      {/* Thumbnail */}
      <div className="relative h-48 overflow-hidden bg-gray-100 dark:bg-gray-900">
        {card.thumbnailUrl ? (
          <img
            src={card.thumbnailUrl}
            alt={ko ? card.nameKo : card.nameEn}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <CategoryIcon className={`w-16 h-16 ${categoryConfig.color} opacity-30`} />
          </div>
        )}

        {/* Category Badge */}
        <div className="absolute top-3 left-3">
          <span className="px-2 py-1 bg-black/60 backdrop-blur-sm text-white text-xs font-bold rounded flex items-center gap-1">
            <CategoryIcon className={`w-3 h-3 ${categoryConfig.color}`} />
            {ko ? categoryConfig.labelKo : categoryConfig.label}
          </span>
        </div>

        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-60" />
      </div>

      {/* Content */}
      <div className="p-5">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white group-hover:text-violet-500 transition-colors">
            {ko ? card.nameKo : card.nameEn}
          </h3>
          {(card.version || card.isNew || card.isBeta) && (
            <span
              className={`text-xs font-mono px-2 py-1 rounded ${
                card.isNew
                  ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400"
                  : card.isBeta
                  ? "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400"
              }`}
            >
              {card.isNew ? "NEW" : card.isBeta ? "BETA" : card.version}
            </span>
          )}
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6 line-clamp-2">
          {ko ? card.descriptionKo : card.descriptionEn}
        </p>

        <Link
          href={card.href}
          className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-semibold text-sm hover:bg-violet-500 dark:hover:bg-violet-500 hover:text-white dark:hover:text-white transition-all group-hover:ring-2 ring-offset-2 dark:ring-offset-gray-800 ring-violet-500"
        >
          <span>{ko ? "워크플로우 시작" : "Start Workflow"}</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </motion.div>
  );
}

function CustomRemixCard() {
  const { language } = useLanguage();
  const ko = language === "ko";

  return (
    <Link
      href="/dimension"
      className="group relative flex flex-col justify-center items-center h-full min-h-[380px] bg-gray-50 dark:bg-gray-800/50 rounded-2xl border-2 border-dashed border-gray-300 dark:border-gray-700 hover:border-violet-500 dark:hover:border-violet-500 transition-all duration-300 cursor-pointer"
    >
      <div className="w-16 h-16 rounded-full bg-violet-500/10 flex items-center justify-center mb-4 group-hover:bg-violet-500 group-hover:text-white text-violet-500 transition-all duration-300">
        <Plus className="w-8 h-8" />
      </div>
      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-1">
        {ko ? "커스텀 리믹스" : "Custom Remix"}
      </h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 text-center px-8">
        {ko
          ? "나만의 워크플로우를 처음부터 만들어보세요"
          : "Build your own workflow from scratch"}
      </p>
    </Link>
  );
}

export function VariationsGrid({ variations, ipSlug }: VariationsGridProps) {
  const { language } = useLanguage();
  const ko = language === "ko";

  return (
    <section className="relative z-30 -mt-10 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-4">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            {ko ? "가능한 변주" : "Possible Variations"}
          </h2>
          <p className="text-gray-500 dark:text-gray-400">
            {ko
              ? "AI 생성 엔진으로 이 IP를 새로운 포맷으로 변환하세요."
              : "Transform this IP into new formats using our generative engine."}
          </p>
        </div>

        <div className="flex gap-2">
          <button className="p-2 rounded-full border border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300 transition-colors">
            <Filter className="w-5 h-5" />
          </button>
          <button className="px-4 py-2 rounded-full border border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300 text-sm font-medium transition-colors">
            {ko ? "전체 보기" : "View All"}
          </button>
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {variations.map((card, index) => (
          <motion.div
            key={card.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <VariationCardItem card={card} />
          </motion.div>
        ))}

        {/* Custom Remix Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: variations.length * 0.1 }}
        >
          <CustomRemixCard />
        </motion.div>
      </div>
    </section>
  );
}

export default VariationsGrid;
