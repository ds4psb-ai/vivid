"use client";

/**
 * Featured Characters Section - Stitch V2 Neon Red Design
 *
 * 4-column grid of AI character cards
 * Deep charcoal theme with neon red accents
 */

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { MessageCircle, PlusCircle, ArrowRight } from "lucide-react";

export interface Character {
  id: string;
  name: string;
  imageUrl: string;
  chatCount: string;
  quote: string;
  creator: string;
  badge?: "NEW" | "TOP_RATED";
}

interface FeaturedCharactersProps {
  characters?: Character[];
  onCharacterClick?: (id: string) => void;
}

// Default character data matching stitch_ui_1 design
const DEFAULT_CHARACTERS: Character[] = [
  {
    id: "akari",
    name: "Akari",
    imageUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuDN5xpf62iQyVAxpu6bfMxxxUbBcRwdTWKyxVSWszsqTN31eV3lNWr3ntBTIXhAjJCKXZkUTQqa3EGMRF80TU-gL20v7zBokSFOkWBAsTDF1sbc1ZVFQ9mdz8k7yBCcSho6XXcihaNCoPVzRCdkL4NiFhZDwRx0Kz5naME5XI-yk3VW7t2C2_RlgLPW9xvZ4XUOi8L6hP4pzyuhDSqjwjDdfaFxbpEZl3dpeP0ZGPes6jLYMw8Wtgl9pUvGmoggChFffG4ovuIp3PQ",
    chatCount: "12k",
    quote: "오늘 밤, 네온 사인 아래서 드라이브 어때요?",
    creator: "@neon_dreamer",
    badge: "NEW",
  },
  {
    id: "eunha",
    name: "Eunha",
    imageUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuAEFUIE-TQP1GnONSNxQtpr031HoEzolGFK2FWaSHqPYsH6fpO5MPtnwQjO1hwcDP5jIRxRI32PLsYs0_r7616VUNOCjAblP58zu6tKWxDImRG1UFotWIZLlfdp7PizcXWOM8DzpgmawyougUuKINa34yP-SWURdtC3teIcKW4b5qZn_vK1s78Vog3DWjDnhk94JdYZlgpdJ-tY_S7h3PlNB3BQ4oKHgpzy_9bmErbhIjGQDjaHRs7DbzYv-w6FmWMvdK_VmyAZGEc",
    chatCount: "8.5k",
    quote: "기억은 데이터일 뿐이야, 하지만 감정은...",
    creator: "@cyber_seoul",
  },
  {
    id: "soonae",
    name: "순애",
    imageUrl: "/assets/characters/candidates/pure_love.avif",
    chatCount: "18k",
    quote: "시간을 초월하는 순수한 사랑, 그게 나야.",
    creator: "@romance_ai",
    badge: "NEW",
  },
  {
    id: "koko",
    name: "Koko",
    imageUrl: "/assets/characters/candidates/koko.jpg",
    chatCount: "21k",
    quote: "HTML로 세상을 코딩하는 안드로이드, 반가워요!",
    creator: "@android_dev",
    badge: "TOP_RATED",
  },
];

export function FeaturedCharacters({
  characters = DEFAULT_CHARACTERS,
  onCharacterClick,
}: FeaturedCharactersProps) {
  return (
    <section className="relative z-20 px-6 md:px-16 pt-24 bg-[var(--bg-base)]">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-end mb-10">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white">
            추천 <span className="text-[var(--fg-primary)]">캐릭터</span>
          </h2>
          <Link
            href="/characters"
            className="text-xs font-bold text-gray-500 hover:text-[var(--fg-primary)] transition-colors uppercase tracking-widest mt-4 md:mt-0 flex items-center"
          >
            모두 보기 <ArrowRight className="w-4 h-4 ml-1" />
          </Link>
        </div>

        {/* Character Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {characters.map((character, index) => (
            <Link key={character.id} href={`/chat/${character.id}`}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="group relative bg-[var(--bg-subtle)] border border-gray-800 rounded-xl overflow-hidden hover:border-[var(--border-primary)]/50 transition-all duration-300 cursor-pointer"
                onClick={() => onCharacterClick?.(character.id)}
              >
                {/* Image */}
                <div className="aspect-[3/4] overflow-hidden relative">
                  <img
                    alt={character.name}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                    src={character.imageUrl}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-90" />

                  {/* Badge */}
                  {character.badge && (
                    <div
                      className={`absolute top-3 right-3 backdrop-blur-sm px-2 py-1 rounded text-[10px] font-bold border ${character.badge === "NEW"
                        ? "bg-black/60 text-[var(--fg-primary)] border-[var(--border-primary)]/30"
                        : "bg-[var(--bg-primary)]/20 text-[var(--fg-primary)] border-[var(--border-primary)]/50"
                        }`}
                    >
                      {character.badge === "NEW" ? "NEW" : "TOP RATED"}
                    </div>
                  )}
                </div>

                {/* Content */}
                <div className="p-5 relative">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-xl font-bold text-white">{character.name}</h3>
                    <div className="flex items-center text-xs text-gray-400">
                      <MessageCircle className="w-3.5 h-3.5 mr-1 text-[var(--fg-primary)]" />
                      {character.chatCount}
                    </div>
                  </div>

                  <p className="text-xs text-gray-400 mb-4 line-clamp-2 italic">
                    &quot;{character.quote}&quot;
                  </p>

                  <div className="flex items-center justify-between border-t border-white/10 pt-3 mt-auto">
                    <span className="text-[10px] text-gray-500 font-mono">
                      {character.creator}
                    </span>
                    <span className="text-[var(--fg-primary)] group-hover:text-white transition-colors">
                      <PlusCircle className="w-5 h-5" />
                    </span>
                  </div>
                </div>
              </motion.div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}

export default FeaturedCharacters;
