"use client";

/**
 * Cinematic Hero Section - Stitch V2 Neon Red Design
 *
 * Split layout with character model card
 * Deep charcoal theme with neon red accents
 */

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Sparkles, Play, ArrowRight } from "lucide-react";

export interface FeaturedIP {
  slug: string;
  title: string;
  titleAccent: string;
  description: string;
  bannerUrl: string;
  tags: string[];
  rating: number;
  remixCount: string;
  matchPercent: number;
  character?: {
    name: string;
    description: string;
    status: string;
  };
}

interface CinematicHeroProps {
  featured: FeaturedIP;
}

export function CinematicHero({ featured }: CinematicHeroProps) {
  return (
    <section className="relative min-h-[90vh] flex items-center pt-20 px-6 md:px-16 overflow-hidden bg-[var(--bg-base)]">
      {/* Background Image */}
      <div className="absolute inset-0 z-0">
        <img
          alt="Featured IP Banner"
          className="absolute right-0 top-0 w-full md:w-2/3 h-full object-cover opacity-60"
          src={featured.bannerUrl}
          style={{
            WebkitMaskImage: "linear-gradient(to right, transparent 0%, black 30%)",
            maskImage: "linear-gradient(to right, transparent 0%, black 30%)",
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-r from-[var(--bg-base)] via-[var(--bg-base)]/90 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-t from-[var(--bg-base)] via-transparent to-transparent" />
      </div>

      {/* Content */}
      <div className="relative z-10 w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        <div className="lg:col-span-6 flex flex-col justify-center space-y-8">
          {/* Tags */}
          <div className="flex items-center space-x-3 text-xs font-bold tracking-[0.1em] text-[var(--fg-primary)]">
            <Sparkles className="w-4 h-4 animate-pulse" />
            <span>AI 활성화</span>
            <span className="text-gray-600">•</span>
            {featured.tags.map((tag, i) => (
              <React.Fragment key={tag}>
                <span className="text-gray-400">{tag}</span>
                {i < featured.tags.length - 1 && <span className="text-gray-600">•</span>}
              </React.Fragment>
            ))}
          </div>

          {/* Title */}
          <div className="relative">
            <h1 className="text-6xl md:text-8xl lg:text-9xl font-black leading-[0.9] tracking-tighter">
              <span className="block text-gray-800/30 absolute -top-12 md:-top-16 left-0 -z-10 select-none font-display">
                {featured.title}
              </span>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FF003C] via-red-500 to-gray-500 drop-shadow-[0_0_15px_rgba(255,0,60,0.5)] font-display">
                {featured.titleAccent}
              </span>
            </h1>
          </div>

          {/* Description */}
          <div className="border-l-2 border-[#FF003C] pl-6 py-1">
            <p className="text-lg md:text-xl text-gray-300 font-normal max-w-md leading-relaxed break-keep">
              {featured.description}
            </p>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 pt-4">
            <Link
              href={`/ip/${featured.slug}`}
              className="group relative px-8 py-4 bg-gray-900 dark:bg-white text-white dark:text-black font-bold tracking-wider uppercase hover:shadow-neon transition-all duration-300 flex items-center justify-center gap-2 overflow-hidden rounded-md"
            >
              <span className="relative z-10">AI로 리믹스하기</span>
              <ArrowRight className="w-4 h-4 relative z-10 group-hover:translate-x-1 transition-transform" />
              <div className="absolute inset-0 bg-[var(--bg-primary)] translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
            </Link>

            <button className="px-8 py-4 border border-gray-700 text-white font-bold tracking-wider uppercase hover:bg-white/10 transition-all duration-300 flex items-center justify-center gap-2 backdrop-blur-sm rounded-md">
              <Play className="w-4 h-4" />
              예고편
            </button>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-12 pt-8 border-t border-white/10">
            <div>
              <div className="text-3xl font-display font-bold text-gray-200">{featured.rating}</div>
              <div className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">평점</div>
            </div>
            <div>
              <div className="text-3xl font-display font-bold text-gray-200">{featured.remixCount}</div>
              <div className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">리믹스</div>
            </div>
            <div>
              <div className="text-3xl font-display font-bold text-[var(--fg-primary)] drop-shadow-[0_0_8px_rgba(255,0,60,0.8)]">
                {featured.matchPercent}%
              </div>
              <div className="text-[10px] uppercase tracking-widest text-[var(--fg-primary)] font-bold">취향 일치</div>
            </div>
          </div>
        </div>

        {/* Character Model Card */}
        <div className="hidden lg:flex lg:col-span-6 relative h-full justify-end items-center">
          {featured.character && (
            <motion.div
              className="absolute bottom-20 right-0 max-w-xs p-4 bg-black/40 backdrop-blur-md border border-white/20 rounded-lg shadow-2xl"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
            >
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-white">
                  {featured.character.status}
                </span>
              </div>
              <h3 className="text-xl font-display text-white mb-1">{featured.character.name}</h3>
              <p className="text-xs text-gray-300 leading-relaxed break-keep">
                {featured.character.description}
              </p>
              <div className="w-full bg-white/20 h-1 mt-3 rounded-full overflow-hidden">
                <div className="w-3/4 bg-[var(--bg-primary)] h-full" />
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </section>
  );
}

export default CinematicHero;
