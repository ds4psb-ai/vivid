"use client";

import { useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Dna } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { DNACard } from "@/components/dna-card";
import { useDNACardNavigation } from "@/hooks/useDNACardNavigation";
import type { DNACard as DNACardType } from "@/types/dna-card";
import {
  MASTER_AUTEURS,
  AUTEUR_SPECIFIC_DATA,
  AUTEUR_HUE_MAP,
} from "@/components/dna-card/constants";

// P0: 거장 카드 (고유 데이터 사용)
const MASTER_CARDS: DNACardType[] = MASTER_AUTEURS.slice(0, 6).map((auteur) => ({
  id: `master-${auteur.key}`,
  type: "master",
  name: auteur.name,
  nameEn: auteur.nameEn,
  description: `${auteur.name} 감독의 시네마틱 DNA를 분석하고 적용해보세요.`,
  thumbnailUrl: auteur.thumbnail,
  metadata: AUTEUR_SPECIFIC_DATA[auteur.key], // P0: 고유 데이터 사용
  megaAppEntry: {
    app: "dna-lab",
    tab: "ad",
    preloadParams: { master: auteur.key },
  },
  badgeText: auteur.key === "bong" ? "HOT" : undefined,
  badgeColor: "#e94560",
  hue: AUTEUR_HUE_MAP[auteur.key] ?? 45,
}));

// P0: 작품 카드 (2개)
const MASTERPIECE_CARDS: DNACardType[] = [
  {
    id: "masterpiece-parasite",
    type: "masterpiece",
    name: "기생충",
    nameEn: "Parasite",
    description: "2019 칸 황금종려상 수상작의 시각 문법 분석",
    thumbnailUrl: "/ip/parasite-thumb.jpg",
    metadata: {
      ipId: "ip-parasite",
      genres: ["드라마", "스릴러", "블랙코미디"],
      logicVectorSummary: {
        compositionStyle: "수직 블로킹 + 계층 구조",
        lightingPattern: "자연광 vs 인공광 대비",
        pacingSignature: "점진적 긴장 고조",
      },
    },
    megaAppEntry: { app: "dna-lab", tab: "vpe" },
    badgeText: "OSCAR",
    badgeColor: "#FFD700",
    hue: 148,
  },
  {
    id: "masterpiece-interstellar",
    type: "masterpiece",
    name: "인터스텔라",
    nameEn: "Interstellar",
    description: "놀란의 우주 서사시 시각 분석",
    thumbnailUrl: "/ip/interstellar-thumb.jpg",
    metadata: {
      ipId: "ip-interstellar",
      genres: ["SF", "드라마", "어드벤처"],
      logicVectorSummary: {
        compositionStyle: "IMAX 광활한 스케일",
        lightingPattern: "자연광 중심 + 실루엣",
        pacingSignature: "병렬 시간대 교차편집",
      },
    },
    megaAppEntry: { app: "dna-lab", tab: "vpe" },
    hue: 200,
  },
];

// P0: 캐릭터 카드 (2개)
const CHARACTER_CARDS: DNACardType[] = [
  {
    id: "character-seoyeon",
    type: "character",
    name: "서연",
    nameEn: "Seoyeon",
    description: "우산 속 인연의 주인공 캐릭터 DNA",
    thumbnailUrl: "/characters/seoyeon-primary.jpg",
    metadata: {
      characterId: "char-seoyeon-001",
      primaryImageUrl: "/characters/seoyeon-primary.jpg",
      tags: ["protagonist", "female", "romantic"],
      memoryKeyframeCount: 24,
      consistencyScore: 0.87,
    },
    megaAppEntry: { app: "story-engine", tab: "story" },
    badgeText: "NEW",
    badgeColor: "#8B5CF6",
    hue: 280,
  },
  {
    id: "character-minho",
    type: "character",
    name: "민호",
    nameEn: "Minho",
    description: "도시의 밤 주인공 캐릭터",
    thumbnailUrl: "/characters/minho-primary.jpg",
    metadata: {
      characterId: "char-minho-001",
      primaryImageUrl: "/characters/minho-primary.jpg",
      tags: ["protagonist", "male", "urban"],
      memoryKeyframeCount: 18,
      consistencyScore: 0.92,
    },
    megaAppEntry: { app: "story-engine", tab: "story" },
    hue: 260,
  },
];

// 통합 카드 데이터 (3종 혼합)
const MOCK_DNA_CARDS: DNACardType[] = [
  ...MASTER_CARDS.slice(0, 4),
  ...MASTERPIECE_CARDS.slice(0, 2),
  ...CHARACTER_CARDS,
  ...MASTER_CARDS.slice(4),
];

export function DNACardsSection() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  const { navigateToMegaApp } = useDNACardNavigation({ source: "home_dna_section" });

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
    setCanScrollLeft(scrollLeft > 0);
    setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 10);
  };

  const scroll = (direction: "left" | "right") => {
    if (!scrollRef.current) return;
    const scrollAmount = 300;
    scrollRef.current.scrollBy({
      left: direction === "left" ? -scrollAmount : scrollAmount,
      behavior: "smooth",
    });
  };

  return (
    <section className="py-16 bg-[var(--bg-base)]">
      <div className="max-w-7xl mx-auto px-4 md:px-6">
        {/* 헤더 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="flex items-center justify-between mb-8"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center">
              <Dna className="w-5 h-5 text-amber-500" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-[var(--fg-default)]">
                DNA Cards
              </h2>
              <p className="text-sm text-[var(--fg-muted)]">
                거장의 DNA를 선택하고 당신의 창작에 적용하세요
              </p>
            </div>
          </div>

          {/* 네비게이션 버튼 */}
          <div className="hidden md:flex gap-2">
            <button
              onClick={() => scroll("left")}
              disabled={!canScrollLeft}
              className="p-2 rounded-lg bg-[var(--surface-1)] border border-[var(--border-muted)] disabled:opacity-30 hover:bg-[var(--surface-2)] transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              onClick={() => scroll("right")}
              disabled={!canScrollRight}
              className="p-2 rounded-lg bg-[var(--surface-1)] border border-[var(--border-muted)] disabled:opacity-30 hover:bg-[var(--surface-2)] transition-colors"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </motion.div>

        {/* P1: 반응형 카드 레일 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <div
            ref={scrollRef}
            onScroll={handleScroll}
            className={cn(
              "flex gap-3 md:gap-4 overflow-x-auto",
              "scrollbar-hide pb-4",
              "snap-x snap-mandatory",
              "-mx-4 px-4 md:mx-0 md:px-0" // 모바일: 엣지 투 엣지
            )}
          >
            {MOCK_DNA_CARDS.map((card, index) => (
              <motion.div
                key={card.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.05 }}
                className="snap-start flex-shrink-0"
              >
                <DNACard
                  card={card}
                  onClick={navigateToMegaApp}
                  showPreviewOnHover
                />
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* 모바일 스크롤 힌트 */}
        <div className="flex md:hidden justify-center mt-4 gap-1">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className={cn(
                "w-2 h-2 rounded-full transition-colors",
                i === 0 ? "bg-white/60" : "bg-white/20"
              )}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
