"use client";

/**
 * Characters Gallery Page
 *
 * Browse all AI characters and start conversations
 * Server-side filtering via API
 */

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { MessageCircle, Search, Loader2 } from "lucide-react";
import { api, type HomepageCharacter } from "@/lib/api";

// Fallback character data for when API is unavailable
const FALLBACK_CHARACTERS: HomepageCharacter[] = [
  {
    id: "akari",
    name: "Akari",
    imageUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuDN5xpf62iQyVAxpu6bfMxxxUbBcRwdTWKyxVSWszsqTN31eV3lNWr3ntBTIXhAjJCKXZkUTQqa3EGMRF80TU-gL20v7zBokSFOkWBAsTDF1sbc1ZVFQ9mdz8k7yBCcSho6XXcihaNCoPVzRCdkL4NiFhZDwRx0Kz5naME5XI-yk3VW7t2C2_RlgLPW9xvZ4XUOi8L6hP4pzyuhDSqjwjDdfaFxbpEZl3dpeP0ZGPes6jLYMw8Wtgl9pUvGmoggChFffG4ovuIp3PQ",
    chatCount: "12k",
    quote: "오늘 밤, 네온 사인 아래서 드라이브 어때요?",
    creator: "@neon_dreamer",
    badge: "NEW",
    category: "Cyberpunk",
  },
  {
    id: "eunha",
    name: "Eunha",
    imageUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuAEFUIE-TQP1GnONSNxQtpr031HoEzolGFK2FWaSHqPYsH6fpO5MPtnwQjO1hwcDP5jIRxRI32PLsYs0_r7616VUNOCjAblP58zu6tKWxDImRG1UFotWIZLlfdp7PizcXWOM8DzpgmawyougUuKINa34yP-SWURdtC3teIcKW4b5qZn_vK1s78Vog3DWjDnhk94JdYZlgpdJ-tY_S7h3PlNB3BQ4oKHgpzy_9bmErbhIjGQDjaHRs7DbzYv-w6FmWMvdK_VmyAZGEc",
    chatCount: "8.5k",
    quote: "기억은 데이터일 뿐이야, 하지만 감정은...",
    creator: "@cyber_seoul",
    category: "Sci-Fi",
  },
  {
    id: "soonae",
    name: "순애",
    imageUrl: "/assets/characters/candidates/pure_love.avif",
    chatCount: "18k",
    quote: "시간을 초월하는 순수한 사랑, 그게 나야.",
    creator: "@romance_ai",
    badge: "NEW",
    category: "Romance",
  },
  {
    id: "koko",
    name: "Koko",
    imageUrl: "/assets/characters/candidates/koko.jpg",
    chatCount: "21k",
    quote: "HTML로 세상을 코딩하는 안드로이드, 반가워요!",
    creator: "@android_dev",
    badge: "TOP_RATED",
    category: "Tech",
  },
  {
    id: "mira",
    name: "Mira",
    imageUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuAihzfhGiK-cuyzA7vJ5LoaYLBNwFq9NbSV8MnnXnPBSTJ0XUOVFxAumhkmxbgCj4hsOOIShlq-BklMirnrDFvYeTvnB3PUVYLmx1lWT8zTuEA4uf4IkrxVHaLHnmrzuZVJDuP0wUmowLewq6h6_O5wuJXN4AWq2iiKk1VfwulRt0WdAN-X7cztQf_UHxYLYAg5QEuRhgMoAvRpKYCwNaXCkHnFyBAowBERxVKP441K3b-5P2142Vd1HTvNi5yNOK1cT0dcJPjt21M",
    chatCount: "15k",
    quote: "별빛 아래서 우리의 이야기를 써나가요.",
    creator: "@starlight_story",
    category: "Fantasy",
  },
  {
    id: "haru",
    name: "Haru",
    imageUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuC5QaTGBVcDFzYQmvqdFxg5zg8m7N76grsISsepxva09mAhxwyLWx9xtuTAlX5Rgu3X5zt05t2thp0sLSZUolkH-Tq9Or8bYlIDDmY6s7fFTFgEIy6u_lnBrDDSc-c68xgfCfjX3SjKQdC3CFai9FTXRaQRx39qkjsI0YaYN8_jPaOT2nxeAMsgUn1zS6Y2sHLtm7oa_YNmKKwrRMpyK96vIbkDXJO376o0-Kc4tPYcbuenE8_odv9PdmwC3wLF_Dy5w0FmwdoGNHM",
    chatCount: "9k",
    quote: "매일 새로운 모험이 기다리고 있어!",
    creator: "@adventure_ai",
    category: "Adventure",
  },
];

const CATEGORIES = ["All", "Cyberpunk", "Sci-Fi", "Romance", "Tech", "Fantasy", "Adventure"];

// Debounce hook for search input
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export default function CharactersPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");
  const [characters, setCharacters] = useState<HomepageCharacter[]>(FALLBACK_CHARACTERS);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(FALLBACK_CHARACTERS.length);

  const debouncedSearch = useDebounce(searchQuery, 300);

  // Fetch characters from API with search and filter
  const fetchCharacters = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.listCharacters({
        search: debouncedSearch || undefined,
        category: activeCategory !== "All" ? activeCategory : undefined,
        page: 1,
        pageSize: 20,
      });

      if (response.items.length > 0) {
        setCharacters(response.items);
        setTotal(response.total);
      } else if (!debouncedSearch && activeCategory === "All") {
        // No results and no filters - use fallback
        setCharacters(FALLBACK_CHARACTERS);
        setTotal(FALLBACK_CHARACTERS.length);
      } else {
        // No results with filters - show empty
        setCharacters([]);
        setTotal(0);
      }
    } catch (error) {
      console.warn("Using fallback characters:", error);
      // On error, filter fallback data client-side
      let filtered = FALLBACK_CHARACTERS;
      if (debouncedSearch) {
        const searchLower = debouncedSearch.toLowerCase();
        filtered = filtered.filter(
          (c) =>
            c.name.toLowerCase().includes(searchLower) ||
            c.quote.toLowerCase().includes(searchLower)
        );
      }
      if (activeCategory !== "All") {
        filtered = filtered.filter((c) => c.category === activeCategory);
      }
      setCharacters(filtered);
      setTotal(filtered.length);
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, activeCategory]);

  // Fetch on mount and when filters change
  useEffect(() => {
    fetchCharacters();
  }, [fetchCharacters]);

  const handleCategoryClick = (category: string) => {
    setActiveCategory(category);
  };

  return (
    <main className="min-h-screen bg-[var(--bg-base)] pt-24 pb-16">
      <div className="max-w-7xl mx-auto px-6 md:px-16">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            AI <span className="text-[var(--fg-primary)]">캐릭터</span>
          </h1>
          <p className="text-gray-400 max-w-2xl">
            다양한 AI 캐릭터들과 대화를 나눠보세요. 각 캐릭터는 고유한 성격과 배경을 가지고 있습니다.
          </p>
        </motion.div>

        {/* Search and Filter */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="flex flex-col md:flex-row gap-4 mb-8"
        >
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="text"
              placeholder="캐릭터 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-[var(--bg-subtle)] border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-[var(--border-primary)]/50 transition-colors"
            />
            {loading && (
              <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500 animate-spin" />
            )}
          </div>

          {/* Category Filters */}
          <div className="flex gap-2 flex-wrap">
            {CATEGORIES.map((category) => (
              <button
                key={category}
                onClick={() => handleCategoryClick(category)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  category === activeCategory
                    ? "bg-[var(--bg-primary)] text-white"
                    : "bg-[var(--bg-subtle)] text-gray-400 hover:bg-white/10 hover:text-white border border-white/10"
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </motion.div>

        {/* Results count */}
        {(debouncedSearch || activeCategory !== "All") && (
          <p className="text-gray-500 text-sm mb-4">
            {total}개의 캐릭터
            {debouncedSearch && <span> &quot;{debouncedSearch}&quot; 검색 결과</span>}
          </p>
        )}

        {/* Characters Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {loading ? (
            // Loading skeleton
            [...Array(4)].map((_, index) => (
              <div key={index} className="animate-pulse">
                <div className="bg-[var(--bg-subtle)] border border-gray-800 rounded-xl overflow-hidden">
                  <div className="aspect-[3/4] bg-gray-800" />
                  <div className="p-5">
                    <div className="flex justify-between items-start mb-2">
                      <div className="h-6 bg-gray-800 rounded w-20" />
                      <div className="h-4 bg-gray-800 rounded w-12" />
                    </div>
                    <div className="h-4 bg-gray-800 rounded w-full mb-2" />
                    <div className="h-4 bg-gray-800 rounded w-3/4 mb-4" />
                    <div className="border-t border-white/10 pt-3">
                      <div className="flex justify-between items-center">
                        <div className="h-3 bg-gray-800 rounded w-20" />
                        <div className="h-4 bg-gray-800 rounded w-16" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : characters.length === 0 ? (
            // Empty state
            <div className="col-span-full text-center py-16">
              <p className="text-gray-400 text-lg mb-2">캐릭터를 찾을 수 없습니다</p>
              <p className="text-gray-500 text-sm">
                다른 검색어나 카테고리를 시도해 보세요
              </p>
            </div>
          ) : characters.map((character, index) => (
            <motion.div
              key={character.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + index * 0.05 }}
            >
              <Link href={`/chat/${character.id}`}>
                <div className="group relative bg-[var(--bg-subtle)] border border-gray-800 rounded-xl overflow-hidden hover:border-[var(--border-primary)]/50 transition-all duration-300 cursor-pointer">
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
                        className={`absolute top-3 right-3 backdrop-blur-sm px-2 py-1 rounded text-[10px] font-bold border ${
                          character.badge === "NEW"
                            ? "bg-black/60 text-[var(--fg-primary)] border-[var(--border-primary)]/30"
                            : "bg-[var(--bg-primary)]/20 text-[var(--fg-primary)] border-[var(--border-primary)]/50"
                        }`}
                      >
                        {character.badge === "NEW" ? "NEW" : "TOP RATED"}
                      </div>
                    )}

                    {/* Category */}
                    {character.category && (
                      <div className="absolute top-3 left-3 bg-black/60 backdrop-blur-sm px-2 py-1 rounded text-[10px] font-medium text-gray-300 border border-white/10">
                        {character.category}
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
                      <span className="text-[var(--fg-primary)] text-xs font-medium group-hover:text-white transition-colors">
                        대화하기 &rarr;
                      </span>
                    </div>
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </main>
  );
}
