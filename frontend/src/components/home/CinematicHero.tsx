"use client";

/**
 * Cinematic Hero Section
 *
 * Netflix-style full-width hero with featured IP
 * - Blurred background image with gradient overlay
 * - Large title with gradient text
 * - Tags, rating, remix stats
 * - CTA buttons: "Remix with AI", "Watch Original"
 */

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Sparkles, Play, Star, BarChart3 } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

export interface FeaturedIP {
  slug: string;
  titleKo: string;
  titleEn: string;
  descriptionKo: string;
  descriptionEn: string;
  bannerUrl: string;
  tags: string[];
  rating?: number;
  remixCount: number;
  topStyle?: string;
}

interface CinematicHeroProps {
  featured: FeaturedIP;
}

export function CinematicHero({ featured }: CinematicHeroProps) {
  const { language } = useLanguage();
  const ko = language === "ko";

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <section className="relative w-full h-[85vh] overflow-hidden">
      {/* Background Image with Blur */}
      <div className="absolute inset-0 z-0">
        <img
          src={featured.bannerUrl}
          alt=""
          className="w-full h-full object-cover blur-sm scale-105"
        />
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-gray-900/40 via-gray-900/80 to-gray-900" />
      </div>

      {/* Content */}
      <div className="relative z-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex items-end pb-24">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 w-full">
          {/* Left: Title & CTA */}
          <motion.div
            className="lg:col-span-7 flex flex-col justify-end space-y-6"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          >
            {/* Tags */}
            <div className="flex items-center gap-3 flex-wrap">
              {featured.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1 bg-white/10 backdrop-blur-md border border-white/20 rounded-full text-xs font-semibold text-white tracking-wide uppercase"
                >
                  {tag}
                </span>
              ))}
              {featured.rating && (
                <div className="flex items-center text-yellow-400 text-sm font-bold">
                  <Star className="w-4 h-4 mr-1 fill-current" />
                  {featured.rating.toFixed(1)}
                </div>
              )}
            </div>

            {/* Title */}
            <h1 className="font-bold text-5xl md:text-7xl text-white leading-tight drop-shadow-lg">
              {ko ? featured.titleKo : featured.titleEn}
            </h1>

            {/* Description */}
            <p className="text-lg md:text-xl text-gray-200 max-w-2xl font-light leading-relaxed drop-shadow-md">
              {ko ? featured.descriptionKo : featured.descriptionEn}
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap items-center gap-4 pt-4">
              <Link
                href={`/ip/${featured.slug}`}
                className="group relative inline-flex items-center justify-center px-8 py-4 text-base font-bold text-white transition-all duration-200 bg-violet-500 rounded-full hover:bg-violet-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-500 focus:ring-offset-gray-900 shadow-lg shadow-violet-500/30"
              >
                <Sparkles className="w-5 h-5 mr-2 animate-pulse" />
                {ko ? "AI로 리믹스" : "Remix with AI"}
                <div className="absolute inset-0 rounded-full ring-2 ring-white/20 group-hover:ring-white/40 transition-all" />
              </Link>

              <button className="inline-flex items-center justify-center px-8 py-4 text-base font-medium text-white transition-all duration-200 bg-white/10 backdrop-blur-md border border-white/20 rounded-full hover:bg-white/20 focus:outline-none">
                <Play className="w-5 h-5 mr-2" />
                {ko ? "원본 보기" : "Watch Original"}
              </button>
            </div>
          </motion.div>

          {/* Right: Remix Stats Card */}
          <motion.div
            className="hidden lg:flex lg:col-span-5 flex-col justify-end items-end space-y-4"
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
          >
            <div className="bg-black/40 backdrop-blur-xl border border-white/10 p-6 rounded-2xl w-full max-w-sm">
              <h3 className="text-white font-bold text-lg mb-4 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-violet-400" />
                {ko ? "리믹스 통계" : "Remix Stats"}
              </h3>

              <div className="space-y-4">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-300">
                    {ko ? "총 리믹스" : "Total Remixes"}
                  </span>
                  <span className="text-white font-mono font-bold">
                    {formatNumber(featured.remixCount)}
                  </span>
                </div>

                <div className="w-full bg-gray-700/50 rounded-full h-1.5">
                  <div
                    className="bg-gradient-to-r from-violet-500 to-pink-500 h-1.5 rounded-full transition-all duration-500"
                    style={{ width: "75%" }}
                  />
                </div>

                {featured.topStyle && (
                  <div className="flex justify-between items-center text-sm pt-2">
                    <span className="text-gray-300">
                      {ko ? "인기 스타일" : "Top Style"}
                    </span>
                    <span className="text-violet-300 font-semibold">
                      {featured.topStyle}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Bottom Gradient Fade */}
      <div className="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-gray-50 dark:from-gray-900 to-transparent z-20" />
    </section>
  );
}

export default CinematicHero;
