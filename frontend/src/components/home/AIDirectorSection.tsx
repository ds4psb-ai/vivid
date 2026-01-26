"use client";

/**
 * AI Director Section - DNA Library Style Cards
 *
 * Based on stitch_shorti_ai_landing_page_dark_variant design:
 * - aspect-[3/4] portrait cards
 * - Hover: portrait → style image transition
 * - Bottom info area with tags and description
 * - Add button on hover
 */

import { useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Plus, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { DNACardPreview } from "@/components/dna-card/DNACardPreview";
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
  description: string;
  portraitUrl: string;
  styleUrl: string;
  tags: string[];
  hue: number;
}

// Specialty mapping for each auteur
const AUTEUR_SPECIALTY: Record<string, string> = {
  kang: "Social Satire",
  epoch: "Epic Scale",
  velvet: "Neon Aesthetics",
  voltage: "Pop Culture",
  yoon: "Dark Elegance",
  abyss: "Cosmic Vision",
  azure: "Poetic Light",
  prism: "Geometric Precision",
  seoyeon: "Raw Tension",
};

// Transform auteur data to AI Director cards
const AI_DIRECTOR_CARDS: AIDirectorCard[] = MASTER_AUTEURS.slice(0, 6).map((auteur) => {
  const metadata = AUTEUR_SPECIFIC_DATA[auteur.key];
  return {
    id: `director-${auteur.key}`,
    key: auteur.key,
    name: auteur.name,
    nameEn: auteur.nameEn,
    specialty: AUTEUR_SPECIALTY[auteur.key] || "Master Director",
    description: metadata?.signatureMoods?.slice(0, 2).join(", ") || "Cinematic DNA",
    portraitUrl: auteur.thumbnail,
    styleUrl: auteur.thumbnail, // Use same image with filter effect
    tags: metadata?.films?.slice(0, 2) || ["Film", "Director"],
    hue: AUTEUR_HUE_MAP[auteur.key] ?? 45,
  };
});

export function AIDirectorSection() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);
  const [previewCard, setPreviewCard] = useState<AIDirectorCard | null>(null);

  const { navigateToMegaApp } = useDNACardNavigation({ source: "home_ai_director" });

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
    setCanScrollLeft(scrollLeft > 0);
    setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 10);
  };

  const scroll = (direction: "left" | "right") => {
    if (!scrollRef.current) return;
    const scrollAmount = 320;
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
      description: card.description,
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
    <section className="py-20 bg-[var(--bg-base)]">
      <div className="max-w-7xl mx-auto px-4 md:px-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="flex items-center justify-between mb-10"
        >
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500/20 to-red-600/20 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-red-500" />
              </div>
              <h2 className="text-3xl md:text-4xl font-bold text-white">
                AI <span className="text-red-500">디렉터</span>
              </h2>
            </div>
            <p className="text-gray-400 max-w-lg">
              거장 감독들의 시네마틱 DNA로 당신의 영상을 디렉팅하세요
            </p>
          </div>

          {/* Navigation buttons */}
          <div className="hidden md:flex gap-2">
            <button
              onClick={() => scroll("left")}
              disabled={!canScrollLeft}
              className="p-2.5 rounded-xl bg-[var(--surface-1)] border border-white/10 disabled:opacity-30 hover:bg-[var(--surface-2)] hover:border-red-600/30 transition-all"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              onClick={() => scroll("right")}
              disabled={!canScrollRight}
              className="p-2.5 rounded-xl bg-[var(--surface-1)] border border-white/10 disabled:opacity-30 hover:bg-[var(--surface-2)] hover:border-red-600/30 transition-all"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </motion.div>

        {/* Cards Rail */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="relative"
        >
          <div
            ref={scrollRef}
            onScroll={handleScroll}
            className={cn(
              "flex gap-4 md:gap-5 overflow-x-auto",
              "scrollbar-hide pb-4",
              "snap-x snap-mandatory",
              "-mx-4 px-4 md:mx-0 md:px-0"
            )}
          >
            {AI_DIRECTOR_CARDS.map((card, index) => (
              <motion.div
                key={card.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.05 }}
                className="snap-start flex-shrink-0"
                onMouseEnter={() => {
                  setHoveredCard(card.id);
                  setPreviewCard(card);
                }}
                onMouseLeave={() => {
                  setHoveredCard(null);
                  setPreviewCard(null);
                }}
              >
                <div
                  onClick={() => handleCardClick(card)}
                  className={cn(
                    "group relative w-[220px] md:w-[260px] aspect-[3/4] rounded-2xl overflow-hidden cursor-pointer",
                    "bg-[var(--surface-1)] border border-white/10",
                    "hover:border-red-600/40 transition-all duration-300",
                    "hover:shadow-[0_0_30px_rgba(220,38,38,0.3)]"
                  )}
                  style={{
                    "--card-hue": card.hue,
                  } as React.CSSProperties}
                >
                  {/* Portrait Image (default) */}
                  <div className="absolute inset-0 z-20">
                    <img
                      src={card.portraitUrl}
                      alt={card.name}
                      className={cn(
                        "w-full h-full object-cover",
                        "grayscale group-hover:grayscale-0",
                        "transition-all duration-500",
                        "group-hover:opacity-0 group-hover:scale-105"
                      )}
                    />
                  </div>

                  {/* Style Image (hover) */}
                  <div className="absolute inset-0 z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                    <img
                      src={card.styleUrl}
                      alt={`${card.name} style`}
                      className="w-full h-full object-cover scale-105 group-hover:scale-110 transition-transform duration-700"
                      style={{
                        filter: `sepia(20%) hue-rotate(${card.hue}deg) saturate(1.2)`,
                      }}
                    />
                  </div>

                  {/* Gradient Overlay */}
                  <div className="absolute inset-0 z-30 bg-gradient-to-t from-black via-black/20 to-transparent opacity-90" />

                  {/* Bottom Info */}
                  <div className="absolute bottom-0 left-0 right-0 p-5 z-40">
                    {/* Tags */}
                    <div className="flex flex-wrap gap-1.5 mb-3">
                      {card.tags.map((tag) => (
                        <span
                          key={tag}
                          className={cn(
                            "px-2 py-0.5 rounded-full text-[10px] font-medium",
                            "bg-white/10 backdrop-blur-sm border border-white/10",
                            "text-gray-300"
                          )}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>

                    {/* Name */}
                    <h4 className="text-lg font-bold text-white mb-1">
                      {card.name}
                    </h4>
                    <p className="text-xs text-red-300 font-medium mb-2">
                      {card.specialty}
                    </p>
                    <p className="text-xs text-gray-400 line-clamp-2 mb-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      {card.description}
                    </p>

                    {/* Add Button (hover) */}
                    <div className="flex items-center justify-between opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-2 group-hover:translate-y-0">
                      <span className="text-xs text-gray-400">
                        {card.nameEn} DNA
                      </span>
                      <button
                        className={cn(
                          "w-8 h-8 rounded-full flex items-center justify-center",
                          "bg-red-600 hover:bg-red-500",
                          "transition-all duration-200",
                          "hover:scale-110"
                        )}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCardClick(card);
                        }}
                      >
                        <Plus className="w-4 h-4 text-white" />
                      </button>
                    </div>
                  </div>

                  {/* Specialty Badge (top) */}
                  <div className="absolute top-4 left-4 z-40">
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-black/50 backdrop-blur-sm border border-white/10 text-white">
                      {card.specialty.split(" ")[0]}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Preview Panel (for existing hover preview functionality) */}
          <AnimatePresence>
            {previewCard && hoveredCard === previewCard.id && (
              <DNACardPreview
                card={{
                  id: previewCard.id,
                  type: "master",
                  name: previewCard.name,
                  nameEn: previewCard.nameEn,
                  description: previewCard.description,
                  thumbnailUrl: previewCard.portraitUrl,
                  metadata: AUTEUR_SPECIFIC_DATA[previewCard.key],
                  megaAppEntry: {
                    app: "dna-lab",
                    tab: "ad",
                    preloadParams: { master: previewCard.key },
                  },
                  hue: previewCard.hue,
                }}
              />
            )}
          </AnimatePresence>
        </motion.div>

        {/* Mobile scroll hint */}
        <div className="flex md:hidden justify-center mt-4 gap-1.5">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className={cn(
                "w-2 h-2 rounded-full transition-colors",
                i === 0 ? "bg-red-500" : "bg-white/20"
              )}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

export default AIDirectorSection;
