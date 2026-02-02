"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, PromptyTemplate } from "@/lib/api";

const CATEGORIES = [
  { id: "", label: "전체" },
  { id: "video", label: "영상" },
  { id: "image", label: "이미지" },
  { id: "audio", label: "오디오" },
  { id: "social", label: "소셜" },
];

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<PromptyTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 12;

  useEffect(() => {
    loadTemplates();
  }, [category, page]);

  async function loadTemplates() {
    setLoading(true);
    try {
      const response = await api.listPromptyTemplates(page, pageSize, {
        category: category || undefined,
        search: search || undefined,
      });
      setTemplates(response.items);
      setTotal(response.total);
    } catch (error) {
      console.error("Failed to load templates:", error);
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    loadTemplates();
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold">템플릿 마켓플레이스</h1>
        <p className="text-muted-foreground mt-1">
          검증된 워크플로우로 바로 시작하세요
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4 mb-8">
        {/* Category Tabs */}
        <div className="flex gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => {
                setCategory(cat.id);
                setPage(1);
              }}
              className={`px-4 py-2 rounded-lg transition ${
                category === cat.id
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted hover:bg-muted/80"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="flex-1 max-w-md">
          <div className="relative">
            <input
              type="text"
              placeholder="템플릿 검색..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-4 py-2 bg-muted rounded-lg pl-10"
            />
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
              🔍
            </span>
          </div>
        </form>
      </div>

      {/* Templates Grid */}
      {loading ? (
        <div className="grid md:grid-cols-3 lg:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-64 rounded-xl bg-muted animate-pulse" />
          ))}
        </div>
      ) : templates.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-6xl mb-4">🔍</div>
          <h2 className="text-xl font-semibold mb-2">템플릿이 없습니다</h2>
          <p className="text-muted-foreground">
            {search
              ? "검색어를 변경해 보세요"
              : "아직 등록된 템플릿이 없습니다"}
          </p>
        </div>
      ) : (
        <>
          <div className="grid md:grid-cols-3 lg:grid-cols-4 gap-6">
            {templates.map((template) => (
              <Link
                key={template.id}
                href={`/prompty/templates/${template.id}`}
                className="group block rounded-xl border border-border bg-card overflow-hidden hover:border-primary/50 transition"
              >
                {/* Thumbnail */}
                <div className="aspect-video bg-muted relative">
                  {template.thumbnail_url ? (
                    <img
                      src={template.thumbnail_url}
                      alt={template.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-4xl">
                      {getCategoryEmoji(template.category)}
                    </div>
                  )}
                  {template.is_featured && (
                    <span className="absolute top-2 right-2 px-2 py-1 bg-primary text-primary-foreground text-xs rounded">
                      추천
                    </span>
                  )}
                </div>

                {/* Info */}
                <div className="p-4">
                  <h3 className="font-semibold mb-1 group-hover:text-primary transition line-clamp-1">
                    {template.title}
                  </h3>
                  <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                    {template.description}
                  </p>

                  {/* Tags */}
                  {template.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {template.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 bg-muted text-xs rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Stats */}
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{template.use_count} 사용</span>
                    <span>★ {template.rating_avg.toFixed(1)}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-8">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 rounded-lg bg-muted hover:bg-muted/80 disabled:opacity-50 transition"
              >
                이전
              </button>
              <span className="px-4 py-2">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 rounded-lg bg-muted hover:bg-muted/80 disabled:opacity-50 transition"
              >
                다음
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function getCategoryEmoji(category: string): string {
  const emojis: Record<string, string> = {
    video: "🎬",
    image: "🖼️",
    audio: "🎵",
    social: "📱",
    marketing: "📈",
  };
  return emojis[category] || "📄";
}
