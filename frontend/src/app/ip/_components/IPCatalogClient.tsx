"use client";

import React, { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Search, Filter, Grid, List, ChevronDown } from "lucide-react";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";
import IPCard from "@/components/ip/IPCard";
import HomeRailSection from "@/components/home/HomeRailSection";

interface IPCatalogItem {
  id: string;
  slug: string;
  name_ko: string;
  name_en: string;
  thumbnail_url: string | null;
  genre: string[];
  tags: string[];
  preset_count: number;
  generation_count: number;
  license_status: "allowed" | "restricted" | "prohibited";
  is_featured: boolean;
}

interface Genre {
  key: string;
  label_ko: string;
  label_en: string;
  count: number;
}

interface HomeRailSection {
  section_id: string;
  title_ko: string;
  title_en: string;
  items: {
    id: string;
    slug: string;
    name_ko: string;
    name_en: string;
    thumbnail_url: string | null;
    license_status: string;
    preset_count: number;
  }[];
  has_more: boolean;
}

export default function IPCatalogClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { language } = useLanguage();

  // State
  const [items, setItems] = useState<IPCatalogItem[]>([]);
  const [genres, setGenres] = useState<Genre[]>([]);
  const [rails, setRails] = useState<HomeRailSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"rail" | "grid">("rail");

  // Filters
  const [searchQuery, setSearchQuery] = useState(searchParams.get("search") || "");
  const [selectedGenre, setSelectedGenre] = useState(searchParams.get("genre") || "");
  const [sortBy, setSortBy] = useState(searchParams.get("sort") || "popular");
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(0);

  // Fetch home rails
  useEffect(() => {
    async function fetchRails() {
      try {
        const response = await fetch("/api/v1/ip/home/rails");
        if (response.ok) {
          const data = await response.json();
          setRails(data.sections || []);
        }
      } catch (err) {
        console.error("Failed to fetch rails:", err);
      }
    }
    fetchRails();
  }, []);

  // Fetch genres
  useEffect(() => {
    async function fetchGenres() {
      try {
        const response = await fetch("/api/v1/ip/genres");
        if (response.ok) {
          const data = await response.json();
          setGenres(data.genres || []);
        }
      } catch (err) {
        console.error("Failed to fetch genres:", err);
      }
    }
    fetchGenres();
  }, []);

  // Fetch IP catalog
  useEffect(() => {
    async function fetchCatalog() {
      setLoading(true);
      setError(null);

      try {
        const params = new URLSearchParams();
        params.set("page", page.toString());
        params.set("page_size", "20");
        params.set("sort_by", sortBy);
        if (searchQuery) params.set("search", searchQuery);
        if (selectedGenre) params.set("genre", selectedGenre);

        const response = await fetch("/api/v1/ip/catalog?" + params.toString());
        if (!response.ok) {
          throw new Error("Failed to fetch catalog");
        }

        const data = await response.json();
        setItems(data.items || []);
        setTotal(data.total || 0);
        setHasMore(data.has_more || false);
      } catch (err) {
        setError("Failed to load IP catalog");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchCatalog();
  }, [page, sortBy, searchQuery, selectedGenre]);

  const handleItemClick = (item: { slug: string }) => {
    router.push("/ip/" + item.slug);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    // URL update would happen here in production
  };

  return (
    <AppShell showTopBar={false}>
      <div className="min-h-screen bg-white dark:bg-slate-950">
        {/* Header */}
        <div className="border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/80 backdrop-blur-xl sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                  {language === "ko" ? "IP 갤러리" : "IP Gallery"}
                </h1>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                  {language === "ko"
                    ? "좋아하는 IP로 AI 팬 창작물을 만들어보세요"
                    : "Create AI fan content with your favorite IPs"}
                </p>
              </div>

              {/* View toggle */}
              <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
                <button
                  onClick={() => setViewMode("rail")}
                  className={"p-2 rounded " + (viewMode === "rail" ? "bg-white dark:bg-slate-700 shadow-sm" : "")}
                  aria-label="Rail view"
                >
                  <List className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode("grid")}
                  className={"p-2 rounded " + (viewMode === "grid" ? "bg-white dark:bg-slate-700 shadow-sm" : "")}
                  aria-label="Grid view"
                >
                  <Grid className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Search and filters */}
            <div className="flex items-center gap-4 mt-4">
              <form onSubmit={handleSearch} className="flex-1 max-w-md">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="search"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder={language === "ko" ? "IP 검색..." : "Search IPs..."}
                    className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
                  />
                </div>
              </form>

              {/* Genre filter */}
              <div className="relative">
                <select
                  value={selectedGenre}
                  onChange={(e) => {
                    setSelectedGenre(e.target.value);
                    setPage(1);
                  }}
                  className="appearance-none pl-4 pr-10 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
                >
                  <option value="">{language === "ko" ? "모든 장르" : "All Genres"}</option>
                  {genres.map((genre) => (
                    <option key={genre.key} value={genre.key}>
                      {language === "ko" ? genre.label_ko : genre.label_en} ({genre.count})
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              </div>

              {/* Sort */}
              <div className="relative">
                <select
                  value={sortBy}
                  onChange={(e) => {
                    setSortBy(e.target.value);
                    setPage(1);
                  }}
                  className="appearance-none pl-4 pr-10 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
                >
                  <option value="popular">{language === "ko" ? "인기순" : "Popular"}</option>
                  <option value="new">{language === "ko" ? "최신순" : "Newest"}</option>
                  <option value="name">{language === "ko" ? "이름순" : "Name"}</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-7xl mx-auto py-6">
          {viewMode === "rail" ? (
            // Rail View
            <div className="space-y-8">
              {rails.map((section) => (
                <HomeRailSection
                  key={section.section_id}
                  sectionId={section.section_id}
                  titleKo={section.title_ko}
                  titleEn={section.title_en}
                  items={section.items.map((item) => ({
                    ...item,
                    license_status: item.license_status as "allowed" | "restricted" | "prohibited",
                  }))}
                  hasMore={section.has_more}
                  onSeeMore={() => {
                    // Could filter by genre or show more
                    setViewMode("grid");
                  }}
                  onItemClick={handleItemClick}
                />
              ))}

              {/* All IPs section */}
              {items.length > 0 && (
                <div className="px-4">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                    {language === "ko" ? "전체 IP" : "All IPs"}
                  </h2>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                    {items.map((item) => (
                      <IPCard
                        key={item.id}
                        id={item.id}
                        slug={item.slug}
                        nameKo={item.name_ko}
                        nameEn={item.name_en}
                        thumbnailUrl={item.thumbnail_url}
                        genre={item.genre}
                        tags={item.tags}
                        presetCount={item.preset_count}
                        generationCount={item.generation_count}
                        licenseStatus={item.license_status}
                        isFeatured={item.is_featured}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            // Grid View
            <div className="px-4">
              {loading ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                  {Array.from({ length: 10 }).map((_, i) => (
                    <div key={i} className="animate-pulse">
                      <div className="w-full h-64 rounded-xl bg-slate-200 dark:bg-slate-800 mb-2" />
                      <div className="h-4 w-3/4 rounded bg-slate-200 dark:bg-slate-800 mb-1" />
                      <div className="h-3 w-1/2 rounded bg-slate-200 dark:bg-slate-800" />
                    </div>
                  ))}
                </div>
              ) : error ? (
                <div className="text-center py-12">
                  <p className="text-red-500">{error}</p>
                  <button
                    onClick={() => window.location.reload()}
                    className="mt-4 px-4 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700"
                  >
                    {language === "ko" ? "다시 시도" : "Try Again"}
                  </button>
                </div>
              ) : items.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-4xl mb-4">🎬</div>
                  <h3 className="text-lg font-medium text-slate-900 dark:text-white">
                    {language === "ko" ? "IP를 찾을 수 없습니다" : "No IPs found"}
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400 mt-1">
                    {language === "ko" ? "다른 검색어를 시도해보세요" : "Try a different search"}
                  </p>
                </div>
              ) : (
                <>
                  <div className="mb-4 text-sm text-slate-600 dark:text-slate-400">
                    {language === "ko"
                      ? total + "개의 IP"
                      : total + " IPs"}
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                    {items.map((item) => (
                      <IPCard
                        key={item.id}
                        id={item.id}
                        slug={item.slug}
                        nameKo={item.name_ko}
                        nameEn={item.name_en}
                        thumbnailUrl={item.thumbnail_url}
                        genre={item.genre}
                        tags={item.tags}
                        presetCount={item.preset_count}
                        generationCount={item.generation_count}
                        licenseStatus={item.license_status}
                        isFeatured={item.is_featured}
                      />
                    ))}
                  </div>

                  {/* Load more */}
                  {hasMore && (
                    <div className="text-center mt-8">
                      <button
                        onClick={() => setPage((p) => p + 1)}
                        className="px-6 py-2 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                      >
                        {language === "ko" ? "더 보기" : "Load More"}
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
