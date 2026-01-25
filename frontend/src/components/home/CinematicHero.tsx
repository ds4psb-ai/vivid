"use client";

/**
 * Cinematic Hero Section
 *
 * Netflix-style full-width hero with featured IP
 * Exact match to Stitch AI design
 */

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useLanguage } from "@/contexts/LanguageContext";

export interface FeaturedIP {
  slug: string;
  titleLine1: string;
  titleLine2: string;
  description: string;
  descriptionKo: string;
  bannerUrl: string;
  tags: string[];
  rating: number;
  remixCount: string;
  topStyle: string;
}

interface CinematicHeroProps {
  featured: FeaturedIP;
}

export function CinematicHero({ featured }: CinematicHeroProps) {
  const { language } = useLanguage();
  const ko = language === "ko";

  return (
    <div className="relative w-full h-[85vh] overflow-hidden">
      {/* Background with cinematic gradient overlay */}
      <img
        alt="Cinematic Background"
        className="absolute inset-0 w-full h-full object-cover z-0 blur-sm scale-105"
        src={featured.bannerUrl}
      />
      {/* Cinematic gradient overlay */}
      <div
        className="absolute inset-0 z-10"
        style={{
          background: 'linear-gradient(to bottom, rgba(17, 24, 39, 0.4) 0%, rgba(17, 24, 39, 0.8) 60%, rgba(17, 24, 39, 1) 100%)'
        }}
      />

      {/* Content */}
      <div className="relative z-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex items-end pb-24">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 w-full">
          {/* Left column - Title & CTA */}
          <motion.div
            className="lg:col-span-7 flex flex-col justify-end space-y-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            {/* Tags */}
            <div className="flex items-center gap-3">
              {featured.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1 bg-white/10 backdrop-blur-md border border-white/20 rounded-full text-xs font-semibold text-white tracking-wide uppercase"
                >
                  {tag}
                </span>
              ))}
              <div className="flex items-center text-yellow-400 text-sm font-bold">
                <span className="material-icons-round text-base mr-1">star</span>
                {featured.rating}
              </div>
            </div>

            {/* Title with gradient */}
            <h1 className="font-display text-5xl md:text-7xl font-bold text-white leading-tight drop-shadow-lg">
              {featured.titleLine1}
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
                {featured.titleLine2}
              </span>
            </h1>

            {/* Description */}
            <p className="text-lg md:text-xl text-gray-200 max-w-2xl font-light leading-relaxed drop-shadow-md">
              {ko ? featured.descriptionKo : featured.description}
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap items-center gap-4 pt-4">
              <Link
                href={`/ip/${featured.slug}`}
                className="group relative inline-flex items-center justify-center px-8 py-4 text-base font-bold text-white transition-all duration-200 bg-violet-500 rounded-full hover:bg-violet-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-500 focus:ring-offset-gray-900 shadow-lg shadow-violet-500/30"
              >
                <span className="material-icons-round mr-2 animate-pulse">auto_awesome</span>
                {ko ? "AI로 리믹스" : "Remix with AI"}
                <div className="absolute inset-0 rounded-full ring-2 ring-white/20 group-hover:ring-white/40 transition-all" />
              </Link>

              <button className="inline-flex items-center justify-center px-8 py-4 text-base font-medium text-white transition-all duration-200 bg-white/10 backdrop-blur-md border border-white/20 rounded-full hover:bg-white/20 focus:outline-none">
                <span className="material-icons-round mr-2">play_arrow</span>
                {ko ? "원본 보기" : "Watch Original"}
              </button>
            </div>
          </motion.div>

          {/* Right column - Remix Stats */}
          <motion.div
            className="hidden lg:flex lg:col-span-5 flex-col justify-end items-end space-y-4"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <div className="bg-black/40 backdrop-blur-xl border border-white/10 p-6 rounded-2xl w-full max-w-sm">
              <h3 className="text-white font-display font-bold text-lg mb-4 flex items-center gap-2">
                <span className="material-icons-round text-violet-400">analytics</span>
                {ko ? "리믹스 통계" : "Remix Stats"}
              </h3>

              <div className="space-y-4">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-300">{ko ? "총 리믹스" : "Total Remixes"}</span>
                  <span className="text-white font-mono font-bold">{featured.remixCount}</span>
                </div>

                <div className="w-full bg-gray-700/50 rounded-full h-1.5">
                  <div
                    className="bg-gradient-to-r from-violet-500 to-pink-500 h-1.5 rounded-full"
                    style={{ width: "75%" }}
                  />
                </div>

                <div className="flex justify-between items-center text-sm pt-2">
                  <span className="text-gray-300">{ko ? "인기 스타일" : "Top Style"}</span>
                  <span className="text-violet-300 font-semibold">{featured.topStyle}</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Bottom gradient fade to page background */}
      <div className="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-gray-50 dark:from-gray-900 to-transparent z-20" />
    </div>
  );
}

export default CinematicHero;
