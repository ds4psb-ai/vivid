"use client";

/**
 * Variations Grid Section - Stitch V2 Neon Red Design
 *
 * Bento Box layout with varying card sizes
 * Deep charcoal theme with neon red accents
 */

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Film,
  Gamepad2,
  BookOpen,
  Headphones,
  Plus,
  Play,
  ArrowUpRight,
} from "lucide-react";

export interface VariationCard {
  id: string;
  name: string;
  description: string;
  thumbnailUrl: string;
  category: "visual" | "video" | "story" | "audio" | "interactive";
  badge?: string;
  badgeColor?: string;
  href: string;
  layout?: "tall" | "wide" | "normal" | "two-thirds" | "one-third";
  icon?: React.ReactNode;
  iconColor?: string;
}

interface VariationsGridProps {
  variations: VariationCard[];
}

const CATEGORY_ICONS = {
  visual: Film,
  video: Film,
  story: BookOpen,
  audio: Headphones,
  interactive: Gamepad2,
};

const ICON_COLORS = {
  visual: "text-pink-400",
  video: "text-blue-400",
  story: "text-yellow-400",
  audio: "text-green-400",
  interactive: "text-purple-400",
};

const PROGRESS_COLORS = {
  visual: "bg-[var(--bg-primary)]",
  video: "bg-blue-500",
  story: "bg-yellow-500",
  audio: "bg-green-500",
  interactive: "bg-purple-500",
};

export function VariationsGrid({ variations }: VariationsGridProps) {
  return (
    <section className="relative z-20 px-6 md:px-16 pt-10 bg-[var(--bg-base)]">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6 max-w-7xl mx-auto">
        <div>
          <h2 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight text-white">
            가능한 <span className="text-[var(--fg-primary)]">변형</span>
          </h2>
          <p className="text-gray-400 max-w-lg font-light break-keep">
            우리의 신경망 엔진을 사용하여 이 IP를 완전히 새로운 포맷으로 해체하고 재구성하세요.
          </p>
        </div>
        <div className="flex gap-4">
          <button className="px-6 py-2 rounded-full border border-white/20 text-xs font-bold tracking-widest uppercase hover:bg-[var(--bg-primary)] hover:border-[var(--border-primary)] hover:text-white transition-all text-gray-300">
            인기순
          </button>
          <button className="px-6 py-2 rounded-full border border-white/20 text-xs font-bold tracking-widest uppercase hover:bg-[var(--bg-primary)] hover:border-[var(--border-primary)] hover:text-white transition-all text-gray-300">
            최신순
          </button>
        </div>
      </div>

      {/* Bento Grid - 12-column layout */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 h-auto md:h-[600px] max-w-7xl mx-auto">
        {/* Left Column - 애니메이션 각색 (full height) */}
        <div className="md:col-span-3 h-[400px] md:h-full">
          {variations.filter(c => c.layout === "tall").map((card, index) => {
            const Icon = CATEGORY_ICONS[card.category];
            const iconColor = ICON_COLORS[card.category];
            return (
              <motion.div
                key={card.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="group relative rounded-2xl overflow-hidden bg-[var(--bg-subtle)] border border-white/10 hover:border-[var(--border-primary)]/50 transition-all duration-300 h-full"
              >
                <img
                  alt={card.name}
                  className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                  src={card.thumbnailUrl}
                />
                <div className="absolute inset-0 z-10 bg-gradient-to-t from-black via-black/60 to-black/30 opacity-90 group-hover:opacity-95 transition-opacity" />
                <div className="absolute bottom-0 left-0 w-full p-6 z-20">
                  {card.badge && (
                    <span className="px-2 py-1 bg-[var(--bg-primary)] text-white text-[10px] font-bold uppercase tracking-wider rounded mb-3 inline-block">
                      {card.badge}
                    </span>
                  )}
                  <h3 className="text-3xl font-bold text-white mb-2 leading-none break-keep drop-shadow-lg">
                    애니메이션<br />각색
                  </h3>
                  <button className="mt-4 flex items-center text-xs font-bold tracking-widest text-[var(--fg-primary)] hover:text-white transition-colors drop-shadow-md">
                    워크플로우 시작 <ArrowUpRight className="w-4 h-4 ml-1" />
                  </button>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Center Column - 숏폼 드라마 (top) + 2-grid (bottom) */}
        <div className="md:col-span-6 flex flex-col gap-6 h-auto md:h-full">
          {/* 숏폼 드라마 - 1/2 height */}
          {variations.filter(c => c.layout === "wide").map((card, index) => (
            <motion.div
              key={card.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="group relative rounded-2xl overflow-hidden bg-[var(--bg-subtle)] border border-white/10 hover:border-[var(--border-primary)]/50 transition-all duration-300 h-[280px] md:h-1/2"
            >
              <img
                alt={card.name}
                className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                src={card.thumbnailUrl}
              />
              <div className="absolute inset-0 z-10 bg-gradient-to-r from-black/95 via-black/70 to-transparent opacity-90 group-hover:opacity-95 transition-opacity" />
              <div className="absolute bottom-0 left-0 w-full p-8 z-20 flex flex-col justify-center items-start h-full max-w-md">
                <span className="text-blue-400 font-bold uppercase text-xs tracking-widest mb-2 drop-shadow-md">포맷</span>
                <h3 className="text-4xl font-bold text-white mb-4 drop-shadow-lg">숏폼 드라마</h3>
                <p className="text-gray-200 text-sm mb-6 break-keep drop-shadow-md">
                  바이럴 소셜 플랫폼에 최적화된 강렬한 60초 세로형 에피소드입니다.
                </p>
                <button className="w-12 h-12 rounded-full border border-white/50 bg-black/30 flex items-center justify-center hover:bg-[var(--bg-primary)] hover:border-[var(--border-primary)] transition-all cursor-pointer group-hover:scale-110">
                  <Play className="w-5 h-5 text-white drop-shadow-md" />
                </button>
              </div>
            </motion.div>
          ))}

          {/* Bottom 2-grid: Graphic Novel + 3D Audio */}
          <div className="grid grid-cols-2 gap-6 h-[200px] md:h-1/2">
            {variations.filter(c => c.layout === "normal" && c.category !== "interactive").slice(0, 2).map((card, index) => {
              const Icon = CATEGORY_ICONS[card.category];
              const iconColor = ICON_COLORS[card.category];
              return (
                <motion.div
                  key={card.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + index * 0.1 }}
                  className="group relative rounded-2xl overflow-hidden bg-[var(--bg-subtle)] border border-white/10 hover:border-[var(--border-primary)]/50 transition-all duration-300"
                >
                  <img
                    alt={card.name}
                    className={`absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-110 ${
                      card.category === "audio" ? "grayscale group-hover:grayscale-0" : ""
                    }`}
                    src={card.thumbnailUrl}
                  />
                  <div className="absolute inset-0 z-10 bg-gradient-to-t from-black via-black/60 to-black/30 opacity-90 group-hover:opacity-95 transition-opacity" />
                  <div className="absolute bottom-0 left-0 w-full p-6 z-20">
                    <Icon className={`w-10 h-10 mb-2 opacity-90 ${iconColor} drop-shadow-md`} />
                    <h3 className="text-xl font-bold text-white drop-shadow-lg">{card.name}</h3>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Right Column - Interactive Game (2/3) + Custom Workflow (1/3) */}
        <div className="md:col-span-3 flex flex-col gap-6 h-auto md:h-full">
          {/* Interactive Game - 2/3 height */}
          {variations.filter(c => c.category === "interactive").map((card, index) => {
            const Icon = CATEGORY_ICONS[card.category];
            const iconColor = ICON_COLORS[card.category];
            return (
              <motion.div
                key={card.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="group relative rounded-2xl overflow-hidden bg-[var(--bg-subtle)] border border-white/10 hover:border-[var(--border-primary)]/50 transition-all duration-300 h-[300px] md:h-2/3"
              >
                <img
                  alt={card.name}
                  className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                  src={card.thumbnailUrl}
                />
                <div className="absolute inset-0 z-10 bg-gradient-to-t from-black via-black/60 to-black/30 opacity-90 group-hover:opacity-95 transition-opacity" />
                <div className="absolute bottom-0 left-0 w-full p-6 z-20">
                  <Icon className={`w-10 h-10 mb-2 opacity-90 ${iconColor} drop-shadow-md`} />
                  <h3 className="text-xl font-bold text-white drop-shadow-lg">{card.name}</h3>
                </div>
              </motion.div>
            );
          })}

          {/* Custom Workflow Card - 1/3 height */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="group relative rounded-2xl overflow-hidden bg-transparent border border-dashed border-gray-600 hover:border-[var(--border-primary)] transition-all duration-300 flex flex-col items-center justify-center cursor-pointer h-[150px] md:h-1/3"
          >
            <Link href="/dimension" className="relative z-10 flex flex-col items-center">
              <div className="w-12 h-12 rounded-full border border-gray-500 dark:border-gray-600 flex items-center justify-center mb-3 group-hover:bg-[var(--bg-primary)] group-hover:border-[var(--border-primary)] transition-all">
                <Plus className="w-6 h-6 text-gray-500 dark:text-gray-400 group-hover:text-white" />
              </div>
              <h3 className="text-base font-bold text-gray-600 dark:text-gray-300 group-hover:text-[var(--fg-primary)] transition-colors">
                커스텀 워크플로우
              </h3>
              <p className="text-xs text-gray-500 font-bold mt-1">나만의 디자인 만들기</p>
            </Link>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

export default VariationsGrid;
