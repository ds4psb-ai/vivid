"use client";

/**
 * Crebit Home Page - Netflix-style AI OTT Platform
 *
 * Exact implementation of Stitch AI design (January 2026)
 * Using actual image URLs and data from the original HTML
 */

import React, { Suspense } from "react";
import { CrebitNavbar } from "@/components/home/CrebitNavbar";
import { CinematicHero, FeaturedIP } from "@/components/home/CinematicHero";
import { VariationsGrid, VariationCard } from "@/components/home/VariationsGrid";
import { CrebitFooter } from "@/components/home/CrebitFooter";

// Featured IP data - exact match to Stitch design
const FEATURED_IP: FeaturedIP = {
  slug: "neon-horizon",
  titleLine1: "Neon Horizon:",
  titleLine2: "The Awakening",
  description:
    "In a city that never sleeps, a rogue AI begins to dream. Follow Kael as he navigates the neon-drenched underworld to uncover the truth about his synthetic origins before the corporation erases his memory forever.",
  descriptionKo:
    "잠들지 않는 도시에서, 불량 AI가 꿈을 꾸기 시작한다. 카엘이 네온 불빛 가득한 언더월드를 헤쳐나가며 기업이 그의 기억을 영원히 지우기 전에 자신의 합성적 기원에 대한 진실을 밝혀내는 여정을 따라가세요.",
  bannerUrl:
    "https://lh3.googleusercontent.com/aida-public/AB6AXuDh2e3UoFCS76v_Zznn9MxmBvQaJyklYFDZbBaI6UWaLtBrvkSxVQOSfTDbNVaX0cJij8j99B6IkOH0_MLfMlraZlyPRnRaY35g62p2Fe3R-yGq81_vnAl8ApHAzCfA3X79StAD67u-A4-DR_a7qo79v8QqKabI5tSUDJOkrj3ar1DGf6NekiqYpIm1BRm9w-yJGN3id3hoUa69Gg5AfkthMK_sMISLHxIrIsXNKIn0RZbHYaG5XLjO7cA22Oe0bJx8HDku_VFzYNg",
  tags: ["Sci-Fi Thriller", "4K HDR"],
  rating: 4.9,
  remixCount: "12,405",
  topStyle: "Cyberpunk Anime",
};

// Variation cards data - exact match to Stitch design with actual image URLs
const VARIATION_CARDS: VariationCard[] = [
  {
    id: "anime-adaptation",
    name: "Anime Adaptation",
    nameKo: "애니메이션 각색",
    description:
      "Reimagine the gritty streets as a high-octane anime series. Focus on exaggerated action sequences and vibrant color palettes.",
    descriptionKo:
      "도시의 거친 거리를 고속 애니메이션 시리즈로 재탄생. 과장된 액션과 생동감 넘치는 색감에 집중합니다.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuA0r2qo4L4VmyuCId41jiXkjFCO1haV7IDSbJhzCT6sPC8I6bFdZoQ5VQLPEsgaDpW2JOJCpwKmN0UJA_6nPVGcahgFpfO173A6v14e7C8XM8-kEdxrM6gZ-TZS4TQt2a7UMte3lDWQcJqLmkD6ngyZQavT8o6TPkBBqKrIbGYOHcD-TeIJ9TEVzGHA_xBxbmGL_EG2quNe5YDycI_3U9pBrWvnSqZuWgsBM8fwrFmuTEI8Fx6RlNSom13VC6oaPwi8ZZK8ku4Ccpg",
    category: "visual",
    categoryIcon: "brush",
    categoryColor: "text-pink-400",
    badge: "V2.0",
    href: "/dimension/visual-realizer",
    isPrimary: true,
  },
  {
    id: "shortform-drama",
    name: "Short-form Drama",
    nameKo: "숏폼 드라마",
    description:
      "Condense the storyline into punchy 60-second vertical episodes optimized for social platforms.",
    descriptionKo:
      "스토리라인을 60초의 세로 에피소드로 압축. 소셜 플랫폼에 최적화된 콘텐츠를 생성합니다.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuB2tBApxBE_y5JRz_79of0LwA_koCjfEHgjOyoZf-2CVrADOm8_JKbNcctgPyf3UtxEJKmBaw3uTQvbxKjduBeL0Z6Mz43TAIAVzOd_qDFhow4m2v6SmhINvJX-47fh4Wvc0_ZBjZnIz-A5jf3Yz3eLMG3bnGw7hbkSBM-RFY59uxEaghM_I1l9Oio_CN263M4wqBXOMEWca2FWIo6VKIj-c_qJbdRoougP0LQ7Imc2xIedTOaaDUzBOsI4rYWLAlrzNUFGovWrQrM",
    category: "video",
    categoryIcon: "movie",
    categoryColor: "text-blue-400",
    badge: "BETA",
    href: "/dimension/video-maker",
  },
  {
    id: "graphic-novel",
    name: "Graphic Novel",
    nameKo: "그래픽 노블",
    description:
      "Generate a full-color graphic novel layout. Extracts key dialogue and creates consistent character art panels.",
    descriptionKo:
      "풀 컬러 그래픽 노블 레이아웃 생성. 핵심 대화를 추출하고 일관된 캐릭터 아트 패널을 만듭니다.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuAEjDABfWSOWoCE8z39Uf9HewzfInWI575WbW6482O4KXOTY4J6Ybhkw-yssBuKTYCIYzZP8WeUtfvQCCnfp6z7jPJblSnyIDsDGoKMtm5csZjfOkyHQr2dG_Aywxj49Dpp_f_mgb98_I5E7DTFWKX7nLFa6FH_9VYSadkBwZ0IuCNBxjWETlsCn_GrcELcuXzy3OTzT1XvbBgvCiYe9l_gSJ8GMJ2foRZh3pI6Fb5CQ5jzeWBLShpIKNYekf2x4rWV60GtVQS9yIA",
    category: "story",
    categoryIcon: "auto_stories",
    categoryColor: "text-yellow-400",
    badge: "V1.5",
    href: "/dimension/storyboard-sketcher",
  },
  {
    id: "immersive-audio",
    name: "Immersive Audio",
    nameKo: "이머시브 오디오",
    description:
      "Convert the script into a 3D binaural audio drama with AI voice actors and generated soundscapes.",
    descriptionKo:
      "스크립트를 3D 바이노럴 오디오 드라마로 변환. AI 성우와 생성된 사운드스케이프를 활용합니다.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuCYZPJFPKgMSdKVU_W3iR-uzF7kSGHOsv3rhcmwdb-TRfrnJZIib_FptEDLGD6MwCRe1cIbPOoWkZhcr54lZc3bateyYL9vgzf-IudGmZv4aTceiquaSXjj8FzpR3pqqtDtPw303Kvoz__-yP3u2u3rNK2Do3dNfBPCNwlZR16hSrXOSx9VcIJJE56EUiMs1T4mJ9TDj8fQBdgLeB9MPSIbRsxzHRfZnYpzlwjn-c6q-9R2Qr8O5ncDux8qhYXzRKSiUmdtDz6RWUk",
    category: "audio",
    categoryIcon: "headphones",
    categoryColor: "text-green-400",
    badge: "V3.1",
    href: "/dimension/sound-crafter",
  },
  {
    id: "interactive-novel",
    name: "Interactive Visual Novel",
    nameKo: "인터랙티브 비주얼 노블",
    description:
      "Create a branching narrative game where users can choose different paths for Kael.",
    descriptionKo:
      "사용자가 카엘의 다양한 경로를 선택할 수 있는 분기형 내러티브 게임을 만듭니다.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuCcUjKInzOtfp5cZifxh65zNNJgO0SHc3gwqrIYN83WKGibsUZxOuzS646dMw8NQYrVJeCY1iUbp-olKPlBnzlfuii2pTXStRq2-9HMGivbpfRQ92rETfQeRL5vi3w0FkA2S5g2YfjHun1F0FkcMduJY9ISG_0m7AlaTpvfn0gc_ZMn499FAUEJ1XDT_kO4H2vherED8sacBwgnPUgDFlSzUu9prPIj7Gb9-kg6tw7Jmurqtbu4lWihBv93ivATNMC135caqdvH25M",
    category: "interactive",
    categoryIcon: "sports_esports",
    categoryColor: "text-purple-400",
    badge: "NEW",
    href: "/dimension/scenario-generator",
  },
];

function HomePageContent() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 font-sans transition-colors duration-300">
      {/* Navigation */}
      <CrebitNavbar />

      {/* Main Content */}
      <main className="relative pt-16">
        {/* Cinematic Hero */}
        <CinematicHero featured={FEATURED_IP} />

        {/* Variations Grid */}
        <VariationsGrid variations={VARIATION_CARDS} />
      </main>

      {/* Footer */}
      <CrebitFooter />

      {/* Mobile FAB */}
      <div className="fixed bottom-6 right-6 z-40 md:hidden">
        <button className="bg-violet-500 text-white p-4 rounded-full shadow-lg shadow-violet-500/40">
          <span className="material-icons-round">menu</span>
        </button>
      </div>
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
