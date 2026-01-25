"use client";

/**
 * Crebit Home Page - Netflix-style AI OTT Platform
 *
 * A cinematic landing page featuring:
 * 1. Full-screen hero with featured IP
 * 2. Variations grid showing possible remixes
 * 3. Clean navigation and footer
 *
 * Design: Stitch AI (January 2026)
 */

import React, { Suspense, useMemo } from "react";
import { CrebitNavbar } from "@/components/home/CrebitNavbar";
import { CinematicHero, FeaturedIP } from "@/components/home/CinematicHero";
import { VariationsGrid, VariationCard } from "@/components/home/VariationsGrid";
import { CrebitFooter } from "@/components/home/CrebitFooter";
import { DEMO_IP_OVERRIDES } from "@/lib/demo-ip-overrides";

/**
 * Transform demo IP data to Featured IP format
 */
function getFeaturedIP(): FeaturedIP {
  // Use the most popular IP as featured
  const demoIP = DEMO_IP_OVERRIDES["cooking-anime-mv"];

  return {
    slug: demoIP.slug,
    titleKo: demoIP.titleKo,
    titleEn: demoIP.titleEn,
    descriptionKo: demoIP.descKo,
    descriptionEn: demoIP.descEn,
    bannerUrl:
      demoIP.thumbnailUrl ||
      "https://images.unsplash.com/photo-1534809027769-b00d750a6bac?w=1920&q=80",
    tags: ["Anime", "Music Video", "4K HDR"],
    rating: 4.9,
    remixCount: 12405,
    topStyle: "Cyberpunk Anime",
  };
}

/**
 * Transform demo workflows to Variation Cards
 * Maps our dimension apps to the new card format
 */
function getVariationCards(): VariationCard[] {
  return [
    {
      id: "anime-adaptation",
      slug: "anime-adaptation",
      nameKo: "애니메이션 각색",
      nameEn: "Anime Adaptation",
      descriptionKo:
        "도시의 거친 거리를 고속 애니메이션 시리즈로 재탄생. 과장된 액션과 생동감 넘치는 색감에 집중합니다.",
      descriptionEn:
        "Reimagine the gritty streets as a high-octane anime series. Focus on exaggerated action sequences and vibrant color palettes.",
      thumbnailUrl:
        "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=600&q=80",
      category: "visual",
      version: "V2.0",
      href: "/dimension/visual-realizer",
    },
    {
      id: "shortform-drama",
      slug: "shortform-drama",
      nameKo: "숏폼 드라마",
      nameEn: "Short-form Drama",
      descriptionKo:
        "스토리라인을 60초의 세로 에피소드로 압축. 소셜 플랫폼에 최적화된 콘텐츠를 생성합니다.",
      descriptionEn:
        "Condense the storyline into punchy 60-second vertical episodes optimized for social platforms.",
      thumbnailUrl:
        "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=600&q=80",
      category: "video",
      isBeta: true,
      href: "/dimension/video-maker",
    },
    {
      id: "graphic-novel",
      slug: "graphic-novel",
      nameKo: "그래픽 노블",
      nameEn: "Graphic Novel",
      descriptionKo:
        "풀 컬러 그래픽 노블 레이아웃 생성. 핵심 대화를 추출하고 일관된 캐릭터 아트 패널을 만듭니다.",
      descriptionEn:
        "Generate a full-color graphic novel layout. Extracts key dialogue and creates consistent character art panels.",
      thumbnailUrl:
        "https://images.unsplash.com/photo-1618336753974-aae8e04506aa?w=600&q=80",
      category: "story",
      version: "V1.5",
      href: "/dimension/storyboard-sketcher",
    },
    {
      id: "immersive-audio",
      slug: "immersive-audio",
      nameKo: "이머시브 오디오",
      nameEn: "Immersive Audio",
      descriptionKo:
        "스크립트를 3D 바이노럴 오디오 드라마로 변환. AI 성우와 생성된 사운드스케이프를 활용합니다.",
      descriptionEn:
        "Convert the script into a 3D binaural audio drama with AI voice actors and generated soundscapes.",
      thumbnailUrl:
        "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&q=80",
      category: "audio",
      version: "V3.1",
      href: "/dimension/sound-crafter",
    },
    {
      id: "interactive-novel",
      slug: "interactive-novel",
      nameKo: "인터랙티브 비주얼 노블",
      nameEn: "Interactive Visual Novel",
      descriptionKo:
        "사용자가 캐릭터의 다양한 경로를 선택할 수 있는 분기형 내러티브 게임을 만듭니다.",
      descriptionEn:
        "Create a branching narrative game where users can choose different paths for the character.",
      thumbnailUrl:
        "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=600&q=80",
      category: "interactive",
      isNew: true,
      href: "/dimension/scenario-generator",
    },
  ];
}

function HomePageContent() {
  const featuredIP = useMemo(() => getFeaturedIP(), []);
  const variations = useMemo(() => getVariationCards(), []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
      {/* Navigation */}
      <CrebitNavbar />

      {/* Main Content */}
      <main className="relative pt-16">
        {/* Cinematic Hero */}
        <CinematicHero featured={featuredIP} />

        {/* Variations Grid */}
        <VariationsGrid variations={variations} ipSlug={featuredIP.slug} />
      </main>

      {/* Footer */}
      <CrebitFooter />
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
          <div className="flex flex-col items-center gap-4">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-purple-400 flex items-center justify-center text-white font-bold animate-pulse">
              C
            </div>
            <div className="h-1 w-24 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div className="h-full w-1/2 bg-violet-500 rounded-full animate-pulse" />
            </div>
          </div>
        </div>
      }
    >
      <HomePageContent />
    </Suspense>
  );
}
