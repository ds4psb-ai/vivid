"use client";

/**
 * Cinematic Hero Section - Stitch V2 Design
 *
 * Split layout with character model card
 * Ultra-dark theme with neon accents
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
    <section className="relative min-h-screen flex flex-col lg:flex-row overflow-hidden bg-[#030014]">
      {/* Background Grid Pattern */}
      <div className="fixed inset-0 bg-grid z-0 pointer-events-none" />

      {/* Left Column - Content */}
      <div className="w-full lg:w-1/2 relative flex flex-col justify-center px-6 sm:px-12 lg:px-20 py-24 lg:py-0 z-20">
        {/* Gradient overlay for mobile */}
        <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-[#030014]/0 via-[#030014]/20 to-[#030014] lg:bg-gradient-to-r lg:from-[#030014] lg:via-[#030014] lg:to-transparent z-[-1]" />

        <motion.div
          className="space-y-8 max-w-xl"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          {/* Tags */}
          <div className="flex flex-wrap items-center gap-4 text-xs font-mono tracking-widest uppercase text-gray-400">
            <span className="flex items-center gap-1 text-fuchsia-400">
              <Sparkles className="w-3.5 h-3.5" />
              AI Enabled
            </span>
            {featured.tags.map((tag, i) => (
              <React.Fragment key={tag}>
                <span className="w-1 h-1 bg-gray-600 rounded-full" />
                <span>{tag}</span>
              </React.Fragment>
            ))}
          </div>

          {/* Title */}
          <h1 className="font-display font-bold text-6xl md:text-7xl lg:text-8xl leading-[0.9] tracking-tighter text-white">
            {featured.title}
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-fuchsia-500 to-violet-600 text-glow">
              {featured.titleAccent}
            </span>
          </h1>

          {/* Description */}
          <p className="text-gray-400 text-lg font-light leading-relaxed max-w-md border-l-2 border-violet-500/30 pl-6">
            {featured.description}
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-6 pt-6">
            <Link
              href={`/ip/${featured.slug}`}
              className="group relative px-8 py-4 bg-white text-[#030014] font-display font-bold text-lg tracking-wide hover:bg-gray-200 transition-colors flex items-center gap-3 overflow-hidden"
            >
              <span className="relative z-10">REMIX WITH AI</span>
              <ArrowRight className="w-5 h-5 relative z-10 group-hover:translate-x-1 transition-transform" />
              <div className="absolute inset-0 bg-gradient-to-r from-fuchsia-500 to-violet-600 opacity-0 group-hover:opacity-10 transition-opacity" />
            </Link>

            <button className="px-8 py-4 border border-white/20 text-white font-display font-medium text-lg tracking-wide hover:bg-white/5 transition-colors flex items-center gap-2 backdrop-blur-sm">
              <Play className="w-5 h-5" />
              <span>TRAILER</span>
            </button>
          </div>

          {/* Stats */}
          <div className="pt-12 grid grid-cols-3 gap-8 border-t border-white/10">
            <div>
              <div className="text-2xl font-display font-bold text-white">
                {featured.rating}
              </div>
              <div className="text-xs text-gray-500 uppercase tracking-widest">
                Rating
              </div>
            </div>
            <div>
              <div className="text-2xl font-display font-bold text-white">
                {featured.remixCount}
              </div>
              <div className="text-xs text-gray-500 uppercase tracking-widest">
                Remixes
              </div>
            </div>
            <div>
              <div className="text-2xl font-display font-bold text-fuchsia-400">
                {featured.matchPercent}%
              </div>
              <div className="text-xs text-gray-500 uppercase tracking-widest">
                Match
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Right Column - Image */}
      <div className="absolute inset-0 lg:relative lg:w-1/2 h-full min-h-[50vh]">
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#030014] via-transparent to-transparent lg:bg-gradient-to-l lg:from-transparent lg:via-transparent lg:to-[#030014] z-10" />

        <img
          alt="Featured IP Banner"
          className="w-full h-full object-cover object-center lg:object-left filter contrast-125 brightness-90 saturate-150"
          src={featured.bannerUrl}
        />

        {/* Character Model Card */}
        {featured.character && (
          <motion.div
            className="hidden lg:block absolute bottom-12 right-12 z-20"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <div className="character-card p-6 max-w-xs rounded-lg">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-2 h-2 bg-green-500 rounded-full status-pulse" />
                <span className="text-xs font-mono uppercase text-gray-300">
                  {featured.character.status}
                </span>
              </div>
              <h3 className="text-xl font-display font-bold text-white mb-1">
                {featured.character.name}
              </h3>
              <p className="text-sm text-gray-400">
                {featured.character.description}
              </p>
            </div>
          </motion.div>
        )}
      </div>
    </section>
  );
}

export default CinematicHero;
