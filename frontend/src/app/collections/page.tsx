"use client";

import { motion } from "framer-motion";
import {
    FolderOpen,
    Plus,
    Star,
    MoreVertical,
    Edit2,
    Share2,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";

interface Collection {
    id: string;
    name: string;
    description: string;
    itemCount: number;
    isStarred: boolean;
    updatedAt: string;
}

export default function CollectionsPage() {
    const { language } = useLanguage();
    const collections: Collection[] =
        language === "ko"
            ? [
                  {
                      id: "col-1",
                      name: "내 즐겨찾기",
                      description: "저장한 패턴과 템플릿",
                      itemCount: 12,
                      isStarred: true,
                      updatedAt: "2025-12-24",
                  },
                  {
                      id: "col-2",
                      name: "영화 스타일",
                      description: "감독 스타일 분석",
                      itemCount: 6,
                      isStarred: false,
                      updatedAt: "2025-12-23",
                  },
                  {
                      id: "col-3",
                      name: "숏폼 콘텐츠",
                      description: "유튜브 쇼츠 패턴",
                      itemCount: 8,
                      isStarred: false,
                      updatedAt: "2025-12-22",
                  },
              ]
            : [
                  {
                      id: "col-1",
                      name: "My Favorites",
                      description: "Saved patterns and templates",
                      itemCount: 12,
                      isStarred: true,
                      updatedAt: "2025-12-24",
                  },
                  {
                      id: "col-2",
                      name: "Film Styles",
                      description: "Director style analysis",
                      itemCount: 6,
                      isStarred: false,
                      updatedAt: "2025-12-23",
                  },
                  {
                      id: "col-3",
                      name: "Short-form Content",
                      description: "YouTube Shorts patterns",
                      itemCount: 8,
                      isStarred: false,
                      updatedAt: "2025-12-22",
                  },
              ];

    const labels = {
        title: language === "ko" ? "컬렉션" : "Collections",
        subtitle: language === "ko" ? "패턴과 참조 자료를 정리하세요" : "Organize your patterns and references",
        newCollection: language === "ko" ? "새 컬렉션" : "New Collection",
        createCollection: language === "ko" ? "컬렉션 만들기" : "Create Collection",
        items: language === "ko" ? "개 항목" : "items",
        starred: language === "ko" ? "즐겨찾기" : "Starred",
        moreOptions: language === "ko" ? "더보기" : "More options",
        editCollection: language === "ko" ? "컬렉션 편집" : "Edit collection",
        shareCollection: language === "ko" ? "컬렉션 공유" : "Share collection",
    };

    return (
        <AppShell showTopBar={false}>
            <div className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
                <div className="mx-auto max-w-4xl">
                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-6 flex flex-col gap-4 sm:mb-8 sm:flex-row sm:items-center sm:justify-between"
                    >
                        <div>
                            <h1 className="text-xl font-bold text-[var(--fg-0)] sm:text-2xl">{labels.title}</h1>
                            <p className="mt-1 text-sm text-[var(--fg-muted)] sm:text-base">{labels.subtitle}</p>
                        </div>
                        <button
                            className="flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-sky-500 to-sky-600 px-4 py-2 font-semibold text-white shadow-lg shadow-sky-500/25 transition-all hover:from-sky-400 hover:to-sky-500"
                            aria-label={labels.newCollection}
                        >
                            <Plus className="h-4 w-4" aria-hidden="true" />
                            {labels.newCollection}
                        </button>
                    </motion.div>

                    {/* Collections Grid */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="grid gap-3 sm:grid-cols-2 sm:gap-4 lg:grid-cols-3"
                        role="list"
                        aria-label={labels.title}
                    >
                        {collections.map((collection, index) => (
                            <motion.article
                                key={collection.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.15 + index * 0.05 }}
                                className="group relative cursor-pointer rounded-lg border border-white/10 bg-slate-950/60 p-4 transition-all hover:border-white/20 sm:rounded-xl sm:p-5"
                                role="listitem"
                            >
                                {/* Header */}
                                <div className="flex items-start justify-between">
                                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--accent)]/10 sm:h-10 sm:w-10">
                                        <FolderOpen className="h-4 w-4 text-[var(--accent)] sm:h-5 sm:w-5" aria-hidden="true" />
                                    </div>
                                    <div className="flex items-center gap-1">
                                        {collection.isStarred && (
                                            <Star
                                                className="h-4 w-4 fill-amber-400 text-amber-400"
                                                aria-label={labels.starred}
                                            />
                                        )}
                                        <button
                                            className="rounded-lg p-1 text-[var(--fg-muted)] opacity-0 transition-all group-hover:opacity-100 hover:bg-white/10"
                                            aria-label={labels.moreOptions}
                                        >
                                            <MoreVertical className="h-4 w-4" aria-hidden="true" />
                                        </button>
                                    </div>
                                </div>

                                {/* Content */}
                                <div className="mt-3 sm:mt-4">
                                    <h3 className="font-semibold text-[var(--fg-0)] group-hover:text-white transition-colors">
                                        {collection.name}
                                    </h3>
                                    <p className="mt-1 text-xs text-[var(--fg-muted)] line-clamp-2 sm:text-sm">
                                        {collection.description}
                                    </p>
                                </div>

                                {/* Footer */}
                                <div className="mt-3 flex items-center justify-between text-[10px] text-[var(--fg-muted)] sm:mt-4 sm:text-xs">
                                    <span>{collection.itemCount} {labels.items}</span>
                                    <span>{collection.updatedAt}</span>
                                </div>

                                {/* Hover Actions */}
                                <div className="absolute bottom-4 right-4 flex gap-1 opacity-0 transition-all group-hover:opacity-100 sm:bottom-5 sm:right-5">
                                    <button
                                        className="rounded-lg bg-white/5 p-2 text-[var(--fg-muted)] hover:bg-white/10 hover:text-[var(--fg-0)]"
                                        aria-label={labels.editCollection}
                                    >
                                        <Edit2 className="h-3 w-3" aria-hidden="true" />
                                    </button>
                                    <button
                                        className="rounded-lg bg-white/5 p-2 text-[var(--fg-muted)] hover:bg-white/10 hover:text-[var(--fg-0)]"
                                        aria-label={labels.shareCollection}
                                    >
                                        <Share2 className="h-3 w-3" aria-hidden="true" />
                                    </button>
                                </div>
                            </motion.article>
                        ))}

                        {/* Empty State / Add New */}
                        <motion.button
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3 }}
                            className="flex min-h-[140px] flex-col items-center justify-center rounded-lg border border-dashed border-white/20 bg-white/5 transition-all hover:border-white/30 hover:bg-white/10 sm:min-h-[160px] sm:rounded-xl"
                            aria-label={labels.createCollection}
                        >
                            <Plus className="h-6 w-6 text-[var(--fg-muted)] sm:h-8 sm:w-8" aria-hidden="true" />
                            <span className="mt-2 text-xs text-[var(--fg-muted)] sm:text-sm">
                                {labels.createCollection}
                            </span>
                        </motion.button>
                    </motion.div>
                </div>
            </div>
        </AppShell>
    );
}
