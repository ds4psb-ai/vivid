"use client";

/**
 * Crebit Home Page - Stitch V2 Cinematic AI OTT Experience
 *
 * Deep charcoal theme with neon red accents
 * Split hero layout with character model card
 * Bento box variations grid
 * Featured characters + Masters touch + Human Cloud CTA
 *
 * API-connected homepage with graceful fallbacks
 */

import React, { Suspense, useState, useEffect } from "react";
import { CrebitNavbar } from "@/components/home/CrebitNavbar";
import { CinematicHero, FeaturedIP } from "@/components/home/CinematicHero";
import { MegaAppShowcase } from "@/components/home/MegaAppShowcase";
import { VariationsGrid, VariationCard } from "@/components/home/VariationsGrid";
import { FeaturedCharacters, Character, DEFAULT_CHARACTERS } from "@/components/home/FeaturedCharacters";
import { AIDirectorSection } from "@/components/home/AIDirectorSection";
import { UserCinemaSection, CinemaCard } from "@/components/home/UserCinemaSection";
import { HumanCloudCTA, Creator, DEFAULT_CREATORS } from "@/components/home/HumanCloudCTA";
import { CrebitFooter } from "@/components/home/CrebitFooter";
import { api, type HomepageFeaturedIP, type HomepageCharacter, type HomepageCinemaCard, type HomepageCreator } from "@/lib/api";

// Featured IP data - Stitch V2 Neon Red design
const FEATURED_IP: FeaturedIP = {
  slug: "neon-horizon",
  title: "NEON",
  titleAccent: "HORIZON",
  description:
    "잠들지 않는 도시에서, 이단 AI가 꿈을 꾸기 시작합니다. 당신의 기억이 지워지기 전에 합성된 진실을 밝혀내세요.",
  bannerUrl:
    "https://lh3.googleusercontent.com/aida-public/AB6AXuAnK4vWkCZjrOPWwMEwuJ0km4m8lqtIFwhUKg1REgmZyY5i9xLX3f-0C3U3caIjYYL0EY7zr0_TuMwG4hSbxBUVCLDMNdm6l241-FenheSVYCdrI8w8KIeXS3v4UgTHeg9UwJiM2pBaX_Mk-IqEQuOBJv70c3nN2zf9k6Pk0XBs7VjoAFv07GZc2VxmGhNk3Y4To7R0IB9w2tyC2sMilOgnpEMAMotqozzHfufSs234LzjzB9gByd-GQiBOB0_NHW9FMlqiRwEd4RE",
  tags: ["시즌 1", "2042"],
  rating: 4.9,
  remixCount: "12K",
  matchPercent: 98,
  character: {
    name: "아카리",
    description: "네온 사인 아래 밤 드라이브를 즐기는 감성 AI. 도시의 불빛 속에서 당신과 함께합니다.",
    status: "캐릭터 모델 준비 완료",
    imageUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuDN5xpf62iQyVAxpu6bfMxxxUbBcRwdTWKyxVSWszsqTN31eV3lNWr3ntBTIXhAjJCKXZkUTQqa3EGMRF80TU-gL20v7zBokSFOkWBAsTDF1sbc1ZVFQ9mdz8k7yBCcSho6XXcihaNCoPVzRCdkL4NiFhZDwRx0Kz5naME5XI-yk3VW7t2C2_RlgLPW9xvZ4XUOi8L6hP4pzyuhDSqjwjDdfaFxbpEZl3dpeP0ZGPes6jLYMw8Wtgl9pUvGmoggChFffG4ovuIp3PQ",
  },
};

// Variation cards data - Bento box layout with Crebit dimension mapping
const VARIATION_CARDS: VariationCard[] = [
  {
    id: "anime-adaptation",
    name: "Anime Adaptation",
    description:
      "Reimagine the gritty streets as a high-octane anime series with vibrant color palettes.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuA0r2qo4L4VmyuCId41jiXkjFCO1haV7IDSbJhzCT6sPC8I6bFdZoQ5VQLPEsgaDpW2JOJCpwKmN0UJA_6nPVGcahgFpfO173A6v14e7C8XM8-kEdxrM6gZ-TZS4TQt2a7UMte3lDWQcJqLmkD6ngyZQavT8o6TPkBBqKrIbGYOHcD-TeIJ9TEVzGHA_xBxbmGL_EG2quNe5YDycI_3U9pBrWvnSqZuWgsBM8fwrFmuTEI8Fx6RlNSom13VC6oaPwi8ZZK8ku4Ccpg",
    category: "visual",
    badge: "VISUAL STYLE",
    badgeColor: "bg-red-600",
    href: "/dimension/visual-realizer",
    layout: "tall",
  },
  {
    id: "shortform-drama",
    name: "Short-form Drama",
    description:
      "Punchy 60-second vertical episodes optimized for viral social platforms.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuB2tBApxBE_y5JRz_79of0LwA_koCjfEHgjOyoZf-2CVrADOm8_JKbNcctgPyf3UtxEJKmBaw3uTQvbxKjduBeL0Z6Mz43TAIAVzOd_qDFhow4m2v6SmhINvJX-47fh4Wvc0_ZBjZnIz-A5jf3Yz3eLMG3bnGw7hbkSBM-RFY59uxEaghM_I1l9Oio_CN263M4wqBXOMEWca2FWIo6VKIj-c_qJbdRoougP0LQ7Imc2xIedTOaaDUzBOsI4rYWLAlrzNUFGovWrQrM",
    category: "video",
    badge: "FORMAT",
    badgeColor: "bg-blue-600",
    href: "/dimension/video-maker",
    layout: "wide",
  },
  {
    id: "interactive-game",
    name: "Interactive Game",
    description:
      "Create a branching narrative game where users can choose different paths.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuCcUjKInzOtfp5cZifxh65zNNJgO0SHc3gwqrIYN83WKGibsUZxOuzS646dMw8NQYrVJeCY1iUbp-olKPlBnzlfuii2pTXStRq2-9HMGivbpfRQ92rETfQeRL5vi3w0FkA2S5g2YfjHun1F0FkcMduJY9ISG_0m7AlaTpvfn0gc_ZMn499FAUEJ1XDT_kO4H2vherED8sacBwgnPUgDFlSzUu9prPIj7Gb9-kg6tw7Jmurqtbu4lWihBv93ivATNMC135caqdvH25M",
    category: "interactive",
    href: "/dimension/story-architect",
    layout: "normal",
  },
  {
    id: "graphic-novel",
    name: "Graphic Novel",
    description:
      "Generate a full-color graphic novel layout with consistent character art panels.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuAEjDABfWSOWoCE8z39Uf9HewzfInWI575WbW6482O4KXOTY4J6Ybhkw-yssBuKTYCIYzZP8WeUtfvQCCnfp6z7jPJblSnyIDsDGoKMtm5csZjfOkyHQr2dG_Aywxj49Dpp_f_mgb98_I5E7DTFWKX7nLFa6FH_9VYSadkBwZ0IuCNBxjWETlsCn_GrcELcuXzy3OTzT1XvbBgvCiYe9l_gSJ8GMJ2foRZh3pI6Fb5CQ5jzeWBLShpIKNYekf2x4rWV60GtVQS9yIA",
    category: "story",
    href: "/dimension/storyboard",
    layout: "normal",
  },
  {
    id: "3d-audio",
    name: "3D Audio",
    description:
      "Convert the script into a 3D binaural audio drama with AI voice actors.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuCYZPJFPKgMSdKVU_W3iR-uzF7kSGHOsv3rhcmwdb-TRfrnJZIib_FptEDLGD6MwCRe1cIbPOoWkZhcr54lZc3bateyYL9vgzf-IudGmZv4aTceiquaSXjj8FzpR3pqqtDtPw303Kvoz__-yP3u2u3rNK2Do3dNfBPCNwlZR16hSrXOSx9VcIJJE56EUiMs1T4mJ9TDj8fQBdgLeB9MPSIbRsxzHRfZnYpzlwjn-c6q-9R2Qr8O5ncDux8qhYXzRKSiUmdtDz6RWUk",
    category: "audio",
    href: "/dimension/sound-crafter",
    layout: "normal",
  },
];

// Interface for homepage data state
interface HomepageData {
  featured: FeaturedIP | null;
  characters: Character[] | null;
  cinema: CinemaCard[] | null;
  cinemaTotal: number;
  creators: Creator[] | null;
}

// Transform API response to component format
// API returns snake_case, convert to camelCase for component
function transformFeatured(data: HomepageFeaturedIP): FeaturedIP {
  // Cast to any to access snake_case properties from API
  const raw = data as any;
  return {
    slug: raw.slug,
    title: raw.title,
    titleAccent: raw.title_accent || raw.titleAccent || "",
    description: raw.description,
    bannerUrl: raw.banner_url || raw.bannerUrl || "",
    tags: raw.tags || [],
    rating: raw.rating || 0,
    remixCount: raw.remix_count || raw.remixCount || "0",
    matchPercent: raw.match_percent || raw.matchPercent || 0,
    character: raw.character ? {
      name: raw.character.name,
      description: raw.character.description,
      status: raw.character.status,
      imageUrl: raw.character.image_url || raw.character.imageUrl || "",
    } : undefined,
  };
}

function transformCharacters(data: HomepageCharacter[]): Character[] {
  return data.map((c) => {
    const raw = c as any;
    return {
      id: raw.id,
      name: raw.name,
      imageUrl: raw.image_url || raw.imageUrl || "",
      chatCount: raw.chat_count || raw.chatCount || "0",
      quote: raw.quote,
      creator: raw.creator,
      badge: raw.badge,
    };
  });
}

function transformCinema(data: HomepageCinemaCard[]): CinemaCard[] {
  return data.map((c) => {
    const raw = c as any;
    return {
      id: raw.id,
      title: raw.title,
      description: raw.description,
      thumbnailUrl: raw.thumbnail_url || raw.thumbnailUrl || "",
      duration: raw.duration,
      category: raw.category,
      categoryColor: raw.category_color || raw.categoryColor || "",
      creator: {
        name: raw.creator?.name || "",
        avatarUrl: raw.creator?.avatar_url || raw.creator?.avatarUrl || "",
      },
      views: raw.views,
      likePercent: raw.like_percent || raw.likePercent || 0,
    };
  });
}

function transformCreators(data: HomepageCreator[]): Creator[] {
  return data.map((c) => {
    const raw = c as any;
    return {
      id: raw.id,
      initial: raw.initial,
      name: raw.name,
      specialty: raw.specialty,
      specialtyColor: raw.specialty_color || raw.specialtyColor || "",
      rating: raw.rating || 0,
      description: raw.description,
    };
  });
}

function HomePageContent() {
  const [data, setData] = useState<HomepageData>({
    featured: null,
    characters: null,
    cinema: null,
    cinemaTotal: 12, // Default count
    creators: null,
  });
  const [loading, setLoading] = useState({
    featured: true,
    characters: true,
    cinema: true,
    creators: true,
  });

  // Fetch homepage data on mount
  useEffect(() => {
    async function fetchData() {
      // Fetch all data in parallel
      const [featuredResult, charactersResult, cinemaResult, creatorsResult] = await Promise.allSettled([
        api.getHomepageFeatured(),
        api.getHomepageCharacters(4),
        api.getHomepageCinema(3),
        api.getHomepageCreators(3),
      ]);

      // Process featured
      if (featuredResult.status === "fulfilled") {
        setData((prev) => ({
          ...prev,
          featured: transformFeatured(featuredResult.value),
        }));
      }
      setLoading((prev) => ({ ...prev, featured: false }));

      // Process characters
      if (charactersResult.status === "fulfilled" && charactersResult.value.length > 0) {
        setData((prev) => ({
          ...prev,
          characters: transformCharacters(charactersResult.value),
        }));
      }
      setLoading((prev) => ({ ...prev, characters: false }));

      // Process cinema
      if (cinemaResult.status === "fulfilled" && cinemaResult.value.length > 0) {
        setData((prev) => ({
          ...prev,
          cinema: transformCinema(cinemaResult.value),
          cinemaTotal: cinemaResult.value.length > 0 ? 12 : 3, // TODO: Get actual count from API
        }));
      }
      setLoading((prev) => ({ ...prev, cinema: false }));

      // Process creators
      if (creatorsResult.status === "fulfilled" && creatorsResult.value.length > 0) {
        setData((prev) => ({
          ...prev,
          creators: transformCreators(creatorsResult.value),
        }));
      }
      setLoading((prev) => ({ ...prev, creators: false }));
    }

    fetchData();
  }, []);

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--fg-default)] font-sans selection:bg-[var(--bg-primary)] selection:text-white overflow-x-hidden">
      {/* Navigation - transparent overlay on hero */}
      <CrebitNavbar transparent showSpacer={false} />

      {/* Main Content */}
      <main className="relative w-full min-h-screen pb-20">
        {/* 1. Cinematic Hero */}
        <CinematicHero featured={data.featured ?? FEATURED_IP} />

        {/* 2. User AI Cinema & Animation */}
        <UserCinemaSection
          cards={data.cinema ?? undefined}
          totalCount={data.cinemaTotal}
          loading={loading.cinema}
        />

        {/* 3. Mega App Showcase - 창작 워크플로우 */}
        <MegaAppShowcase />

        {/* 4. Variations Grid - 가능한 변형 */}
        <VariationsGrid variations={VARIATION_CARDS} />

        {/* 5. Featured Characters - 추천 캐릭터 */}
        <FeaturedCharacters
          characters={data.characters ?? undefined}
          loading={loading.characters}
        />

        {/* 6. AI Director Section - AI 디렉터 */}
        <AIDirectorSection />

        {/* 7. Human Cloud CTA */}
        <HumanCloudCTA
          creators={data.creators ?? undefined}
          loading={loading.creators}
        />
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
        <div className="min-h-screen flex items-center justify-center bg-[var(--bg-base)]">
          <div className="flex flex-col items-center gap-4">
            <div className="w-10 h-10 bg-[var(--fg-default)] text-[var(--bg-base)] font-display font-bold text-xl flex items-center justify-center rounded-sm animate-pulse">
              C
            </div>
            <div className="h-1 w-24 bg-gray-800 rounded-full overflow-hidden">
              <div className="h-full w-1/2 bg-[var(--bg-primary)] rounded-full animate-pulse" />
            </div>
          </div>
        </div>
      }
    >
      <HomePageContent />
    </Suspense>
  );
}
