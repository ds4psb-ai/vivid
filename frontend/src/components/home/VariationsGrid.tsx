"use client";

/**
 * Variations Grid Section - Stitch V2 Design
 *
 * Bento Box layout with varying card sizes
 * Neon border effects and glass panels
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
  layout?: "tall" | "wide" | "normal";
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
  visual: "bg-pink-500",
  video: "bg-blue-500",
  story: "bg-yellow-500",
  audio: "bg-green-500",
  interactive: "bg-purple-500",
};

export function VariationsGrid({ variations }: VariationsGridProps) {
  return (
    <section className="relative py-24 px-6 sm:px-12 lg:px-20 bg-[#030014]">
      {/* Top divider */}
      <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-violet-500/50 to-transparent" />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-6 max-w-7xl mx-auto">
        <div>
          <h2 className="text-4xl md:text-5xl font-display font-bold text-white mb-4">
            Possible{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-500 to-fuchsia-500">
              Variations
            </span>
          </h2>
          <p className="text-gray-400 max-w-md text-lg">
            Deconstruct and reconstruct this IP into entirely new formats using
            our neural engine.
          </p>
        </div>
        <div className="flex gap-4">
          <button className="px-6 py-2 border border-white/10 rounded-full text-sm font-medium hover:border-violet-500 transition-colors text-gray-300 hover:text-white">
            Most Popular
          </button>
          <button className="px-6 py-2 border border-white/10 rounded-full text-sm font-medium hover:border-violet-500 transition-colors text-gray-300 hover:text-white">
            Newest
          </button>
        </div>
      </div>

      {/* Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 auto-rows-[300px] max-w-7xl mx-auto">
        {variations.map((card, index) => {
          const Icon = CATEGORY_ICONS[card.category];
          const iconColor = ICON_COLORS[card.category];
          const progressColor = PROGRESS_COLORS[card.category];

          // Determine grid span based on layout
          const gridClass =
            card.layout === "tall"
              ? "lg:col-span-1 lg:row-span-2"
              : card.layout === "wide"
                ? "md:col-span-2 lg:col-span-2"
                : "md:col-span-1 lg:col-span-1";

          return (
            <motion.div
              key={card.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`group relative rounded-2xl overflow-hidden neon-border ${gridClass}`}
            >
              {/* Background */}
              <div className="absolute inset-0 bg-[#0F0720] z-0" />

              {/* Image */}
              <img
                alt={card.name}
                className={`absolute inset-0 w-full h-full object-cover opacity-60 group-hover:opacity-80 group-hover:scale-110 transition-all duration-700 ${
                  card.category === "audio"
                    ? "grayscale group-hover:grayscale-0"
                    : ""
                }`}
                src={card.thumbnailUrl}
              />

              {/* Gradient overlay */}
              <div
                className={`absolute inset-0 z-10 ${
                  card.layout === "wide"
                    ? "bg-gradient-to-r from-black via-black/50 to-transparent"
                    : "bg-gradient-to-t from-black via-black/40 to-transparent"
                }`}
              />

              {/* Content */}
              <div
                className={`absolute bottom-0 left-0 w-full p-6 z-20 ${
                  card.layout === "wide"
                    ? "flex flex-col justify-end items-start h-full p-8"
                    : ""
                }`}
              >
                <div
                  className={`transform group-hover:translate-y-[-8px] transition-transform duration-300 ${
                    card.layout === "wide" ? "group-hover:translate-x-2" : ""
                  }`}
                >
                  {/* Badge */}
                  {card.badge && (
                    <span
                      className={`inline-block px-2 py-1 mb-3 text-[10px] font-bold tracking-widest uppercase text-white ${
                        card.badgeColor || "bg-violet-600"
                      }`}
                    >
                      {card.badge}
                    </span>
                  )}

                  {/* Title */}
                  {card.layout === "tall" ? (
                    <h3 className="text-2xl font-display font-bold text-white mb-2 leading-tight">
                      {card.name.split(" ").map((word, i) => (
                        <React.Fragment key={i}>
                          {word}
                          {i === 0 && <br />}
                        </React.Fragment>
                      ))}
                    </h3>
                  ) : card.layout === "wide" ? (
                    <>
                      <h3 className="text-3xl font-display font-bold text-white mb-2">
                        {card.name}
                      </h3>
                      <p className="text-gray-300 max-w-md mb-4 text-sm">
                        {card.description}
                      </p>
                      <button className="w-12 h-12 rounded-full bg-white/10 backdrop-blur-md flex items-center justify-center text-white hover:bg-white hover:text-black transition-all">
                        <Play className="w-5 h-5" />
                      </button>
                    </>
                  ) : (
                    <>
                      <Icon
                        className={`w-10 h-10 mb-2 opacity-80 ${iconColor}`}
                      />
                      <h3 className="text-xl font-display font-bold text-white mb-1">
                        {card.name}
                      </h3>
                      {/* Progress bar on hover */}
                      <div
                        className={`h-1 w-0 ${progressColor} group-hover:w-full transition-all duration-500`}
                      />
                    </>
                  )}

                  {/* Description for tall cards */}
                  {card.layout === "tall" && (
                    <>
                      <p className="text-sm text-gray-400 mb-4 line-clamp-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300 delay-100">
                        {card.description}
                      </p>
                      <Link
                        href={card.href}
                        className="flex items-center gap-2 text-fuchsia-400 font-bold text-sm tracking-wide group-hover:text-white transition-colors"
                      >
                        START WORKFLOW{" "}
                        <ArrowUpRight className="w-4 h-4" />
                      </Link>
                    </>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}

        {/* Custom Workflow Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: variations.length * 0.1 }}
          className="group relative md:col-span-1 lg:col-span-1 bg-gradient-to-br from-gray-900 to-black rounded-2xl border border-white/10 hover:border-violet-500/50 transition-colors flex flex-col items-center justify-center text-center p-6 cursor-pointer overflow-hidden"
        >
          {/* Carbon fiber pattern */}
          <div
            className="absolute inset-0 opacity-20"
            style={{
              backgroundImage:
                "url('https://www.transparenttextures.com/patterns/carbon-fibre.png')",
            }}
          />

          <Link href="/dimension" className="relative z-10 flex flex-col items-center">
            <div className="w-16 h-16 rounded-full border border-dashed border-gray-600 group-hover:border-violet-500 flex items-center justify-center mb-4 transition-colors">
              <Plus className="w-8 h-8 text-gray-400 group-hover:text-violet-500 transition-colors" />
            </div>
            <h3 className="text-xl font-display font-bold text-white mb-1 group-hover:text-violet-500 transition-colors">
              Custom Workflow
            </h3>
            <p className="text-xs text-gray-500 mt-2">Design from scratch</p>
          </Link>
        </motion.div>
      </div>
    </section>
  );
}

export default VariationsGrid;
