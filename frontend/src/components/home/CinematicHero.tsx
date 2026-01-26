"use client";

/**
 * Cinematic Hero Section - Stitch V2 Dark Design
 *
 * Full-screen hero with character card
 * Based on Stitch design with dark mode adaptation
 */

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Play, ArrowRight } from "lucide-react";

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
    imageUrl?: string;
  };
}

interface CinematicHeroProps {
  featured: FeaturedIP;
}

export function CinematicHero({ featured }: CinematicHeroProps) {
  return (
    <header className="relative min-h-screen flex items-center justify-center pt-16 overflow-hidden bg-[var(--bg-base)]">
      {/* Background Image */}
      <div className="absolute inset-0 z-0">
        <img
          alt="Futuristic Cyber City"
          className="w-full h-full object-cover opacity-60"
          src={featured.bannerUrl}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[var(--bg-base)] via-transparent to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-r from-[var(--bg-base)]/90 to-transparent" />
      </div>

      {/* Content Grid */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 md:px-16 w-full grid lg:grid-cols-2 gap-12 items-center">
        {/* Left: Text Content */}
        <div className="space-y-8">
          {/* AI Revolution Tag */}
          <div>
            <h5 className="text-[var(--fg-primary)] font-bold tracking-[0.2em] text-sm uppercase flex items-center gap-2">
              <span className="w-8 h-[2px] bg-[var(--bg-primary)] block" />
              AI 혁명 v3.0
            </h5>
          </div>

          {/* Title - Split Design */}
          <h1 className="text-6xl md:text-8xl font-black tracking-tighter leading-none">
            <span className="block text-transparent bg-clip-text bg-gradient-to-b from-white to-gray-400">
              {featured.title}
            </span>
            <span className="block text-[var(--fg-primary)] drop-shadow-[0_0_20px_rgba(255,30,86,0.5)]">
              {featured.titleAccent}
            </span>
          </h1>

          {/* Description with border */}
          <p className="text-lg md:text-xl text-[var(--fg-muted)] max-w-lg leading-relaxed border-l-2 border-[var(--border-primary)] pl-6 break-keep">
            {featured.description}
          </p>

          {/* CTA Buttons - Pill Style */}
          <div className="flex flex-wrap gap-4">
            <Link
              href={`/ip/${featured.slug}`}
              className="bg-[var(--bg-primary)] text-white px-8 py-3 rounded-full font-bold flex items-center gap-2 hover:bg-red-600 transition-all shadow-[0_0_20px_rgba(255,30,86,0.4)] hover:shadow-[0_0_30px_rgba(255,30,86,0.6)]"
            >
              <span>AI로 리믹스하기</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <button className="px-8 py-3 rounded-full font-bold border border-white/30 text-white flex items-center gap-2 hover:bg-white/10 transition-all backdrop-blur-sm">
              <Play className="w-4 h-4" />
              <span>예고편</span>
            </button>
          </div>

          {/* Stats */}
          <div className="flex gap-8 pt-8 border-t border-white/10">
            <div>
              <div className="text-2xl font-bold">{featured.rating}</div>
              <div className="text-xs text-gray-500 uppercase tracking-wider">평점</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{featured.remixCount}</div>
              <div className="text-xs text-gray-500 uppercase tracking-wider">리믹스</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-[var(--fg-primary)]">{featured.matchPercent}%</div>
              <div className="text-xs text-gray-500 uppercase tracking-wider">매치율</div>
            </div>
          </div>
        </div>

        {/* Right: Character Card - Stitch Style */}
        <div className="hidden lg:block relative">
          {featured.character && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              whileHover={{ y: -8, scale: 1.02 }}
              className="group relative w-80 ml-auto bg-black/40 backdrop-blur-xl border border-white/10 hover:border-[var(--border-primary)]/50 rounded-2xl p-4 shadow-2xl cursor-pointer transition-colors duration-300"
            >
              {/* Status Badge - Top Right */}
              <div className="absolute -top-4 -right-4 bg-[var(--bg-primary)] text-white text-xs font-bold px-3 py-1 rounded-full shadow-lg group-hover:shadow-[0_0_20px_rgba(255,30,86,0.5)] transition-shadow">
                {featured.character.status}
              </div>

              {/* Character Image */}
              <div className="aspect-[3/4] rounded-xl overflow-hidden mb-4 relative">
                <img
                  alt="Character Portrait"
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                  src={featured.character.imageUrl || "https://lh3.googleusercontent.com/aida-public/AB6AXuB7A2Y_KtEP8fVbTQXGCKp766B5wgZGTvVrGAluur7jkYJpAapyOR2PrT_Bv_tnsHl7y6xEL3uXzp72KZCyk4NQTNpM-LnQlreCoxoTzxnI_N3DnnZla1Hr5rwDpZ8vpNqmHKs7AzgpV24D7Eln4zzc6cdrAhCYyeubXz22yKkIZBIL7nX-xbjqpkXJKkmFcor65s9ZdyfAg7Az7y2IZdRkSVKdwSRTRBk1QPkS0AnMsdFT-1MO1AKYGk797pV5PJalILDsTS_fVHU"}
                />
                {/* Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
                {/* Character Info */}
                <div className="absolute bottom-4 left-4 right-4">
                  <h3 className="text-white text-xl font-bold">{featured.character.name}</h3>
                  <p className="text-gray-300 text-xs mt-1 line-clamp-2">
                    {featured.character.description}
                  </p>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="h-1 w-full bg-gray-700 rounded-full overflow-hidden">
                <div className="h-full bg-[var(--bg-primary)] w-3/4" />
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-2">
                <span>동기화 중...</span>
                <span>75%</span>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </header>
  );
}

export default CinematicHero;
