"use client";

/**
 * AI Director Section - Stitch V2 Style (Dark Mode)
 *
 * Based on Stitch design:
 * - Horizontal scroll cards with grayscale hover effect
 * - Top badge with style tag
 * - Bottom info with name and specialty
 */

import { useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useDNACardNavigation } from "@/hooks/useDNACardNavigation";
import {
  MASTER_AUTEURS,
  AUTEUR_SPECIFIC_DATA,
  AUTEUR_HUE_MAP,
} from "@/components/dna-card/constants";

// AI Director card data
interface AIDirectorCard {
  id: string;
  key: string;
  name: string;
  nameEn: string;
  specialty: string;
  tag: string;
  portraitUrl: string;
  hue: number;
}

// Tag mapping for each auteur
const AUTEUR_TAGS: Record<string, string> = {
  kang: "SOCIAL",
  epoch: "EPIC",
  velvet: "NEON",
  voltage: "POP",
  yoon: "DARK",
  abyss: "COSMIC",
};

// Specialty mapping for each auteur (Korean)
const AUTEUR_SPECIALTY: Record<string, string> = {
  kang: "소셜 풍자",
  epoch: "에픽 스케일",
  velvet: "네온 미학",
  voltage: "팝 컬처",
  yoon: "다크 엘레강스",
  abyss: "코스믹 비전",
};

// Transform auteur data to AI Director cards
const AI_DIRECTOR_CARDS: AIDirectorCard[] = MASTER_AUTEURS.slice(0, 5).map((auteur) => {
  return {
    id: `director-${auteur.key}`,
    key: auteur.key,
    name: auteur.name,
    nameEn: auteur.nameEn,
    specialty: AUTEUR_SPECIALTY[auteur.key] || "Master Director",
    tag: AUTEUR_TAGS[auteur.key] || "MASTER",
    portraitUrl: auteur.thumbnail,
    hue: AUTEUR_HUE_MAP[auteur.key] ?? 45,
  };
});

export function AIDirectorSection() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  const { navigateToMegaApp } = useDNACardNavigation({ source: "home_ai_director" });

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
    setCanScrollLeft(scrollLeft > 0);
    setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 10);
  };

  const scroll = (direction: "left" | "right") => {
    if (!scrollRef.current) return;
    const scrollAmount = 260;
    scrollRef.current.scrollBy({
      left: direction === "left" ? -scrollAmount : scrollAmount,
      behavior: "smooth",
    });
  };

  const handleCardClick = (card: AIDirectorCard) => {
    navigateToMegaApp({
      id: card.id,
      type: "master",
      name: card.name,
      nameEn: card.nameEn,
      description: card.specialty,
      thumbnailUrl: card.portraitUrl,
      metadata: AUTEUR_SPECIFIC_DATA[card.key],
      megaAppEntry: {
        app: "dna-lab",
        tab: "ad",
        preloadParams: { master: card.key },
      },
      hue: card.hue,
    });
  };

  return (
    <section className="py-16 bg-[var(--bg-base)] overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 md:px-16">
        {/* Header - Stitch Style */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="flex items-center gap-3 mb-10"
        >
          <div className="w-8 h-8 rounded-full bg-red-500/10 flex items-center justify-center text-[var(--fg-primary)]">
            <Sparkles className="w-4 h-4" />
          </div>
          <h2 className="text-2xl font-bold text-white">
            AI <span className="text-[var(--fg-primary)]">디렉터</span>
          </h2>
          <span className="text-sm text-gray-500 ml-2 border-l border-gray-700 pl-3">
            거장 감독들의 시네마틱 DNA로 당신의 영상을 디렉팅하세요
          </span>
          <div className="flex-grow" />

          {/* Navigation buttons */}
          <div className="hidden md:flex gap-2">
            <button
              onClick={() => scroll("left")}
              disabled={!canScrollLeft}
              className="w-8 h-8 rounded-full border border-gray-700 flex items-center justify-center hover:bg-gray-800 text-gray-500 disabled:opacity-30 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => scroll("right")}
              disabled={!canScrollRight}
              className="w-8 h-8 rounded-full border border-gray-700 flex items-center justify-center hover:bg-gray-800 text-gray-500 disabled:opacity-30 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </motion.div>

        {/* Cards Rail - Stitch Style */}
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="flex gap-6 overflow-x-auto scrollbar-hide pb-8"
        >
          {AI_DIRECTOR_CARDS.map((card, index) => (
            <motion.div
              key={card.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: index * 0.05 }}
              onClick={() => handleCardClick(card)}
              className={cn(
                "group relative flex-shrink-0",
                "w-[240px] h-[360px] rounded-2xl overflow-hidden cursor-pointer",
                "grayscale hover:grayscale-0 transition-all duration-500"
              )}
            >
              {/* Portrait Image */}
              <img
                src={card.portraitUrl}
                alt={card.name}
                className="w-full h-full object-cover"
              />

              {/* Gradient Overlay */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-transparent to-transparent" />

              {/* Primary Color Overlay on Hover */}
              <div className="absolute inset-0 bg-[var(--bg-primary)]/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 mix-blend-overlay" />

              {/* Top Badge */}
              <div className="absolute top-4 left-4">
                <span className="text-[10px] font-bold bg-white/20 backdrop-blur text-white px-2 py-1 rounded">
                  {card.tag}
                </span>
              </div>

              {/* Bottom Info */}
              <div className="absolute bottom-6 left-6">
                <h3 className="text-lg font-bold text-white mb-0.5 drop-shadow-[0_2px_8px_rgba(0,0,0,1)]">
                  {card.name}
                </h3>
                <p className="text-xs text-white/80 drop-shadow-[0_2px_8px_rgba(0,0,0,1)]">{card.specialty}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default AIDirectorSection;
